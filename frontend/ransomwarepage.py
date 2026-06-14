# frontend/ransomware_detection.py
# Ransomware Detection page — converted from teammate's dashboard.html to PyQt6
# Matches the style of insider_threat.py exactly.

import json
import math
import threading
import urllib.request
from pathlib import Path
from datetime import datetime

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QPushButton, QScrollArea, QSizePolicy, QStackedWidget,
)
from PyQt6.QtCore import Qt, QTimer, QRect, pyqtSignal
from PyQt6.QtGui import (
    QColor, QPainter, QPen, QBrush, QFont, QLinearGradient, QCursor
)

# ── Colors (identical to insider_threat.py) ───────────────────────────────────
BG_MAIN    = "#0b0f1a"
BG_CARD    = "#131929"
BG_CARD2   = "#161e30"
BG_SIDEBAR = "#0d1120"
BG_ROW     = "#0f1520"
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

FLASK_URL  = "http://localhost:5000/api"


# ── Flask API helper ──────────────────────────────────────────────────────────

def _api(path):
    """Fetch JSON from Flask API. Returns dict or None on failure."""
    try:
        with urllib.request.urlopen(f"{FLASK_URL}{path}", timeout=2) as r:
            return json.loads(r.read().decode())
    except Exception:
        return None


# ── Flask launcher ────────────────────────────────────────────────────────────

def _start_flask():
    import sys, os, importlib.util
    teammate_dir = os.path.normpath(
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "ransomware_part")
    )
    if teammate_dir not in sys.path:
        sys.path.insert(0, teammate_dir)
    try:
        import logging
        logging.getLogger("werkzeug").setLevel(logging.ERROR)
        spec = importlib.util.spec_from_file_location("api", os.path.join(teammate_dir, "api.py"))
        mod  = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        mod.app.run(port=5000, debug=False, use_reloader=False)
    except Exception as e:
        print(f"[NOVASPHERE] Flask API error: {e}")


def launch_flask_thread():
    t = threading.Thread(target=_start_flask, daemon=True)
    t.start()
    return t


# ── Shared card builder (same as insider_threat.py) ──────────────────────────

def _card(title="", sub=""):
    f = QFrame()
    f.setStyleSheet(f"QFrame{{background:{BG_CARD};border:1px;border-radius:12px;}}")
    lay = QVBoxLayout(f)
    lay.setContentsMargins(20, 15, 20, 20)
    lay.setSpacing(8)
    lay.setAlignment(Qt.AlignmentFlag.AlignTop)
    if title:
        t = QLabel(title)
        t.setStyleSheet(f"color:{TEXT_WHITE};font-size:17px;font-weight:900;background:transparent;")
        lay.addWidget(t)
    if sub:
        s = QLabel(sub)
        s.setStyleSheet(f"color:{TEXT_MUTED};font-size:12px;background:transparent;")
        lay.addWidget(s)
    return f, lay


# ── Stat card ─────────────────────────────────────────────────────────────────

def _stat_card(icon, label, color):
    f = QFrame()
    f.setStyleSheet(f"QFrame{{background:{BG_CARD};border:1px;border-radius:10px;}}")
    f.setFixedHeight(76)
    fl = QVBoxLayout(f)
    fl.setContentsMargins(14, 8, 14, 8)
    fl.setSpacing(2)
    fl.setAlignment(Qt.AlignmentFlag.AlignCenter)
    top = QHBoxLayout()
    il = QLabel(icon)
    il.setStyleSheet(f"color:{color};font-size:15px;background:transparent;")
    top.addWidget(il); top.addStretch()
    fl.addLayout(top)
    vl = QLabel("0")
    vl.setStyleSheet(f"color:{TEXT_WHITE};font-size:20px;font-weight:700;background:transparent;")
    ll = QLabel(label.upper())
    ll.setStyleSheet(f"color:{TEXT_MUTED};font-size:9px;letter-spacing:1px;background:transparent;")
    fl.addWidget(vl); fl.addWidget(ll)
    return f, vl


# ── Scan ring widget ──────────────────────────────────────────────────────────

