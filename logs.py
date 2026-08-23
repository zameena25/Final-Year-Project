# NOVASPHERE — Logs Page
# frontend / logs.py

import sqlite3
import json
import csv
from pathlib import Path
from auth.app_paths import get_logs_dir
from datetime import datetime
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QScrollArea, QFrame, QComboBox, QGridLayout,
    QSizePolicy, QMessageBox, QFileDialog
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QCursor, QColor

_DB_PATH = get_logs_dir() / "novasphere.db"
_ALERT_JSONL = get_logs_dir() / "alerts.jsonl"

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

_ETYPE_SEV = {
    "CREATED": "Info",
    "MODIFIED": "Info",
    "RENAMED": "Warning",
    "DELETED": "High",
}
_STATUS_MAP = {
    "Info": "ALLOWED",
    "Warning": "FLAGGED",
    "High": "BLOCKED",
    "Critical": "BLOCKED",
    "Success": "SUCCESS",
}

SEVERITY_STYLE = {
    "Critical": "background:#3a0a0a; color:#ff4444; border:1px solid #7a1a1a;",
    "High":     "background:#3a2000; color:#ff9800; border:1px solid #7a4000;",
    "Warning":  "background:#2e2500; color:#ffc107; border:1px solid #5a4a00;",
    "Info":     "background:#002a3a; color:#00bcd4; border:1px solid #005a7a;",
    "Success":  "background:#0a2e1a; color:#4caf50; border:1px solid #1a5a2a;",
}

def _load_logs() -> list[tuple]:
    """
    Read from events table -> (timestamp, severity, user, process, file, action, status).
    Returns an empty list when no real monitoring data is available.
    """
    rows=[]

    if _DB_PATH.exists():
        try:
            con = sqlite3.connect(_DB_PATH, check_same_thread=False)
            cur = con.cursor()
            cur.execute(
                "SELECT timestamp, event_type, file_path, username "
                "FROM events ORDER BY rowid DESC LIMIT 200"
            )
            for ts, etype, fpath, user in cur.fetchall():
                sev = _ETYPE_SEV.get((etype or "").upper(), "Info")
                action = (etype or "File Event").replace("_"," ").title()
                status= _STATUS_MAP.get(sev, "ALLOWED")
                proc= _guess_process(fpath)
                rows.append((
                    ts or "-",
                    sev,
                    user or "SYSTEM",
                    proc,
                    fpath or "N/A",
                    action,
                    status,
                ))
            con.close()
            if rows:
                return rows
        except Exception:
            pass
    
    return []

def _guess_process(fpath:str) -> str:
    if not fpath:
        return "system"
    f1 = fpath.lower()
    if "powershell" in f1: return "powershell.exe"
    if "cmd" in f1: return "cmd.exe"
    if ".py" in f1: return "python.exe"
    if "chrome" in f1: return "chrome.exe"
    return "explorer.exe"

def _count_logs(logs: list[tuple]) -> dict:
    counts = {"total": len(logs), "critical": 0, "warning":0, "resolved": 0}
    for row in logs:
        sev = row[1]
        status=row[6]
        if sev in ("Critical", "High"):
            counts["critical"] += 1
        if sev == "Warning": 
            counts["warning"] += 1
        if status in ("ALLOWED", "SUCCESS", "COMPLETED"):
            counts["resolved"] += 1
    return counts

# ── Colour tokens (match main window) ─────────────────────────────────────────
BG_MAIN    = "#0b0f1a"
BG_CARD    = "#131929"
BG_CARD2   = "#161e30"
CYAN       = "#00bcd4"
BORDER     = "#1e2d45"
TEXT_WHITE = "#e8eaf0"
TEXT_MUTED = "#4a5a78"
TEXT_SUB   = "#6b7a99"


