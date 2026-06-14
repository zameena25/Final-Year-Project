#Main Window of NOVASPHERE
import os
import sys
import math
import random
import threading
from pathlib import Path
from datetime import datetime
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QFrame, QScrollArea, QStackedWidget,
    QLineEdit, QCheckBox, QGridLayout, QSizePolicy
)
from PyQt6.QtCore import Qt, QTimer, QRect, QSize, pyqtSignal, QThread
from PyQt6.QtGui import (
    QColor, QPalette, QPainter, QPen, QBrush, QFont,
    QLinearGradient, QCursor
)

# ── Colors ────────────────────────────────────────────────────────────────────
BG_MAIN    = "#0b0f1a"
BG_SIDEBAR = "#0d1120"
BG_TOPBAR  = "#0d1120"
BG_CARD    = "#131929"
BG_CARD2   = "#161e30"
BG_MODULE  = "#131929"
CYAN       = "#00bcd4"
CYAN_DIM   = "#007a8a"
CYAN_GLOW  = "#00d4f0"
BORDER     = "#1e2d45"
TEXT_WHITE = "#e8eaf0"
TEXT_MUTED = "#4a5a78"
TEXT_CYAN  = "#00bcd4"
TEXT_SUB   = "#6b7a99"

STYLE = f"""
* {{ font-family: 'Segoe UI', sans-serif; }}
QMainWindow, QWidget {{ 
    background: {BG_MAIN}; color: {TEXT_WHITE}; 
    }}
QScrollArea {{ 
    border: none; background: transparent; 
    }}
QScrollBar:vertical {{ 
    background: {BG_MAIN}; width: 5px; border-radius: 2px; 
    }}
QScrollBar::handle:vertical {{ 
    background: {BORDER}; border-radius: 2px; min-height: 30px; 
    }}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
#topbar {{ 
background: {BG_TOPBAR}; border-bottom: 5px solid {BORDER}; 
}}
#sidebar {{ 
background: {BG_SIDEBAR}; border-right: 5px solid {BORDER}; min-width: 300px; max-width: 300px; 
}}
QPushButton#nav_btn {{
    background: transparent; border: none; color: {TEXT_MUTED};
    text-align: left; padding: 11px 20px; font-size: 17px;
    border-left: 3px solid transparent; border-radius: 0;
}}
QPushButton#nav_btn:hover {{ 
    color: {TEXT_WHITE}; 
    background: #111827; 
    border-left: 3px solid {BORDER}; 
    }}
QPushButton#nav_btn[active="true"] {{ 
    color: {TEXT_WHITE}; 
    background: #111827; 
    border-left: 10px solid {CYAN}; 
    }}
QPushButton#signout_btn {{
    background: transparent; border: none; color: {TEXT_MUTED};
    text-align: left; padding: 11px 20px; font-size: 15px;
}}
QPushButton#signout_btn:hover {{ color: #ff5252; }}
QPushButton#notif_btn {{ 
    background: transparent; 
    border: none; color: {TEXT_MUTED}; 
    font-size: 25px; 
    padding: 4px 8px; }}
QPushButton#notif_btn:hover {{ color: {CYAN}; }}
#search_bar {{
    background: #111827; border: 2px solid {BORDER};
    border-radius: 10px; color: {TEXT_WHITE}; font-size: 15px;
    padding: 7px 16px; min-width: 500px;
}}
#search_bar:focus {{ border: 2px solid {CYAN}; }}
#stat_card {{ background: {BG_CARD}; border: 1px solid {BORDER}; border-radius: 20px; }}
#card_val {{ color: {TEXT_WHITE}; font-size: 30px; font-weight: 700; background: transparent; }}
#card_lbl {{ color: {TEXT_MUTED}; font-size: 10px; letter-spacing: 1px; background: transparent; }}
#card_icon {{ color: {CYAN}; font-size: 20px; background: transparent; }}
#status_active {{ color: {CYAN}; font-size: 14px; font-weight: 600; background: transparent; }}
QPushButton#scan_tab {{
    background: transparent; border: 1px solid {BORDER};
    color: {TEXT_MUTED}; font-size: 13px; font-weight: 700;
    padding: 10px 0; letter-spacing: 2px;
}}
QPushButton#scan_tab[active="true"] {{ background: {CYAN}; color: #000; border-color: {CYAN}; }}
QPushButton#scan_tab:hover {{ color: {CYAN}; border-color: {CYAN}; }}
QPushButton#scan_tab[active="true"]:hover {{ color: #000; }}
#config_card {{ background: {BG_CARD2}; border: 1px solid {BORDER}; border-radius: 12px; }}
#config_title {{ color: {TEXT_WHITE}; font-size: 16px; font-weight: 700; background: transparent; }}
#config_sub {{ color: {TEXT_MUTED}; font-size: 12px; background: transparent; }}
#module_card {{ background: {BG_MODULE}; border: 1px solid {BORDER}; border-radius: 8px; }}
#module_card[checked="true"] {{ border: 1px solid {CYAN}; background: #0f1e2e; }}
#module_title {{ color: {TEXT_WHITE}; font-size: 15px; font-weight: 600; background: transparent; }}
#module_desc {{ color: {TEXT_SUB}; font-size: 12px; background: transparent; }}
QCheckBox#mod_check {{ spacing: 0; background: transparent; }}
QCheckBox#mod_check::indicator {{
    width: 18px; height: 18px; border: 1px solid {BORDER};
    border-radius: 4px; background: {BG_MAIN};
}}
QCheckBox#mod_check::indicator:checked {{ background: {CYAN}; border-color: {CYAN}; }}
#section_lbl {{ color: {TEXT_WHITE}; font-size: 20px; letter-spacing: 2px; font-weight: 700; background: transparent; }}
#purpose_lbl {{ color: {CYAN}; font-size: 15px; background: transparent; }}
#scan_hint {{ color: {TEXT_MUTED}; font-size: 12px; background: transparent; }}
"""

