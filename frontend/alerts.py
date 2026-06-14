# NOVASPHERE — Alerts Management Page

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QScrollArea, QLineEdit, QComboBox, QSizePolicy
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QCursor, QFont

# ── Color tokens (mirrored from main dashboard) ───────────────────────────────
BG_MAIN    = "#0b0f1a"
BG_CARD    = "#131929"
BG_CARD2   = "#161e30"
CYAN       = "#00bcd4"
BORDER     = "#1e2d45"
TEXT_WHITE = "#e8eaf0"
TEXT_MUTED = "#4a5a78"
TEXT_SUB   = "#6b7a99"

SEV_CRITICAL = "#e53935"
SEV_HIGH     = "#fb8c00"
SEV_MEDIUM   = "#fdd835"
SEV_LOW      = "#42a5f5"

STATUS_OPEN        = ("#e53935", "#2a1010")
STATUS_INVESTIGATING = ("#fb8c00", "#1e1500")
STATUS_RESOLVED    = ("#00c853", "#0a1f0f")

STYLE = f"""
QWidget#alerts_root {{
    background: {BG_MAIN};
}}
#page_title {{
    color: {TEXT_WHITE}; font-size: 26px; font-weight: 700;
    background: transparent;
}}
#page_sub {{
    color: {TEXT_MUTED}; font-size: 13px; background: transparent;
}}
#export_btn {{
    background: {BG_CARD}; border: 1px solid {BORDER};
    color: {TEXT_WHITE}; font-size: 13px; font-weight: 600;
    padding: 9px 20px; border-radius: 8px;
}}
#export_btn:hover {{
    border-color: {CYAN}; color: {CYAN};
}}
/* Severity summary cards */
#sev_card {{
    background: {BG_CARD}; border: 1px solid {BORDER};
    border-radius: 14px;
}}
#sev_count {{
    font-size: 32px; font-weight: 800; background: transparent;
}}
#sev_label {{
    color: {TEXT_MUTED}; font-size: 12px; letter-spacing: 1px;
    background: transparent;
}}
/* Table area */
#table_wrap {{
    background: {BG_CARD}; border: 1px solid {BORDER};
    border-radius: 14px;
}}
#search_alert {{
    background: {BG_MAIN}; border: 1px solid {BORDER};
    border-radius: 8px; color: {TEXT_WHITE}; font-size: 13px;
    padding: 8px 14px; min-width: 320px;
}}
#search_alert:focus {{ border-color: {CYAN}; }}
QComboBox#sev_filter {{
    background: {BG_MAIN}; border: 1px solid {BORDER};
    border-radius: 8px; color: {TEXT_WHITE}; font-size: 13px;
    padding: 7px 14px; min-width: 150px;
}}
QComboBox#sev_filter:hover {{ border-color: {CYAN}; }}
QComboBox#sev_filter QAbstractItemView {{
    background: {BG_CARD2}; color: {TEXT_WHITE};
    border: 1px solid {BORDER}; selection-background-color: {CYAN};
    selection-color: #000;
}}
QComboBox#sev_filter::drop-down {{ border: none; }}
/* Table header */
#th_lbl {{
    color: {TEXT_SUB}; font-size: 11px; font-weight: 700;
    letter-spacing: 1px; background: transparent;
    border-bottom: 1px solid {BORDER};
    padding-bottom: 8px;
}}
/* Row */
#row_frame {{
    background: transparent;
    border-bottom: 1px solid {BORDER};
}}
#row_frame:hover {{
    background: #0f1e2e;
}}
#alert_id {{
    color: {CYAN}; font-size: 13px; font-weight: 600;
    background: transparent;
}}
#threat_type {{
    color: {TEXT_WHITE}; font-size: 13px; font-weight: 600;
    background: transparent;
}}
#affected_user {{
    color: {TEXT_MUTED}; font-size: 13px; background: transparent;
}}
#target_proc {{
    color: {TEXT_MUTED}; font-size: 13px; background: transparent;
}}
#time_lbl {{
    color: {TEXT_SUB}; font-size: 12px; background: transparent;
}}
#arrow_btn {{
    background: transparent; border: none; color: {TEXT_MUTED};
    font-size: 16px; padding: 2px 4px;
}}
#arrow_btn:hover {{ color: {CYAN}; }}
"""