class ScanRing(QWidget):
    """Animated scan ring — idle, scanning (with %), or monitoring active."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._pct      = 0
        self._state    = "idle"   # idle | scanning | active
        self._angle    = 0
        self.setFixedSize(160, 160)
        self._spin_timer = QTimer(self)
        self._spin_timer.timeout.connect(self._tick)

    def set_state(self, state, pct=0):
        self._state = state
        self._pct   = pct
        if state == "active":
            self._spin_timer.start(30)
        else:
            self._spin_timer.stop()
        self.update()

    def _tick(self):
        self._angle = (self._angle + 3) % 360
        self.update()

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        cx = cy = 80
        R = 72

        if self._state == "idle":
            # Static dashed ring
            pen = QPen(QColor(BORDER), 1.5, Qt.PenStyle.DashLine)
            p.setPen(pen); p.setBrush(Qt.BrushStyle.NoBrush)
            p.drawEllipse(cx - R, cy - R, R * 2, R * 2)
            pen2 = QPen(QColor(BORDER), 1)
            p.setPen(pen2)
            p.drawEllipse(cx - 60, cy - 60, 120, 120)

        elif self._state == "scanning":
            # Progress arc
            pen = QPen(QColor(BORDER), 1.5, Qt.PenStyle.DashLine)
            p.setPen(pen); p.setBrush(Qt.BrushStyle.NoBrush)
            p.drawEllipse(cx - R, cy - R, R * 2, R * 2)
            span = int((self._pct / 100) * 360 * 16)
            pen2 = QPen(QColor(CYAN), 2)
            p.setPen(pen2)
            p.drawArc(cx - R, cy - R, R * 2, R * 2, 90 * 16, -span)

        elif self._state == "active":
            # Spinning green arc
            pen = QPen(QColor(GREEN), 1.5, Qt.PenStyle.DashLine)
            p.setPen(pen); p.setBrush(Qt.BrushStyle.NoBrush)
            p.drawEllipse(cx - R, cy - R, R * 2, R * 2)
            pen2 = QPen(QColor(GREEN), 2)
            p.setPen(pen2)
            start = (90 - self._angle) * 16
            p.drawArc(cx - R, cy - R, R * 2, R * 2, start, 50 * 16)

        p.end()


# ── Risk score bar (like insider_threat RiskBar) ──────────────────────────────

class RiskScoreRow(QWidget):
    def __init__(self, filename, score, parent=None):
        super().__init__(parent)
        self.setFixedHeight(52)
        color = RED if score >= 80 else ORANGE if score >= 50 else CYAN

        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 2, 0, 2)
        lay.setSpacing(4)

        top = QHBoxLayout()
        name = QLabel(filename)
        name.setStyleSheet(f"color:{TEXT_WHITE};font-size:12px;font-weight:700;font-family:Consolas;background:transparent;")
        score_lbl = QLabel(str(int(score)))
        score_lbl.setStyleSheet(f"color:{color};font-size:14px;font-weight:800;background:transparent;")
        badge_txt = "HIGH" if score >= 80 else "MEDIUM" if score >= 50 else "LOW"
        badge = QLabel(badge_txt)
        badge.setStyleSheet(
            f"color:{color};background:transparent;font-size:9px;font-weight:800;"
            f"border:1px solid {color};border-radius:3px;padding:1px 5px;"
        )
        top.addWidget(name, 1)
        top.addWidget(score_lbl)
        top.addSpacing(6)
        top.addWidget(badge)
        lay.addLayout(top)

        bar_bg = QFrame()
        bar_bg.setFixedHeight(5)
        bar_bg.setStyleSheet(f"background:{BORDER};border-radius:2px;")
        bar_lay = QHBoxLayout(bar_bg)
        bar_lay.setContentsMargins(0, 0, 0, 0)
        fill_w = max(int((min(score, 100) / 100) * 260), 4)
        fill = QFrame()
        fill.setFixedHeight(5)
        fill.setStyleSheet(f"background:{color};border-radius:2px;min-width:{fill_w}px;max-width:{fill_w}px;")
        bar_lay.addWidget(fill); bar_lay.addStretch()
        lay.addWidget(bar_bg)


# ── Alert table row ───────────────────────────────────────────────────────────

def _alert_row(alert_id, severity, a_type, filename, rule, score, timestamp, status):
    sev_color  = {"Critical": RED, "High": ORANGE, "Medium": YELLOW, "Low": BLUE}.get(severity, TEXT_MUTED)
    stat_color = {"Open": RED, "Investigating": ORANGE, "Resolved": GREEN}.get(status, TEXT_MUTED)

    w = QWidget()
    w.setFixedHeight(42)
    w.setStyleSheet(
        f"QWidget{{background:{BG_ROW};border-radius:4px;}}"
        f"QWidget:hover{{background:{BG_CARD2};}}"
    )
    lay = QHBoxLayout(w)
    lay.setContentsMargins(12, 0, 12, 0)
    lay.setSpacing(0)

    def cell(text, width=None, color=TEXT_MUTED, bold=False, mono=False):
        l = QLabel(str(text))
        ff = "Consolas" if mono else "Segoe UI"
        l.setStyleSheet(
            f"color:{color};font-size:11px;font-weight:{'700' if bold else '400'};"
            f"font-family:{ff};background:transparent;"
        )
        if width:
            l.setFixedWidth(width)
        return l

    def badge(text, color):
        b = QLabel(text)
        b.setFixedWidth(75)
        b.setAlignment(Qt.AlignmentFlag.AlignCenter)
        b.setStyleSheet(
            f"color:{color};font-size:9px;font-weight:800;"
            f"border:1px solid {color};border-radius:3px;padding:1px 4px;background:transparent;"
        )
        return b

    lay.addWidget(cell(alert_id, 70, TEXT_SUB, mono=True))
    lay.addWidget(badge(severity, sev_color))
    lay.addSpacing(8)
    lay.addWidget(cell(a_type, 130, TEXT_WHITE, bold=True))
    lay.addWidget(cell(filename, 140, TEXT_MUTED, mono=True))
    lay.addWidget(cell(rule, 120, TEXT_SUB, mono=True))
    lay.addWidget(cell(score, 40, sev_color, bold=True))
    lay.addWidget(cell(timestamp, 70, TEXT_MUTED, mono=True))
    lay.addStretch()
    lay.addWidget(badge(status, stat_color))
    return w


def _alert_table_header():
    w = QWidget()
    w.setFixedHeight(32)
    w.setStyleSheet(f"background:{BG_CARD2};border-radius:4px;")
    lay = QHBoxLayout(w)
    lay.setContentsMargins(12, 0, 12, 0)
    lay.setSpacing(0)
    for col, width in [("ID",70),("SEV",83),("TYPE",138),("FILE",140),("RULE",120),("SCORE",40),("TIME",70),("STATUS",None)]:
        l = QLabel(col)
        l.setStyleSheet(f"color:{TEXT_MUTED};font-size:9px;font-weight:900;letter-spacing:1px;background:transparent;")
        if width:
            l.setFixedWidth(width)
        else:
            lay.addStretch()
        lay.addWidget(l)
    return w


# ── Quarantine table row ──────────────────────────────────────────────────────

def _quarantine_row(name, size, modified):
    w = QWidget()
    w.setFixedHeight(42)
    w.setStyleSheet(
        f"QWidget{{background:{BG_ROW};border-radius:4px;}}"
        f"QWidget:hover{{background:{BG_CARD2};}}"
    )
    lay = QHBoxLayout(w)
    lay.setContentsMargins(12, 0, 12, 0)
    lay.setSpacing(0)

    def cell(text, width=None, color=TEXT_WHITE, mono=False):
        l = QLabel(str(text))
        l.setStyleSheet(
            f"color:{color};font-size:11px;"
            f"font-family:{'Consolas' if mono else 'Segoe UI'};background:transparent;"
        )
        if width: l.setFixedWidth(width)
        return l

    iso = QLabel("Isolated")
    iso.setStyleSheet(
        f"color:{RED};font-size:9px;font-weight:800;"
        f"border:1px solid {RED};border-radius:3px;padding:1px 5px;background:transparent;"
    )

    lay.addWidget(cell(name, color=TEXT_WHITE, mono=True))
    lay.addStretch()
    lay.addWidget(cell(f"{size} B", 70, TEXT_MUTED))
    lay.addWidget(cell(modified, 140, TEXT_MUTED, mono=True))
    lay.addSpacing(10)
    lay.addWidget(iso)
    return w


# ── Honeypot row ──────────────────────────────────────────────────────────────

def _honeypot_row(name, path, intact):
    w = QWidget()
    w.setFixedHeight(50)
    w.setStyleSheet(f"QWidget{{background:{BG_CARD2};border:1px solid {BORDER};border-radius:8px;}}")
    lay = QHBoxLayout(w)
    lay.setContentsMargins(14, 0, 14, 0)

    icon = QLabel("🍯")
    icon.setStyleSheet(f"font-size:18px;background:transparent;")
    name_lbl = QLabel(name)
    name_lbl.setStyleSheet(f"color:{TEXT_WHITE};font-size:12px;font-family:Consolas;font-weight:700;background:transparent;")
    path_lbl = QLabel(path)
    path_lbl.setStyleSheet(f"color:{TEXT_MUTED};font-size:10px;background:transparent;")
    name_col = QVBoxLayout(); name_col.setSpacing(1)
    name_col.addWidget(name_lbl); name_col.addWidget(path_lbl)

    status_text = "Active" if intact else "Triggered"
    status_color = GREEN if intact else RED
    status = QLabel(status_text)
    status.setStyleSheet(
        f"color:{status_color};font-size:9px;font-weight:800;"
        f"border:1px solid {status_color};border-radius:3px;padding:2px 8px;background:transparent;"
    )

    lay.addWidget(icon)
    lay.addSpacing(8)
    lay.addLayout(name_col, 1)
    lay.addWidget(status)
    return w


# ── Log line ──────────────────────────────────────────────────────────────────

def _log_line(text):
    color = RED if any(x in text for x in ("HIGH", "HONEYPOT", "CRITICAL")) \
        else ORANGE if any(x in text for x in ("MEDIUM", "WARN")) \
        else GREEN if any(x in text for x in ("Rollback", "Reset", "success")) \
        else TEXT_MUTED
    l = QLabel(text)
    l.setStyleSheet(
        f"color:{color};font-size:11px;font-family:Consolas;"
        f"background:transparent;border-bottom:1px solid {BORDER};padding:2px 0;"
    )
    l.setWordWrap(True)
    return l


# ── Pages ─────────────────────────────────────────────────────────────────────

class DashboardSubPage(QWidget):
    """Dashboard sub-page: scan ring + security overview stats."""
    scan_requested = pyqtSignal()
    stop_requested = pyqtSignal()
    reset_requested = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._monitoring = False
        self._scanning   = False
        self._build()

    def _build(self):
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(14)
        lay.setAlignment(Qt.AlignmentFlag.AlignTop)

        # Scan ring card
        ring_card, ring_lay = _card()
        ring_lay.setAlignment(Qt.AlignmentFlag.AlignHCenter)

        self._ring = ScanRing()
        ring_lay.addWidget(self._ring, alignment=Qt.AlignmentFlag.AlignHCenter)

        self._ring_status = QLabel("CLICK TO START SCAN")
        self._ring_status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._ring_status.setStyleSheet(f"color:{TEXT_MUTED};font-size:12px;font-family:Consolas;letter-spacing:1px;background:transparent;")
        ring_lay.addWidget(self._ring_status)

        self._ring_sub = QLabel("")
        self._ring_sub.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._ring_sub.setStyleSheet(f"color:{TEXT_MUTED};font-size:10px;font-family:Consolas;background:transparent;")
        ring_lay.addWidget(self._ring_sub)

        # Progress bar (hidden unless scanning)
        self._prog_frame = QFrame()
        self._prog_frame.setFixedHeight(8)
        self._prog_frame.setStyleSheet(f"background:{BG_CARD2};border-radius:4px;")
        self._prog_frame.setFixedWidth(260)
        self._prog_frame.hide()
        prog_lay = QHBoxLayout(self._prog_frame)
        prog_lay.setContentsMargins(0, 0, 0, 0)
        self._prog_fill = QFrame()
        self._prog_fill.setFixedHeight(8)
        self._prog_fill.setStyleSheet(f"background:{CYAN};border-radius:4px;min-width:4px;max-width:4px;")
        prog_lay.addWidget(self._prog_fill); prog_lay.addStretch()
        ring_lay.addWidget(self._prog_frame, alignment=Qt.AlignmentFlag.AlignHCenter)

        # Buttons row
        btn_row = QHBoxLayout(); btn_row.setSpacing(10)
        btn_row.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        self._scan_btn = QPushButton("🛡  Start Monitoring")
        self._scan_btn.setFixedHeight(34)
        self._scan_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self._scan_btn.setStyleSheet(
            f"QPushButton{{background:transparent;border:1px solid {CYAN};"
            f"border-radius:8px;color:{CYAN};font-size:12px;font-weight:700;padding:0 16px;}}"
            f"QPushButton:hover{{background:rgba(0,188,212,0.1);}}"
        )
        self._scan_btn.clicked.connect(self._on_scan_click)

        reset_btn = QPushButton("↺  Reset Scores")
        reset_btn.setFixedHeight(34)
        reset_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        reset_btn.setStyleSheet(
            f"QPushButton{{background:transparent;border:1px solid {BORDER};"
            f"border-radius:8px;color:{TEXT_MUTED};font-size:12px;padding:0 14px;}}"
            f"QPushButton:hover{{border-color:{CYAN};color:{CYAN};}}"
        )
        reset_btn.clicked.connect(self.reset_requested)
        btn_row.addWidget(self._scan_btn)
        btn_row.addWidget(reset_btn)
        ring_lay.addLayout(btn_row)
        lay.addWidget(ring_card)

        # Security overview stats
        stat_lbl = QLabel("SECURITY OVERVIEW")
        stat_lbl.setStyleSheet(f"color:{TEXT_MUTED};font-size:10px;letter-spacing:2px;font-family:Consolas;background:transparent;")
        lay.addWidget(stat_lbl)

        grid = QHBoxLayout(); grid.setSpacing(10)
        sc1, self._v_scanned   = _stat_card("📄", "Files Scanned",    CYAN)
        sc2, self._v_threats   = _stat_card("🛡", "Threats Detected", RED)
        sc3, self._v_status    = _stat_card("⚡", "Protection Status", GREEN)
        sc4, self._v_quarantine= _stat_card("🔒", "Quarantined",      ORANGE)
        for c in [sc1, sc2, sc3, sc4]: grid.addWidget(c)
        lay.addLayout(grid)

    def _on_scan_click(self):
        if self._monitoring or self._scanning:
            self.stop_requested.emit()
        else:
            self.scan_requested.emit()

    def update_status(self, status, progress):
        monitoring = status.get("monitoring_active", False) if status else False
        scanned    = status.get("files_scanned", 0) if status else 0
        threats    = status.get("threats_detected", 0) if status else 0
        quarantine = status.get("quarantine_count", 0) if status else 0

        self._v_scanned.setText(str(scanned))
        self._v_threats.setText(str(threats))
        self._v_quarantine.setText(str(quarantine))

        scanning = progress.get("running", False) if progress else False
        pct      = progress.get("percent", 0) if progress else 0
        found    = progress.get("found", 0) if progress else 0
        total    = progress.get("total", 0) if progress else 0
        current  = progress.get("current", 0) if progress else 0

        self._monitoring = monitoring
        self._scanning   = scanning

        if scanning:
            self._ring.set_state("scanning", pct)
            self._ring_status.setText("SCANNING FILES...")
            self._ring_status.setStyleSheet(f"color:{CYAN};font-size:12px;font-family:Consolas;letter-spacing:1px;background:transparent;")
            self._ring_sub.setText(f"{current} / {total} files — {found} suspicious")
            self._prog_frame.show()
            fill_w = max(int((pct / 100) * 260), 4)
            self._prog_fill.setFixedWidth(fill_w)
            self._scan_btn.setText("⏹  Stop Monitoring")
            self._v_status.setText("Scanning")
            self._v_status.setStyleSheet(f"color:{CYAN};font-size:20px;font-weight:700;background:transparent;")
        elif monitoring:
            self._ring.set_state("active")
            self._ring_status.setText("MONITORING ACTIVE")
            self._ring_status.setStyleSheet(f"color:{GREEN};font-size:12px;font-family:Consolas;letter-spacing:1px;background:transparent;")
            self._ring_sub.setText(f"Initial scan complete — {scanned} files checked")
            self._prog_frame.hide()
            self._scan_btn.setText("⏹  Stop Monitoring")
            self._v_status.setText("Active")
            self._v_status.setStyleSheet(f"color:{GREEN};font-size:20px;font-weight:700;background:transparent;")
        else:
            self._ring.set_state("idle")
            self._ring_status.setText("CLICK TO START SCAN")
            self._ring_status.setStyleSheet(f"color:{TEXT_MUTED};font-size:12px;font-family:Consolas;letter-spacing:1px;background:transparent;")
            self._ring_sub.setText("")
            self._prog_frame.hide()
            self._scan_btn.setText("🛡  Start Monitoring")
            self._v_status.setText("Inactive")
            self._v_status.setStyleSheet(f"color:{TEXT_MUTED};font-size:20px;font-weight:700;background:transparent;")


class RansomwareSubPage(QWidget):
    """Active risk scores page."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self._score_layout = None
        self._build()

    def _build(self):
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(12)
        lay.setAlignment(Qt.AlignmentFlag.AlignTop)

        # Stats row
        grid = QHBoxLayout(); grid.setSpacing(10)
        sc1, self._v_active  = _stat_card("🔴", "Active Threats",    RED)
        sc2, self._v_high_th = _stat_card("⚠",  "High Threshold",    ORANGE)
        sc3, self._v_med_th  = _stat_card("📡",  "Medium Threshold",  CYAN)
        for c in [sc1, sc2, sc3]: grid.addWidget(c)
        lay.addLayout(grid)

        scores_card, scores_lay = _card("⚡ Active Risk Scores", "Files currently being tracked")
        self._score_layout = QVBoxLayout()
        self._score_layout.setSpacing(6)
        self._score_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        scores_lay.addLayout(self._score_layout)
        lay.addWidget(scores_card)

    def update_data(self, scores, status):
        self._v_active.setText(str(len(scores)))
        self._v_high_th.setText(str(status.get("high_threshold", 80) if status else 80))
        self._v_med_th.setText(str(status.get("medium_threshold", 50) if status else 50))

        while self._score_layout.count():
            item = self._score_layout.takeAt(0)
            if item.widget(): item.widget().deleteLater()

        if scores:
            for filename, score in sorted(scores.items(), key=lambda x: -x[1]):
                self._score_layout.addWidget(RiskScoreRow(filename, score))
        else:
            el = QLabel("✅  No active threats detected")
            el.setStyleSheet(f"color:{GREEN};font-size:13px;background:transparent;padding:16px 0;")
            self._score_layout.addWidget(el)
        self._score_layout.addStretch()


