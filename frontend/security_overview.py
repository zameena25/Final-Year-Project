# security_overview.py
# Security Overview / Dashboard page
# Connect in dash.py:
#   from security_overview import SecurityOverviewPage
#   items = [("  ⊞  Dashboard", SecurityOverviewPage(scan_callback=self._go_to_scan_page)), ...]

import sqlite3
import math
import random
from datetime import datetime, timedelta
from pathlib import Path
from collections import defaultdict

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QPushButton, QScrollArea, QSizePolicy, QCheckBox,QStackedWidget
)
from PyQt6.QtCore import Qt, QTimer, QRect, QPropertyAnimation, QEasingCurve
from PyQt6.QtGui import (
    QColor, QPainter, QPen, QBrush, QFont, QLinearGradient, QCursor
)
from scan import ScanPage

# ── Colors ────────────────────────────────────────────────────────────────────
BG_MAIN    = "#0b0f1a"
BG_CARD    = "#131929"
BG_CARD2   = "#161e30"
BG_STATUS  = "#0a1f1a"
CYAN       = "#00bcd4"
BORDER     = "#1e2d45"
TEXT_WHITE = "#e8eaf0"
TEXT_MUTED = "#4a5a78"
TEXT_SUB   = "#6b7a99"
RED        = "#ff4757"
ORANGE     = "#ffa726"
GREEN      = "#26de81"
YELLOW     = "#fed330"
BLUE       = "#4fc3f7"

DB_PATH     = Path("logs/novasphere.db")
ALERT_JSONL = Path("logs/alerts.jsonl")


# ── DB helpers ────────────────────────────────────────────────────────────────

def _conn():
    if DB_PATH.exists():
        try:
            return sqlite3.connect(DB_PATH, check_same_thread=False)
        except Exception:
            pass
    return None


def _load_alerts():
    alerts = []
    c = _conn()
    if c:
        try:
            cur = c.cursor()
            cur.execute("SELECT timestamp, alert_type, severity, message, file_path, source FROM alerts ORDER BY rowid DESC LIMIT 500")
            for r in cur.fetchall():
                alerts.append({"timestamp": r[0], "alert_type": r[1], "severity": r[2], "message": r[3], "file_path": r[4] or "", "source": r[5] or ""})
            c.close()
        except Exception:
            pass
    if not alerts and ALERT_JSONL.exists():
        try:
            import json
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


def _load_events(limit=500):
    events = []
    c = _conn()
    if c:
        try:
            cur = c.cursor()
            cur.execute("SELECT timestamp, event_type, file_path, username FROM events ORDER BY rowid DESC LIMIT ?", (limit,))
            for r in cur.fetchall():
                events.append({"timestamp": r[0], "event_type": r[1], "file_path": r[2] or "", "username": r[3] or "unknown"})
            c.close()
        except Exception:
            pass
    return events


def _user_risk_scores(alerts):
    scores, counts = defaultdict(int), defaultdict(int)
    for a in alerts:
        u = a.get("username") or "System"
        if isinstance(u, dict):
            u = "System"
        counts[u] += 1
        scores[u] += {"CRITICAL": 25, "HIGH": 15, "MEDIUM": 8, "LOW": 3}.get(a.get("severity", "LOW"), 3)
    result = [(u, min(scores[u], 100), counts[u]) for u in scores]
    result.sort(key=lambda x: x[1], reverse=True)
    return result[:6]


def _hourly_activity(alerts):
    """Returns 24 hourly alert counts for Ransomware Activity chart."""
    counts = [0] * 24
    for a in alerts:
        try:
            h = datetime.strptime(a["timestamp"], "%Y-%m-%d %H:%M:%S").hour
            counts[h] += 1
        except Exception:
            pass
    return counts


# ── Threat score donut ────────────────────────────────────────────────────────