# ── Animated scan ring ────────────────────────────────────────────────────────
class ScanRing(QWidget):
    clicked = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(450, 450)
        self._angle = 0
        self._dot   = 0
        self._pulse = 0.0
        self._pdir  = 1
        self._state = "idle"
        self._pct = 0
        self._threats = 0
        self._scan  = False
        t = QTimer(self)
        t.timeout.connect(self._tick)
        t.start(20)
    
    def set_state(self, state: str, pct: int = 0, threats: int = 0):
        self._state = state
        self._pct = pct
        self._threats = threats

    def _tick(self):
        if self._state in ("scanning", "analyzing"):
            self._angle = (self._angle + 3) % 360
            self._dot   = (self._dot   + 2) % 360
        self._pulse += 0.04 * self._pdir    
        if self._pulse >= 1: self._pdir = -1
        if self._pulse <= 0: self._pdir =  1
        self.update()

    def mousePressEvent(self, _):
        if self._state in ("idle", "clean", "threat"):
            self.clicked.emit()

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        cx = cy = self.width() // 2

        is_red = self._state in ("analyzing", "threat")
        is_green = self._state == "clean"
        arc_color = "#ff3b3b" if is_red else ("#00e676" if is_green else CYAN_GLOW)
        ring_color = "#cc2222" if is_red else ("#00a152" if is_green else CYAN_DIM)
        dot_color = "#ff6060" if is_red else ("#69f0ae" if is_green else CYAN_GLOW)

        def ring(r, w, color, dash=False):
            pen = QPen(QColor(color), w)
            if dash: 
                pen.setStyle(Qt.PenStyle.DashLine)
            pen.setCapStyle(Qt.PenCapStyle.RoundCap)
            p.setPen(pen)
            p.setBrush(Qt.BrushStyle.NoBrush)
            p.drawEllipse(cx-r, cy-r, r*2, r*2)

        ring(165, 1.5, BORDER, dash=True)
        ring(132, 1.5, ring_color)

        # Rotating arc
        pen = QPen(QColor(arc_color), 3)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        p.setPen(pen)
        p.drawArc(cx-132, cy-132, 264, 264, 
                  int(self._angle*16), 90*16)

        ring(115, 1, BORDER)

        alpha = int(60 + 55*self._pulse)
        pulse_color = f"#{hex(alpha)[2:].zfill(2)}{'3b3b' if is_red else 'bcd4'}"
        ring(90, 2, pulse_color)

        if is_red:
            glow = QColor("#ff3b3b")
            glow.setAlpha(int(20 + 18 * self._pulse))
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(QBrush(glow))
            p.drawEllipse(cx - 88, cy - 88, 176, 176)
        
        # Inner dark circle
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QBrush(QColor("#0e1520")))
        p.drawEllipse(cx-80, cy-80, 160, 160)

        if self._state == "idle":
            self._draw_idle(p, cx, cy)
        elif self._state in ("scanning", "analyzing"):
            self._draw_progress(p, cx, cy)
        elif self._state == "threat":
            self._draw_threat(p, cx, cy)
        elif self._state == "clean":
            self._draw_clean(p, cx, cy)

        # Orbit dots
        for i, off in enumerate([0, 130, 250]):
            a = math.radians(self._dot + off)
            dx = cx + 132*math.cos(a); dy = cy + 132*math.sin(a)
            sz = 8 if i == 0 else 5
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(QBrush(QColor(CYAN_GLOW if i==0 else CYAN_DIM)))
            p.drawEllipse(int(dx-sz/2), int(dy-sz/2), sz, sz)

        # Fixed bottom dot
        bx = cx + 132*math.cos(math.radians(90))
        by = cy + 132*math.sin(math.radians(90))
        p.setBrush(QBrush(QColor(CYAN)))
        p.drawEllipse(int(bx-5), int(by-5), 10, 10)
        p.end()
    
    def _draw_idle(self, p, cx, cy):
        p.setPen(QPen(QColor(CYAN)))
        f = QFont("Segoe UI", 26)
        p.setFont(f)
        p.drawText(QRect(cx-35, cy-48, 70, 44), 
                   Qt.AlignmentFlag.AlignCenter, 
                   "🛡")
        p.setPen(QPen(QColor(TEXT_WHITE)))
        f2 = QFont("Segoe UI", 
                   9, 
                   QFont.Weight.Bold)
        f2.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, 2)
        p.setFont(f2)
        p.drawText(QRect(cx-55, cy+6, 110, 22), 
                   Qt.AlignmentFlag.AlignCenter, 
                   "SCAN SYSTEM")
    
    def _draw_progress(self, p, cx, cy):
        label = "SCANNING..." if self._state == "scanning" else "ANALYZING..."
        p.setPen(QPen(QColor("#ff3b3b" if self._state == "analyzing" else CYAN)))
        f = QFont("Segoe UI", 10, QFont.Weight.Bold)
        f.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, 1)
        p.setFont(f)
        p.drawText(QRect(cx - 55, cy - 18, 110, 22),
                   Qt.AlignmentFlag.AlignCenter, label)
        p.setPen(QPen(QColor(TEXT_WHITE)))
        f2 = QFont("Segoe UI", 9)
        p.setFont(f2)
        p.drawText(QRect(cx - 40, cy + 6, 80, 20),
                   Qt.AlignmentFlag.AlignCenter, f"{self._pct}%")
    
    def _draw_threat(self, p, cx, cy):
        p.setPen(QPen(QColor("#ff3b3b")))
        f = QFont("Segoe UI", 22)
        p.setFont(f)
        p.drawText(QRect(cx - 35, cy - 44, 70, 40),
                   Qt.AlignmentFlag.AlignCenter, "⚠")
        f2 = QFont("Segoe UI", 9, QFont.Weight.Bold)
        f2.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, 1)
        p.setFont(f2)
        p.drawText(QRect(cx - 60, cy + 4, 120, 20),
                   Qt.AlignmentFlag.AlignCenter, "THREATS FOUND")
    
    def _draw_clean(self, p, cx, cy):
        p.setPen(QPen(QColor("#00e676")))
        f = QFont("Segoe UI", 22)
        p.setFont(f)
        p.drawText(QRect(cx - 35, cy - 44, 70, 40),
                   Qt.AlignmentFlag.AlignCenter, "✔")
        f2 = QFont ("Segoe UI", 9, QFont.Weight.Bold)
        f2.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, 1)
        p.setFont(f2)
        p.drawText(QRect(cx - 65, cy + 4, 130, 20),
                   Qt.AlignmentFlag.AlignCenter, "DEVICE SECURED")