# ── Sample alert data ─────────────────────────────────────────────────────────
SAMPLE_ALERTS = [
    {"id": "ALT-1042", "severity": "Critical", "threat": "Ransomware",      "user": "SYSTEM",          "target": "File Server 01",  "status": "Open",          "time": "2 mins ago"},
    {"id": "ALT-1041", "severity": "High",     "threat": "Insider Threat",  "user": "jdoe",            "target": "Workstation-04",  "status": "Investigating", "time": "15 mins ago"},
    {"id": "ALT-1040", "severity": "Medium",   "threat": "Ransomware",      "user": "admin",           "target": "DC-02",           "status": "Resolved",      "time": "45 mins ago"},
    {"id": "ALT-1039", "severity": "Low",      "threat": "Policy Violation","user": "mscott",          "target": "Workstation-09",  "status": "Resolved",      "time": "1 hour ago"},
    {"id": "ALT-1038", "severity": "High",     "threat": "Insider Threat",  "user": "service_account", "target": "Database-01",     "status": "Open",          "time": "2 hours ago"},
    {"id": "ALT-1037", "severity": "Medium",   "threat": "Phishing",        "user": "pbeesly",         "target": "Mail Server",     "status": "Investigating", "time": "3 hours ago"},
    {"id": "ALT-1036", "severity": "Critical", "threat": "Privilege Escalation", "user": "guest",      "target": "AD-Controller",   "status": "Open",          "time": "4 hours ago"},
    {"id": "ALT-1035", "severity": "Low",      "threat": "Port Scan",       "user": "SYSTEM",          "target": "Firewall-01",     "status": "Resolved",      "time": "5 hours ago"},
]

# ── Severity badge widget ─────────────────────────────────────────────────────
class SeverityBadge(QLabel):
    ICONS   = {"Critical": "🔴", "High": "⚠️", "Medium": "🔔", "Low": "🔷"}
    COLORS  = {
        "Critical": (SEV_CRITICAL, "#2a1010"),
        "High":     (SEV_HIGH,     "#1e1500"),
        "Medium":   (SEV_MEDIUM,   "#1e1900"),
        "Low":      (SEV_LOW,      "#0a1520"),
    }

    def __init__(self, severity: str, parent=None):
        super().__init__(parent)
        icon = self.ICONS.get(severity, "")
        fg, bg = self.COLORS.get(severity, (TEXT_MUTED, BG_CARD))
        self.setText(f"  {icon}  {severity}  ")
        self.setFixedHeight(26)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setStyleSheet(
            f"color: {fg}; background: {bg}; border: 1px solid {fg};"
            f"border-radius: 13px; font-size: 12px; font-weight: 700;"
        )


# ── Status badge widget ───────────────────────────────────────────────────────
class StatusBadge(QLabel):
    STYLES = {
        "Open":          (SEV_CRITICAL, "#2a1010"),
        "Investigating": (SEV_HIGH,     "#1e1500"),
        "Resolved":      ("#00c853",    "#0a1f0f"),
    }

    def __init__(self, status: str, parent=None):
        super().__init__(parent)
        fg, bg = self.STYLES.get(status, (TEXT_MUTED, BG_CARD))
        self.setText(f"  {status}  ")
        self.setFixedHeight(24)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setStyleSheet(
            f"color: {fg}; background: {bg}; border: 1px solid {fg};"
            f"border-radius: 4px; font-size: 12px; font-weight: 600;"
        )


# ── Summary card ──────────────────────────────────────────────────────────────
class SeverityCard(QFrame):
    ICON_MAP = {
        "Critical": ("🛡", SEV_CRITICAL),
        "High":     ("⚠", SEV_HIGH),
        "Medium":   ("🔔", SEV_MEDIUM),
        "Low":      ("🔷", SEV_LOW),
    }

    def __init__(self, severity: str, count: int, parent=None):
        super().__init__(parent)
        self.setObjectName("sev_card")
        lay = QHBoxLayout(self)
        lay.setContentsMargins(20, 18, 20, 18)
        lay.setSpacing(16)

        icon_char, color = self.ICON_MAP.get(severity, ("●", CYAN))

        left = QVBoxLayout(); left.setSpacing(4)
        lbl = QLabel(f"{severity} Alerts")
        lbl.setObjectName("sev_label")
        count_lbl = QLabel(str(count))
        count_lbl.setObjectName("sev_count")
        count_lbl.setStyleSheet(f"color: {color}; font-size: 32px; font-weight: 800; background: transparent;")
        left.addWidget(lbl)
        left.addWidget(count_lbl)

        icon_w = QLabel(icon_char)
        icon_w.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon_w.setFixedSize(44, 44)
        icon_w.setStyleSheet(
            f"background: {color}22; border: 1px solid {color}55;"
            f"border-radius: 22px; font-size: 20px; color: {color};"
        )

        lay.addLayout(left, 1)
        lay.addWidget(icon_w)


