# NOVASPHERE — Main Dashboard
#frontend / main_window.py

import sqlite3
import sys
import os
import qtawesome as qta
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import math
import random
from datetime import datetime
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QFrame, QScrollArea, QStackedWidget,
    QLineEdit, QCheckBox, QGridLayout, QSizePolicy, QMenu
)
from PyQt6.QtCore import Qt, QTimer, QRect, QSize
from PyQt6.QtGui import (
    QColor, QPalette, QPainter, QPen, QBrush, QFont,
    QLinearGradient, QCursor,QFontDatabase

)

from .scan import ScanPage
from .insider_threat import InsiderThreatPage
from .security_overview import SecurityOverviewPage
from .ransomwarepage import RansomwareDetectionPage, launch_flask_thread
from .quarantine import QuarantinePage
from .alerts import AlertsPage
from .live_monitoring_page import LiveMonitoringPage
from .deception_page import DeceptionPage 
from .logs import LogsPage
from .settings import SettingsPage
from .reports import ReportsPage
import threading
from auth.auth_db import cleanup_old_alerts

# Colors 
from .nova_style import (
    BG_MAIN, BG_CARD, BG_CARD2, BG_ROW, CYAN, CYAN_DIM, BG_TOPBAR, BG_SIDEBAR, BG_MODULE, BORDER, TEXT_WHITE, TEXT_MUTED, TEXT_SUB,
    RED, ORANGE, GREEN, YELLOW, BLUE
)

