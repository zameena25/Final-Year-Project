# ── ransomwarepage.py — NovaSphere Ransomware Detection Page 
# frontend / ransomwarepage.py

import sys
import os
import math
import random
import threading
import sqlite3
from datetime import datetime
from pathlib import Path
from auth.app_paths import get_logs_dir 

from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QFrame, QScrollArea, QGridLayout,
    QSizePolicy, QStackedWidget, QMenu
)
from PyQt6.QtCore import Qt, QTimer, QRect, QSize, pyqtSignal, QObject, QThread
from PyQt6.QtGui import (
    QColor, QPainter, QPen, QBrush, QFont,
    QLinearGradient, QPolygon, QCursor, QAction
)
from PyQt6.QtCore import QPoint

from frontend import alerts

DB_PATH = get_logs_dir() / "novasphere.db"

# ── Color palette (matches dashboard) ─────────────────────────────────────────
BG_MAIN    = "#0b0f1a"
BG_CARD    = "#131929"
BG_CARD2   = "#161e30"
BG_SIDEBAR = "#0d1120"
CYAN       = "#00bcd4"
CYAN_DIM   = "#007a8a"
RED        = "#ff3b3b"
RED_DIM    = "#8b1a1a"
ORANGE     = "#ff8c42"
YELLOW     = "#ffd166"
GREEN      = "#06d6a0"
BORDER     = "#1e2d45"
TEXT_WHITE = "#e8eaf0"
TEXT_MUTED = "#4a5a78"
TEXT_SUB   = "#6b7a99"

# ── Try importing backend modules ─────────────────────────────────────────────
try:
    from ransomware_part.detector import RansomwareDetector
    DETECTOR_AVAILABLE = True
except ImportError:
    DETECTOR_AVAILABLE = False

try:
    from ransomware_part.monitor import FileSystemMonitor
    MONITOR_AVAILABLE = True
except ImportError:
    MONITOR_AVAILABLE = False

try:
    from ransomware_part.prevention import PreventionEngine
    PREVENTION_AVAILABLE = True
except ImportError:
    PREVENTION_AVAILABLE = False

try:
    from ransomware_part.simulator import RansomwareSimulator
    SIMULATOR_AVAILABLE = True
except ImportError:
    SIMULATOR_AVAILABLE = False

def _load_recent_alerts(limit=20):
    alerts = []
    if not DB_PATH.exists():
        return alerts
    try:
        conn = sqlite3.connect(DB_PATH, check_same_thread=False, timeout=5)
        cur = conn.cursor()
        cur.execute(
            "SELECT timestamp, alert_type, severity, message, file_path, source "
            "FROM alerts ORDER BY rowid DESC LIMIT ?", (limit,)
        )
        for r in cur.fetchall():
            alerts.append({
                "timestamp": r[0], "alert_type": r[1], "severity": r[2],
                "message": r[3], "file_path": r[4] or "", "source": r[5] or "",
            })
        conn.close()
    except Exception as e:
        print(f"[ransomwarepage] DB read failed: {e}")
    return alerts 

# ── Flask thread launcher (used by dashboard) ─────────────────────────────────
_flask_started = False

def launch_flask_thread():
    """Launch Flask API backend in a daemon thread (safe to call multiple times)."""
    global _flask_started
    if _flask_started:
        return
    try:
        from ransomware_part.api import app as flask_app
        t = threading.Thread(
            target=lambda: flask_app.run(port=5050, debug=False, use_reloader=False),
            daemon=True
        )
        t.start()
        _flask_started = True
    except Exception:
        pass  # API not available, continue without it


# Sparkline / area chart widget