#── Stat card ─────────────────────────────────────────────────────────────────
def stat_card(icon, value, label, special=None):
    f = QFrame(); f.setObjectName("stat_card")
    f.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
    f.setFixedHeight(130)
    lay = QVBoxLayout(f); lay.setContentsMargins(24,18,24,18); lay.setSpacing(4)
    top = QHBoxLayout()
    il = QLabel(icon); il.setObjectName("card_icon"); top.addWidget(il); top.addStretch()
    if special == "dot":
        dl = QLabel("●"); dl.setStyleSheet(f"color:{CYAN};font-size:10px;background:transparent;"); top.addWidget(dl)
    lay.addLayout(top)
    vl = QLabel(str(value)); vl.setObjectName("card_val")
    ll = QLabel(label.upper()); ll.setObjectName("card_lbl")
    if special == "active":
        vl.hide()
        sl = QLabel("Active"); sl.setObjectName("status_active"); lay.addWidget(sl)
    elif special == "time":
        vl.setText("2 hours ago")
        vl.setStyleSheet(f"color:{TEXT_WHITE};font-size:15px;font-weight:600;background:transparent;")
    lay.addWidget(vl); lay.addWidget(ll)
    return f, vl

# ── Module card ───────────────────────────────────────────────────────────────
class ModuleCard(QFrame):
    def __init__(self, icon, title, desc, parent=None):
        super().__init__(parent)
        self.setObjectName("module_card")
        self._checked = True
        self.setProperty("checked","true")
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        lay = QHBoxLayout(self); lay.setContentsMargins(14,12,14,12); lay.setSpacing(12)
        self._cb = QCheckBox(); self._cb.setObjectName("mod_check"); self._cb.setChecked(True)
        self._cb.stateChanged.connect(self._toggle)
        col = QVBoxLayout(); col.setSpacing(4)
        tr = QHBoxLayout(); tr.setSpacing(8)
        ic = QLabel(icon); ic.setStyleSheet(f"color:{CYAN};font-size:14px;background:transparent;")
        tl = QLabel(title); tl.setObjectName("module_title")
        tr.addWidget(ic); tr.addWidget(tl); tr.addStretch()
        dl = QLabel(desc); dl.setObjectName("module_desc"); dl.setWordWrap(True)
        col.addLayout(tr); col.addWidget(dl)
        lay.addWidget(self._cb); lay.addLayout(col,1)

    def _toggle(self, s):
        self.setProperty("checked","true" if s==2 else "false")
        self.style().unpolish(self); self.style().polish(self)

    def mousePressEvent(self,_): self._cb.setChecked(not self._cb.isChecked())

