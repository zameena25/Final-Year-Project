# NOVASPHERE — Logs Page
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QScrollArea, QFrame, QComboBox, QGridLayout,
    QSizePolicy
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QCursor, QColor

# ── Colour tokens (match main window) ─────────────────────────────────────────
BG_MAIN    = "#0b0f1a"
BG_CARD    = "#131929"
BG_CARD2   = "#161e30"
CYAN       = "#00bcd4"
BORDER     = "#1e2d45"
TEXT_WHITE = "#e8eaf0"
TEXT_MUTED = "#4a5a78"
TEXT_SUB   = "#6b7a99"

# ── Sample log data ────────────────────────────────────────────────────────────
SAMPLE_LOGS = [
    ("2025-05-15 14:32:45", "Critical",  "SYSTEM",          "svchost.exe",        "C:/Windows/System32/drivers/etc/hosts",  "Write Attempt",       "BLOCKED"),
    ("2025-05-15 14:30:12", "Warning",   "jdoe",            "powershell.exe",      "D:/Data/Finance/Q2_Report.xlsx",         "Mass Delete",         "FLAGGED"),
    ("2025-05-15 14:28:05", "Info",      "network_service", "chrome.exe",          "N/A",                                    "Outbound Connection",  "ALLOWED"),
    ("2025-05-15 14:15:22", "High",      "admin",           "cmd.exe",             "C:/Users/Admin/AppData/Local/Temp/malware.bat", "Execution",     "QUARANTINED"),
    ("2025-05-15 13:55:01", "Success",   "backup_svc",      "backup_agent.exe",    "E:/Backups/Daily_Full.zip",              "File Write",          "COMPLETED"),
    ("2025-05-15 13:42:19", "Warning",   "guest",           "explorer.exe",        "Z:/Shared/Confidential",                 "Access Denied",       "BLOCKED"),
    ("2025-05-15 13:30:00", "Info",      "SYSTEM",          "update_service.exe",  "C:/Program Files/Updates",               "Patch Install",       "SUCCESS"),
    ("2025-05-15 13:15:44", "Critical",  "unknown",         "ransom.exe",          "D:/Data/User/Docs/*",                    "Encryption",          "BLOCKED"),
    ("2025-05-15 12:50:11", "High",      "mscott",          "outlook.exe",         "C:/Users/mscott/Downloads/invoice.js",   "Download",            "SCANNED"),
    ("2025-05-15 12:45:33", "Success",   "SYSTEM",          "winlogon.exe",        "N/A",                                    "User Login",          "SUCCESS"),
    ("2025-05-15 12:30:15", "Info",      "jdoe",            "code.exe",            "C:/Projects/Source/main.ts",             "File Read",           "ALLOWED"),
    ("2025-05-15 12:10:05", "Warning",   "SYSTEM",          "firewall.exe",        "N/A",                                    "Port Scan Detected",  "BLOCKED"),
]

# ── Severity badge colours ─────────────────────────────────────────────────────
SEVERITY_STYLE = {
    "Critical": ("background:#3a0a0a; color:#ff4444; border:1px solid #7a1a1a;"),
    "High":     ("background:#3a2000; color:#ff9800; border:1px solid #7a4000;"),
    "Warning":  ("background:#2e2500; color:#ffc107; border:1px solid #5a4a00;"),
    "Info":     ("background:#002a3a; color:#00bcd4; border:1px solid #005a7a;"),
    "Success":  ("background:#0a2e1a; color:#4caf50; border:1px solid #1a5a2a;"),
}

# ── Stat card ──────────────────────────────────────────────────────────────────
def _stat_card(icon, value, label, sub, icon_color=TEXT_MUTED):
    card = QFrame()
    card.setObjectName("stat_card")
    card.setStyleSheet(f"""
        QFrame#stat_card {{
            background:{BG_CARD}; border:1px solid {BORDER}; border-radius:14px;
        }}
    """)
    card.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
    card.setFixedHeight(100)

    lay = QHBoxLayout(card)
    lay.setContentsMargins(20, 16, 20, 16)
    lay.setSpacing(14)

    left = QVBoxLayout(); left.setSpacing(2)
    lbl = QLabel(label)
    lbl.setStyleSheet(f"color:{TEXT_MUTED}; font-size:12px; background:transparent;")
    val = QLabel(value)
    val.setStyleSheet(f"color:{TEXT_WHITE}; font-size:28px; font-weight:700; background:transparent;")
    sub_lbl = QLabel(sub)
    sub_lbl.setStyleSheet(f"color:{TEXT_MUTED}; font-size:11px; background:transparent;")
    left.addWidget(lbl); left.addWidget(val); left.addWidget(sub_lbl)

    ico = QLabel(icon)
    ico.setStyleSheet(f"color:{icon_color}; font-size:22px; background:transparent;")
    ico.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignTop)

    lay.addLayout(left, 1)
    lay.addWidget(ico)
    return card