STYLE = f"""
* {{ font-family: 'Segoe UI', 'Material Design Icons', sans-serif; }}

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
background: {BG_SIDEBAR}; border-right: 5px solid {BORDER}; 
min-width: 220px; max-width: 220px;
}}

QPushButton#nav_btn {{
    background: transparent; border: none; color: {TEXT_MUTED};
    text-align: left; padding: 8px 18px; font-size: 14px;
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
    text-align: left; padding: 11px 20px; font-size: 20px;
}}

QPushButton#signout_btn:hover {{ color: #ff5252; }}

QPushButton#notif_btn {{ 
    background: transparent; 
    border: none; color: {TEXT_MUTED}; 
    font-size: 25px; 
    padding: 4px 8px; }}

QPushButton#notif_btn:hover {{ color: {CYAN}; }}

#search_bar {{
    background: #111827; border: 1px solid {BORDER};
    border-radius: 5px; color: {TEXT_WHITE}; font-size: 15px;
    padding: 6px 14px; min-width: 350px;
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

#  Dashboard page 

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
    l.setStyleSheet(f"color:{TEXT_MUTED};font-size:26px;background:transparent;")
    l.setAlignment(Qt.AlignmentFlag.AlignCenter)
    s = QLabel("This section is under development")
    s.setStyleSheet(f"color:{BORDER};font-size:25px;background:transparent;")
    s.setAlignment(Qt.AlignmentFlag.AlignCenter)
    lay.addWidget(l); lay.addSpacing(8); lay.addWidget(s)
    return w

def launch_monitoring_thread():
    """Start file-system + process monitoring in background daemon threads."""
    try:
        from src.monitoring.main import start_monitoring
        from src.monitoring.process_monitor import process_monitor
        from ransomware_part.monitor import start_monitoring as start_ransomware_monitoring

        t = threading.Thread(target=start_monitoring, daemon=True)
        t.start()
        ransomware_thread = threading.Thread(target=start_ransomware_monitoring, daemon=True)
        ransomware_thread.start()
        process_monitor.start()
    except Exception as e:
        print(f"[monitoring] Failed to start background monitoring: {e}")

def _resource_path(rel_path):
    """Resolve a bundled resource path whether running from source or from a frozen .exe."""
    base = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base, rel_path)

def load_icon_font():
    font_path = _resource_path("resources/fonts/materialdesignicons6-webfont-6.9.96.ttf")
    font_id = QFontDatabase.addApplicationFont(font_path)
    if font_id == -1:
        print(f"[fonts] WARNING: failed to load icon font from {font_path}")
        return None
    families = QFontDatabase.applicationFontFamilies(font_id)
    print(f"[fonts] Loaded icon font: {families}")
    return families[0] if families else None

def _load_retention_days(default: int = 30) -> int:
    try:
        from .settings import _load_settings
        saved = _load_settings()
        return saved.get("retention_days", default)
    except Exception as e:
        print(f"[settings] Could not load retention setting, using default: {e}")
        return default

def _run_cleanup_async():
    """Runs on a background thread so it never blocks the splash/UI."""
    try:
        retention = _load_retention_days()
        cleanup_old_alerts(days=retention)
        print(f"[cleanup] Done (retention={retention} days)")
    except Exception as e:
        print(f"[cleanup] Failed: {e}")

# ── Main window 
class NovaSphereWindow(QMainWindow):
    def __init__(self, current_user="Admin"):
        super().__init__()
        print("CHECKPOINT 1: super().__init__ done")
        full_name = current_user or "Admin"
        self._username = full_name.strip().split(" ")[0]
        self._seen_alert_count = 0
        self.setWindowTitle("NOVASPHERE — Security Dashboard")
        self.setMinimumSize(1200,760); self.resize(1380,820)
        self.setStyleSheet(STYLE)
        print("CHECKPOINT 2: style set")
        QTimer.singleShot(5000, lambda: threading.Thread(target=_run_cleanup_async, daemon=True).start())
        print("CHECKPOINT 3: cleanup thread started")
        launch_flask_thread()
        print("CHECKPOINT 4:flask thread launched")
        launch_monitoring_thread()
        print("CHECKPOINT 5: monitoring thread launched")
        self._build()
        print("CHECKPOINT 6: _build() done")

    def _build(self):
        root = QWidget(); self.setCentralWidget(root)
        main = QVBoxLayout(root); main.setContentsMargins(0,0,0,0); main.setSpacing(0)

        # Topbar
        
        tb_w = QWidget(); tb_w.setObjectName("topbar"); tb_w.setFixedHeight(60)
        tb = QHBoxLayout(tb_w); tb.setContentsMargins(20,0,20,0); tb.setSpacing(0)

        shield = QLabel("󰒘"); shield.setStyleSheet(f"color:{CYAN};font-size:26px;background:transparent;padding-right:8px;")
        nova   = QLabel("NOVA"); nova.setStyleSheet(f"color:{TEXT_WHITE};font-size:25px;font-weight:800;background:transparent;")
        sphere = QLabel("SPHERE"); sphere.setStyleSheet(f"color:{CYAN};font-size:25px;font-weight:800;background:transparent;")
        self._col_btn = QPushButton("‹"); self._col_btn.setObjectName("notif_btn")
        self._col_btn.setFixedSize(50,50); self._col_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        for w in [shield,nova,sphere]: tb.addWidget(w)
        tb.addSpacing(12); tb.addWidget(self._col_btn); tb.addStretch()

        self._global_search = QLineEdit()
        self._global_search.setObjectName("search_bar")
        self._global_search.setPlaceholderText(
            "Search threats, users, files, or logs... Press Enter"
        )
        self._global_search.setMaximumWidth(380)
        self._global_search.returnPressed.connect(self._run_global_search)

        tb.addWidget(self._global_search)
        tb.addStretch()

        notif = QPushButton("󰂜"); notif.setObjectName("notif_btn"); notif.setFixedSize(36,36)
        tb.addWidget(notif); tb.addSpacing(16)

        self._notif_btn = notif
        self._notif_btn.setToolTip("Open new security alerts")
        self._notif_btn.clicked.connect(self._show_notification_menu)

        ac = QVBoxLayout(); ac.setSpacing(1); ac.setAlignment(Qt.AlignmentFlag.AlignVCenter)
        an = QLabel(self._username); an.setStyleSheet(f"color:{TEXT_WHITE};font-size:17px;font-weight:600;background:transparent;")
        ar = QLabel("Security Operations"); ar.setStyleSheet(f"color:{CYAN};font-size:13px;background:transparent;")
        ac.addWidget(an); ac.addWidget(ar); tb.addLayout(ac); tb.addSpacing(12)

        initial = self._username[0].upper() if self._username else "A"
        av = QLabel(initial); av.setAlignment(Qt.AlignmentFlag.AlignCenter); av.setFixedSize(36,36)
        av.setStyleSheet(f"background:{CYAN};color:#000;border-radius:18px;font-size:14px;font-weight:800;")
        tb.addWidget(av)
        main.addWidget(tb_w)

        # Body
        body = QHBoxLayout(); body.setSpacing(0); body.setContentsMargins(0,0,0,0)

        # Sidebar
        self._sb = QWidget(); self._sb.setObjectName("sidebar"); self._sb.setFixedWidth(300)
        sbl = QVBoxLayout(self._sb); sbl.setContentsMargins(0,25,0,25); sbl.setSpacing(2)

        self._pages = QStackedWidget()
        self._btns  = []

        self._security_page = SecurityOverviewPage(scan_callback=self._go_to_scan_page)
        print("CHECKPOINT 7: SecurityOverviewPage created")

        ransomware_page = RansomwareDetectionPage()
        print("CHECKPOINT 7a: RansomwareDetectionPage created")

        insider_page = InsiderThreatPage(current_user=self._username)
        print("CHECKPOINT 7b: InsiderThreatPage created")

        deception_page = DeceptionPage()
        print("CHECKPOINT 7c: DeceptionPage created")

        live_page = LiveMonitoringPage()
        print("CHECKPOINT 7d: LiveMonitoringPage created")

        quarantine_page = QuarantinePage()
        print("CHECKPOINT 7e: QuarantinePage created")

        alerts_page = AlertsPage()
        print("CHECKPOINT 7f: AlertsPage created")

        logs_page = LogsPage()
        print("CHECKPOINT 7g: LogsPage created")

        reports_page = ReportsPage()
        print("CHECKPOINT 7h: ReportsPage created")

        settings_page = SettingsPage()
        print("CHECKPOINT 7i: SettingsPage created")
        
        items = [
            ("  󰕮  Dashboard",  self._security_page),
            ("  󰚽  Ransomware Detection", RansomwareDetectionPage()),
            ("  󰀩  Insider Threat",       InsiderThreatPage(current_user=self._username)),
            ("  󰎛  Deception System",     DeceptionPage()),
            ("  󰌵  Live Monitoring",      live_page),
            ("  󰍁  Quarantine",           QuarantinePage()),
            ("  󰀦  Alerts",              alerts_page),
            ("  󱀉  Logs",               LogsPage()),
            ("  󰂺  Reports",            ReportsPage()),
            ("  󰢻  Settings",          SettingsPage()),
        ]
        # Manual scans persist detections in the background. Refresh the pages
        # that present those detections as soon as the scan is complete.
        self._security_page._scan_page.scan_complete.connect(
            lambda _total, _threats: alerts_page.reload()
        )
        self._security_page._scan_page.scan_complete.connect(
            lambda _total, _threats: live_page.reload()
        )
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

        QTimer.singleShot(800, self._security_page._run_startup_scan)

        body.addWidget(self._sb); body.addWidget(self._pages,1)
        bw = QWidget(); bw.setLayout(body)
        main.addWidget(bw,1)

        self._sb_vis = True
        self._col_btn.clicked.connect(self._toggle_sb)
        self._seen_alert_count = self._alert_count()
        self._notification_timer = QTimer(self)
        self._notification_timer.timeout.connect(self._refresh_notification_badge)
        self._notification_timer.start(2_000)

    def _nav(self, idx):
        if getattr(self, "_navigating", False):
            return
        self._navigating = True
        try:
            self._pages.setCurrentIndex(idx)
            for i, b in enumerate(self._btns):
                b.setProperty("active", "true" if i == idx else "false")
                b.style().unpolish(b); b.style().polish(b)
            page = self._pages.currentWidget()
            if hasattr(page, "reload"):
                page.reload()
        finally:
            self._navigating = False
                
    def _toggle_sb(self):
        self._sb_vis = not self._sb_vis
        self._sb.setVisible(self._sb_vis)
        self._col_btn.setText("›" if not self._sb_vis else "‹")
    
    def _alert_count(self) -> int:
        """Read persisted alerts, never sample UI data."""
        try:
            from auth.app_paths import get_logs_dir
            with sqlite3.connect(get_logs_dir() / "novasphere.db", timeout=5) as conn:
                return conn.execute("SELECT COUNT(*) FROM alerts").fetchone()[0]
        except sqlite3.Error:
            return 0

    def _refresh_notification_badge(self):
        unread = max(0, self._alert_count() - self._seen_alert_count)
        if unread:
            self._notif_btn.setText(f"󰂜 {unread}")
            self._notif_btn.setStyleSheet(f"color:{RED}; font-weight:700;")
        else:
            self._notif_btn.setText("󰂜")
            self._notif_btn.setStyleSheet("")

    def _open_notifications(self):
        """Mark current alerts as seen and open the live Alerts page."""
        self._seen_alert_count = self._alert_count()
        self._refresh_notification_badge()
        self._nav(6)

    def _recent_alerts(self, limit=5):
            """Return the newest persisted alerts for the notification dropdown."""
            try:
                from auth.app_paths import get_logs_dir
    
                with sqlite3.connect(get_logs_dir() / "novasphere.db", timeout=5) as conn:
                    rows = conn.execute(
                        """
                        SELECT timestamp, alert_type, severity, message
                        FROM alerts
                        ORDER BY rowid DESC
                        LIMIT ?
                        """,
                        (limit,),
                    ).fetchall()
    
                return rows
            except sqlite3.Error:
                return []

    def _run_global_search(self):
        """Search real alert and event data, then open the relevant page."""
        query = self._global_search.text().strip()

        if not query:
            return

        pattern = f"%{query}%"
        alert_match = False
        event_match = False

        try:
            from auth.app_paths import get_logs_dir

            with sqlite3.connect(get_logs_dir() / "novasphere.db", timeout=5) as conn:
                alert_match = conn.execute(
                    """
                    SELECT 1
                    FROM alerts
                    WHERE alert_type LIKE ?
                        OR message LIKE ?
                        OR file_path LIKE ?
                        OR source LIKE ?
                    LIMIT 1
                    """,
                    (pattern, pattern, pattern, pattern),
                ).fetchone() is not None

                event_match = conn.execute(
                    """
                    SELECT 1
                    FROM events
                    WHERE event_type LIKE ?
                        OR file_path LIKE ?
                        OR username LIKE ?
                    LIMIT 1
                    """,
                    (pattern, pattern, pattern),
                ).fetchone() is not None

        except sqlite3.Error as exc:
            print(f"[search] Database search failed: {exc}")

        if alert_match:
            # Alerts page is index 6 in the main navigation.
            self._nav(6)
            alerts_page = self._pages.widget(6)
            alerts_page._search.setText(query)

        elif event_match:
            # Logs page is index 7 in the main navigation.
            self._nav(7)
            logs_page = self._pages.widget(7)
            logs_page._search.setText(query)

        else:
            # Show an empty filtered Alerts page when there is no match.
            self._nav(6)
            alerts_page = self._pages.widget(6)
            alerts_page._search.setText(query)

    def _go_to_scan_page(self):
        self._nav(0)
        if hasattr(self._security_page, "_show_scan"):
            self._security_page._show_scan()


    def _show_notification_menu(self):
        """Display the newest alerts under the notification bell."""
        menu = QMenu(self)
        menu.setStyleSheet(f"""
            QMenu {{
                background: {BG_CARD};
                color: {TEXT_WHITE};
                border: 1px solid {BORDER};
                border-radius: 8px;
                padding: 6px;
                min-width: 340px;
            }}
            QMenu::item {{
                padding: 10px 12px;
                border-radius: 5px;
            }}
            QMenu::item:selected {{
                background: {BG_CARD2};
                color: {CYAN};
            }}
            QMenu::separator {{
                height: 1px;
                background: {BORDER};
                margin: 5px 8px;
            }}
        """)

        alerts = self._recent_alerts()

        if not alerts:
            empty = menu.addAction("No new alerts")
            empty.setEnabled(False)
        else:
            for timestamp, alert_type, severity, message in alerts:
                text = (
                    f"[{severity}] {alert_type.replace('_', ' ').title()}\n"
                    f"{message or 'Security alert detected'} — {timestamp}"
                )
                action = menu.addAction(text)
                action.triggered.connect(self._open_notifications)

            menu.addSeparator()

            view_all = menu.addAction("View all alerts")
            view_all.triggered.connect(self._open_notifications)

        # Opening the dropdown marks current alerts as seen.
        self._seen_alert_count = self._alert_count()
        self._refresh_notification_badge()

        menu.exec(
            self._notif_btn.mapToGlobal(
                self._notif_btn.rect().bottomLeft()
            )
        )

    def _signout(self):
        try:
            from auth.session_manager import SessionManager
            session_mgr = SessionManager()
            token = session_mgr.load_token_from_disk()
            if token:
                session_mgr.revoke_session(token)
            session_mgr.clear_token_from_disk()
        except Exception as e:
            print(f"[signout] Failed to clear session: {e}")
        try:
            from frontend.login import MainWindow
            self.hide()
            self._lw = MainWindow()
            if not self._lw._dashboard_launched:
                self._lw.show()
        except ImportError:
            self.close()

# ── Entry ─────────────────────────────────────────────────────────────────────
def main():
    app = QApplication(sys.argv)
    icon_family = load_icon_font()
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