class ScanWorker(QThread):
    progress = pyqtSignal(int, int)
    threat_found = pyqtSignal(str, int)
    finished = pyqtSignal(int, int)

    SUSPICIOUS_EXT = {
        ".exe", ".bat", ".cmd", ".vds", ".ps1", ".scr", ".pif", ".com",
    }
    RANSOM_KEYWORDS = {
        "your_files_are_encrypted",
        "files_have_been_encrypted",
        "how_to_decrypt",
        "how_to_recover",
        "ransom_note",
        "pay_bitcoin",
        "decryppt_instructions",
        "locked_files",
    }
    SAFE_NAMES = {
        "readme.md", "readme.txt", "readme.rst", "license.txt", "license.md", "changelog.md", "setup.py", "requirements.txt",
    }

    def __init__(self, scan_path: str):
        super().__init__()
        self._path = scan_path
        self._stop = False

    def stop(self):
        self._stop = True

    def run(self):                        # QThread calls run() automatically
        all_files = []
        for root, dirs, files in os.walk(self._path):
            dirs[:] = [
                d for d in dirs
                if not d.startswith(".") and d not in {
                    "Windows", "System32", "$Recycle.Bin",
                    "__pycache__", "node_modules",
                }
            ]
            for fname in files:
                all_files.append(os.path.join(root, fname))

        total = len(all_files)
        if total == 0:
            self.finished.emit(0, 0)
            return

        scanned = 0
        threats = 0

        for fpath in all_files:
            if self._stop:
                self.finished.emit(scanned, threats)
                return

            fname = os.path.basename(fpath)
            scanned += 1
            ext   = Path(fname).suffix.lower()
            name  = fname.lower()
            is_threat = False

            if ext in self.SUSPICIOUS_EXT:
                is_threat = True

            if not is_threat:
                for kw in self.RANSOM_KEYWORDS:
                    if kw in name:
                        is_threat = True
                        break

            if not is_threat and ext in {".txt", ".html", ".xml", ".json", ".cfg", ".ini"}:
                try:
                    with open(fpath, "r", errors="ignore") as fh:
                        head = fh.read(512).lower()
                    for kw in self.RANSOM_KEYWORDS:
                        if kw in head:
                            is_threat = True
                            break
                except (PermissionError, OSError):
                    pass

            if is_threat:
                threats += 1
                self.threat_found.emit(fpath, threats)

            if scanned % 5 == 0 or scanned == total:
                self.progress.emit(scanned, total)

        self.finished.emit(scanned, threats)