# ── Single alert row ──────────────────────────────────────────────────────────
class AlertRow(QFrame):
    def __init__(self, alert: dict, parent=None):
        super().__init__(parent)
        self.setObjectName("row_frame")
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.setFixedHeight(56)

        lay = QHBoxLayout(self)
        lay.setContentsMargins(16, 0, 12, 0)
        lay.setSpacing(0)

        def cell(w, stretch=0):
            lay.addWidget(w, stretch)

        # Alert ID
        id_lbl = QLabel(alert["id"]); id_lbl.setObjectName("alert_id")
        id_lbl.setFixedWidth(90)
        cell(id_lbl)

        # Severity badge
        badge = SeverityBadge(alert["severity"])
        badge.setFixedWidth(110)
        cell(badge)

        lay.addSpacing(8)

        # Threat type
        tt = QLabel(alert["threat"]); tt.setObjectName("threat_type")
        tt.setFixedWidth(160)
        cell(tt)

        # Affected user
        user_icon = QLabel(f"👤  {alert['user']}"); user_icon.setObjectName("affected_user")
        user_icon.setFixedWidth(170)
        cell(user_icon)

        # Target / process
        tgt = QLabel(alert["target"]); tgt.setObjectName("target_proc")
        tgt.setFixedWidth(160)
        cell(tgt)

        # Status
        st = StatusBadge(alert["status"])
        st.setFixedWidth(120)
        cell(st)

        # Time
        tm = QLabel(alert["time"]); tm.setObjectName("time_lbl")
        tm.setFixedWidth(110)
        cell(tm)

        # Arrow
        arr = QPushButton("›"); arr.setObjectName("arrow_btn"); arr.setFixedSize(24, 24)
        cell(arr)