# ── Stat card ──────────────────────────────────────────────────────────────────
def _stat_card(icon, value, label, sub, icon_color=TEXT_MUTED):
    card = QFrame()
    card.setObjectName("stat_card")
    card.setStyleSheet(f"""
        QFrame#stat_card {{
            background:{BG_CARD}; border:1px solid {BORDER}; border-radius:14px;
        }}
    """)
    card.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
    card.setFixedHeight(88)

    lay = QHBoxLayout(card)
    lay.setContentsMargins(20, 16, 20, 16)
    lay.setSpacing(14)

    left = QVBoxLayout(); left.setSpacing(2)
    lbl = QLabel(label)
    lbl.setStyleSheet(f"color:{TEXT_MUTED}; font-size:13px; background:transparent;")
    val = QLabel(value)
    val.setStyleSheet(f"color:{TEXT_WHITE}; font-size:26px; font-weight:700; background:transparent;")
    sub_lbl = QLabel(sub)
    sub_lbl.setStyleSheet(f"color:{TEXT_MUTED}; font-size:12px; background:transparent;")
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
            border-bottom:1px; border:none;
        }}
        QFrame:hover {{ background:#1a2540; }}
    """)

    lay = QHBoxLayout(row)
    lay.setContentsMargins(14, 10, 14, 10)
    lay.setSpacing(10)

    def col(text, color=TEXT_MUTED, mono=False, min_w=60):
        lbl = QLabel(text)
        lbl.setMinimumWidth(min_w)
        lbl.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        font_fam = "'Consolas','Courier New',monospace" if mono else "'Segoe UI',sans-serif"
        lbl.setStyleSheet(
            f"color:{color}; font-size:12px; background:transparent; font-family:{font_fam}; border:none;"
        )
        lbl.setWordWrap(False)
        return lbl

    # Timestamp
    lay.addWidget(col(timestamp, TEXT_MUTED, mono=True, min_w=120), 12)

    # Severity badge
    badge = QLabel(severity)
    sty = SEVERITY_STYLE.get(severity, f"background:{BG_CARD}; color:{TEXT_MUTED}; border:1px solid {BORDER};")
    badge.setStyleSheet(
        f"{sty} font-size:11px; font-weight:600; border-radius:6px; padding:2px 8px;"
    )
    badge.setFixedWidth(80)
    badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
    lay.addWidget(badge)

    # User
    user_w = QHBoxLayout(); user_w.setSpacing(4); user_w.setContentsMargins(0,0,0,0)
    ico = QLabel("󰀄"); ico.setStyleSheet("font-size:11px; background:transparent;")
    u_lbl = col(user, TEXT_WHITE, min_w=90)
    user_w.addWidget(ico); user_w.addWidget(u_lbl)
    user_container = QWidget(); user_container.setLayout(user_w)
    user_container.setStyleSheet("background:transparent; border:none;")
    lay.addWidget(user_container, 10)

    # Process
    proc_w = QHBoxLayout(); proc_w.setSpacing(4); proc_w.setContentsMargins(0,0,0,0)
    p_ico = QLabel("󰒓"); p_ico.setStyleSheet("font-size:11px; background:transparent;")
    p_lbl = QLabel(process)
    p_lbl.setMinimumWidth(100)
    p_lbl.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
    p_lbl.setStyleSheet(
        f"color:#7ecfda; font-size:11px; background:transparent; border:none;"
        f"font-family:'Consolas','Courier New',monospace;"
    )
    proc_w.addWidget(p_ico); proc_w.addWidget(p_lbl)
    proc_container = QWidget(); proc_container.setLayout(proc_w)
    proc_container.setStyleSheet("background:transparent; border: none;")
    lay.addWidget(proc_container, 12)

    # File/Target
    file_lbl = QLabel(file_target)
    file_lbl.setStyleSheet(
        f"color:{TEXT_MUTED}; font-size:11px; background:transparent; border:none;"
        f"font-family:'Consolas','Courier New',monospace;"
    )
    file_lbl.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
    file_lbl.setWordWrap(False)
    lay.addWidget(file_lbl, 22)

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
    action_container.setStyleSheet("background:transparent; border:none;")
    action_container.setMinimumWidth(120)
    lay.addWidget(action_container, 12)

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
        self._live_logs = _load_logs()
        self._filtered_logs = list(self._live_logs)
        self._current_page = 1
        self._page_size = 10
        self._build()
        self._refresh_timer = QTimer(self)
        self._refresh_timer.timeout.connect(self.reload)
        self._refresh_timer.start(3_000)

    def _build(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        # Scrollable body 
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

        # ── Header row ────────────────────────────
        hdr = QHBoxLayout()
        title_col = QVBoxLayout(); title_col.setSpacing(3)
        t = QLabel("Incident Logs")
        t.setStyleSheet(f"color:{TEXT_WHITE}; font-size:20px; font-weight:700; background:transparent;")
        sub = QLabel("Review system activities, security alerts, and user interactions")
        sub.setStyleSheet(f"color:{TEXT_MUTED}; font-size:15px; background:transparent;")
        title_col.addWidget(t); title_col.addWidget(sub)
        hdr.addLayout(title_col, 1)

        pdf_btn = QPushButton(" 󰂺  Generate PDF Report")
        pdf_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        pdf_btn.setStyleSheet(f"""
            QPushButton {{
                background:transparent; border:1px solid {BORDER}; color:{TEXT_WHITE};
                font-size:13px; padding:8px 16px; border-radius:8px;
            }}
            QPushButton:hover {{ border-color:{CYAN}; color:{CYAN}; }}
        """)

        csv_btn = QPushButton(" 󰮓  Export CSV")
        csv_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        csv_btn.setStyleSheet(f"""
            QPushButton {{
                background:{CYAN}; border:none; color:#000;
                font-size:13px; font-weight:600; padding:8px 16px; border-radius:8px;
            }}
            QPushButton:hover {{ background:#00d4f0; }}
        """)
        csv_btn.clicked.connect(self._export_csv)
        pdf_btn.clicked.connect(self._export_pdf)

        hdr.addWidget(pdf_btn)
        hdr.addSpacing(8)
        hdr.addWidget(csv_btn)
        body.addLayout(hdr)

        # ── Stat cards ─────────────────────────────────────────────────────────

        c = _count_logs(self._live_logs)

        cards_row = QHBoxLayout()
        cards_row.setSpacing(14)
        
        cards_row.addWidget(_stat_card("󰂺", str(c["total"]),    "Total Incidents",  "Last 24 hours",     TEXT_MUTED), 1)
        cards_row.addWidget(_stat_card("󰯪", str(c["critical"]), "Critical Threats",  "+live from DB",     "#ff4444"), 1)
        cards_row.addWidget(_stat_card("󰀪",  str(c["warning"]),  "Warnings",          "Requires review",   "#ffc107"), 1)
        cards_row.addWidget(_stat_card("󰄬", str(c["resolved"]), "Auto-Resolved",     "from events table", "#4caf50"), 1)
        body.addLayout(cards_row)

        # ── Search + filter bar ────────────────────────────────────────────────
        filter_row = QHBoxLayout(); filter_row.setSpacing(10)

        self._search = QLineEdit()
        self._search.setPlaceholderText(" 󰍉   Search by user, process, file, or event...")
        self._search.setStyleSheet(f"""
            QLineEdit {{
                background:#111827; border:1px; border-radius:8px;
                color:{TEXT_WHITE}; font-size:13px; padding:9px 14px;
            }}
            QLineEdit:focus {{ border-color:{CYAN}; }}
        """)
        self._search.textChanged.connect(self._apply_filter)

        self._sev_combo = QComboBox()
        self._sev_combo.addItems(["All Severities", "Critical", "High", "Warning", "Info", "Success"])
        self._sev_combo.setStyleSheet(f"""
            QComboBox {{
                background:#111827; border:1px; border-radius:8px;
                color:{TEXT_WHITE}; font-size:13px; padding:8px 12px; min-width:140px;
            }}
            QComboBox:hover {{ border-color:{CYAN}; }}
            QComboBox QAbstractItemView {{
                background:#111827; border:1px; color:{TEXT_WHITE};
                selection-background-color:{CYAN}; selection-color:#000;
            }}
        """)
        self._sev_combo.currentTextChanged.connect(self._filter_severity)

        time_combo = QComboBox()
        time_combo.addItems(["Last 24 Hours", "Last 7 Days", "Last 30 Days", "All Time"])
        time_combo.setStyleSheet(self._sev_combo.styleSheet())

        filter_row.addWidget(self._search, 1)
        filter_row.addWidget(self._sev_combo)
        filter_row.addWidget(time_combo)
        body.addLayout(filter_row)

        # ── Table ──────────────────────────────────────────────────────────────
        table_frame = QFrame()
        table_frame.setStyleSheet(f"""
            QFrame {{
                background:{BG_CARD}; border:1px; border-radius:12px;
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
            return l
        
        hdr_lay.setSpacing(10)
        hdr_lay.addWidget(hdr_col("TIMESTAMP"), 12)

        sev_hdr = hdr_col("SEVERITY")
        sev_hdr.setFixedWidth(80)
        hdr_lay.addWidget(sev_hdr, 0)

        hdr_lay.addWidget(hdr_col("USER"), 10)
        hdr_lay.addWidget(hdr_col("PROCESS"), 12)
        hdr_lay.addWidget(hdr_col("FILE / TARGET"), 22)
        hdr_lay.addWidget(hdr_col("ACTION"), 12)

        end_spacer = QLabel("")
        end_spacer.setFixedWidth(28)
        hdr_lay.addWidget(end_spacer, 0)

        # Rows container
        self._rows_widget = QWidget()
        self._rows_widget.setStyleSheet("background:transparent;")
        self._rows_lay = QVBoxLayout(self._rows_widget)
        self._rows_lay.setContentsMargins(0, 0, 0, 0)
        self._rows_lay.setSpacing(0)
        table_lay.addWidget(self._rows_widget)

        # Pagination footer
        footer = QFrame()
        footer.setFixedHeight(48)
        footer.setStyleSheet(f"background:{BG_CARD2}; border-top:1px solid {BORDER}; border-radius:0 0 12px 12px;")
        foot_lay = QHBoxLayout(footer)
        foot_lay.setContentsMargins(16, 0, 16, 0)

        self._showing_lbl = QLabel()
        self._showing_lbl.setStyleSheet(f"color:{TEXT_MUTED}; font-size:12px; background:transparent;")
        foot_lay.addWidget(self._showing_lbl, 1)

        self._pagination_btns_container = QWidget()
        self._pagination_btns_container.setStyleSheet("background:transparent;")
        self._pagination_btns_lay = QHBoxLayout(self._pagination_btns_container)
        self._pagination_btns_lay.setContentsMargins(0, 0, 0, 0)
        self._pagination_btns_lay.setSpacing(4)
        foot_lay.addWidget(self._pagination_btns_container)

        table_lay.addWidget(footer)
        body.addWidget(table_frame)

        scroll.setWidget(body_w)
        outer.addWidget(scroll)

        #Initial view update
        self._update_display()
    
    def _export_csv(self):
        default_name = f"novasphere_logs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        fname, _ = QFileDialog.getSaveFileName(
            self, "Export CSV", default_name, "CSV Files (*.csv)"
        )
        if not fname:
            return

        try:
            with open(fname, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(["Timestamp", "Severity", "User", "Process", "File/Target", "Action", "Status"])
                writer.writerows(self._live_logs)
            
            msg = QMessageBox(self)
            msg.setWindowTitle("Export Complete")
            msg.setText(f" Logs exported to:\n{fname}")
            msg.setStandardButtons(QMessageBox.StandardButton.Ok)
            msg.setStyleSheet(f"QWidget{{background:{BG_CARD};color:{TEXT_WHITE};}}"
                          f"QPushButton{{background:{CYAN};border:none;color:#000;"
                          f"border-radius:6px;padding:6px 20px;font-weight:700;}}")
            msg.exec()
        except Exception as e:
            QMessageBox.critical(self, "Export Failed", str(e))

    def _export_pdf(self):
        default_name = f"novasphere_logs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        fname, _ = QFileDialog.getSaveFileName(
            self, "Generate PDF Report", default_name, "PDF Files (*.pdf)"
        )
        if not fname:
            return

        try:
            print("PDF export strated, target:", fname)
            from reportlab.lib import colors
            from reportlab.lib.pagesizes import landscape, A4
            from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
            from reportlab.lib.styles import getSampleStyleSheet
            from reportlab.lib.units import mm

            doc = SimpleDocTemplate(fname, pagesize=landscape(A4),
                                    leftMargin=18*mm, rightMargin=18*mm,
                                    topMargin=15*mm, bottomMargin=15*mm)
            styles = getSampleStyleSheet()
            elements = []

            title = Paragraph("NOVASPHERE - Incident Logs Report", styles["Title"])
            subtitle = Paragraph(
                f"Generated {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} &nbsp;|&nbsp; "
                f"{len(self._live_logs)} record(s)",
                styles["Normal"]
            )
            elements += [title, subtitle, Spacer(1, 10*mm)]

            headers = ["Timestamp", "Severity", "User", "Process", "File/Target", "Action", "Status"]
            data = [headers] + [list(map(str, row)) for row in self._live_logs]

            table = Table(data, repeatRows=1)
            table.setStyle(TableStyle([
                ("BACKGROUND", (0,0), (-1, 0), colors.HexColor("#161e30")),
                ("TEXTCOLOR", (0,0), (-1, 0), colors.white),
                ("FONTSIZE", (0,0), (-1, -1), 7),
                ("GRID", (0,0), (-1,-1), 0.4, colors.HexColor("#cccccc")),
                ("ROWBACKGROUNDS", (0,1), (-1,-1), [colors.white, colors.HexColor("#f2f2f2")]),
                ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
            ]))
            elements.append(table)

            doc.build(elements)

            msg = QMessageBox(self)
            msg.setWindowTitle("PDF Report Generated")
            msg.setText(f" Report saved to:\n{fname}")
            msg.setStandardButtons(QMessageBox.StandardButton.Ok)
            msg.setStyleSheet(f"QWidget{{background:{BG_CARD};color:{TEXT_WHITE};}}"
                              f"QPushButton{{background:{CYAN};border:none;color:#000;"
                              f"border-radius:6px;padding:6px 20px;font-weight:700;}}")
            msg.exec()
        except ImportError:
            QMessageBox.critical(self, "Missing Dependency",
                                 "PDF export requires the 'reportlab' package.\n\nInstall it with:\n pip install reportlab")
        except Exception as e:
            import traceback
            traceback.print_exc()
            QMessageBox.critical(self, "Export Failed", str(e))

    # ── helpers ────────────────────────────────────────────────────────────────
    def _go_page(self, page):
        self._current_page = page
        self._update_display()

    def _update_display(self):
        total_logs = len(self._filtered_logs)
        total_pages = max(1, (total_logs + self._page_size - 1) // self._page_size)
        self._current_page = max(1, min(self._current_page, total_pages))

        start_idx = (self._current_page - 1) * self._page_size
        end_idx = min(start_idx + self._page_size, total_logs)
        page_logs = self._filtered_logs[start_idx:end_idx]

        # 1. Clear & populate table rows for current page
        while self._rows_lay.count():
            child = self._rows_lay.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
        for i, entry in enumerate(page_logs):        
            row = _table_row(*entry, zebra=(i % 2 == 0))
            self._rows_lay.addWidget(row)

        # 2. Update showing label
        if total_logs > 0:
            self._showing_lbl.setText(f"Showing <b>{start_idx + 1} to {end_idx}</b> of <b>{total_logs}</b> results")
        else:
            self._showing_lbl.setText("Showing <b>0</b> results")

        # 3. Clear & rebuild pagination buttons
        while self._pagination_btns_lay.count():
            child = self._pagination_btns_lay.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        # Previous button
        prev_btn = QPushButton("Previous")
        prev_btn.setFixedHeight(28)
        prev_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        if self._current_page > 1:
            prev_btn.setStyleSheet(f"""
                QPushButton {{ background:transparent; border:1px solid {BORDER}; color:{TEXT_WHITE}; border-radius:6px; font-size:12px; padding:0 10px; }}
                QPushButton:hover {{ border-color:{CYAN}; color:{CYAN}; }}
            """)
            prev_btn.clicked.connect(lambda: self._go_page(self._current_page - 1))
        else:
            prev_btn.setEnabled(False)
        prev_btn.setStyleSheet(f"QPushButton {{ background:transparent; border:1px solid {BORDER}; color:{TEXT_MUTED}; border-radius:6px; font-size:12px; padding:0 10px; }}")
        self._pagination_btns_lay.addWidget(prev_btn)
        self._pagination_btns_lay.addSpacing(3)

        # Next button
        next_btn = QPushButton("Next")
        next_btn.setFixedHeight(28)
        next_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        if self._current_page < total_pages:
            next_btn.setStyleSheet(f"""
                QPushButton {{ background:transparent; border:1px solid {BORDER}; color:{TEXT_WHITE}; border-radius:6px; font-size:12px; padding:0 10px; }}
                QPushButton:hover {{ border-color:{CYAN}; color:{CYAN}; }}
            """)
            next_btn.clicked.connect(lambda: self._go_page(self._current_page + 1))
        else:
            next_btn.setEnabled(False)
            next_btn.setStyleSheet(f"QPushButton {{ background:transparent; border:1px solid {BORDER}; color:{TEXT_MUTED}; border-radius:6px; font-size:12px; padding:0 10px; }}")
        self._pagination_btns_lay.addWidget(next_btn)

    def _apply_filter(self, text=None):
        search_txt = self._search.text().lower()
        sev_txt = self._sev_combo.currentText()

        filtered = self._live_logs
        if search_txt:
            filtered = [log for log in filtered if search_txt in " ".join(log).lower()]
        if sev_txt and sev_txt != "All Severities":
            filtered = [log for log in filtered if log[1] == sev_txt]

        self._filtered_logs = filtered
        self._current_page = 1
        self._update_display()

    def _filter_severity(self, sev=None):
        self._apply_filter()
        
    def reload(self):
        """Called by main window on tab switch — refresh from DB."""
        self._live_logs = _load_logs()
        self._apply_filter()