class AlertsSubPage(QWidget):
    """Alerts table page."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self._alert_layout = None
        self._build()

    def _build(self):
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(12)
        lay.setAlignment(Qt.AlignmentFlag.AlignTop)

        # Summary pills row
        grid = QHBoxLayout(); grid.setSpacing(10)
        sc1, self._v_crit = _stat_card("🔴", "Critical",  RED)
        sc2, self._v_high = _stat_card("🟠", "High",      ORANGE)
        sc3, self._v_med  = _stat_card("🔵", "Medium",    CYAN)
        sc4, self._v_low  = _stat_card("⚪", "Low",       TEXT_MUTED)
        for c in [sc1, sc2, sc3, sc4]: grid.addWidget(c)
        lay.addLayout(grid)

        # Table card
        tbl_card, tbl_lay = _card("🔔 All Alerts")

        # Export button
        hdr_row = QHBoxLayout()
        hdr_row.addStretch()
        export_btn = QPushButton("⬇  Export CSV")
        export_btn.setFixedHeight(30)
        export_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        export_btn.setStyleSheet(
            f"QPushButton{{background:transparent;border:1px solid {BORDER};"
            f"border-radius:6px;color:{TEXT_MUTED};font-size:11px;padding:0 12px;}}"
            f"QPushButton:hover{{border-color:{CYAN};color:{CYAN};}}"
        )
        self._export_btn = export_btn
        hdr_row.addWidget(export_btn)
        tbl_lay.addLayout(hdr_row)
        tbl_lay.addWidget(_alert_table_header())

        self._alert_layout = QVBoxLayout()
        self._alert_layout.setSpacing(3)
        self._alert_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        tbl_lay.addLayout(self._alert_layout)
        lay.addWidget(tbl_card)

    def update_data(self, alerts, summary):
        self._v_crit.setText(str(summary.get("Critical", 0)))
        self._v_high.setText(str(summary.get("High", 0)))
        self._v_med.setText(str(summary.get("Medium", 0)))
        self._v_low.setText(str(summary.get("Low", 0)))

        while self._alert_layout.count():
            item = self._alert_layout.takeAt(0)
            if item.widget(): item.widget().deleteLater()

        if alerts:
            for a in alerts[:20]:
                self._alert_layout.addWidget(_alert_row(
                    a.get("id","—"), a.get("severity","Low"),
                    a.get("type","—"), a.get("file","—"),
                    a.get("rule","—"), a.get("score","—"),
                    a.get("timestamp","—"), a.get("status","—"),
                ))
            self._alert_layout.addStretch()
        else:
            el = QLabel("✅  No alerts — run a scan first")
            el.setStyleSheet(f"color:{GREEN};font-size:13px;background:transparent;padding:16px 0;")
            self._alert_layout.addWidget(el)
            self._alert_layout.addStretch()


class QuarantineSubPage(QWidget):
    """Quarantine files page."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self._q_layout = None
        self._build()

    def _build(self):
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setAlignment(Qt.AlignmentFlag.AlignTop)

        card, card_lay = _card("🔒 Isolated Files", "Files blocked due to ransomware or suspicious behavior")
        self._count_lbl = QLabel("0 files")
        self._count_lbl.setStyleSheet(f"color:{ORANGE};font-size:11px;font-weight:800;border:1px solid {ORANGE};border-radius:3px;padding:2px 8px;background:transparent;")

        hdr = QHBoxLayout()
        hdr.addStretch(); hdr.addWidget(self._count_lbl)
        card_lay.addLayout(hdr)

        self._q_layout = QVBoxLayout()
        self._q_layout.setSpacing(4)
        self._q_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        card_lay.addLayout(self._q_layout)
        lay.addWidget(card)

    def update_data(self, files):
        self._count_lbl.setText(f"{len(files)} files")
        while self._q_layout.count():
            item = self._q_layout.takeAt(0)
            if item.widget(): item.widget().deleteLater()
        if files:
            for f in files:
                self._q_layout.addWidget(_quarantine_row(f["name"], f["size"], f["modified"]))
            self._q_layout.addStretch()
        else:
            el = QLabel("✅  No files currently in quarantine — system is secure")
            el.setStyleSheet(f"color:{GREEN};font-size:13px;background:transparent;padding:20px 0;")
            el.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self._q_layout.addWidget(el)
            self._q_layout.addStretch()