# ── Log table row ──────────────────────────────────────────────────────────────
def _table_row(timestamp, severity, user, process, file_target, action, status, zebra=False):
    row = QFrame()
    row.setStyleSheet(f"""
        QFrame {{
            background:{"#10172a" if zebra else BG_MAIN};
            border-bottom:1px solid {BORDER};
        }}
        QFrame:hover {{ background:#1a2540; }}
    """)

    lay = QHBoxLayout(row)
    lay.setContentsMargins(14, 10, 14, 10)
    lay.setSpacing(0)

    def col(text, width, color=TEXT_MUTED, mono=False):
        lbl = QLabel(text)
        lbl.setFixedWidth(width)
        font_fam = "'Consolas','Courier New',monospace" if mono else "'Segoe UI',sans-serif"
        lbl.setStyleSheet(
            f"color:{color}; font-size:12px; background:transparent; font-family:{font_fam};"
        )
        lbl.setWordWrap(False)
        return lbl

    # Timestamp
    lay.addWidget(col(timestamp, 145, TEXT_MUTED, mono=True))

    # Severity badge
    badge = QLabel(severity)
    sty = SEVERITY_STYLE.get(severity, f"background:{BG_CARD}; color:{TEXT_MUTED}; border:1px solid {BORDER};")
    badge.setStyleSheet(
        f"{sty} font-size:11px; font-weight:600; border-radius:6px; padding:2px 8px; background:transparent;"
        .replace("background:transparent;", "")   # keep badge bg
    )
    badge.setFixedWidth(80)
    badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
    lay.addWidget(badge)
    lay.addSpacing(10)

    # User
    user_w = QHBoxLayout(); user_w.setSpacing(4); user_w.setContentsMargins(0,0,0,0)
    ico = QLabel("👤"); ico.setStyleSheet("font-size:11px; background:transparent;")
    u_lbl = col(user, 120, TEXT_WHITE)
    user_w.addWidget(ico); user_w.addWidget(u_lbl)
    user_container = QWidget(); user_container.setLayout(user_w)
    user_container.setStyleSheet("background:transparent;")
    lay.addWidget(user_container)

    # Process
    proc_w = QHBoxLayout(); proc_w.setSpacing(4); proc_w.setContentsMargins(0,0,0,0)
    p_ico = QLabel("⚙"); p_ico.setStyleSheet("font-size:11px; background:transparent;")
    p_lbl = QLabel(process)
    p_lbl.setFixedWidth(140)
    p_lbl.setStyleSheet(
        f"color:#7ecfda; font-size:11px; background:transparent; "
        f"font-family:'Consolas','Courier New',monospace;"
    )
    proc_w.addWidget(p_ico); proc_w.addWidget(p_lbl)
    proc_container = QWidget(); proc_container.setLayout(proc_w)
    proc_container.setStyleSheet("background:transparent;")
    lay.addWidget(proc_container)

    # File/Target
    file_lbl = QLabel(file_target)
    file_lbl.setStyleSheet(
        f"color:{TEXT_MUTED}; font-size:11px; background:transparent; "
        f"font-family:'Consolas','Courier New',monospace;"
    )
    file_lbl.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
    file_lbl.setWordWrap(False)
    lay.addWidget(file_lbl, 1)

    # Action + Status
    action_w = QVBoxLayout(); action_w.setSpacing(1); action_w.setContentsMargins(0,0,0,0)
    a_lbl = QLabel(action)
    a_lbl.setStyleSheet(f"color:{TEXT_WHITE}; font-size:12px; background:transparent;")
    s_lbl = QLabel(status)
    status_color = {
        "BLOCKED": "#ff4444", "FLAGGED": "#ffc107", "ALLOWED": "#4caf50",
        "QUARANTINED": "#ff9800", "COMPLETED": "#4caf50", "SUCCESS": "#4caf50",
        "SCANNED": CYAN,
    }.get(status, TEXT_MUTED)
    s_lbl.setStyleSheet(f"color:{status_color}; font-size:10px; font-weight:600; letter-spacing:1px; background:transparent;")
    action_w.addWidget(a_lbl); action_w.addWidget(s_lbl)
    action_container = QWidget()
    action_container.setLayout(action_w)
    action_container.setStyleSheet("background:transparent;")
    action_container.setFixedWidth(140)
    lay.addWidget(action_container)

    # ⋯ menu button
    more = QPushButton("⋯")
    more.setFixedSize(28, 28)
    more.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
    more.setStyleSheet(f"""
        QPushButton {{ background:transparent; border:none; color:{TEXT_MUTED}; font-size:16px; }}
        QPushButton:hover {{ color:{CYAN}; }}
    """)
    lay.addWidget(more)

    return row