# ── Main Alerts page ──────────────────────────────────────────────────────────
class AlertsPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("alerts_root")
        self.setStyleSheet(STYLE)
        self._all_alerts = list(SAMPLE_ALERTS)
        self._filter_sev = "All Severities"
        self._search_txt = ""
        self._build()
        # Live-update timer: bumps the first alert's time every 30s
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick)
        self._timer.start(30_000)

    # ── Build UI ──────────────────────────────────────────────────────────────
    def _build(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(32, 24, 32, 28)
        outer.setSpacing(20)
        outer.setAlignment(Qt.AlignmentFlag.AlignTop)

        # ── Header row ────────────────────────────────────────────────────────
        hdr = QHBoxLayout(); hdr.setSpacing(0)

        titles = QVBoxLayout(); titles.setSpacing(3)
        page_title = QLabel("Alerts Management"); page_title.setObjectName("page_title")
        page_sub   = QLabel("Real-time incident monitoring and response"); page_sub.setObjectName("page_sub")
        titles.addWidget(page_title); titles.addWidget(page_sub)
        hdr.addLayout(titles); hdr.addStretch()

        export_btn = QPushButton("⬇  Export Report"); export_btn.setObjectName("export_btn")
        export_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        hdr.addWidget(export_btn)
        outer.addLayout(hdr)

        # ── Severity summary cards ────────────────────────────────────────────
        cards_row = QHBoxLayout(); cards_row.setSpacing(16)
        self._sev_counts = self._count_severities()
        self._sev_cards  = {}
        for sev in ("Critical", "High", "Medium", "Low"):
            card = SeverityCard(sev, self._sev_counts.get(sev, 0))
            self._sev_cards[sev] = card
            cards_row.addWidget(card, 1)
        outer.addLayout(cards_row)

        # ── Table card ────────────────────────────────────────────────────────
        table_card = QFrame(); table_card.setObjectName("table_wrap")
        tc_lay = QVBoxLayout(table_card)
        tc_lay.setContentsMargins(16, 16, 16, 16)
        tc_lay.setSpacing(10)

        # Search + filter bar
        sf_row = QHBoxLayout(); sf_row.setSpacing(12)
        self._search = QLineEdit()
        self._search.setObjectName("search_alert")
        self._search.setPlaceholderText("🔍   Search alert ID, user, or target...")
        self._search.textChanged.connect(self._on_search)
        sf_row.addWidget(self._search, 1)
        sf_row.addStretch()

        self._filter = QComboBox(); self._filter.setObjectName("sev_filter")
        for opt in ("All Severities", "Critical", "High", "Medium", "Low"):
            self._filter.addItem(opt)
        self._filter.currentTextChanged.connect(self._on_filter)
        sf_row.addWidget(self._filter)
        tc_lay.addLayout(sf_row)

        # Column headers
        th_row = QHBoxLayout(); th_row.setContentsMargins(16, 0, 12, 0); th_row.setSpacing(0)
        headers = [
            ("ALERT ID",       90),
            ("SEVERITY",       118),
            ("THREAT TYPE",    168),
            ("AFFECTED USER",  178),
            ("TARGET / PROCESS", 168),
            ("STATUS",         128),
            ("TIME",           110),
        ]
        for txt, w in headers:
            lbl = QLabel(txt); lbl.setObjectName("th_lbl"); lbl.setFixedWidth(w)
            th_row.addWidget(lbl)
        th_row.addStretch()
        tc_lay.addLayout(th_row)

        # Scrollable rows area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")

        self._rows_widget = QWidget()
        self._rows_widget.setStyleSheet("background: transparent;")
        self._rows_layout = QVBoxLayout(self._rows_widget)
        self._rows_layout.setContentsMargins(0, 0, 0, 0)
        self._rows_layout.setSpacing(0)
        self._rows_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        scroll.setWidget(self._rows_widget)

        tc_lay.addWidget(scroll, 1)
        outer.addWidget(table_card, 1)

        self._populate_rows()

    # ── Data helpers ──────────────────────────────────────────────────────────
    def _count_severities(self):
        counts: dict[str, int] = {}
        for a in self._all_alerts:
            counts[a["severity"]] = counts.get(a["severity"], 0) + 1
        return counts

    def _filtered(self):
        result = self._all_alerts
        if self._filter_sev != "All Severities":
            result = [a for a in result if a["severity"] == self._filter_sev]
        if self._search_txt:
            q = self._search_txt.lower()
            result = [
                a for a in result
                if q in a["id"].lower()
                or q in a["user"].lower()
                or q in a["target"].lower()
                or q in a["threat"].lower()
            ]
        return result

    def _populate_rows(self):
        # Clear existing rows
        while self._rows_layout.count():
            item = self._rows_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        for alert in self._filtered():
            row = AlertRow(alert)
            self._rows_layout.addWidget(row)

        # Empty-state label
        if not self._filtered():
            empty = QLabel("No alerts match your search.")
            empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
            empty.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 14px; padding: 40px; background: transparent;")
            self._rows_layout.addWidget(empty)

    def _refresh_sev_cards(self):
        counts = self._count_severities()
        for sev, card in self._sev_cards.items():
            # Update the count label (second widget in the left layout)
            left_lay = card.layout().itemAt(0).layout()
            count_lbl = left_lay.itemAt(1).widget()
            count_lbl.setText(str(counts.get(sev, 0)))

    # ── Slots ─────────────────────────────────────────────────────────────────
    def _on_search(self, text: str):
        self._search_txt = text
        self._populate_rows()

    def _on_filter(self, text: str):
        self._filter_sev = text
        self._populate_rows()

    def _tick(self):
        """Called by timer — simulate a new incoming alert."""
        import random
        new_id_num = int(self._all_alerts[0]["id"].split("-")[1]) + 1
        new_alert = {
            "id":       f"ALT-{new_id_num}",
            "severity": random.choice(["Critical", "High", "Medium", "Low"]),
            "threat":   random.choice(["Ransomware", "Insider Threat", "Policy Violation", "Phishing"]),
            "user":     random.choice(["SYSTEM", "jdoe", "admin", "mscott", "service_account"]),
            "target":   random.choice(["File Server 01", "Workstation-04", "DC-02", "Database-01"]),
            "status":   "Open",
            "time":     "just now",
        }
        self._all_alerts.insert(0, new_alert)
        self._refresh_sev_cards()
        self._populate_rows()

    # ── Called by NovaSphereWindow on tab switch ──────────────────────────────
    def reload(self):
        self._populate_rows()