# frontend/insider_threat_page.py

import sqlite3
import sys
import json
import math
from pathlib import Path
from datetime import datetime
from collections import defaultdict
from auth.app_paths import get_logs_dir

from PyQt6.QtWidgets import (
    QApplication, QDialog, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QCheckBox as _QCheckBox,
    QPushButton, QScrollArea, QSizePolicy, QGridLayout, QSizePolicy, QLineEdit, QStackedWidget, 
)
from PyQt6.QtCore import Qt, QTimer, QRect, QSize, pyqtSignal 
from PyQt6.QtGui import (
    QPalette, QColor, QPainter, QPen, QBrush, QFont, QLinearGradient, QConicalGradient, QCursor 
)

# ── Colors 
from .nova_style import (
    BG_MAIN, BG_CARD, BG_CARD2, BG_ROW, CYAN, CYAN_DIM, BG_TOPBAR, BG_SIDEBAR, BG_MODULE, BORDER, TEXT_WHITE, TEXT_MUTED, TEXT_SUB,
    RED, ORANGE, GREEN, YELLOW, BLUE
)

DB_PATH     = get_logs_dir() / "novasphere.db"
ALERT_JSONL = get_logs_dir() / "alerts.jsonl"

# ── DB helpers 

def _conn():
    if DB_PATH.exists():
        try:
            return sqlite3.connect(DB_PATH, check_same_thread=False, timeout=5)
        except Exception:
            pass
    return None


