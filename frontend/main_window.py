# NOVASPHERE — Main Dashboard
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

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

from scan import ScanPage
from insider_threat import InsiderThreatPage
from security_overview import SecurityOverviewPage
from ransomwarepage import RansomwareDetectionPage, launch_flask_thread
from quarantine import QuarantinePage
from alerts import AlertsPage
from live_monitoring_page import LiveMonitoringPage
from deception_page import DeceptionPage 
from frontend.logs import LogsPage

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

# ── Dashboard page ────────────────────────────────────────────────────────────
class MainWindow(QWidget):
    def __init__(self, parent=None, scan_callback=None):
        super().__init__(parent)
        self._scan_callback = scan_callback
        scroll = QScrollArea(self)
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        ol = QVBoxLayout(self); ol.setContentsMargins(0,0,0,0); ol.addWidget(scroll)

        content = QWidget(); scroll.setWidget(content)
        root = QVBoxLayout(content)
        root.setContentsMargins(32,24,32,32); root.setSpacing(18)
        root.setAlignment(Qt.AlignmentFlag.AlignTop)

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
        launch_flask_thread()
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
            ("Dashboard",  SecurityOverviewPage()), #should make a dashboard page 
            ("  🦠  Ransomware Detection", RansomwareDetectionPage()),
            ("  👤  Insider Threat",       InsiderThreatPage()),
            ("  🎣  Deception System",     DeceptionPage()),
            ("  📡  Live Monitoring",      LiveMonitoringPage()),
            ("  🔒  Quarantine",           QuarantinePage()),
            ("  🔔  Alerts",              AlertsPage()),
            ("  📋  Logs",               LogsPage()),
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
        page = self._pages.currentWidget ()
        if hasattr(page, "reload"):
            page.reload()

    def _toggle_sb(self):
        self._sb_vis = not self._sb_vis
        self._sb.setVisible(self._sb_vis)
        self._col_btn.setText("›" if not self._sb_vis else "‹")
    
    def _go_to_scan_page(self):
        """Navigate to the Security Scan page when button is clicked from dashboard."""
        scan_index = self._pages.indexOf(self._scan_page)
        if scan_index != -1:
            self._nav(scan_index)

    def _signout(self):
        try:
            from frontend.login import MainWindow
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