class DeceptionSubPage(QWidget):
    """Honeypot / deception system page."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self._hp_layout = None
        self._build()

    def _build(self):
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(12)
        lay.setAlignment(Qt.AlignmentFlag.AlignTop)

        grid = QHBoxLayout(); grid.setSpacing(10)
        sc1, self._v_active   = _stat_card("🍯", "Active Bait Files", CYAN)
        sc2, self._v_triggered= _stat_card("🔴", "Traps Triggered",   RED)
        sc3, self._v_defense  = _stat_card("🛡", "Active Defense",    GREEN)
        for c in [sc1, sc2, sc3]: grid.addWidget(c)
        lay.addLayout(grid)

        self._v_defense.setText("Enabled")
        self._v_defense.setStyleSheet(f"color:{GREEN};font-size:14px;font-weight:700;background:transparent;")

        card, card_lay = _card("🍯 Honeypot Bait Files", "Any access triggers immediate CRITICAL alert")
        self._hp_layout = QVBoxLayout()
        self._hp_layout.setSpacing(6)
        self._hp_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        card_lay.addLayout(self._hp_layout)
        lay.addWidget(card)

    def update_data(self, honeypots):
        active    = sum(1 for h in honeypots if h.get("intact"))
        triggered = sum(1 for h in honeypots if not h.get("intact"))
        self._v_active.setText(str(active))
        self._v_triggered.setText(str(triggered))

        while self._hp_layout.count():
            item = self._hp_layout.takeAt(0)
            if item.widget(): item.widget().deleteLater()

        if honeypots:
            for h in honeypots:
                self._hp_layout.addWidget(_honeypot_row(h["name"], h["path"], h["intact"]))
            self._hp_layout.addStretch()
        else:
            el = QLabel("No honeypot files configured")
            el.setStyleSheet(f"color:{TEXT_MUTED};font-size:13px;background:transparent;padding:16px 0;")
            self._hp_layout.addWidget(el)
            self._hp_layout.addStretch()


class LogsSubPage(QWidget):
    """System logs page."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self._log_layout = None
        self._build()

    def _build(self):
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        card, card_lay = _card("📋 System Logs")
        self._count_lbl = QLabel("0 entries")
        self._count_lbl.setStyleSheet(f"color:{TEXT_MUTED};font-size:11px;font-family:Consolas;background:transparent;")
        hdr = QHBoxLayout(); hdr.addStretch(); hdr.addWidget(self._count_lbl)
        card_lay.addLayout(hdr)
        self._log_layout = QVBoxLayout()
        self._log_layout.setSpacing(0)
        self._log_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        card_lay.addLayout(self._log_layout)
        lay.addWidget(card)

    def update_data(self, lines):
        self._count_lbl.setText(f"{len(lines)} entries")
        while self._log_layout.count():
            item = self._log_layout.takeAt(0)
            if item.widget(): item.widget().deleteLater()
        if lines:
            for line in reversed(lines[-50:]):
                self._log_layout.addWidget(_log_line(line))
            self._log_layout.addStretch()
        else:
            el = QLabel("No log entries yet")
            el.setStyleSheet(f"color:{TEXT_MUTED};font-size:13px;background:transparent;padding:16px 0;")
            self._log_layout.addWidget(el)
            self._log_layout.addStretch()