class AreaChartWidget(QWidget):
    """Draws two area series (reads / writes) over time."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumHeight(220)
        self._reads:  list[int] = []
        self._writes: list[int] = []
        self._labels: list[str] = []
        self._hover_idx: int | None = None
        self.setMouseTracking(True)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

    def push(self, ts: str, reads: int, writes: int):
        self._reads.append(reads)
        self._writes.append(writes)
        self._labels.append(ts)
        if len(self._reads) > 40:
            self._reads.pop(0)
            self._writes.pop(0)
            self._labels.pop(0)
        self.update()

    def mouseMoveEvent(self, e):
        if not self._reads:
            return
        pad_l, pad_r = 56, 20
        w = self.width() - pad_l - pad_r
        n = len(self._reads)
        step = w / max(n - 1, 1)
        mx = e.position().x()
        idx = round((mx - pad_l) / step)
        idx = max(0, min(idx, n - 1))
        self._hover_idx = idx
        self.update()

    def leaveEvent(self, e):
        self._hover_idx = None
        self.update()

    def paintEvent(self, _):
        if not self._reads:
            return
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)

        pad_l, pad_r, pad_t, pad_b = 56, 20, 16, 36
        w = self.width() - pad_l - pad_r
        h = self.height() - pad_t - pad_b

        all_vals = self._reads + self._writes
        mx_val = max(all_vals) if all_vals else 1
        # round up nicely
        tick_count = 5
        nice = math.ceil(mx_val / tick_count / 500) * 500 or 1000
        mx_val = nice * tick_count

        n = len(self._reads)
        step = w / max(n - 1, 1)

        def xp(i): return pad_l + i * step
        def yp(v): return pad_t + h - (v / mx_val) * h

        # Grid lines + y-labels
        p.setPen(QPen(QColor(BORDER), 1, Qt.PenStyle.DashLine))
        for k in range(tick_count + 1):
            val = k * nice
            y = yp(val)
            p.drawLine(QPoint(pad_l, int(y)), QPoint(pad_l + w, int(y)))
            p.setPen(QColor(TEXT_MUTED))
            p.setFont(QFont("Segoe UI", 8))
            p.drawText(QRect(0, int(y) - 10, pad_l - 4, 20),
                       Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter,
                       str(int(val)))
            p.setPen(QPen(QColor(BORDER), 1, Qt.PenStyle.DashLine))

        def draw_area(series, hex_line, hex_fill_top, hex_fill_bot):
            pts_top = [QPoint(int(xp(i)), int(yp(series[i]))) for i in range(n)]
            poly = QPolygon(pts_top +
                            [QPoint(int(xp(n - 1)), int(yp(0))),
                             QPoint(int(xp(0)), int(yp(0)))])
            grad = QLinearGradient(0, pad_t, 0, pad_t + h)
            grad.setColorAt(0.0, QColor(hex_fill_top))
            grad.setColorAt(1.0, QColor(hex_fill_bot))
            p.setBrush(QBrush(grad))
            p.setPen(Qt.PenStyle.NoPen)
            p.drawPolygon(poly)

            p.setBrush(Qt.BrushStyle.NoBrush)
            p.setPen(QPen(QColor(hex_line), 2))
            for i in range(n - 1):
                p.drawLine(pts_top[i], pts_top[i + 1])

        draw_area(self._reads,  CYAN,  "#1a4a5580", "#0b0f1a00")
        draw_area(self._writes, RED,   "#5a1a1a80", "#0b0f1a00")

        # X labels (every ~5 points)
        p.setPen(QColor(TEXT_MUTED))
        p.setFont(QFont("Segoe UI", 8))
        for i, lbl in enumerate(self._labels):
            if i % 5 == 0 or i == n - 1:
                p.drawText(QRect(int(xp(i)) - 24, pad_t + h + 6, 48, 20),
                           Qt.AlignmentFlag.AlignCenter, lbl)

        # Hover crosshair
        idx = self._hover_idx
        if idx is not None and 0 <= idx < n:
            x = int(xp(idx))
            p.setPen(QPen(QColor(TEXT_MUTED), 1, Qt.PenStyle.DashLine))
            p.drawLine(QPoint(x, pad_t), QPoint(x, pad_t + h))

            bx, by = x + 12, pad_t + 8
            bw, bh2 = 140, 64
            if bx + bw > self.width() - 8:
                bx = x - bw - 12
            p.setBrush(QBrush(QColor("#1a2540e0")))
            p.setPen(QPen(QColor(BORDER), 1))
            p.drawRoundedRect(bx, by, bw, bh2, 8, 8)

            p.setPen(QColor(TEXT_WHITE))
            p.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
            p.drawText(bx + 8, by + 16, self._labels[idx])
            p.setPen(QColor(RED))
            p.setFont(QFont("Segoe UI", 9))
            p.drawText(bx + 8, by + 32, f"writes : {self._writes[idx]:,}")
            p.setPen(QColor(CYAN))
            p.drawText(bx + 8, by + 48, f"reads  : {self._reads[idx]:,}")

        p.end()


# Styled helpers

def card(parent=None) -> QFrame:
    f = QFrame(parent)
    f.setStyleSheet(f"QFrame{{background:{BG_CARD};border:1px;"
                    f"border-radius:14px;}}")
    return f

def label(text="", size=12, color=TEXT_WHITE, bold=False) -> QLabel:
    lbl = QLabel(text)
    w = "700" if bold else "400"
    lbl.setStyleSheet(f"color:{color};font-size:{size}px;font-weight:{w};"
                      f"background:transparent;")
    return lbl

def risk_badge(level: str) -> QLabel:
    colors = {"Critical": RED, "High": ORANGE, "Medium": YELLOW, "Low": GREEN}
    bg = colors.get(level, BORDER)
    b = QLabel(level)
    b.setAlignment(Qt.AlignmentFlag.AlignCenter)
    b.setFixedSize(72, 22)
    b.setStyleSheet(f"background:{bg};color:#000;border-radius:11px;"
                    f"font-size:11px;font-weight:700;")
    return b

def status_badge(text: str) -> QLabel:
    icons = {"Terminated": ("✓", GREEN), "Isolated": ("◆", CYAN),
             "Monitoring": ("●", YELLOW)}
    icon, col = icons.get(text, ("•", TEXT_MUTED))
    b = QLabel(f"{icon}  {text}")
    b.setStyleSheet(f"color:{col};font-size:12px;font-weight:600;"
                    f"background:transparent;")
    return b


# Main page
class SeverityDropdown(QMenu):
    selectionChanged = pyqtSignal(str)
    LEVELS = ["All Severities", "Critical", "High", "Medium", "Low"]

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet(f"""
              QMenu {{
                    background: {BG_CARD}; border: 1px;
                    border-radius: 8px; padding: 4px;
              }}
              QMenu::item {{
                    color: {TEXT_WHITE}; font-size: 13px;
                    padding: 8px 20px; border-radius: 4px;
              }}
              QMenu::item::selected {{
                    background: {BORDER}; color:{CYAN};
              }}
        """)
        for level in self.LEVELS:
            action = QAction(level, self)
            action.triggered.connect(lambda _, l=level: self.selectionChanged.emit(l))
            self.addAction(action)

class RansomwareDetectionPage(QWidget):
    """Drop-in replacement for the dashboard placeholder."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._build()
        self._init_backend()

        # Simulation timer (updates chart + timeline every 2 s)
        self._tick = 0
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._update)
        self._timer.start(2000)

    #  Build UI 
    def _build(self):
        self._sev_btn = QPushButton("󰁋 All Severities")
        self._sev_btn.setCursor (QCursor(Qt.CursorShape.PointingHandCursor))
        self._sev_btn.setStyleSheet(
            f"QPushButton{{background:transparent; border:1px solid {BORDER};"
            f"color:{TEXT_MUTED};border-radius:8px; padding:8px 16px; font-size:13px;}}"
            f"QPushButton:hover{{border-color:{CYAN};color:{CYAN};}}"
        )
        scroll = QScrollArea(self)
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setStyleSheet("QScrollArea{border:none;background:transparent;}"
                             f"QScrollBar:vertical{{background:{BG_MAIN};width:5px;border-radius:2px;}}"
                             f"QScrollBar::handle:vertical{{border-radius:2px;min-height:30px;}}"
                             "QScrollBar::add-line:vertical,QScrollBar::sub-line:vertical{height:0;}")
        ol = QVBoxLayout(self)
        ol.setContentsMargins(0, 0, 0, 0)
        ol.addWidget(scroll)

        content = QWidget()
        scroll.setWidget(content)
        root = QVBoxLayout(content)
        root.setContentsMargins(28, 22, 28, 28)
        root.setSpacing(16)
        root.setAlignment(Qt.AlignmentFlag.AlignTop)

        #  Top bar
         
        tb = QHBoxLayout()
        title_col = QVBoxLayout()
        title_col.setSpacing(2)
        title_col.addWidget(label("Ransomware Monitor", 20, TEXT_WHITE, bold=True))
        title_col.addWidget(label("Real-time heuristic analysis and encryption detection", 15, TEXT_MUTED))
        tb.addSpacing(8)
        tb.addLayout(title_col)
        tb.addStretch()

        self._current_sev = "All Severities"
        self._sev_btn.clicked.connect(self._show_sev_dropdown)

        self._lock_btn = QPushButton(" 󰜺  Emergency Lockdown")
        self._lock_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self._lock_btn.setStyleSheet(
            f"QPushButton{{background:transparent;border:2px solid {RED};"
            f"color:{RED};border-radius:8px;padding:8px 18px;font-size:13px;font-weight:700;}}"
            f"QPushButton:hover{{background:{RED_DIM};}}")
        self._lock_btn.clicked.connect(self._emergency_lockdown)

        tb.addWidget(self._sev_btn)
        tb.addSpacing(10)
        tb.addWidget(self._lock_btn)
        root.addLayout(tb)

        #  Main two-column body 
        cols = QHBoxLayout()
        cols.setSpacing(16)

        # Left column
        left = QVBoxLayout()
        left.setSpacing(14)

        # Chart card
        chart_card = card()
        chart_card.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        chart_card.setFixedHeight(290)
        cl = QVBoxLayout(chart_card)
        cl.setContentsMargins(18, 14, 18, 10)

        ch_hdr = QHBoxLayout()
        ch_hdr.addWidget(label("File System Activity", 15, TEXT_WHITE, bold=True))
        ch_hdr.addStretch()
        leg_r = label("● Reads", 13, CYAN)
        leg_w = label("● Writes", 13, RED)
        ch_hdr.addWidget(leg_r)
        ch_hdr.addSpacing(10)
        ch_hdr.addWidget(leg_w)
        cl.addLayout(ch_hdr)

        self._chart = AreaChartWidget()
        cl.addWidget(self._chart, 1)
        left.addWidget(chart_card)

        # Suspicious Processes card
        proc_card = card()
        pl = QVBoxLayout(proc_card)
        pl.setContentsMargins(18, 14, 18, 14)
        pl.setSpacing(10)

        phdr = QHBoxLayout()
        phdr.addWidget(label("Suspicious Processes", 15, TEXT_WHITE, bold=True))
        phdr.addStretch()
        pl.addLayout(phdr)

        # Table header
        th = QHBoxLayout()
        for txt, stretch in [("PROCESS NAME", 3), ("PID", 1),
                              ("ACTIVITY PATTERN", 3), ("RISK LEVEL", 2), ("STATUS", 2)]:
            l = label(txt, 10, TEXT_MUTED)
            l.setMinimumWidth(60)
            th.addWidget(l, stretch)
        pl.addLayout(th)

        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet(f"color:{BORDER};background:{BORDER};")
        sep.setFixedHeight(1)
        pl.addWidget(sep)

        self._proc_rows_layout = QVBoxLayout()
        self._proc_rows_layout.setSpacing(6)
        pl.addLayout(self._proc_rows_layout)
        left.addWidget(proc_card)
        left.addStretch()

        # Right column
        right = QVBoxLayout()
        right.setSpacing(14)

        # Detected family card
        fam_card = card()
        fam_card.setStyleSheet(
            f"QFrame{{background:#1a0f0f;border:1px;"
            f"border-radius:14px;}}")
        fl = QVBoxLayout(fam_card)
        fl.setContentsMargins(18, 16, 18, 16)
        fl.setSpacing(6)

        fl.addWidget(label("DETECTED FAMILY", 15, RED))
        self._family_lbl = label("LockBit 3.0", 24, TEXT_WHITE, bold=True)
        fl.addWidget(self._family_lbl)
        fl.addSpacing(8)

        for key, attr in [("Extension", "_ext_lbl"), ("Ransom Note", "_note_lbl"),
                           ("Encryption Type", "_enc_lbl")]:
            row = QHBoxLayout()
            row.addWidget(label(key, 13, TEXT_SUB))
            row.addStretch()
            val = label("—", 13, TEXT_WHITE)
            setattr(self, attr, val)
            row.addWidget(val)
            fl.addLayout(row)

        right.addWidget(fam_card)

        # Encryption rate card

        enc_card = card()
        el = QVBoxLayout(enc_card)
        el.setContentsMargins(18, 16, 18, 16)
        el.setSpacing(8)

        ehdr = QHBoxLayout()
        ehdr.addWidget(label("Encryption Rate", 16, TEXT_WHITE, bold=True))
        ehdr.addStretch()
        el.addLayout(ehdr)

        rate_row = QHBoxLayout()
        self._rate_lbl = label("4,281", 32, TEXT_WHITE, bold=True)
        rate_row.addWidget(self._rate_lbl)
        rate_row.addStretch()
        rate_row.addWidget(label("files/sec", 12, RED))
        el.addLayout(rate_row)

        self._rate_bar = QFrame()
        self._rate_bar.setFixedHeight(6)
        self._rate_bar.setStyleSheet(f"background:{RED};border-radius:3px;")
        el.addWidget(self._rate_bar)
        el.addWidget(label("High-velocity encryption detected. Automated containment protocols initiated.",
                           13, TEXT_MUTED))
        right.addWidget(enc_card)

        # Attack Timeline card
        tl_card = card()
        tl_card.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Expanding)
        tl = QVBoxLayout(tl_card)
        tl.setContentsMargins(18, 16, 18, 16)
        tl.setSpacing(0)
        tl.addWidget(label("Attack Timeline", 15, TEXT_WHITE, bold=True))
        tl.addSpacing(12)

        self._timeline_layout = QVBoxLayout()
        self._timeline_layout.setSpacing(10)
        tl.addLayout(self._timeline_layout)
        tl.addStretch()
        right.addWidget(tl_card, 1)

        cols.addLayout(left, 3)
        cols.addLayout(right, 2)
        root.addLayout(cols)

        #  Seed initial data 

        self._seed_initial_data()

    def _show_sev_dropdown(self):
        dropdown = SeverityDropdown(self)
        dropdown.selectionChanged.connect(self._filter_by_severity)
        pos = self._sev_btn.mapToGlobal(
            self._sev_btn.rect().bottomLeft()
        )
        dropdown.exec(pos)

    def _filter_by_severity(self, sev:str):
        self._current_sev = sev
        self._sev_btn.setText(f"▼  {sev}")

        for i in range(self._proc_rows_layout.count()):
            item = self._proc_rows_layout.itemAt(i)
            if item and item.widget():
                row_w = item.widget()

                labels = row_w.findChildren(QLabel)
                row_sev = None
                for lbl in labels:
                    if lbl.text() in ("Critical", "High", "Medium", "Low"):
                        row_sev = lbl.text()
                        break
                if sev == "All Severities" or row_sev == sev:
                    row_w.setVisible(True)
                else:
                    row_w.setVisible(False)
                    
    #  Seed demo data 

    def _seed_initial_data(self):
        base_reads  = [120,400,900,1600,2500,3300,3900,4000,3600,3000,2200,1400,800,300,80]
        base_writes = [80, 250,700,1400,2200,3000,3800,4500,3900,3200,2400,1600,900,400,100]
        for i, (r, w) in enumerate(zip(base_reads, base_writes)):
            mins = 10 * 60 + i * 2
            ts = f"{mins // 60:02d}:{mins % 60:02d}"
            self._chart.push(ts, r, w)

        self._refresh_from_db()

        self._ext_lbl.setText(".lockbit")
        self._note_lbl.setText("Restore-My-Files.txt")
        self._enc_lbl.setText("AES-256 + RSA")

        events = [
            (YELLOW, "10:14:22", "Suspicious process started (PID: 4521)"),
            (RED,    "10:15:05", "Mass file modification detected in /Data"),
            (RED,    "10:15:08", "High entropy write pattern identified (Encryption)"),
            (CYAN,   "10:15:10", "Ransomware family identified: LockBit 3.0"),
            (GREEN,  "10:15:12", "Automated Response: PID 4521 Terminated"),
            (GREEN,  "10:15:15", "Network Isolation enforced on Host-004"),
        ]
        for color, ts, msg in events:
            self._add_timeline_event(color, ts, msg)

    #  Update processes table 
    def _update_processes(self, processes):
        #clear old rows
        while self._proc_rows_layout.count():
            item = self._proc_rows_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        for proc_name, pid, pattern, risk, status in processes:
            row_w = QWidget()
            row_w.setStyleSheet(f"background:{BG_CARD2};border-radius:8px;")
            row = QHBoxLayout(row_w)
            row.setContentsMargins(8, 6, 8, 6)

            def add(txt, col=TEXT_WHITE, stretch=1):
                l = label(txt, 12, col)
                row.addWidget(l, stretch)

            add(proc_name, TEXT_WHITE, 3)
            add(pid, TEXT_MUTED, 1)
            add(pattern, TEXT_SUB, 3)
            row.addWidget(risk_badge(risk), 2)
            row.addWidget(status_badge(status), 2)
            self._proc_rows_layout.addWidget(row_w)
            
    def _refresh_from_db(self):
        alerts = _load_recent_alerts(20)
        if not alerts:
            self._update_processes([])
            return

        sev_map = {"CRITICAL": "Critical", "HIGH": "High", "MEDIUM": "Medium", "LOW": "Low"}
        rows = []
        for a in alerts:
            fname = Path(a["file_path"]).name if a["file_path"] else a.get("message", "unknown")[:40]
            severity = sev_map.get(a.get("severity", "LOW"), "Low")
            status = "Monitoring" if severity in ("Low", "Medium") else "Isolated"
            rows.append((fname, "—", a.get("alert_type", "").replace("_", " ").title(), severity, status))

        self._update_processes(rows)

        # Update timeline with real recent events
        self._timeline_layout.parentWidget()
        for a in alerts[:6]:
            sev = a.get("severity", "LOW")
            color = {"CRITICAL": RED, "HIGH": ORANGE, "MEDIUM": YELLOW, "LOW": GREEN}.get(sev, TEXT_MUTED)
            ts = a.get("timestamp", "—")
            msg = a.get("message", a.get("alert_type", "Event detected"))
            self._add_timeline_event(color, ts, msg)

    #  Add timeline event 

    def _add_timeline_event(self, dot_color: str, ts: str, msg: str):
        row = QHBoxLayout()
        row.setSpacing(10)

        dot = QLabel("●")
        dot.setStyleSheet(f"color:{dot_color};font-size:13px;background:transparent;")
        dot.setFixedWidth(14)
        row.addWidget(dot, 0, Qt.AlignmentFlag.AlignTop)

        col = QVBoxLayout()
        col.setSpacing(1)
        col.addWidget(label(ts, 10, TEXT_MUTED))
        col.addWidget(label(msg, 11, dot_color if dot_color != YELLOW else TEXT_WHITE))
        row.addLayout(col)

        self._timeline_layout.addLayout(row)

    # Backend init

    def _init_backend(self):
        self._detector  = None
        self._monitor   = None
        self._prevention = None

        if DETECTOR_AVAILABLE:
            try:
                self._detector = RansomwareDetector()
            except Exception:
                pass

        if MONITOR_AVAILABLE:
            try:
                self._monitor = FileSystemMonitor()
            except Exception:
                pass

        if PREVENTION_AVAILABLE:
            try:
                self._prevention = PreventionEngine()
            except Exception:
                pass

    #  Periodic update

    def _update(self):
        self._tick += 1
        now = datetime.now()
        ts = now.strftime("%H:%M")

        # Try to get real data from monitor
        reads, writes = self._get_fs_activity()
        self._chart.push(ts, reads, writes)
        if self._tick % 10 == 0:
            self._refresh_from_db()

        # Update rate label
        rate = writes + random.randint(-50, 50)
        rate = max(0, rate)
        self._rate_lbl.setText(f"{rate:,}")

        # Try real detector data
        self._poll_detector()

    def _get_fs_activity(self):
        """Pull from monitor backend or fall back to simulation."""
        if self._monitor:
            try:
                data = self._monitor.get_activity()
                if data:
                    return data.get("reads", 0), data.get("writes", 0)
            except Exception:
                pass
        # Simulated decay after spike

        base = max(0, 4500 - self._tick * 120)
        r = base + random.randint(-200, 200)
        w = base * 1.1 + random.randint(-200, 200)
        return int(max(0, r)), int(max(0, w))

    def _poll_detector(self):
        """Pull detection results from detector backend if available."""
        if not self._detector:
            return
        try:
            result = self._detector.get_latest()
            if result:
                family = result.get("family", "Unknown")
                self._family_lbl.setText(family)
                self._ext_lbl.setText(result.get("extension", "—"))
                self._note_lbl.setText(result.get("ransom_note", "—"))
                self._enc_lbl.setText(result.get("encryption", "—"))
        except Exception:
            pass

    #  Emergency lockdown 

    def _emergency_lockdown(self):
        if self._prevention:
            try:
                self._prevention.emergency_lockdown()
            except Exception:
                pass
        # Visual feedback
        self._lock_btn.setText("⊘  LOCKDOWN ACTIVE")
        self._lock_btn.setStyleSheet(
            f"QPushButton{{background:{RED_DIM};border:2px solid {RED};"
            f"color:{RED};border-radius:8px;padding:8px 18px;"
            f"font-size:13px;font-weight:700;}}")
        ts = datetime.now().strftime("%H:%M:%S")
        self._add_timeline_event(RED, ts, "🔴 Emergency Lockdown initiated by operator")

    # Called by dashboard on tab switch 
    def reload(self):
        if not self._timer.isActive():
            self._timer.start(2000)


#  Standalone test

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyleSheet(f"* {{font-family:'Segoe UI',sans-serif;}}"
                      f"QWidget{{background:{BG_MAIN};color:{TEXT_WHITE};}}")
    w = RansomwareDetectionPage()
    w.setWindowTitle("Ransomware Detection — NovaSphere")
    w.resize(1280, 800)
    w.show()
    sys.exit(app.exec())