# ── Logs Page ──────────────────────────────────────────────────────────────────
class LogsPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet(f"background:{BG_MAIN};")
        self._current_logs = list(SAMPLE_LOGS)
        self._build()

    def _build(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        # ── Scrollable body ────────────────────────────────────────────────────
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setStyleSheet("border:none; background:transparent;")

        body_w = QWidget()
        body_w.setStyleSheet(f"background:{BG_MAIN};")
        body = QVBoxLayout(body_w)
        body.setContentsMargins(28, 24, 28, 28)
        body.setSpacing(18)
        body.setAlignment(Qt.AlignmentFlag.AlignTop)

        # ── Header row ─────────────────────────────────────────────────────────
        hdr = QHBoxLayout()
        title_col = QVBoxLayout(); title_col.setSpacing(3)
        t = QLabel("Incident Logs")
        t.setStyleSheet(f"color:{TEXT_WHITE}; font-size:22px; font-weight:700; background:transparent;")
        sub = QLabel("Review system activities, security alerts, and user interactions")
        sub.setStyleSheet(f"color:{TEXT_MUTED}; font-size:13px; background:transparent;")
        title_col.addWidget(t); title_col.addWidget(sub)
        hdr.addLayout(title_col, 1)

        pdf_btn = QPushButton("  📄  Generate PDF Report")
        pdf_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        pdf_btn.setStyleSheet(f"""
            QPushButton {{
                background:transparent; border:1px solid {BORDER}; color:{TEXT_WHITE};
                font-size:13px; padding:8px 16px; border-radius:8px;
            }}
            QPushButton:hover {{ border-color:{CYAN}; color:{CYAN}; }}
        """)

        csv_btn = QPushButton("  ⬇  Export CSV")
        csv_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        csv_btn.setStyleSheet(f"""
            QPushButton {{
                background:{CYAN}; border:none; color:#000;
                font-size:13px; font-weight:600; padding:8px 16px; border-radius:8px;
            }}
            QPushButton:hover {{ background:#00d4f0; }}
        """)

        hdr.addWidget(pdf_btn)
        hdr.addSpacing(8)
        hdr.addWidget(csv_btn)
        body.addLayout(hdr)

        # ── Stat cards ─────────────────────────────────────────────────────────
        cards_row = QHBoxLayout(); cards_row.setSpacing(14)
        cards_row.addWidget(_stat_card("📋", "1,284", "Total Incidents",   "Last 24 hours",    TEXT_MUTED))
        cards_row.addWidget(_stat_card("🚨", "12",    "Critical Threats",   "+2 from yesterday", "#ff4444"))
        cards_row.addWidget(_stat_card("⚠",  "45",    "Warnings",           "Requires review",   "#ffc107"))
        cards_row.addWidget(_stat_card("✅", "892",   "Auto-Resolved",      "98% success rate",  "#4caf50"))
        body.addLayout(cards_row)

        # ── Search + filter bar ────────────────────────────────────────────────
        filter_row = QHBoxLayout(); filter_row.setSpacing(10)

        self._search = QLineEdit()
        self._search.setPlaceholderText("  🔍  Search by user, process, file, or event...")
        self._search.setStyleSheet(f"""
            QLineEdit {{
                background:#111827; border:1px solid {BORDER}; border-radius:8px;
                color:{TEXT_WHITE}; font-size:13px; padding:9px 14px;
            }}
            QLineEdit:focus {{ border-color:{CYAN}; }}
        """)
        self._search.textChanged.connect(self._apply_filter)

        sev_combo = QComboBox()
        sev_combo.addItems(["All Severities", "Critical", "High", "Warning", "Info", "Success"])
        sev_combo.setStyleSheet(f"""
            QComboBox {{
                background:#111827; border:1px solid {BORDER}; border-radius:8px;
                color:{TEXT_WHITE}; font-size:13px; padding:8px 12px; min-width:140px;
            }}
            QComboBox:hover {{ border-color:{CYAN}; }}
            QComboBox QAbstractItemView {{
                background:#111827; border:1px solid {BORDER}; color:{TEXT_WHITE};
                selection-background-color:{CYAN}; selection-color:#000;
            }}
        """)
        sev_combo.currentTextChanged.connect(self._filter_severity)

        time_combo = QComboBox()
        time_combo.addItems(["Last 24 Hours", "Last 7 Days", "Last 30 Days", "All Time"])
        time_combo.setStyleSheet(sev_combo.styleSheet())

        filter_row.addWidget(self._search, 1)
        filter_row.addWidget(sev_combo)
        filter_row.addWidget(time_combo)
        body.addLayout(filter_row)

        # ── Table ──────────────────────────────────────────────────────────────
        table_frame = QFrame()
        table_frame.setStyleSheet(f"""
            QFrame {{
                background:{BG_CARD}; border:1px solid {BORDER}; border-radius:12px;
            }}
        """)
        table_lay = QVBoxLayout(table_frame)
        table_lay.setContentsMargins(0, 0, 0, 0)
        table_lay.setSpacing(0)

        # Column headers
        hdr_row = QFrame()
        hdr_row.setFixedHeight(38)
        hdr_row.setStyleSheet(f"background:{BG_CARD2}; border-bottom:1px solid {BORDER}; border-radius:12px 12px 0 0;")
        hdr_lay = QHBoxLayout(hdr_row)
        hdr_lay.setContentsMargins(14, 0, 14, 0)
        hdr_lay.setSpacing(0)

        def hdr_col(text, width=None, stretch=False):
            l = QLabel(text)
            l.setStyleSheet(f"color:{TEXT_MUTED}; font-size:11px; font-weight:600; letter-spacing:1px; background:transparent;")
            if width:
                l.setFixedWidth(width)
            if stretch:
                l.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
            return l

        hdr_lay.addWidget(hdr_col("TIMESTAMP", 145))
        hdr_lay.addWidget(hdr_col("SEVERITY",  90))
        hdr_lay.addSpacing(10)
        hdr_lay.addWidget(hdr_col("USER",      120))
        hdr_lay.addSpacing(15)
        hdr_lay.addWidget(hdr_col("PROCESS",   155))
        hdr_lay.addWidget(hdr_col("FILE / TARGET", stretch=True))
        hdr_lay.addWidget(hdr_col("ACTION",    140))
        hdr_lay.addWidget(hdr_col("",          28))
        table_lay.addWidget(hdr_row)

        # Rows container
        self._rows_widget = QWidget()
        self._rows_widget.setStyleSheet("background:transparent;")
        self._rows_lay = QVBoxLayout(self._rows_widget)
        self._rows_lay.setContentsMargins(0, 0, 0, 0)
        self._rows_lay.setSpacing(0)
        self._populate_rows(SAMPLE_LOGS)
        table_lay.addWidget(self._rows_widget)

        # Pagination footer
        footer = QFrame()
        footer.setFixedHeight(48)
        footer.setStyleSheet(f"background:{BG_CARD2}; border-top:1px solid {BORDER}; border-radius:0 0 12px 12px;")
        foot_lay = QHBoxLayout(footer)
        foot_lay.setContentsMargins(16, 0, 16, 0)

        showing = QLabel(f"Showing <b>1 to {min(12,len(SAMPLE_LOGS))}</b> of <b>1,284</b> results")
        showing.setStyleSheet(f"color:{TEXT_MUTED}; font-size:12px; background:transparent;")
        foot_lay.addWidget(showing, 1)

        for lbl, active in [("Previous", False), ("1", True), ("2", False), ("3", False), ("…", False), ("12", False), ("Next", False)]:
            btn = QPushButton(lbl)
            btn.setFixedSize(36, 28)
            btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
            if active:
                btn.setStyleSheet(f"QPushButton {{ background:{CYAN}; color:#000; border:none; border-radius:6px; font-size:12px; font-weight:600; }}")
            else:
                btn.setStyleSheet(f"""
                    QPushButton {{ background:transparent; border:1px solid {BORDER}; color:{TEXT_MUTED}; border-radius:6px; font-size:12px; }}
                    QPushButton:hover {{ border-color:{CYAN}; color:{CYAN}; }}
                """)
            foot_lay.addWidget(btn)
            foot_lay.addSpacing(3)

        table_lay.addWidget(footer)
        body.addWidget(table_frame)

        scroll.setWidget(body_w)
        outer.addWidget(scroll)

    # ── helpers ────────────────────────────────────────────────────────────────
    def _populate_rows(self, logs):
        # Clear existing rows
        while self._rows_lay.count():
            child = self._rows_lay.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
        for i, entry in enumerate(logs):
            row = _table_row(*entry, zebra=(i % 2 == 0))
            self._rows_lay.addWidget(row)

    def _apply_filter(self, text):
        text = text.lower()
        filtered = [
            log for log in SAMPLE_LOGS
            if text in " ".join(log).lower()
        ]
        self._populate_rows(filtered)

    def _filter_severity(self, sev):
        if sev == "All Severities":
            self._populate_rows(SAMPLE_LOGS)
        else:
            self._populate_rows([log for log in SAMPLE_LOGS if log[1] == sev])

    def reload(self):
        """Called by main window on navigation — refresh if needed."""
        pass