class ThreatDonut(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._pct = 28
        self.setFixedSize(110, 110)

    def set_pct(self, v):
        self._pct = max(0, min(100, v))
        self.update()

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        cx = cy = self.width() // 2
        R, thick = 44, 10

        # Background ring
        pen = QPen(QColor(BORDER), thick)
        pen.setCapStyle(Qt.PenCapStyle.FlatCap)
        p.setPen(pen); p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawEllipse(cx-R, cy-R, R*2, R*2)

        # Filled arc
        color = RED if self._pct >= 70 else ORANGE if self._pct >= 40 else GREEN
        pen2 = QPen(QColor(color), thick)
        pen2.setCapStyle(Qt.PenCapStyle.RoundCap)
        p.setPen(pen2)
        span = int((self._pct / 100) * 360 * 16)
        p.drawArc(cx-R, cy-R, R*2, R*2, 90*16, -span)

        # Text
        p.setPen(QPen(QColor(TEXT_WHITE)))
        p.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        p.drawText(QRect(cx-25, cy-14, 50, 22), Qt.AlignmentFlag.AlignCenter, f"{self._pct}%")
        p.setPen(QPen(QColor(TEXT_MUTED)))
        p.setFont(QFont("Segoe UI", 7))
        lbl = "Low Risk" if self._pct < 40 else "Med Risk" if self._pct < 70 else "High Risk"
        p.drawText(QRect(cx-25, cy+8, 50, 14), Qt.AlignmentFlag.AlignCenter, lbl)
        p.end()


# ── Ransomware activity line chart ────────────────────────────────────────────

class ActivityChart(QWidget):
    LABELS = ["00:00","04:00","08:00","12:00","16:00","20:00","24:00"]

    def __init__(self, parent=None):
        super().__init__(parent)
        self._data = [random.randint(0, 4) for _ in range(24)]
        self.setMinimumHeight(180)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

    def set_data(self, values):
        self._data = values if len(values) == 24 else [0]*24
        self.update()

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        W, H = self.width(), self.height()
        PL, PR, PB, PT = 32, 16, 28, 12
        CW = W - PL - PR
        CH = H - PB - PT
        mx = max(self._data) or 1
        step = CW / 23

        # Grid lines
        p.setPen(QPen(QColor(BORDER), 1, Qt.PenStyle.DotLine))
        for i in range(5):
            y = PT + int(CH * i / 4)
            p.drawLine(PL, y, W - PR, y)
            val = int(mx * (4 - i) / 4)
            p.setPen(QPen(QColor(TEXT_MUTED)))
            p.setFont(QFont("Segoe UI", 7))
            p.drawText(QRect(0, y - 7, PL - 4, 14), Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter, str(val))
            p.setPen(QPen(QColor(BORDER), 1, Qt.PenStyle.DotLine))

        # Fill gradient
        pts_x = [PL + int(i * step) for i in range(24)]
        pts_y = [PT + CH - int((v / mx) * CH) for v in self._data]

        from PyQt6.QtGui import QPolygonF
        from PyQt6.QtCore import QPointF

        poly = QPolygonF()
        poly.append(QPointF(pts_x[0], PT + CH))
        for x, y in zip(pts_x, pts_y):
            poly.append(QPointF(x, y))
        poly.append(QPointF(pts_x[-1], PT + CH))

        grad = QLinearGradient(0, PT, 0, PT + CH)
        grad.setColorAt(0, QColor(255, 71, 87, 100))
        grad.setColorAt(1, QColor(255, 71, 87, 0))
        p.setBrush(QBrush(grad))
        p.setPen(Qt.PenStyle.NoPen)
        p.drawPolygon(poly)

        # Line
        pen = QPen(QColor(RED), 2)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
        p.setPen(pen)
        p.setBrush(Qt.BrushStyle.NoBrush)
        for i in range(len(pts_x) - 1):
            p.drawLine(pts_x[i], pts_y[i], pts_x[i+1], pts_y[i+1])

        # X labels
        p.setPen(QPen(QColor(TEXT_MUTED)))
        p.setFont(QFont("Segoe UI", 7))
        for i, lbl in enumerate(self.LABELS):
            x = PL + int(i * 4 * step) - 15
            p.drawText(QRect(x, H - PB + 4, 40, 16), Qt.AlignmentFlag.AlignCenter, lbl)
        p.end()


# ── User risk score bar ───────────────────────────────────────────────────────

def _risk_bar_row(username: str, score: int) -> QWidget:
    color = RED if score >= 80 else ORANGE if score >= 60 else YELLOW if score >= 40 else GREEN
    w = QWidget()
    lay = QHBoxLayout(w)
    lay.setContentsMargins(0, 3, 0, 3)
    lay.setSpacing(8)

    name = QLabel(username)
    name.setFixedWidth(60)
    name.setStyleSheet(f"color:{TEXT_WHITE};font-size:11px;background:transparent;")
    name.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

    bar_bg = QFrame()
    bar_bg.setFixedHeight(10)
    bar_bg.setStyleSheet(f"background:{BORDER};border-radius:5px;")
    bar_lay = QHBoxLayout(bar_bg)
    bar_lay.setContentsMargins(0, 0, 0, 0)
    fill_w = max(int((score / 100) * 200), 4)
    bar_fill = QFrame()
    bar_fill.setFixedHeight(10)
    bar_fill.setStyleSheet(f"background:{color};border-radius:5px;min-width:{fill_w}px;max-width:{fill_w}px;")
    bar_lay.addWidget(bar_fill)
    bar_lay.addStretch()

    lay.addWidget(name)
    lay.addWidget(bar_bg, 1)
    return w


# ── Stat card ─────────────────────────────────────────────────────────────────

def _stat_card(icon, label, value, sub="", color=CYAN, bg=BG_CARD):
    f = QFrame()
    f.setStyleSheet(f"QFrame{{background:{bg};border:1px;border-radius:12px;}}")
    f.setFixedHeight(110)
    lay = QVBoxLayout(f)
    lay.setContentsMargins(18, 14, 18, 14)
    lay.setSpacing(2)

    top = QHBoxLayout()
    lbl = QLabel(label.upper())
    lbl.setStyleSheet(f"color:{TEXT_MUTED};font-size:15px;letter-spacing:1px;background:transparent;")
    ic = QLabel(icon)
    ic.setStyleSheet(f"color:{color};font-size:30px;background:transparent;")
    top.addWidget(lbl); top.addStretch(); top.addWidget(ic)
    lay.addLayout(top)

    vl = QLabel(str(value))
    vl.setStyleSheet(f"color:{TEXT_WHITE};font-size:25px;font-weight:700;background:transparent;")
    lay.addWidget(vl)

    if sub:
        sl = QLabel(sub)
        sl.setStyleSheet(f"color:{color};font-size:15px;background:transparent;")
        lay.addWidget(sl)

    return f, vl


# ── Incident row ──────────────────────────────────────────────────────────────

def _incident_row(inc_id, inc_type, source, severity, status, time_ago) -> QWidget:
    sev_color  = {"Critical": RED, "High": ORANGE, "Medium": YELLOW, "Low": BLUE}.get(severity, TEXT_MUTED)
    stat_color = {"Blocked": GREEN, "Investigating": ORANGE, "Flagged": YELLOW, "Logged": TEXT_MUTED, "Resolved": BLUE}.get(status, TEXT_MUTED)

    w = QWidget()
    w.setFixedHeight(46)
    w.setStyleSheet(f"QWidget{{background:{BG_CARD2};border-radius:6px;}} QWidget:hover{{background:#1a2540;}}")
    lay = QHBoxLayout(w)
    lay.setContentsMargins(14, 0, 14, 0)
    lay.setSpacing(0)

    def cell(text, width, color=TEXT_MUTED, bold=False):
        l = QLabel(text)
        l.setStyleSheet(
            f"color:{color};font-size:12px;font-weight:{'700' if bold else '400'};background:transparent;"
        )
        if width:
            l.setFixedWidth(width)
        return l

    def badge(text, color):
        b = QLabel(text)
        b.setFixedWidth(80)
        b.setAlignment(Qt.AlignmentFlag.AlignCenter)
        b.setStyleSheet(
            f"color:{color};border:1px;border-radius:10px;"
            f"font-size:13px;font-weight:700;padding:2px 6px;background:transparent;"
        )
        return b

    lay.addWidget(cell(inc_id, 80, TEXT_SUB))
    lay.addWidget(cell(inc_type, 160, TEXT_WHITE, bold=True))
    lay.addWidget(cell(source, 150))
    lay.addWidget(badge(severity, sev_color))
    lay.addSpacing(16)
    lay.addWidget(badge(status, stat_color))
    lay.addStretch()
    lay.addWidget(cell(time_ago, 80, TEXT_MUTED))
    lay.addWidget(cell("⋮", 20, TEXT_MUTED))
    return w


def _incidents_from_alerts(alerts):
    """Convert real alerts into incident table rows."""
    rows = []
    type_map = {
        "RAPID_FILE_ACTIVITY":    ("Ransomware", "File System"),
        "INSIDER_THREAT_PROCESS": ("Insider Threat", "User Workstation"),
        "RANSOMWARE_CMDLINE":     ("Ransomware", "Process"),
        "RANSOMWARE_CPU_SPIKE":   ("Ransomware", "Process"),
        "SUSPICIOUS_PROCESS":     ("Insider Threat", "User Workstation"),
        "MASS_DELETE":            ("Ransomware", "File System"),
        "MASS_RENAME":            ("Ransomware", "File System"),
    }
    stat_map = {"CRITICAL": "Blocked", "HIGH": "Investigating", "MEDIUM": "Flagged", "LOW": "Logged"}
    sev_map  = {"CRITICAL": "Critical","HIGH": "High","MEDIUM": "Medium","LOW": "Low"}

    for i, a in enumerate(alerts[:8]):
        at = a.get("alert_type", "")
        inc_type, source = type_map.get(at, (at.replace("_", " ").title(), "System"))
        severity = sev_map.get(a.get("severity","LOW"), "Low")
        status   = stat_map.get(a.get("severity","LOW"), "Logged")
        try:
            dt = datetime.strptime(a["timestamp"], "%Y-%m-%d %H:%M:%S")
            diff = datetime.now() - dt
            if diff.seconds < 120: ago = f"{diff.seconds}s ago"
            elif diff.seconds < 3600: ago = f"{diff.seconds//60}m ago"
            elif diff.days == 0: ago = f"{diff.seconds//3600}h ago"
            else: ago = f"{diff.days}d ago"
        except Exception:
            ago = "—"
        rows.append((f"INC-{i+1:03d}", inc_type, source, severity, status, ago))
    return rows


# ── Live File Activity ────────────────────────────────────────────────────────

class LiveFileActivity(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet(f"QFrame{{background:{BG_CARD};border:1px;border-radius:12px;}}")

        lay = QVBoxLayout(self)
        lay.setContentsMargins(18, 14, 18, 14)
        lay.setSpacing(12)

        # Header
        hdr = QHBoxLayout()
        title = QLabel("⚡  Live File Activity")
        title.setStyleSheet(f"color:{TEXT_WHITE};font-size:18px;font-weight:700;background:transparent;")
        dot = QLabel("● Real-time")
        dot.setStyleSheet(f"color:{GREEN};font-size:15px;background:transparent;")
        hdr.addWidget(title); hdr.addStretch(); hdr.addWidget(dot)
        lay.addLayout(hdr)

        # Stats
        stats = QHBoxLayout(); stats.setSpacing(40)
        self._modified_val  = self._stat_col("Files Modified (per min)", "0")
        self._renamed_val   = self._stat_col("Files Renamed", "0")
        self._encrypted_val = self._stat_col("Suspicious Encryption", "0", RED)
        for col in [self._modified_val[0], self._renamed_val[0], self._encrypted_val[0]]:
            stats.addWidget(col)
        stats.addStretch()
        lay.addLayout(stats)

    def _stat_col(self, label, value, color=TEXT_WHITE):
        col = QWidget()
        col.setStyleSheet("background:transparent;")
        cl = QVBoxLayout(col); cl.setContentsMargins(0,0,0,0); cl.setSpacing(2)
        lbl = QLabel(label)
        lbl.setStyleSheet(f"color:{TEXT_MUTED};font-size:15px;background:transparent;")
        val = QLabel(value)
        val.setStyleSheet(f"color:{color};font-size:26px;font-weight:700;background:transparent;")
        cl.addWidget(lbl); cl.addWidget(val)
        return col, val

    def update_stats(self, modified, renamed, encrypted):
        self._modified_val[1].setText(str(modified))
        self._renamed_val[1].setText(str(renamed))
        enc_color = RED if encrypted > 0 else TEXT_WHITE
        self._encrypted_val[1].setText(str(encrypted))
        self._encrypted_val[1].setStyleSheet(
            f"color:{enc_color};font-size:26px;font-weight:700;background:transparent;"
        )


# ── Main Security Overview Page ───────────────────────────────────────────────

class SecurityOverviewPage(QWidget):
    """
    Full Security Overview / Dashboard page.
    Pass scan_callback to wire the "Run Security Scan" button to the scan page.

    Usage in dash.py:
        self._security_page = SecurityOverviewPage(scan_callback=self._go_to_scan_page)
        items = [("  ⊞  Dashboard", self._security_page), ...]
    """ 

    def __init__(self, scan_callback=None, parent=None):
        super().__init__(parent)
        self._scan_callback = scan_callback
        self._last_scan_type   = None
        self._last_scan_result = None
        self._last_scan_color  = None
        self._incident_layout  = None
        self._stat_vals        = {}
        self._chart            = None
        self._live_activity    = None
        self._risk_container   = None
        self._donut            = None
        self._build_ui()
        self._refresh()

        t = QTimer(self)
        t.timeout.connect(self._refresh)
        t.start(10000)

        # Simulate live file activity ticks
        lt = QTimer(self)
        lt.timeout.connect(self._live_tick)
        lt.start(3000)
        self._mod_count = 0
        self._ren_count = 0

    # ── Public API ────────────────────────────────────────────────────────────

    def notify_scan_complete(self, scan_type, result, result_color):
        """Called by NovaSphereWindow after scan finishes."""
        self._last_scan_type   = scan_type
        self._last_scan_result = result
        self._last_scan_color  = result_color
        self._update_last_scan_info()
    
    def _show_scan(self):
        """Switch the internal stack to the scan page."""
        self._stack.setCurrentIndex(1)
        if self._scan_page._worker is None:
            self._scan_page._start_scan()
    
    def _show_overview(self):
        """Switch back to the overview and refresh stats."""
        self._stack.setCurrentIndex(0)
        self._refresh()

    # ── UI Build ──────────────────────────────────────────────────────────────

    def _build_ui(self):
        self._stack = QStackedWidget()
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(self._stack)
        
        overview_widget = QWidget()
        self._stack.addWidget(overview_widget)
        
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        ov_layout = QVBoxLayout(overview_widget)
        ov_layout.setContentsMargins(0, 0, 0, 0)
        ov_layout.addWidget(scroll)
        
        content = QWidget()
        scroll.setWidget(content)
        root = QVBoxLayout(content)
        root.setContentsMargins(26, 20, 26, 26)
        root.setSpacing(14)
        root.setAlignment(Qt.AlignmentFlag.AlignTop)

        # ── Header ────────────────────────────────────────────────────────────
        hdr = QHBoxLayout()
        tc = QVBoxLayout(); tc.setSpacing(2)
        t1 = QLabel("Security Overview")
        t1.setStyleSheet(f"color:{TEXT_WHITE};font-size:30px;font-weight:700;background:transparent;")
        t2 = QLabel("Real-time threat monitoring and system status")
        t2.setStyleSheet(f"color:{TEXT_MUTED};font-size:15px;background:transparent;")
        tc.addWidget(t1); tc.addWidget(t2)
        hdr.addLayout(tc)
        hdr.addStretch()

        # Real-Time Protection toggle
        rt_row = QHBoxLayout(); rt_row.setSpacing(8)
        rt_lbl = QLabel("Real-Time Protection")
        rt_lbl.setStyleSheet(f"color:{TEXT_WHITE};font-size:15px;background:transparent;")
        self._rt_check = QCheckBox()
        self._rt_check.setChecked(True)
        self._rt_check.setStyleSheet(f"""
            QCheckBox::indicator {{ width:36px; height:20px; border-radius:10px; background:{BORDER}; }}
            QCheckBox::indicator:checked {{ background:{CYAN}; }}
        """)
        rt_row.addWidget(rt_lbl); rt_row.addWidget(self._rt_check)
        hdr.addLayout(rt_row)
        hdr.addSpacing(16)

        # Run Security Scan button
        scan_btn = QPushButton("▶  Run Security Scan")
        scan_btn.setFixedHeight(38)
        scan_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        scan_btn.setStyleSheet(
            f"QPushButton{{background:{CYAN};color:#000;border:none;"
            f"border-radius:8px;font-size:15px;font-weight:700;padding:0 18px;}}"
            f"QPushButton:hover{{background:#00d4f0;}}"
        )
        scan_btn.clicked.connect(self._show_scan)
        if self._scan_callback:
            scan_btn.clicked.connect(self._scan_callback)

        hdr.addWidget(scan_btn)
        root.addLayout(hdr)

        # ── System Status banner ──────────────────────────────────────────────
        self._status_bar = QFrame()
        self._status_bar.setFixedHeight(56)
        self._status_bar.setStyleSheet(
            f"QFrame{{background:{BG_STATUS};border:1px;border-radius:10px;}}"
        )
        sb_lay = QHBoxLayout(self._status_bar)
        sb_lay.setContentsMargins(18, 0, 18, 0)
        sb_icon = QLabel("🛡")
        sb_icon.setStyleSheet(f"color:{GREEN};font-size:25px;background:transparent;")
        self._status_lbl = QLabel("System Status:  ")
        self._status_lbl.setStyleSheet(f"color:{TEXT_WHITE};font-size:18px;background:transparent;")
        self._status_val = QLabel("SECURE")
        self._status_val.setStyleSheet(f"color:{GREEN};font-size:18px;font-weight:700;background:transparent;")
        self._status_sub = QLabel("All systems operating normally")
        self._status_sub.setStyleSheet(f"color:{TEXT_MUTED};font-size:15px;background:transparent;")
        self._status_dot = QLabel("●")
        self._status_dot.setStyleSheet(f"color:{GREEN};font-size:14px;background:transparent;")
        sb_lay.addWidget(sb_icon)
        sb_lay.addWidget(self._status_lbl)
        sb_lay.addWidget(self._status_val)
        sb_lay.addSpacing(16)
        sb_lay.addWidget(self._status_sub)
        sb_lay.addStretch()
        sb_lay.addWidget(self._status_dot)
        root.addWidget(self._status_bar)

        # ── Stat cards row ────────────────────────────────────────────────────
        cards_row = QHBoxLayout(); cards_row.setSpacing(12)

        c1, v1 = _stat_card("🛡", "Total Threats", "0", "+0%", RED, BG_CARD)
        c2, v2 = _stat_card("⚠", "Active Alerts", "0", "+0", ORANGE, BG_CARD)
        c3, v3 = _stat_card("⚡", "System Health", "98%", "Stable", GREEN, BG_CARD)
        c4, v4 = _stat_card("👤", "Insider Risks", "0", "+0", YELLOW, "#1a1608")

        self._stat_vals = {"threats": v1, "alerts": v2, "health": v3, "insider": v4}
        for c in [c1, c2, c3, c4]:
            cards_row.addWidget(c)

        # Threat score donut card
        donut_card = QFrame()
        donut_card.setFixedHeight(150)
        donut_card.setStyleSheet(f"QFrame{{background:{BG_CARD};border:1px;border-radius:12px;}}")
        donut_card.setFixedWidth(180)
        dl = QVBoxLayout(donut_card); dl.setContentsMargins(10, 8, 10, 8); dl.setSpacing(2)
        ts_lbl = QLabel("THREAT SCORE")
        ts_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        ts_lbl.setStyleSheet(f"color:{TEXT_MUTED};font-size:14px;letter-spacing:1px;background:transparent;")
        self._donut = ThreatDonut()
        dl.addWidget(ts_lbl)
        dl.addWidget(self._donut, alignment=Qt.AlignmentFlag.AlignHCenter)
        cards_row.addWidget(donut_card)
        root.addLayout(cards_row)

        # ── Middle row: Chart + Risk scores ──────────────────────────────────
        mid = QHBoxLayout(); mid.setSpacing(14)

        # Ransomware Activity chart card
        chart_card = QFrame()
        chart_card.setStyleSheet(f"QFrame{{background:{BG_CARD};border:1px;border-radius:12px;}}")
        chart_lay = QVBoxLayout(chart_card)
        chart_lay.setContentsMargins(18, 14, 18, 14)
        chart_lay.setSpacing(8)
        ch_hdr = QHBoxLayout()
        ch_title = QLabel("Ransomware Activity")
        ch_title.setStyleSheet(f"color:{TEXT_WHITE};font-size:18px;font-weight:700;background:transparent;")
        ch_badge = QLabel("Last 24 Hours ▾")
        ch_badge.setStyleSheet(
            f"color:{TEXT_MUTED};font-size:14px;border:1px;"
            f"border-radius:4px;padding:2px 8px;background:{BG_CARD2};"
        )
        ch_hdr.addWidget(ch_title); ch_hdr.addStretch(); ch_hdr.addWidget(ch_badge)
        chart_lay.addLayout(ch_hdr)
        self._chart = ActivityChart()
        chart_lay.addWidget(self._chart)
        mid.addWidget(chart_card, 3)

        # Top User Risk Scores card
        risk_card = QFrame()
        risk_card.setStyleSheet(f"QFrame{{background:{BG_CARD};border:1px;border-radius:12px;}}")
        risk_lay = QVBoxLayout(risk_card)
        risk_lay.setContentsMargins(18, 14, 18, 14)
        risk_lay.setSpacing(6)
        rh = QHBoxLayout()
        r_title = QLabel("Top User Risk Scores")
        r_title.setStyleSheet(f"color:{TEXT_WHITE};font-size:16px;font-weight:700;background:transparent;")
        r_idx = QLabel("RISK INDEX")
        r_idx.setStyleSheet(f"color:{TEXT_MUTED};font-size:12px;letter-spacing:1px;background:transparent;")
        rh.addWidget(r_title); rh.addStretch(); rh.addWidget(r_idx)
        risk_lay.addLayout(rh)
        self._risk_container = QVBoxLayout(); self._risk_container.setSpacing(6)
        risk_lay.addLayout(self._risk_container)
        risk_lay.addStretch()
        mid.addWidget(risk_card, 2)
        root.addLayout(mid)

        # ── Detection method label ────────────────────────────────────────────
        det = QLabel("Detection Method: Behavioral + Entropy Analysis")
        det.setStyleSheet(f"color:{CYAN};font-size:18px;background:transparent;")
        det.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        root.addWidget(det)

        # ── Bottom row: Live Activity + Last Scan Info ────────────────────────
        bot = QHBoxLayout(); bot.setSpacing(14)

        self._live_activity = LiveFileActivity()
        bot.addWidget(self._live_activity, 3)

        # Last Scan Info card
        self._scan_card = QFrame()
        self._scan_card.setStyleSheet(
            f"QFrame{{background:{BG_CARD};border:1px;border-radius:12px;}}"
        )
        self._scan_card.setFixedWidth(280)
        sc_lay = QVBoxLayout(self._scan_card)
        sc_lay.setContentsMargins(16, 14, 16, 14)
        sc_lay.setSpacing(8)
        sc_hdr = QHBoxLayout()
        sc_icon = QLabel("✅")
        sc_icon.setStyleSheet("font-size:25px;background:transparent;")
        sc_title = QLabel("Last Scan Info")
        sc_title.setStyleSheet(f"color:{TEXT_WHITE};font-size:18px;font-weight:700;background:transparent;")
        sc_hdr.addWidget(sc_icon); sc_hdr.addWidget(sc_title); sc_hdr.addStretch()
        sc_lay.addLayout(sc_hdr)

        self._scan_time_lbl   = QLabel("🕐  Last Scan:  Never")
        self._scan_type_lbl   = QLabel("📄  Scan Type:  —")
        self._scan_result_lbl = QLabel("✅  Result:  No scan run yet")
        for lbl in [self._scan_time_lbl, self._scan_type_lbl, self._scan_result_lbl]:
            lbl.setStyleSheet(f"color:{TEXT_MUTED};font-size:14px;background:transparent;")
            sc_lay.addWidget(lbl)

        sc_lay.addSpacing(6)
        rpt_btn = QPushButton("View Detailed Report")
        rpt_btn.setFixedHeight(34)
        rpt_btn.setStyleSheet(
            f"QPushButton{{background:{BG_CARD2};border:1px solid {BORDER};"
            f"border-radius:6px;color:{TEXT_WHITE};font-size:14px;}}"
            f"QPushButton:hover{{border-color:{CYAN};color:{CYAN};}}"
        )
        sc_lay.addWidget(rpt_btn)
        sc_lay.addStretch()
        bot.addWidget(self._scan_card)
        root.addLayout(bot)

        # ── Recent Security Incidents ─────────────────────────────────────────
        inc_card = QFrame()
        inc_card.setStyleSheet(f"QFrame{{background:{BG_CARD};border:1px;border-radius:12px;}}")
        inc_lay = QVBoxLayout(inc_card)
        inc_lay.setContentsMargins(18, 14, 18, 14)
        inc_lay.setSpacing(6)

        inc_hdr = QHBoxLayout()
        inc_title = QLabel("Recent Security Incidents")
        inc_title.setStyleSheet(f"color:{TEXT_WHITE};font-size:18px;font-weight:700;background:transparent;")
        view_all = QPushButton("View All")
        view_all.setStyleSheet(
            f"QPushButton{{background:transparent;border:none;color:{CYAN};font-size:15px;}}"
            f"QPushButton:hover{{color:#00d4f0;}}"
        )
        inc_hdr.addWidget(inc_title); inc_hdr.addStretch(); inc_hdr.addWidget(view_all)
        inc_lay.addLayout(inc_hdr)

        # Table header
        th = QWidget()
        th.setFixedHeight(30)
        th.setStyleSheet(f"background:{BG_CARD2};border-radius:4px;")
        th_lay = QHBoxLayout(th); th_lay.setContentsMargins(14, 0, 14, 0); th_lay.setSpacing(0)
        for col, w in [("INCIDENT ID", 80), ("TYPE", 160), ("SOURCE", 150), ("SEVERITY", 96), ("STATUS", 96), ("TIME", 80)]:
            lbl = QLabel(col)
            lbl.setStyleSheet(f"color:{TEXT_MUTED};font-size:12px;font-weight:700;letter-spacing:1px;background:transparent;")
            if w: lbl.setFixedWidth(w)
            th_lay.addWidget(lbl, 0 if w else 1)
        inc_lay.addWidget(th)

        self._incident_layout = QVBoxLayout(); self._incident_layout.setSpacing(3)
        inc_lay.addLayout(self._incident_layout)
        root.addWidget(inc_card)

        self._scan_page = ScanPage()
        self._stack.addWidget(self._scan_page)

        back_btn = QPushButton("← Back to Overview")
        back_btn.setFixedHeight(36)
        back_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        back_btn.setStyleSheet(
            f"QPushButton{{background:transparent;border:1px solid {BORDER};"
            f"border-radius:8px;color:{TEXT_MUTED};font-size:13px;padding:0 14px;}}"
            f"QPushButton:hover{{border-color:{CYAN};color:{CYAN};}}"
        )
        back_btn.clicked.connect(self._show_overview)

        scan_inner= self._scan_page.findChild(QScrollArea)
        if scan_inner and scan_inner.widget():
            scan_inner.widget().layout().insertWidget(0, back_btn)

    # ── Refresh ───────────────────────────────────────────────────────────────

    def _clear(self, layout):
        while layout.count():
            item = layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

    def _refresh(self):
        alerts = _load_alerts()
        events = _load_events()

        total    = len(alerts)
        active   = sum(1 for a in alerts if a.get("severity") in ("CRITICAL", "HIGH"))
        insider  = sum(1 for a in alerts if "INSIDER" in a.get("alert_type","").upper() or "RAPID" in a.get("alert_type","").upper())
        threat_pct = min(int((active / max(total, 1)) * 100), 99) if total else 0

        self._stat_vals["threats"].setText(str(total))
        self._stat_vals["alerts"].setText(str(active))
        self._stat_vals["insider"].setText(str(insider))
        self._donut.set_pct(threat_pct)

        # Status banner
        if active > 5:
            self._status_val.setText("THREAT DETECTED")
            self._status_val.setStyleSheet(f"color:{RED};font-size:15px;font-weight:700;background:transparent;")
            self._status_sub.setText("Active threats require attention")
            self._status_dot.setStyleSheet(f"color:{RED};font-size:12px;background:transparent;")
        else:
            self._status_val.setText("SECURE")
            self._status_val.setStyleSheet(f"color:{GREEN};font-size:15px;font-weight:700;background:transparent;")
            self._status_sub.setText("All systems operating normally")
            self._status_dot.setStyleSheet(f"color:{GREEN};font-size:12px;background:transparent;")

        # Chart
        self._chart.set_data(_hourly_activity(alerts))

        # Risk scores
        self._clear(self._risk_container)
        scores = _user_risk_scores(alerts)
        if scores:
            for username, score, _ in scores:
                self._risk_container.addWidget(_risk_bar_row(username, score))
        else:
            # Demo data if DB empty
            for name, score in [("admin", 85), ("jdoe", 70), ("bsmith", 52), ("alice", 30), ("guest", 15)]:
                self._risk_container.addWidget(_risk_bar_row(name, score))

        # Incidents
        self._clear(self._incident_layout)
        incidents = _incidents_from_alerts(alerts)
        if not incidents:
            # Demo incidents if DB empty
            incidents = [
                ("INC-001", "Ransomware",     "Finance Server",   "Critical", "Blocked",       "2m ago"),
                ("INC-002", "Insider Threat", "User Workstation", "High",     "Investigating",  "15m ago"),
                ("INC-003", "Bait File Access","HR Database",     "Medium",   "Flagged",        "1h ago"),
                ("INC-004", "Failed Login",   "VPN Gateway",      "Low",      "Logged",         "2h ago"),
                ("INC-005", "Policy Violation","Email Gateway",   "Low",      "Resolved",       "4h ago"),
            ]
        for row in incidents:
            self._incident_layout.addWidget(_incident_row(*row))

    def _live_tick(self):
        self._mod_count += random.randint(5, 40)
        self._ren_count += random.randint(0, 3)
        self._live_activity.update_stats(
            self._mod_count % 500,
            self._ren_count % 30,
            0,
        )

    def _update_last_scan_info(self):
        if not self._last_scan_type:
            return
        now = datetime.now().strftime("%d %b %Y – %H:%M")
        color = self._last_scan_color or GREEN
        self._scan_time_lbl.setText(f"🕐  Last Scan:  {now}")
        self._scan_time_lbl.setStyleSheet(f"color:{TEXT_WHITE};font-size:13px;background:transparent;")
        self._scan_type_lbl.setText(f"📄  Scan Type:  {self._last_scan_type}")
        self._scan_type_lbl.setStyleSheet(f"color:{TEXT_WHITE};font-size:13px;background:transparent;")
        self._scan_result_lbl.setText(f"✅  Result:  {self._last_scan_result}")
        self._scan_result_lbl.setStyleSheet(f"color:{color};font-size:13px;background:transparent;")