def _load_alerts() -> list:
    alerts = []
    c = _conn()
    if c:
        try:
            cur = c.cursor()
            cur.execute("""
                SELECT timestamp, alert_type, severity, message, file_path, source
                FROM alerts ORDER BY rowid DESC LIMIT 300
            """)
            for r in cur.fetchall():
                alerts.append({
                    "timestamp": r[0], "alert_type": r[1],
                    "severity": r[2],  "message": r[3],
                    "file_path": r[4] or "", "source": r[5] or "",
                })
            c.close()
        except Exception:
            pass
    if not alerts and ALERT_JSONL.exists():
        try:
            with open(ALERT_JSONL, encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line:
                        try:
                            alerts.append(json.loads(line))
                        except Exception:
                            pass
        except Exception:
            pass
    return alerts


def _load_events(limit=500) -> list:
    events = []
    c = _conn()
    if c:
        try:
            cur = c.cursor()
            cur.execute(
                "SELECT timestamp, event_type, file_path, username "
                "FROM events ORDER BY rowid DESC LIMIT ?", (limit,)
            )
            for r in cur.fetchall():
                events.append({
                    "timestamp": r[0], "event_type": r[1],
                    "file_path": r[2] or "", "username": r[3] or "unknown",
                })
            c.close()
        except Exception:
            pass
    return events


def _risk_scores(alerts, default_user="System"):
    scores, counts = defaultdict(int), defaultdict(int)
    for a in alerts:
        u = a.get("username") or default_user
        if isinstance(u, dict):
            u = default_user
        counts[u] += 1
        scores[u] += {"CRITICAL": 25, "HIGH": 15, "MEDIUM": 8, "LOW": 3}.get(
            a.get("severity", "LOW"), 3
        )
    result = [(u, min(scores[u], 99), counts[u]) for u in scores]
    result.sort(key=lambda x: x[1], reverse=True)
    return result[:5]


def _events_by_day(rows):
    """Accepts either events or alerts list. Maps each to its weekday slot."""
    day_counts = defaultdict(int)
    today = datetime.now().date()
    for e in rows:
        try:
            d = datetime.strptime(e["timestamp"], "%Y-%m-%d %H:%M:%S").date()
            delta = (today - d).days
            if 0 <= delta < 7:
                weekday = d.weekday()   # 0=Mon … 6=Sun, matches DAYS labels
                day_counts[weekday] += 1
        except Exception:
            pass
    return [day_counts[i] for i in range(7)]


def _hourly_counts(events):
    """Returns list of 24 counts (normal, suspicious) per hour.
    Falls back to alerts if events table is empty."""
    normal = [0] * 24
    suspicious = [0] * 24
    rows = events if events else []

    for e in rows:
        try:
            h = datetime.strptime(e["timestamp"], "%Y-%m-%d %H:%M:%S").hour
            sev = e.get("severity", "")
            etype = e.get("event_type", "")

            if sev in ("eCRITICAL", "HIGH") or etype == "MODIFIED":
                suspicious[h] += 1
            else:
                normal[h] += 1
        except Exception:
            pass
    return normal, suspicious

def _severity_breakdown(alerts):
    """Returns real counts per severity for the donut chart."""
    counts = {"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0}
    for a in alerts:
        sev = (a.get("severity") or "LOW").upper()
        if sev in counts:
            counts[sev] += 1
        else:
            counts["LOW"] += 1
    return counts

# ── Severity badge ────────────────────────────────────────────────────────────

def _badge(text: str, color: str) -> QLabel:
    b = QLabel(text)
    b.setFixedWidth(160) #the card size of recent suspicious activities.
    b.setAlignment(Qt.AlignmentFlag.AlignCenter)
    b.setStyleSheet(
        f" color:{color}; background:transparent; "
        f" border-radius: 2px; font-size: 10px; font-weight: 800; padding:1px 0;"
    )
    return b


# ── Section card ──────────────────────────────────────────────────────────────

def _card(title: str, sub: str = "") -> tuple:
    f = QFrame()
    f.setStyleSheet(
        f"QFrame {{background: {BG_CARD}; border:1px; border-radius:14px }}"
    )
    lay = QVBoxLayout(f)
    lay.setContentsMargins(20, 15, 20, 20)
    lay.setSpacing(8)
    lay.setAlignment(Qt.AlignmentFlag.AlignTop)
    if title:
        t = QLabel(title)
        t.setStyleSheet(
            f"color:{TEXT_WHITE}; font-size:15px; font-weight:700; background:transparent;"
        )
        lay.addWidget(t)
    if sub:
        s = QLabel(sub)
        s.setStyleSheet(f" color:{TEXT_MUTED}; font-size:12px; background:transparent;")
        lay.addWidget(s)
    return f, lay


# ── Bar chart (7-day) ─────────────────────────────────────────────────────────

class BarChart(QWidget):
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._data = [0] * 30
        self.setMinimumHeight(175)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

    def set_data(self, v):
        padded = list(v) + [0] * (30 - len(v))
        self._data = padded[:30]
        self.update()

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        W, H = self.width(), self.height()
        PL, PR, PB, PT = 8, 8, 26, 8
        CW = W - PL - PR
        CH = H - PB - PT
        mx = max(self._data) or 1
        n = len(self._data)
        bw = CW // n

        for i, v in enumerate(self._data):
            bh = int((v / mx) * CH)
            x = PL + i * bw + max(bw // 6, 1)
            y = PT + CH - bh
            fw = max(bw * 2 // 3, 2)
            grad = QLinearGradient(x, y, x, y + bh)
            grad.setColorAt(0, QColor(CYAN))
            grad.setColorAt(1, QColor("#003d4a"))
            p.setBrush(QBrush(grad))
            p.setPen(Qt.PenStyle.NoPen)
            if bh > 0:
                p.drawRoundedRect(x, y, fw, bh, 3, 3)

            p.setPen(QPen(QColor(TEXT_MUTED)))
            p.setFont(QFont("Segoe UI", 8))
            from datetime import datetime, timedelta
            today = datetime.now()
            for j in range(0, n, 5):
                lbl = (today - timedelta(days=j)).strftime("%d %b")
                try:
                    lbl = (today - timedelta(days=j)).strftime("%d %b")
                except:
                    lbl = f"-{j}d"
                p.drawText(
                    QRect(PL + j * bw, H - PB + 4, bw * 5, 20),
                    Qt.AlignmentFlag.AlignLeft, lbl
                )
        p.end()


#  Login attempts mini chart (24h) 

class LoginChart(QWidget):
    LABELS = ["00:00", "04:00", "08:00", "12:00", "16:00", "20:00"]

    def __init__(self, parent=None):
        super().__init__(parent)
        self._normal = [0] * 24
        self._susp   = [0] * 24
        self.setFixedHeight(110)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

    def set_data(self, normal, suspicious):
        self._normal = normal
        self._susp   = suspicious
        self.update()

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        W, H = self.width(), self.height()
        PL, PR, PB, PT = 4, 4, 24, 4
        CW = W - PL - PR
        CH = H - PB - PT
        mx = max(max(self._normal), max(self._susp), 1)
        bw = CW // 24

        for i in range(24):
            # Normal bar
            nh = int((self._normal[i] / mx) * CH)
            nx = PL + i * bw
            p.setBrush(QBrush(QColor("#1a3a4a")))
            p.setPen(Qt.PenStyle.NoPen)
            if nh > 0:
                p.drawRoundedRect(nx, PT + CH - nh, max(bw - 1, 2), nh, 1, 1)
            # Suspicious bar
            sh = int((self._susp[i] / mx) * CH)
            if sh > 0:
                p.setBrush(QBrush(QColor(RED)))
                p.drawRoundedRect(nx, PT + CH - sh, max(bw - 1, 2), sh, 1, 1)

        # X labels
        p.setPen(QPen(QColor(TEXT_MUTED)))
        p.setFont(QFont("Segoe UI", 7))
        for i, lbl in enumerate(self.LABELS):
            x = PL + i * 4 * bw
            p.drawText(QRect(x - 15, H - PB + 4, 40, 18),
                       Qt.AlignmentFlag.AlignCenter, lbl)
        p.end()


#  Donut chart (risk distribution) 

class DonutChart(QWidget):
    def __init__(self, score: int = 0, parent=None):
        super().__init__(parent)
        self._score = score
        # (critical, high, medium, low) raw counts — starts empty
        self._counts = {"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0}
        self.setFixedSize(150, 150)

    def set_score(self, s: int):
        self._score = s
        self.update()

    def set_breakdown(self, counts: dict):
        """counts: dict like {'CRITICAL': n, 'HIGH': n, 'MEDIUM': n, 'LOW': n}"""
        self._counts = counts
        self.update()

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        cx = cy = self.width() // 2
        R = 58
        thick = 35

        total = sum(self._counts.values())

        if total == 0:
            # No data yet — draw a neutral empty ring instead of a fake split
            pen = QPen(QColor(BORDER), thick)
            pen.setCapStyle(Qt.PenCapStyle.FlatCap)
            p.setPen(pen)
            p.setBrush(Qt.BrushStyle.NoBrush)
            p.drawArc(cx - R, cy - R, R * 2, R * 2, 0, 360 * 16)
        else:
            order = [("CRITICAL", RED), ("HIGH", ORANGE), ("MEDIUM", YELLOW), ("LOW", BLUE)]
            start = -90
            for key, color in order:
                pct = self._counts.get(key, 0) / total
                if pct <= 0:
                    continue
                span = int(pct * 360)
                pen = QPen(QColor(color), thick)
                pen.setCapStyle(Qt.PenCapStyle.FlatCap)
                p.setPen(pen)
                p.setBrush(Qt.BrushStyle.NoBrush)
                p.drawArc(cx - R, cy - R, R * 2, R * 2, start * 16, span * 16)
                start += span

        # Center text
        p.setPen(QPen(QColor(TEXT_WHITE)))
        p.setFont(QFont("Segoe UI", 25, QFont.Weight.Bold))
        p.drawText(QRect(cx - 30, cy - 18, 60, 28),
                   Qt.AlignmentFlag.AlignCenter, str(self._score))
        p.setPen(QPen(QColor(TEXT_MUTED)))
        p.setFont(QFont("Segoe UI", 10))
        p.drawText(QRect(cx - 20, cy + 8, 40, 16),
                   Qt.AlignmentFlag.AlignCenter, "RISK")
        p.end()

#  Activity table row 

def _activity_row(user, action, target, severity) -> QWidget:
    w = QWidget()
    w.setFixedHeight(44)
    w.setStyleSheet(
        f"QWidget{{background:{BG_ROW};border-radius:1px;}}"
        f"QWidget:hover{{background:{BG_CARD2};}}"
    )
    lay = QHBoxLayout(w)
    lay.setContentsMargins(14, 0, 14, 0)
    lay.setSpacing(0)

    color = {"CRITICAL": RED, "HIGH": ORANGE, "MEDIUM": YELLOW, "LOW": GREEN}.get(
        severity, TEXT_MUTED
    )

    user_lbl = QLabel(user or "System")
    user_lbl.setStyleSheet(
        f"color:{TEXT_WHITE}; font-size:13px; background:transparent;"
    )
    user_lbl.setFixedWidth(150)

    action_lbl = QLabel(action)
    action_lbl.setStyleSheet(
        f"color:{TEXT_SUB}; font-size:13px; background:transparent;"
    )
    action_lbl.setFixedWidth(200)

    target_str = target[-30:] if len(target) > 30 else target
    target_lbl = QLabel(target_str or "—")
    target_lbl.setStyleSheet(
        f"color:{TEXT_MUTED}; font-size:12px; background:transparent;"
    )

    badge = _badge(severity, color)

    lay.addWidget(user_lbl)
    lay.addWidget(action_lbl)
    lay.addWidget(target_lbl, 1)
    lay.addWidget(badge)
    return w


def _table_header() -> QWidget:
    w = QWidget()
    w.setFixedHeight(40)
    w.setStyleSheet(f" background: {BG_CARD2}; border-radius: 4px;")
    lay = QHBoxLayout(w)
    lay.setContentsMargins(8, 0, 8, 0)
    lay.setSpacing(0)
    for col, width in [("USER", 180), ("ACTION", 180), ("TARGET", 140), ("RISK", 100)]:
        lbl = QLabel(col)
        lbl.setStyleSheet(
            f"color:{TEXT_MUTED};font-size:10px;font-weight:700;"
            f"letter-spacing:0.5px;background:transparent;"
        )
        if width:
            lbl.setFixedWidth(width)
        lay.addWidget(lbl, 0 if width else 1)
    return w


def _alert_to_row(a: dict, default_user="System") -> tuple:
    """Convert an alert dict to (user, action, target, severity)."""
    alert_type = a.get("alert_type", "UNKNOWN")
    severity   = a.get("severity", "LOW")
    file_path  = a.get("file_path") or a.get("trigger_path") or ""
    username   = a.get("username") or default_user
    if isinstance(username, dict):
        username = default_user

    action_map = {
        "RAPID_FILE_ACTIVITY":    "Rapid File Activity",
        "INSIDER_THREAT_PROCESS": "Suspicious Process",
        "RANSOMWARE_PROCESS_NAME":"Ransomware Process",
        "RANSOMWARE_CMDLINE":     "Malicious Command",
        "RANSOMWARE_CPU_SPIKE":   "CPU Spike",
        "SUSPICIOUS_PROCESS":     "Suspicious Process",
        "MASS_DELETE":            "Mass Delete",
        "MASS_RENAME":            "Mass Rename",
    }
    action = action_map.get(alert_type, alert_type.replace("_", " ").title())
    target = Path(file_path).name if file_path else a.get("cmdline", "")[:30] or "—"
    return username, action, target, severity

class RiskBar(QWidget):
    clicked = pyqtSignal(str, int, int)
    def __init__(self, username, score, count, role="", parent=None):
        super().__init__(parent)
        self._username = username
        self._score    = score
        self._count    = count
        self.setFixedHeight(60)
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        color = RED if score >= 80 else ORANGE if score >= 60 else YELLOW if score >= 40 else GREEN

        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 2, 0, 2)
        lay.setSpacing(5)

        top = QHBoxLayout()
        initials = "".join(w[0].upper() for w in username.split()[:2]) or "?"
        av = QLabel(initials)
        av.setFixedSize(35, 35)
        av.setAlignment(Qt.AlignmentFlag.AlignCenter)
        av.setStyleSheet(
            f"background:{BORDER};color:{TEXT_WHITE};border-radius:5px;"
            f"font-size:12px;font-weight:800;"
        )
        name_lbl = QLabel(username)
        name_lbl.setStyleSheet(
            f"color:{TEXT_WHITE}; font-size:13px; font-weight:700; background:transparent;"
        )
        # ADDED: role label under name

        role_lbl = QLabel(role or "System User")
        role_lbl.setStyleSheet(
            f"color:{TEXT_MUTED};font-size:10px;background:transparent;"
        )
        name_col = QVBoxLayout()
        name_col.setSpacing(1)
        name_col.addWidget(name_lbl)
        name_col.addWidget(role_lbl)

        score_col = QVBoxLayout()
        score_col.setAlignment(Qt.AlignmentFlag.AlignRight)
        score_lbl = QLabel(str(score))
        score_lbl.setStyleSheet(
            f"color:{color};font-size:16px;font-weight:800;background:transparent;"
        )
        score_sub = QLabel("RISK SCORE")
        score_sub.setStyleSheet(
            f"color:{TEXT_MUTED};font-size:8px;background:transparent;"
        )
        score_col.addWidget(score_lbl)
        score_col.addWidget(score_sub)

        top.addWidget(av)
        top.addSpacing(8)
        top.addLayout(name_col)
        top.addStretch()
        top.addLayout(score_col)
        lay.addLayout(top)

        bar_bg = QFrame()
        bar_bg.setFixedHeight(5)
        bar_bg.setStyleSheet(f"background: {BORDER}; border-radius:1px;")
        bar_lay = QHBoxLayout(bar_bg)
        bar_lay.setContentsMargins(0, 0, 0, 0)
        fill_w = max(int((score / 100) * 260), 4)
        bar_fill = QFrame()
        bar_fill.setFixedHeight(5)
        bar_fill.setStyleSheet(
            f"background:{color};border-radius:2px;"
            f"min-width:{fill_w}px;max-width:{fill_w}px;"
        )
        bar_lay.addWidget(bar_fill)
        bar_lay.addStretch()
        lay.addWidget(bar_bg)

    #emit clicked signal when user clicks this row
    def mousePressEvent(self, event):
        self.clicked.emit(self._username, self._score, self._count)


#  Target profile panel 

class TargetProfile(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet(
            f"QFrame{{background:{BG_CARD}; border:1px; border-radius:14px;}}"
        )
        self.setFixedWidth(250)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(14, 14, 14, 14)
        lay.setSpacing(8)

        hdr = QLabel("TARGET PROFILE")
        hdr.setStyleSheet(
            f"color:{TEXT_MUTED}; font-size:10px; font-weight:700;"
            f"letter-spacing:1px; background:transparent;"
        )
        hdr.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lay.addWidget(hdr)

        self._avatar = QLabel("?")
        self._avatar.setFixedSize(64, 64)
        self._avatar.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._avatar.setStyleSheet(
            f"color:{TEXT_WHITE}; border-radius:20px;"
            f"font-size:15px;font-weight:700;"
        )
        lay.addWidget(self._avatar, alignment=Qt.AlignmentFlag.AlignHCenter)

        self._name = QLabel("No alerts yet")
        self._name.setStyleSheet(
            f"color:{TEXT_WHITE}; font-size:15px; font-weight:700; background:transparent;"
        )
        self._name.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        self._name.setWordWrap(True)
        lay.addWidget(self._name)

        self._role = QLabel("")
        self._role.setStyleSheet(
            f"color:{TEXT_MUTED}; font-size:12px; font-weight: 500; background:transparent;"
        )
        self._role.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        lay.addWidget(self._role)

        # Unusual hours
        sep1 = QFrame()
        sep1.setFixedHeight(1)
        sep1.setStyleSheet(f"background:{BORDER};")
        lay.addWidget(sep1)

        uh_row = QHBoxLayout()
        uh_lbl = QLabel("Unusual Hours")
        uh_lbl.setStyleSheet(
            f"color:{TEXT_WHITE}; font-size:12px; background:transparent;"
        )
        self._uh_val = QLabel("—")
        self._uh_val.setStyleSheet(
            f"color:{CYAN}; font-size:12px; font-weight:700; background:transparent;"
        )
        uh_row.addWidget(uh_lbl)
        uh_row.addStretch()
        uh_row.addWidget(self._uh_val)
        lay.addLayout(uh_row)

        self._uh_sub = QLabel("")
        self._uh_sub.setStyleSheet(
            f"color:{TEXT_MUTED}; font-size:11px; background:transparent;"
        )
        self._uh_sub.setWordWrap(True)
        lay.addWidget(self._uh_sub)

        # Alert count
        sep2 = QFrame()
        sep2.setFixedHeight(1)
        sep2.setStyleSheet(f"background:{BORDER};")
        lay.addWidget(sep2)

        ac_row = QHBoxLayout()
        ac_lbl = QLabel("Alert Count")
        ac_lbl.setStyleSheet(
            f"color: {TEXT_WHITE}; font-size:12px; background:transparent;"
        )
        self._ac_val = QLabel("0")
        self._ac_val.setStyleSheet(
            f"color:{RED}; font-size:12px; font-weight:700; font-align=center; background:transparent;"
        )
        ac_row.addWidget(ac_lbl)
        ac_row.addStretch()
        ac_row.addWidget(self._ac_val)
        lay.addLayout(ac_row)

        lay.addStretch()

    def update_profile(self, username: str, count: int):
        initials = "".join(w[0].upper() for w in username.split()[:2]) or "?"
        self._avatar.setText(initials)
        self._name.setText(username)
        self._role.setText("Monitored User")
        self._ac_val.setText(str(count))
        # Check if any alerts were off-hours
        h = datetime.now().hour
        if h >= 22 or h < 6:
            self._uh_val.setText("Detected")
            self._uh_sub.setText(f"Current time ({h:02d}:00) is outside business hours")
        else:
            self._uh_val.setText("Normal")
            self._uh_sub.setText("Access within business hours")

 
def placeholder(title, icon):
    w = QWidget()
    lay = QVBoxLayout(w); lay.setAlignment(Qt.AlignmentFlag.AlignCenter)
    l = QLabel(f"{icon}  {title}")
    l.setStyleSheet(f"color:{TEXT_MUTED};font-size:22px;background:transparent;")
    l.setAlignment(Qt.AlignmentFlag.AlignCenter)
    s = QLabel("This section is under development")
    s.setStyleSheet(f"font-size:13px;background:transparent;")
    s.setAlignment(Qt.AlignmentFlag.AlignCenter)
    lay.addWidget(l); lay.addSpacing(8); lay.addWidget(s)
    return w

class FiltersDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Filter Alerts")
        self.setFixedSize(300, 280)
        self.setModal(True)
        self.setStyleSheet(f"""
            QDialog {{ background: {BG_CARD}; }}
            QLabel {{ background: transparent; color: {TEXT_WHITE}; }}
            QCheckBox {{ color: {TEXT_WHITE}; font-size: 13px; spacing: 8px; background: transparent; }}
            QCheckBox::indicator {{ width:16px; height:16px; border:1px solid {BORDER}; border-radius:3px; background:{BG_MAIN}; }}
            QCheckBox::indicator:checked {{ background:{CYAN}; border-color:{CYAN}; }}
        """)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(24, 20, 24, 20)
        lay.setSpacing(12)

        lay.addWidget(QLabel("Filter by Severity"))

        self._checks = {}
        for sev in ("CRITICAL", "HIGH", "MEDIUM", "LOW"):
            cb = _QCheckBox(sev.title())
            cb.setChecked(True)
            self._checks[sev] = cb
            lay.addWidget(cb)

        lay.addSpacing(8)
        lay.addWidget(QLabel("Date Range"))
        from PyQt6.QtWidgets import QComboBox
        self._date_combo = QComboBox()
        self._date_combo.addItems(["Last 24 Hours", "Last 7 Days", "Last 30 Days", "All Time"])
        self._date_combo.setStyleSheet(f"""
            QComboBox {{ background:{BG_MAIN}; border:1px solid {BORDER};
                border-radius:6px; color:{TEXT_WHITE}; font-size:13px; padding:6px 10px; }}
            QComboBox QAbstractItemView {{ background:{BG_MAIN}; color:{TEXT_WHITE};
                selection-background-color:{CYAN}; }}
        """)
        lay.addWidget(self._date_combo)
        lay.addStretch()

        apply_btn = QPushButton("Apply Filters")
        apply_btn.setStyleSheet(f"""
            QPushButton {{ background:{CYAN}; border:none; border-radius:8px;
                color:#000; font-size:13px; font-weight:700; padding:10px; }}
            QPushButton:hover {{ background:#00d4f0; }}
        """)
        apply_btn.clicked.connect(self.accept)
        lay.addWidget(apply_btn)

    def get_filters(self) -> dict:
        return {
            "severities": [s for s, cb in self._checks.items() if cb.isChecked()],
            "date_range": self._date_combo.currentText(),
        }
    
#  Main page 

class InsiderThreatPage(QWidget):
    def __init__(self, parent=None, current_user="System"):
        super().__init__(parent)
        self._current_user     = current_user or "System"
        self._risk_container   = None
        self._chart            = None
        self._login_chart      = None
        self._donut            = None
        self._activity_layout  = None
        self._target_profile   = None
        self._stat_labels      = {}

        self._last_alert_count = -1
        self._last_event_count = -1
        self._last_file_size = 0

        self._build_ui()
        self._refresh()

        self._timer = QTimer(self)
        self._timer.timeout.connect(self._refresh)
        self._timer.start(3000)
        self._last_file_size = 0

        self._active_filters = {"severities": ["CRITICAL", "HIGH", "MEDIUM", "LOW"], "data_range": "All Time"}

        self._file_timer = QTimer(self)
        self._file_timer.timeout.connect(self._check_file_changed)
        self._file_timer.start(1000)

    def _build_ui(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        outer.addWidget(scroll)

        content = QWidget()
        scroll.setWidget(content)
        root = QVBoxLayout(content)
        root.setContentsMargins(24, 18, 24, 24)
        root.setSpacing(14)
        root.setAlignment(Qt.AlignmentFlag.AlignTop)

        #Header
        hdr = QHBoxLayout()
        tc = QVBoxLayout(); tc.setSpacing(2)
        t1 = QLabel("Insider Threat Monitoring")
        t1.setStyleSheet(
            f"color:{TEXT_WHITE};font-size:20px;font-weight:700;background:transparent;"
        )
        t2 = QLabel("Behavioral analytics and anomaly detection for internal accounts")
        t2.setStyleSheet(f"color:{TEXT_MUTED};font-size:13px;background:transparent;")
        tc.addWidget(t1); tc.addWidget(t2)
        hdr.addLayout(tc)
        hdr.addStretch()

        #search bar
        self._search = QLineEdit()
        self._search.setPlaceholderText("Search user or event...")
        self._search.setFixedHeight(34)
        self._search.setFixedWidth(220)
        self._search.setStyleSheet(f"""
            QLineEdit {{
                background: #111827;
                border: 1px solid {BORDER};
                border-radius: 6px;
                color: {TEXT_WHITE};
                font-size: 12px;
                padding: 0 10px;
            }}
            QLineEdit:focus {{ border: 1px solid {CYAN}; }}
        """)
        self._search.textChanged.connect(self._filter_activity)

        #filters button
        flt_btn = QPushButton("󰁊  Filters")
        flt_btn.setFixedHeight(34)
        flt_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        flt_btn.setStyleSheet(f"""
            QPushButton {{
                background: {BG_CARD2};
                border: 1px solid {BORDER};
                border-radius: 6px;
                color: {CYAN};
                font-size: 12px;
                padding: 0 14px;
            }}
            QPushButton:hover {{ border-color: {CYAN}; }}
        """)
        flt_btn.clicked.connect(self._show_filters)


        #refresh button stays too
        ref = QPushButton("󰑐 Refresh")
        ref.setFixedHeight(34)
        ref.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        ref.setStyleSheet(f"""
            QPushButton {{
                background: {BG_CARD2};
                border: 1px solid {BORDER};
                border-radius: 6px;
                color: {TEXT_MUTED};
                font-size: 12px;
                padding: 0 12px;
            }}
            QPushButton:hover {{ border-color: {CYAN}; color: {CYAN}; }}
        """)
        ref.clicked.connect(self._refresh)

        hdr.addWidget(self._search)
        hdr.addSpacing(8)
        hdr.addWidget(flt_btn)
        hdr.addSpacing(8)
        hdr.addWidget(ref)
        root.addLayout(hdr)

        # ── Stats row
        sr = QHBoxLayout(); sr.setSpacing(10)
        for key, icon, lbl, color in [
            ("total",    "󰀦", "Total Alerts",  CYAN),
            ("critical", "󰻌", "Critical",       RED),
            ("users",    "󰀄", "Users Flagged",  ORANGE),
            ("events",   "󰧮", "Events Logged",  GREEN),
        ]:
            f = QFrame()
            f.setStyleSheet(
                f"QFrame{{background:{BG_CARD};border:1px; border-radius:14px;}}"
            )
            f.setFixedHeight(100)
            fl = QVBoxLayout(f); fl.setContentsMargins(14,8,14,8); fl.setSpacing(2)
            fl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            top = QHBoxLayout()
            il = QLabel(icon)
            il.setStyleSheet(f"font-size:25px;background:transparent;")
            il.setAlignment(Qt.AlignmentFlag.AlignCenter)
            top.addWidget(il); top.addStretch()
            fl.addLayout(top)
            vl = QLabel("0")
            vl.setStyleSheet(
                f"color:{TEXT_WHITE};font-size:26px;font-weight:800;background:transparent;"
            )
            ll = QLabel(lbl.upper())
            ll.setStyleSheet(
                f"color:{TEXT_MUTED};font-size:10px;letter-spacing:1px;background:transparent;"
            )
            fl.addWidget(vl); fl.addWidget(ll)
            self._stat_labels[key] = vl
            sr.addWidget(f)
        root.addLayout(sr)

        # ── Middle: Risk | Chart | Right panel
        mid = QHBoxLayout(); mid.setSpacing(12)

        # Left: High Risk Users
        risk_card, risk_lay = _card(" 󰀪  High Risk Users", "Scored by severity × frequency")
        risk_card.setFixedWidth(280)
        self._risk_container = QVBoxLayout()
        self._risk_container.setSpacing(4)
        self._risk_container.setAlignment(Qt.AlignmentFlag.AlignTop)
        risk_lay.addLayout(self._risk_container)
        mid.addWidget(risk_card)

        # Centre: chart + activity table
        centre = QVBoxLayout(); centre.setSpacing(12)
        chart_card, chart_lay = _card(
            "󰺑 File Access Anomalies",
            "Volume of file events over last 7 days"
        )
        self._chart = BarChart()
        chart_lay.addWidget(self._chart)
        centre.addWidget(chart_card)

        act_card, act_lay = _card(" 󱇏  Recent Suspicious Activity")
        act_lay.addWidget(_table_header())
        self._activity_layout = QVBoxLayout(); self._activity_layout.setSpacing(3)
        act_lay.addLayout(self._activity_layout)
        centre.addWidget(act_card)
        mid.addLayout(centre, 1)

        # Right panel
        right = QVBoxLayout(); right.setSpacing(12)
        self._target_profile = TargetProfile()
        right.addWidget(self._target_profile)

        lc_card, lc_lay = _card(" 󰕮  LOGIN ATTEMPTS (24H)")
        self._login_chart = LoginChart()
        lc_lay.addWidget(self._login_chart)
        leg = QHBoxLayout()
        for dot, txt in [(BORDER, "Normal"), (RED, "Suspicious")]:
            dl = QLabel("●")
            dl.setStyleSheet(f"color:{dot};font-size:8px;background:transparent;")
            tl = QLabel(txt)
            tl.setStyleSheet(f"color:{TEXT_MUTED};font-size:9px;background:transparent;")
            leg.addWidget(dl); leg.addWidget(tl); leg.addSpacing(8)
        leg.addStretch()
        lc_lay.addLayout(leg)
        right.addWidget(lc_card)

        rd_card, rd_lay = _card("RISK DISTRIBUTION")
        self._donut = DonutChart(0)
        rd_lay.addWidget(self._donut, alignment=Qt.AlignmentFlag.AlignHCenter)
        right.addWidget(rd_card)
        right.addStretch()

        mid.addLayout(right)
        root.addLayout(mid)
    
    def _check_file_changed(self):
        """Triggers refresh immediately when alerts.jsonl file size changes."""
        try:
            current_size = ALERT_JSONL.stat().st_size if ALERT_JSONL.exists() else 0
            if current_size != self._last_file_size:
                self._last_file_size = current_size
                self._last_alert_count = -1
                self._refresh()
        except Exception as e:
            print(f"[file_check_error] {e}")
    
    def _filter_activity(self, text:str):
        text = text.lower()
        alerts = _load_alerts()
        if text:
            alerts= [
                a for a in alerts
                if text in (a.get("source") or "").lower()
                or text in (a.get("alert_type") or "").lower()
                or text in (a.get("file_path") or "").lower()
                or text in (a.get("message") or "").lower()
            ]
        self._clear(self._activity_layout)
        if alerts:
            for a in alerts[:15]:
                u, action, target, sev = _alert_to_row(a, self._current_user)
                self._activity_layout.addWidget(
                    _activity_row(u, action, target, sev)
                )
            self._activity_layout.addStretch()
        else:
            empty = QLabel("No results match your search.")
            empty.setStyleSheet(
                f"color{TEXT_MUTED}; font-size: 12px;"
                f"background: transparent; padding: 16px 0;"
            )
            self._activity_layout.addWidget(empty)
            self._activity_layout.addStretch()

    def _nav(self, idx):
        self._pages.setCurrentIndex(idx)
        for i,b in enumerate(self._btns):
            b.setProperty("active","true" if i==idx else "false")
            b.style().unpolish(b); b.style().polish(b)

    def _toggle_sb(self):
        self._sb_vis = not self._sb_vis
        self._sb.setVisible(self._sb_vis)
        self._col_btn.setText("›" if not self._sb_vis else "‹")

    def _signout(self):
        try:
            from frontend.login import MainWindow
            self.hide(); self._lw = MainWindow(); self._lw.show()
        except ImportError:
            self.close()

    def _clear(self, layout):
        while layout.count():
            item = layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
    
    def _show_filters(self):
        dlg = FiltersDialog(self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            self._active_filters = dlg.get_filters()
            self._apply_filters_to_table()

    def _apply_filters_to_table(self):
        alerts = _load_alerts()
        sevs = self._active_filters.get("severities", [])
        alerts = [a for a in alerts if a.get("severity", "LOW") in sevs]
        self._clear(self._activity_layout)
        for a in alerts[:15]:
            u, action, target, sev = _alert_to_row(a, self._current_user)
            self._activity_layout.addWidget(_activity_row(u, action, target, sev))
        self._activity_layout.addStretch()
    
    def _refresh(self):
        alerts = _load_alerts()
        events = _load_events()

        #only update UI if new data came in — avoids unnecessary redraws
        new_alert_count = len(alerts)
        new_event_count = len(events)
        first_load = (self._last_alert_count == 0 and self._last_event_count == 0)
        data_changed = (
            self._last_alert_count == -1 or
            new_alert_count != self._last_alert_count or
            new_event_count != self._last_event_count or
            new_alert_count == 0
        )
        self._last_alert_count = new_alert_count
        self._last_event_count = new_event_count

        #always update stat numbers even if no change
        total    = new_alert_count
        critical = sum(1 for a in alerts if a.get("severity") in ("CRITICAL", "HIGH"))
        users    = len(set(
            (a.get("username") or "System") for a in alerts
            if not isinstance(a.get("username"), dict)
        ))

        self._stat_labels["total"].setText(str(total))
        self._stat_labels["critical"].setText(str(critical))
        self._stat_labels["users"].setText(str(users))
        self._stat_labels["events"].setText(str(new_event_count))

        #only rebuild heavy widgets if data actually changed
        if not data_changed:
            return

        # Risk bars
        self._clear(self._risk_container)
        scores = _risk_scores(alerts, self._current_user)
        if scores:
            for u, s, c in scores:
                bar = RiskBar(u, s, c)
                bar.clicked.connect(self._on_user_clicked)
                self._risk_container.addWidget(bar)
            self._target_profile.update_profile(scores[0][0], scores[0][2])
            self._donut.set_score(scores[0][1])
            self._donut.set_breakdown(_severity_breakdown(alerts))
        else:
            nl = QLabel(" 󰗠  No threats detected")
            nl.setStyleSheet(
                f"color:{GREEN};font-size:12px;background:transparent;"
            )
            self._risk_container.addWidget(nl)
            self._donut.set_breakdown({"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0})
        
        self._risk_container.addStretch()

        # Charts
        chart_rows = events if events else alerts
        self._chart.set_data(_events_by_day(chart_rows))
        normal, susp = _hourly_counts(chart_rows)
        self._login_chart.set_data(normal, susp)

        # Activity table
        self._clear(self._activity_layout)
        if alerts:
            for a in alerts[:15]:
                u, action, target, sev = _alert_to_row(a, self._current_user)
                self._activity_layout.addWidget(
                    _activity_row(u, action, target, sev)
                )
            self._activity_layout.addStretch()
        else:
            el = QLabel(" 󰗠  No alerts — system is clean")
            el.setStyleSheet(
                f"color:{GREEN};font-size:12px;"
                f"background:transparent;padding:10px 0;"
            )
            self._activity_layout.addWidget(el)
            self._activity_layout.addStretch()
            
    def _on_user_clicked(self, username: str, score: int, count: int):
        self._target_profile.update_profile(username, count)
        self._donut.set_score(score)

    def reload(self):
        """Refresh immediately when the user opens this dashboard page."""
        self._refresh()


def main():
    app = QApplication(sys.argv)
    palette = QPalette()
    palette.setColor(QPalette.ColorRole.Window,     QColor("#0b0f1a"))
    palette.setColor(QPalette.ColorRole.WindowText, QColor("#e8eaf0"))
    app.setPalette(palette)
    app.setStyleSheet(
        "* { font-family: 'Segoe UI', sans-serif; }"
        "QWidget { background: #0b0f1a; color: #e8eaf0; }"
        "QScrollArea { border: none; background: transparent; }"
        "QScrollBar:vertical { background: #0b0f1a; width: 5px; }"
        "QScrollBar::handle:vertical { background: #1e2d45; border-radius: 2px; }"
    )
    win = QMainWindow()
    win.setWindowTitle("Insider Threat — Test")
    win.setMinimumSize(1300, 800)
    win.setCentralWidget(InsiderThreatPage())
    win.show()
    sys.exit(app.exec())
    

if __name__ == "__main__":
    main()