# ── Scan page ────────────────────────────────────────────────────────────
class ScanPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        scroll = QScrollArea(self)
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        ol = QVBoxLayout(self); ol.setContentsMargins(0,0,0,0); ol.addWidget(scroll)

        content = QWidget(); scroll.setWidget(content)
        root = QVBoxLayout(content)
        root.setContentsMargins(24,20,24,24); root.setSpacing(16)
        root.setAlignment(Qt.AlignmentFlag.AlignTop)

        # Scan ring
        rw = QHBoxLayout(); rw.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        self._ring = ScanRing(); rw.addWidget(self._ring)
        root.addLayout(rw)

        self._rescan_btn = QPushButton("Scan Again")
        self._rescan_btn.setFixedSize(200, 44)
        self._rescan_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self._rescan_btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                border: 2px solid {CYAN};
                border-radius: 22px;
                color: {CYAN};
                font-size: 14px;
                font-weight: 700;
                letter-spacing: 1px;
            }}
            QPushButton:hover {{
                background: {CYAN};
                color: #000;
            }}
            """)
        self._rescan_btn.hide()
        self._rescan_btn.clicked.connect(self._do_rescan)
        root.addWidget(self._rescan_btn, alignment = Qt.AlignmentFlag.AlignCenter)
        
        # ALL / MANUAL tabs
        tw = QWidget(); tw.setFixedWidth(500)
        tl = QHBoxLayout(tw); tl.setContentsMargins(0,0,0,0); tl.setSpacing(0)
        self._all_btn = QPushButton("ALL")
        self._all_btn.setObjectName("scan_tab"); self._all_btn.setFixedHeight(44)
        self._all_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self._all_btn.setStyleSheet("border-radius: 6px 0 0 6px;")
        self._man_btn = QPushButton("MANUAL")
        self._man_btn.setObjectName("scan_tab"); self._man_btn.setFixedHeight(44)
        self._man_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self._man_btn.setStyleSheet("border-radius: 0 6px 6px 0;")
        tl.addWidget(self._all_btn); tl.addWidget(self._man_btn)
        root.addWidget(tw, alignment=Qt.AlignmentFlag.AlignHCenter)

        # Purpose label
        self._purpose = QLabel("Purpose: Manual Scanning")
        self._purpose.setObjectName("purpose_lbl"); self._purpose.hide()
        root.addWidget(self._purpose)

        # Section label
        self._sec_lbl = QLabel("SECURITY OVERVIEW")
        self._sec_lbl.setObjectName("section_lbl")
        root.addWidget(self._sec_lbl)

        # Stat cards row
        cr = QHBoxLayout(); cr.setSpacing(16)
        c1,self._fv = stat_card("📄","0","Files Scanned")
        c2,self._tv = stat_card("⚠","0","Threats Detected")
        c3,_        = stat_card("🛡","","Protection Status", special="active")
        c4, self._lv= stat_card("🕐","","Last Scan Time",    special="time")
        for c in [c1,c2,c3,c4]: 
            cr.addWidget(c)
        root.addLayout(cr)

        # Config card (manual)
        self._cfg = self._make_config()
        self._cfg.hide(); root.addWidget(self._cfg)

        # Manual stat cards
        mr = QHBoxLayout(); mr.setSpacing(12)
        mc1,_ = stat_card("📄","0","Files Scanned")
        mc2,_ = stat_card("⚠","0","Threats Detected")
        mc3,_ = stat_card("🛡","","Protection Status",special="active")
        mc4,_ = stat_card("🕐","","Last Scan Time",   special="time")
        for c in [mc1,mc2,mc3,mc4]: mr.addWidget(c)
        self._mw = QWidget(); self._mw.setLayout(mr); self._mw.hide()
        root.addWidget(self._mw)

        self._hint = QLabel(
            "Select modules and click the scan button to start a custom security scan"
            )
        self._hint.setObjectName("scan_hint")
        self._hint.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        self._hint.hide(); root.addWidget(self._hint)
        root.addStretch()

        self._all_btn.clicked.connect(lambda: self._mode("all"))
        self._man_btn.clicked.connect(lambda: self._mode("manual"))
        self._mode("all")

        self._ring.clicked.connect(self._start_scan)

        self._worker = None
        self._thread = None
        self._n = 0 
        self._threats_count = 0
        self._scan_start_time = None

        self._time_ticker = QTimer(self)
        self._time_ticker.timeout.connect(self._update_scan_time)
        self._time_ticker.start(30_000) 

    def _make_config(self):
        card = QFrame(); card.setObjectName("config_card")
        lay = QVBoxLayout(card); lay.setContentsMargins(24,20,24,20); lay.setSpacing(12)
        tl = QLabel("Configure Custom Scan"); tl.setObjectName("config_title")
        sl = QLabel("Select the security modules you want to include in this scan"); sl.setObjectName("config_sub")
        lay.addWidget(tl); lay.addWidget(sl)
        grid = QGridLayout(); grid.setSpacing(10)
        mods = [
            ("🗂","File System Scan","Deep scan of all files for malware and ransomware signatures"),
            ("⚡","Running Process Monitoring","Real-time analysis of active processes and memory behavior"),
            ("👤","Insider Behavior Analysis","Monitor user activity patterns for suspicious data exfiltration"),
            ("🎣","Deception / Bait File Monitoring","Check honeypot files for unauthorized access attempts"),
            ("⚙","Startup & Persistence Scan","Analyze registry keys, scheduled tasks, and autorun entries"),
            ("📡","External Device and Network Scan","Monitor USB devices and network connections for threats"),
        ]
        pos = [(0,0),(0,1),(1,0),(1,1),(2,0),(2,1)]
        for (r,c),(ic,ti,de) in zip(pos,mods):
            grid.addWidget(ModuleCard(ic,ti,de), r, c)
        lay.addLayout(grid)
        return card
    
    def _update_scan_time(self):
        """Update the last scan time card with a human-readable elapsed label."""
        if self._scan_start_time is None:
            return
        diff = datetime.now() - self._scan_start_time
        secs = int(diff.total_seconds())
        mins = secs // 60
        hours = mins // 60

        if secs < 60:
            label = "Just Now"
        elif mins < 60:
            label = f"{mins} min{ 's' if mins > 1 else ''}ago"
        else:
            label = f"{hours} hour{'s' if hours > 1 else ''} ago"

        self._lv.setText(label)
        self._lv.setStyleSheet(
            f"color:{TEXT_WHITE}; font-size: 15px; font-weight: 600; background: transparent"
        )

    def _start_scan(self):
        """Kick off the background acan worker."""
        if self._worker is not None:
            return
        
        self._ring.set_state ("scanning", pct = 0)
        scan_root = str(Path.home())
        self._n = 0
        self._threats_count = 0
        self._scan_start_time = datetime.now()

        self._fv.setText("0")
        self._tv.setText("0")
        self._tv.setStyleSheet(
            f"color:{TEXT_WHITE}; font-size: 30px; font-weight: 700; background: transparent;"
        )
        self._lv.setText("Scanning...")
        self._lv.setStyleSheet(
            f"color:{TEXT_MUTED}; font-size: 13px; background: transparent;"
        )
        self._ring.set_state("scanning", pct=0)

        self._worker = ScanWorker(scan_root)
        self._worker.progress.connect(self._on_progress)
        self._worker.threat_found.connect(self._on_threat)
        self._worker.finished.connect(self._on_finished)
        self._worker.start()
    
    def _on_progress(self, scanned:int, total: int):
        pct = int(scanned/ total * 100)if total else 0
        self._n = scanned 

        state = "analyzing" if pct >= 90 else "scanning"
        self._ring.set_state(state, pct=pct)
        self._fv.setText(str(scanned))

    def _on_threat(self, _fpath:str, count:int):
        self._threats_count = count
        self._tv.setText(str(count))
        self._tv.setStyleSheet(
            "color: #ff3b3b; font-size: 30px; font-weight: 700; background: transparent;"
        )

        self._ring.set_state("threat", pct=self._ring._pct, threats=count)
    
    def _on_finished(self, total: int, threats: int):
        self._worker = None
        self._fv.setText(str(total))
        self._tv.setText(str(threats))
        self._lv.setText("Just Now")
        self._lv.setStyleSheet(
            f"color:{TEXT_WHITE}; font-size: 15px; font-weight: 600; background:transparent;"
        )

        self._scan_start_time = datetime.now()
        self._rescan_btn.show()

        if threats > 0:
            self._ring.set_state("threat", pct = 100, threats=threats)
            self._tv.setStyleSheet(
                "color: #ff3b3b; font-size: 30px; font-weight: 700; background: transparent;"
            )

        else:
            self._ring.set_state("clean",pct=100)
            self._tv.setStyleSheet(
                f"color:{TEXT_WHITE}; font-size: 30px; font-weight: 700; background: transparent;"
            )

    def _mode(self, m):
        is_m = m == "manual"
        self._all_btn.setProperty("active","true" if not is_m else "false")
        self._man_btn.setProperty("active","true" if is_m else "false")
        for b in [self._all_btn, self._man_btn]:
            b.style().unpolish(b); b.style().polish(b)
        self._purpose.setVisible(is_m)
        self._cfg.setVisible(is_m)
        self._mw.setVisible(is_m)
        self._hint.setVisible(is_m)
        self._sec_lbl.setText("MANUAL SCAN STATUS" if is_m else "SECURITY OVERVIEW")
    
    def _do_rescan(self):
        """Hide the button and kick off a fresh scan."""
        self._rescan_btn.hide()
        self._start_scan()

def placeholder(title, icon):
    w = QWidget()
    lay = QVBoxLayout(w); lay.setAlignment(Qt.AlignmentFlag.AlignCenter)
    l = QLabel(f"{icon}  {title}")
    l.setStyleSheet(f"color:{TEXT_MUTED};font-size:22px;background:transparent;")
    l.setAlignment(Qt.AlignmentFlag.AlignCenter)
    s = QLabel("This section is under development")
    s.setStyleSheet(f"color:{BORDER};font-size:13px;background:transparent;")
    s.setAlignment(Qt.AlignmentFlag.AlignCenter)
    lay.addWidget(l); lay.addSpacing(8); lay.addWidget(s)
    return w

def main():
    app = QApplication(sys.argv)
    palette = QPalette()
    palette.setColor(QPalette.ColorRole.Window,     QColor(BG_MAIN))
    palette.setColor(QPalette.ColorRole.WindowText, QColor(TEXT_WHITE))
    palette.setColor(QPalette.ColorRole.Base,       QColor(BG_CARD))
    palette.setColor(QPalette.ColorRole.Text,       QColor(TEXT_WHITE))
    palette.setColor(QPalette.ColorRole.Highlight,  QColor(CYAN))
    app.setPalette(palette)

    app.setStyleSheet(STYLE)

    win = QMainWindow()
    win.setWindowTitle("Scan Page")
    win.setMinimumSize(1300, 800)
    win.setCentralWidget(ScanPage())
    win.show()
    sys.exit(app.exec())
    

if __name__ == "__main__":
    main()