class SettingsSubPage(QWidget):
    """Settings page."""
    toggle_changed = pyqtSignal(str, bool)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._build()

    def _build(self):
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(12)
        lay.setAlignment(Qt.AlignmentFlag.AlignTop)

        det_card, det_lay = _card("⚙ Detection Settings")
        for key, title, sub in [
            ("auto_quarantine",   "Auto Quarantine",    "Automatically isolate detected threats"),
            ("auto_kill_process", "Auto Kill Process",  "Terminate suspicious processes automatically"),
        ]:
            row = QHBoxLayout(); row.setContentsMargins(0,6,0,6)
            tc = QVBoxLayout(); tc.setSpacing(1)
            tl = QLabel(title)
            tl.setStyleSheet(f"color:{TEXT_WHITE};font-size:13px;background:transparent;")
            sl = QLabel(sub)
            sl.setStyleSheet(f"color:{TEXT_MUTED};font-size:11px;background:transparent;")
            tc.addWidget(tl); tc.addWidget(sl)

            toggle = QPushButton("ON")
            toggle.setCheckable(True)
            toggle.setChecked(key == "auto_quarantine")
            toggle.setFixedSize(52, 26)
            toggle.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
            k = key
            def _update_style(checked, btn=toggle, k=k):
                btn.setText("ON" if checked else "OFF")
                btn.setStyleSheet(
                    f"QPushButton{{background:{'rgba(0,188,212,0.2)' if checked else BG_CARD2};"
                    f"border:1px solid {CYAN if checked else BORDER};"
                    f"border-radius:13px;color:{CYAN if checked else TEXT_MUTED};"
                    f"font-size:9px;font-weight:800;}}"
                )
                self.toggle_changed.emit(k, checked)
            toggle.toggled.connect(_update_style)
            _update_style(toggle.isChecked())

            row.addLayout(tc, 1); row.addWidget(toggle)
            sep = QFrame(); sep.setFixedHeight(1); sep.setStyleSheet(f"background:{BORDER};")
            det_lay.addLayout(row); det_lay.addWidget(sep)
        lay.addWidget(det_card)

        thresh_card, thresh_lay = _card("📊 Scoring Thresholds")
        for label, val, color in [
            ("High Risk Threshold",   "80 pts", RED),
            ("Medium Risk Threshold", "50 pts", ORANGE),
            ("Score Decay After",     "20s",    TEXT_MUTED),
        ]:
            row = QHBoxLayout(); row.setContentsMargins(0,6,0,6)
            tl = QLabel(label); tl.setStyleSheet(f"color:{TEXT_WHITE};font-size:13px;background:transparent;")
            vl = QLabel(val); vl.setStyleSheet(f"color:{color};font-size:13px;font-family:Consolas;font-weight:700;background:transparent;")
            row.addWidget(tl, 1); row.addWidget(vl)
            sep = QFrame(); sep.setFixedHeight(1); sep.setStyleSheet(f"background:{BORDER};")
            thresh_lay.addLayout(row); thresh_lay.addWidget(sep)
        lay.addWidget(thresh_card)


