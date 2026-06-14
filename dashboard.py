# NOVASPHERE — Main Dashboard

import sys
import math
import random
from datetime import datetime
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QFrame, QScrollArea, QStackedWidget,
    QLineEdit, QCheckBox, QGridLayout, QSizePolicy
)
from PyQt6.QtCore import Qt, QTimer, QRect, QSize
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
QMainWindow, QWidget {{ background: {BG_MAIN}; color: {TEXT_WHITE}; }}
QScrollArea {{ border: none; background: transparent; }}
QScrollBar:vertical {{ background: {BG_MAIN}; width: 5px; border-radius: 2px; }}
QScrollBar::handle:vertical {{ background: {BORDER}; border-radius: 2px; min-height: 30px; }}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
#topbar {{ background: {BG_TOPBAR}; border-bottom: 1px solid {BORDER}; }}
#sidebar {{ background: {BG_SIDEBAR}; border-right: 1px solid {BORDER}; min-width: 220px; max-width: 220px; }}
QPushButton#nav_btn {{
    background: transparent; border: none; color: {TEXT_MUTED};
    text-align: left; padding: 11px 20px; font-size: 13px;
    border-left: 3px solid transparent; border-radius: 0;
}}
QPushButton#nav_btn:hover {{ color: {TEXT_WHITE}; background: #111827; border-left: 3px solid {BORDER}; }}
QPushButton#nav_btn[active="true"] {{ color: {TEXT_WHITE}; background: #111827; border-left: 3px solid {CYAN}; }}
QPushButton#signout_btn {{
    background: transparent; border: none; color: {TEXT_MUTED};
    text-align: left; padding: 11px 20px; font-size: 13px;
}}
QPushButton#signout_btn:hover {{ color: #ff5252; }}
QPushButton#notif_btn {{ background: transparent; border: none; color: {TEXT_MUTED}; font-size: 18px; padding: 4px 8px; }}
QPushButton#notif_btn:hover {{ color: {CYAN}; }}
#search_bar {{
    background: #111827; border: 1px solid {BORDER};
    border-radius: 20px; color: {TEXT_WHITE}; font-size: 12px;
    padding: 7px 16px; min-width: 320px;
}}
#search_bar:focus {{ border: 1px solid {CYAN}; }}
#stat_card {{ background: {BG_CARD}; border: 1px solid {BORDER}; border-radius: 10px; }}
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
#module_title {{ color: {TEXT_WHITE}; font-size: 13px; font-weight: 600; background: transparent; }}
#module_desc {{ color: {TEXT_SUB}; font-size: 11px; background: transparent; }}
QCheckBox#mod_check {{ spacing: 0; background: transparent; }}
QCheckBox#mod_check::indicator {{
    width: 18px; height: 18px; border: 2px solid {BORDER};
    border-radius: 4px; background: {BG_MAIN};
}}
QCheckBox#mod_check::indicator:checked {{ background: {CYAN}; border-color: {CYAN}; }}
#section_lbl {{ color: {TEXT_WHITE}; font-size: 11px; letter-spacing: 2px; font-weight: 600; background: transparent; }}
#purpose_lbl {{ color: {CYAN}; font-size: 12px; background: transparent; }}
#scan_hint {{ color: {TEXT_MUTED}; font-size: 12px; background: transparent; }}
"""

# ── Animated scan ring ────────────────────────────────────────────────────────
class ScanRing(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(320, 320)
        self._angle = 0
        self._dot   = 0
        self._pulse = 0.0
        self._pdir  = 1
        self._scan  = False
        t = QTimer(self); t.timeout.connect(self._tick); t.start(28)

    def _tick(self):
        if self._scan:
            self._angle = (self._angle + 3) % 360
            self._dot   = (self._dot   + 2) % 360
        self._pulse += 0.04 * self._pdir
        if self._pulse >= 1: self._pdir = -1
        if self._pulse <= 0: self._pdir =  1
        self.update()

    def mousePressEvent(self, _):
        self._scan = not self._scan

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        cx = cy = self.width() // 2

        def ring(r, w, color, dash=False):
            pen = QPen(QColor(color), w)
            if dash: pen.setStyle(Qt.PenStyle.DashLine)
            pen.setCapStyle(Qt.PenCapStyle.RoundCap)
            p.setPen(pen); p.setBrush(Qt.BrushStyle.NoBrush)
            p.drawEllipse(cx-r, cy-r, r*2, r*2)

        ring(150, 1.5, BORDER, dash=True)
        ring(132, 1.5, CYAN_DIM)

        # Rotating arc
        pen = QPen(QColor(CYAN_GLOW), 3)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        p.setPen(pen)
        p.drawArc(cx-132, cy-132, 264, 264, int(self._angle*16), 90*16)

        ring(110, 1, BORDER)
        alpha = int(60 + 55*self._pulse)
        ring(90, 2, f"#{hex(alpha)[2:].zfill(2)}bcd4")  # cyan with pulsing alpha via color trick

        # Inner dark circle
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QBrush(QColor("#0e1520")))
        p.drawEllipse(cx-80, cy-80, 160, 160)

        # Shield + text
        p.setPen(QPen(QColor(CYAN)))
        f = QFont("Segoe UI", 26); p.setFont(f)
        p.drawText(QRect(cx-35, cy-48, 70, 44), Qt.AlignmentFlag.AlignCenter, "🛡")
        p.setPen(QPen(QColor(TEXT_WHITE)))
        f2 = QFont("Segoe UI", 9, QFont.Weight.Bold)
        f2.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, 2)
        p.setFont(f2)
        p.drawText(QRect(cx-55, cy+6, 110, 22), Qt.AlignmentFlag.AlignCenter, "SCAN SYSTEM")

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

# ── Stat card ─────────────────────────────────────────────────────────────────
def stat_card(icon, value, label, special=None):
    f = QFrame(); f.setObjectName("stat_card")
    f.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
    f.setFixedHeight(100)
    lay = QVBoxLayout(f); lay.setContentsMargins(18,14,18,14); lay.setSpacing(3)
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

# ── Dashboard page ────────────────────────────────────────────────────────────
class DashboardPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        scroll = QScrollArea(self)
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        ol = QVBoxLayout(self); ol.setContentsMargins(0,0,0,0); ol.addWidget(scroll)

        content = QWidget(); scroll.setWidget(content)
        root = QVBoxLayout(content)
        root.setContentsMargins(32,24,32,32); root.setSpacing(18)
        root.setAlignment(Qt.AlignmentFlag.AlignTop)

        # Scan ring
        rw = QHBoxLayout(); rw.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        self._ring = ScanRing(); rw.addWidget(self._ring)
        root.addLayout(rw)

        # ALL / MANUAL tabs
        tw = QWidget(); tw.setFixedWidth(380)
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
        cr = QHBoxLayout(); cr.setSpacing(12)
        c1,self._fv = stat_card("📄","0","Files Scanned")
        c2,self._tv = stat_card("⚠","0","Threats Detected")
        c3,_        = stat_card("🛡","","Protection Status", special="active")
        c4,_        = stat_card("🕐","","Last Scan Time",    special="time")
        for c in [c1,c2,c3,c4]: cr.addWidget(c)
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

        self._hint = QLabel("Select modules and click the scan button to start a custom security scan")
        self._hint.setObjectName("scan_hint")
        self._hint.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        self._hint.hide(); root.addWidget(self._hint)
        root.addStretch()

        self._all_btn.clicked.connect(lambda: self._mode("all"))
        self._man_btn.clicked.connect(lambda: self._mode("manual"))
        self._mode("all")

        self._n = 0
        t = QTimer(self); t.timeout.connect(self._tick); t.start(2000)

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

    def _tick(self):
        self._n += random.randint(1,6)
        self._fv.setText(str(self._n))

# ── Placeholder ───────────────────────────────────────────────────────────────
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

# ── Main window ───────────────────────────────────────────────────────────────
class NovaSphereWindow(QMainWindow):
    def __init__(self, username="Admin"):
        super().__init__()
        self.setWindowTitle("NOVASPHERE — Security Dashboard")
        self.setMinimumSize(1200,760); self.resize(1380,820)
        self._build()

    def _build(self):
        root = QWidget(); self.setCentralWidget(root)
        main = QVBoxLayout(root); main.setContentsMargins(0,0,0,0); main.setSpacing(0)

        # Topbar
        tb_w = QWidget(); tb_w.setObjectName("topbar"); tb_w.setFixedHeight(60)
        tb = QHBoxLayout(tb_w); tb.setContentsMargins(20,0,20,0); tb.setSpacing(0)

        shield = QLabel("🛡"); shield.setStyleSheet(f"color:{CYAN};font-size:26px;background:transparent;padding-right:8px;")
        nova   = QLabel("NOVA"); nova.setStyleSheet(f"color:{TEXT_WHITE};font-size:18px;font-weight:800;background:transparent;")
        sphere = QLabel("SPHERE"); sphere.setStyleSheet(f"color:{CYAN};font-size:18px;font-weight:800;background:transparent;")
        self._col_btn = QPushButton("‹"); self._col_btn.setObjectName("notif_btn")
        self._col_btn.setFixedSize(28,28); self._col_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        for w in [shield,nova,sphere]: tb.addWidget(w)
        tb.addSpacing(12); tb.addWidget(self._col_btn); tb.addStretch()

        srch = QLineEdit(); srch.setObjectName("search_bar")
        srch.setPlaceholderText("Search threats, users, or logs...")
        tb.addWidget(srch); tb.addStretch()

        notif = QPushButton("🔔"); notif.setObjectName("notif_btn"); notif.setFixedSize(36,36)
        tb.addWidget(notif); tb.addSpacing(16)

        ac = QVBoxLayout(); ac.setSpacing(1); ac.setAlignment(Qt.AlignmentFlag.AlignVCenter)
        an = QLabel("Admin Console"); an.setStyleSheet(f"color:{TEXT_WHITE};font-size:13px;font-weight:600;background:transparent;")
        ar = QLabel("Security Operations"); ar.setStyleSheet(f"color:{CYAN};font-size:10px;background:transparent;")
        ac.addWidget(an); ac.addWidget(ar); tb.addLayout(ac); tb.addSpacing(12)

        av = QLabel("A"); av.setAlignment(Qt.AlignmentFlag.AlignCenter); av.setFixedSize(36,36)
        av.setStyleSheet(f"background:{CYAN};color:#000;border-radius:18px;font-size:14px;font-weight:800;")
        tb.addWidget(av)
        main.addWidget(tb_w)

        # Body
        body = QHBoxLayout(); body.setSpacing(0); body.setContentsMargins(0,0,0,0)

        # Sidebar
        self._sb = QWidget(); self._sb.setObjectName("sidebar"); self._sb.setFixedWidth(220)
        sbl = QVBoxLayout(self._sb); sbl.setContentsMargins(0,16,0,16); sbl.setSpacing(2)

        self._pages = QStackedWidget()
        self._btns  = []

        items = [
            ("  ⊞  Dashboard",            DashboardPage()),
            ("  🦠  Ransomware Detection", placeholder("Ransomware Detection","🦠")),
            ("  👤  Insider Threat",       placeholder("Insider Threat","👤")),
            ("  🎣  Deception System",     placeholder("Deception System","🎣")),
            ("  📡  Live Monitoring",      placeholder("Live Monitoring","📡")),
            ("  🔒  Quarantine",           placeholder("Quarantine","🔒")),
            ("  🔔  Alerts",              placeholder("Alerts","🔔")),
            ("  📋  Logs",               placeholder("Logs","📋")),
            ("  📊  Reports",            placeholder("Reports","📊")),
            ("  ⚙  Settings",           placeholder("Settings","⚙")),
        ]
        for lbl, page in items:
            btn = QPushButton(lbl); btn.setObjectName("nav_btn")
            btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
            self._pages.addWidget(page); self._btns.append(btn); sbl.addWidget(btn)

        sbl.addStretch()
        so = QPushButton("  ➜  Sign Out"); so.setObjectName("signout_btn")
        so.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        so.clicked.connect(self._signout)
        sbl.addWidget(so)

        for i,b in enumerate(self._btns):
            b.clicked.connect(lambda _,idx=i: self._nav(idx))
        self._nav(0)

        body.addWidget(self._sb); body.addWidget(self._pages,1)
        bw = QWidget(); bw.setLayout(body)
        main.addWidget(bw,1)

        self._sb_vis = True
        self._col_btn.clicked.connect(self._toggle_sb)

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
            from login import MainWindow
            self.hide(); self._lw = MainWindow(); self._lw.show()
        except ImportError:
            self.close()

# ── Entry ─────────────────────────────────────────────────────────────────────
def main():
    app = QApplication(sys.argv)
    app.setStyleSheet(STYLE)
    palette = QPalette()
    palette.setColor(QPalette.ColorRole.Window,     QColor(BG_MAIN))
    palette.setColor(QPalette.ColorRole.WindowText, QColor(TEXT_WHITE))
    palette.setColor(QPalette.ColorRole.Base,       QColor(BG_CARD))
    palette.setColor(QPalette.ColorRole.Text,       QColor(TEXT_WHITE))
    palette.setColor(QPalette.ColorRole.Highlight,  QColor(CYAN))
    app.setPalette(palette)
    w = NovaSphereWindow(); w.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()