# ── Main Ransomware Detection Page ───────────────────────────────────────────

class RansomwareDetectionPage(QWidget):
    """
    Full Ransomware Detection page — native PyQt6 conversion of teammate's
    dashboard.html. Matches insider_threat.py style exactly.
    Connects to Flask API at localhost:5000 for live data.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self._api_online   = False
        self._last_data    = {}
        self._sub_pages    = {}
        self._sub_btns     = {}
        self._build_ui()
        self._refresh()

        self._timer = QTimer(self)
        self._timer.timeout.connect(self._refresh)
        self._timer.start(3000)

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

        # ── Header ────────────────────────────────────────────────────────────
        hdr = QHBoxLayout()
        tc = QVBoxLayout(); tc.setSpacing(2)
        t1 = QLabel("🦠  Ransomware Detection")
        t1.setStyleSheet(f"color:{TEXT_WHITE};font-size:20px;font-weight:700;background:transparent;")
        t2 = QLabel("Behavioral detection, honeypots and real-time file system monitoring")
        t2.setStyleSheet(f"color:{TEXT_MUTED};font-size:12px;background:transparent;")
        tc.addWidget(t1); tc.addWidget(t2)
        hdr.addLayout(tc); hdr.addStretch()

        self._api_badge = QLabel("● API Connecting...")
        self._api_badge.setStyleSheet(f"color:{ORANGE};font-size:11px;font-weight:700;background:transparent;")
        self._path_lbl = QLabel("")
        self._path_lbl.setStyleSheet(
            f"color:{TEXT_MUTED};font-size:10px;font-family:Consolas;"
            f"border:1px solid {BORDER};border-radius:4px;padding:2px 8px;background:transparent;"
        )
        hdr.addWidget(self._path_lbl)
        hdr.addSpacing(8)
        hdr.addWidget(self._api_badge)
        root.addLayout(hdr)

        # ── Sub-nav tabs ──────────────────────────────────────────────────────
        nav = QHBoxLayout(); nav.setSpacing(6)
        pages_def = [
            ("dashboard",  "⊞  Dashboard"),
            ("ransomware", "🦠  Detection"),
            ("deception",  "🍯  Deception"),
            ("quarantine", "🔒  Quarantine"),
            ("alerts",     "🔔  Alerts"),
            ("logs",       "📋  Logs"),
            ("settings",   "⚙  Settings"),
        ]
        for key, label in pages_def:
            btn = QPushButton(label)
            btn.setFixedHeight(30)
            btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
            btn.setCheckable(True)
            btn.setStyleSheet(self._tab_style(False))
            btn.clicked.connect(lambda _, k=key: self._switch_tab(k))
            self._sub_btns[key] = btn
            nav.addWidget(btn)
        nav.addStretch()
        root.addLayout(nav)

        # ── Stacked sub-pages ─────────────────────────────────────────────────
        self._stack = QStackedWidget()

        self._pg_dashboard  = DashboardSubPage()
        self._pg_ransomware = RansomwareSubPage()
        self._pg_deception  = DeceptionSubPage()
        self._pg_quarantine = QuarantineSubPage()
        self._pg_alerts     = AlertsSubPage()
        self._pg_logs       = LogsSubPage()
        self._pg_settings   = SettingsSubPage()

        self._pg_dashboard.scan_requested.connect(self._do_scan)
        self._pg_dashboard.stop_requested.connect(self._do_stop)
        self._pg_dashboard.reset_requested.connect(self._do_reset)
        self._pg_settings.toggle_changed.connect(self._do_toggle)

        self._sub_pages = {
            "dashboard":  (self._pg_dashboard,  0),
            "ransomware": (self._pg_ransomware, 1),
            "deception":  (self._pg_deception,  2),
            "quarantine": (self._pg_quarantine, 3),
            "alerts":     (self._pg_alerts,     4),
            "logs":       (self._pg_logs,       5),
            "settings":   (self._pg_settings,   6),
        }
        for pg, _ in self._sub_pages.values():
            self._stack.addWidget(pg)

        root.addWidget(self._stack)
        self._switch_tab("dashboard")

    def _tab_style(self, active):
        if active:
            return (
                f"QPushButton{{background:{BG_CARD};border:1px solid {CYAN};"
                f"border-radius:6px;color:{CYAN};font-size:11px;font-weight:700;padding:0 12px;}}"
            )
        return (
            f"QPushButton{{background:transparent;border:1px solid {BORDER};"
            f"border-radius:6px;color:{TEXT_MUTED};font-size:11px;padding:0 12px;}}"
            f"QPushButton:hover{{border-color:{CYAN};color:{CYAN};}}"
        )

    def _switch_tab(self, key):
        pg, idx = self._sub_pages[key]
        self._stack.setCurrentIndex(idx)
        for k, btn in self._sub_btns.items():
            btn.setChecked(k == key)
            btn.setStyleSheet(self._tab_style(k == key))

    def _refresh(self):
        """Fetch all API data and update all sub-pages."""
        def fetch():
            status   = _api("/status")
            alerts   = _api("/alerts")
            quarant  = _api("/quarantine")
            scores   = _api("/scores")
            honeypots= _api("/honeypots")
            logs     = _api("/logs?limit=100")
            progress = _api("/scan/progress")
            return status, alerts, quarant, scores, honeypots, logs, progress

        # Run fetch in thread, update UI on main thread
        def _run():
            results = fetch()
            QTimer.singleShot(0, lambda: self._update_ui(*results))
        threading.Thread(target=_run, daemon=True).start()

    def _update_ui(self, status, alerts_data, quarant, scores_data, honeypots, logs, progress):
        online = status is not None
        self._api_online = online

        if online:
            self._api_badge.setText("● API: Online")
            self._api_badge.setStyleSheet(f"color:{GREEN};font-size:11px;font-weight:700;background:transparent;")
            path = status.get("monitor_path","")
            parts = path.replace("\\","/").split("/")
            self._path_lbl.setText("/".join(parts[-2:]) if len(parts) >= 2 else path)
        else:
            self._api_badge.setText("● API: Offline")
            self._api_badge.setStyleSheet(f"color:{RED};font-size:11px;font-weight:700;background:transparent;")

        alerts   = alerts_data.get("alerts", [])    if alerts_data   else []
        summary  = alerts_data.get("summary", {})   if alerts_data   else {}
        qfiles   = quarant.get("files", [])         if quarant       else []
        scores   = scores_data.get("active_scores",{}) if scores_data else {}
        hpots    = honeypots.get("honeypots", [])   if honeypots     else []
        log_lines= logs.get("lines", [])            if logs          else []

        self._pg_dashboard.update_status(status, progress)
        self._pg_ransomware.update_data(scores, status)
        self._pg_deception.update_data(hpots)
        self._pg_quarantine.update_data(qfiles)
        self._pg_alerts.update_data(alerts, summary)
        self._pg_logs.update_data(log_lines)

    def _do_scan(self):
        def _req():
            try:
                req = urllib.request.Request(
                    f"{FLASK_URL}/scan/start",
                    data=b"{}",
                    headers={"Content-Type": "application/json"},
                    method="POST"
                )
                urllib.request.urlopen(req, timeout=3)
            except Exception:
                pass
        threading.Thread(target=_req, daemon=True).start()
        QTimer.singleShot(500, self._refresh)

    def _do_stop(self):
        def _req():
            try:
                req = urllib.request.Request(
                    f"{FLASK_URL}/scan/stop",
                    data=b"{}",
                    headers={"Content-Type": "application/json"},
                    method="POST"
                )
                urllib.request.urlopen(req, timeout=3)
            except Exception:
                pass
        threading.Thread(target=_req, daemon=True).start()
        QTimer.singleShot(500, self._refresh)

    def _do_reset(self):
        def _req():
            try:
                req = urllib.request.Request(
                    f"{FLASK_URL}/reset",
                    data=b"{}",
                    headers={"Content-Type": "application/json"},
                    method="POST"
                )
                urllib.request.urlopen(req, timeout=3)
            except Exception:
                pass
        threading.Thread(target=_req, daemon=True).start()
        QTimer.singleShot(500, self._refresh)

    def _do_toggle(self, key, value):
        def _req():
            try:
                body = json.dumps({key: value}).encode()
                req = urllib.request.Request(
                    f"{FLASK_URL}/settings",
                    data=body,
                    headers={"Content-Type": "application/json"},
                    method="POST"
                )
                urllib.request.urlopen(req, timeout=3)
            except Exception:
                pass
        threading.Thread(target=_req, daemon=True).start()