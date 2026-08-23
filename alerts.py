# NOVASPHERE — Alerts Management Page
# frontend / alerts_page.py

import csv
import sqlite3
import json
from datetime import datetime
from auth.app_paths import get_logs_dir

from pathlib import Path
from typing import Self
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QMessageBox, QFileDialog,
    QFrame, QScrollArea, QLineEdit, QComboBox, QSizePolicy, QDialog, QDialogButtonBox
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QCursor, QFont

# ── Color tokens (mirrored from main dashboard) ───────────────────────────────
from .nova_style import (
    BG_MAIN, BG_CARD, BG_CARD2, BG_ROW, CYAN, CYAN_DIM, BG_TOPBAR, BG_SIDEBAR, BG_MODULE, BORDER, TEXT_WHITE, TEXT_MUTED, TEXT_SUB,
    RED, ORANGE, GREEN, YELLOW, BLUE
)

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
    color: {TEXT_WHITE}; font-size: 20px; font-weight: 700;
    background: transparent;
}}
#page_sub {{
    color: {TEXT_MUTED}; font-size: 15px; background: transparent;
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
_DB_PATH     = get_logs_dir() / "novasphere.db"
_ALERT_JSONL = get_logs_dir() / "alerts.jsonl"

_SEV_MAP  = {"CRITICAL": "Critical", "HIGH": "High", "MEDIUM": "Medium", "LOW": "Low"}
_STAT_MAP = {"CRITICAL": "Open", "HIGH": "Investigating", "MEDIUM": "Resolved", "LOW": "Resolved"}

def _load_alerts() -> list[dict]:
    """DB first -> jsonl fallback -> hardcoded fallback."""
    alerts=[]

    if _DB_PATH.exists():
        try:
            con = sqlite3.connect(_DB_PATH, check_same_thread=False,timeout=5)
            cur = con.cursor()
            cur.execute(
                "SELECT rowid, alert_type, severity, message, file_path, source, timestamp "
                "FROM alerts ORDER BY rowid DESC LIMIT 200"
            )
            for rowid, alert_type, severity, message, file_path, source, timestamp in cur.fetchall():
                sev = _SEV_MAP.get(severity, "Low")
                status = _STAT_MAP.get(severity, "Low")
                alerts.append({
                    "id": f"ALT-{1000 + rowid}",
                    "severity": sev,
                    "threat": (alert_type or "Unknown").replace("_", " ").title(),
                    "user": _parse_user(message, source),
                    "target": (file_path or "System").split("/")[-1].split("\\")[-1],
                    "status": status,
                    "time": _time_ago(timestamp),
                })
            con.close()
        except Exception:
            pass
    
    if alerts:
        return alerts 
    
    if _ALERT_JSONL.exists():
        try:
            with open(_ALERT_JSONL, encoding="utf-8") as f:
                all_lines = f.readlines()
            recent_lines = all_lines[-200:]   # only the most recent 200
            for i, line in enumerate(recent_lines):
                line = line.strip()
                if not line:
                    continue
                try:
                    a = json.loads(line)
                    sev = _SEV_MAP.get(a.get("severity", "LOW"), "LOW")
                    status = _STAT_MAP.get(a.get("severity","LOW"), "Resolved")
                    alerts.append({
                        "id": f"ALT-{1000 + i}",
                        "severity": sev,
                        "threat": a.get("alert_type", "Unknown").replace("_", " ").title(),
                        "user": a.get("source", "SYSTEM"),
                        "target": (a.get("file_path")or "System").split("/")[-1],
                        "status": status,
                        "time": _time_ago(a.get("timestamp")),
                    })
                except Exception:
                    pass
        except Exception:
            pass
    
    if alerts:
        return alerts
    
    return _FALLBACK_ALERTS

def _parse_user(message: str, source: str) -> str:
    if not message:
        return source or "SYSTEM"
    for word in message.split():
        if word.startswith("user:") or word.startswith("USER:"):
            return word.split(":", 1)[1]
    return source or "SYSTEM"


def _time_ago(timestamp: str | None) -> str:
    if not timestamp:
        return "—"
    try:
        from datetime import datetime
        dt   = datetime.strptime(timestamp, "%Y-%m-%d %H:%M:%S")
        diff = (datetime.now() - dt).total_seconds()
        if diff < 60:   return f"{int(diff)}s ago"
        if diff < 3600: return f"{int(diff//60)}m ago"
        if diff < 86400:return f"{int(diff//3600)}h ago"
        return f"{int(diff//86400)}d ago"
    except Exception:
        return "—"

_FALLBACK_ALERTS = [
    {"id": "ALT-1042", "severity": "Critical", "threat": "Ransomware",      "user": "SYSTEM",          "target": "File Server 01",  "status": "Open",          "time": "2 mins ago"},
    {"id": "ALT-1041", "severity": "High",     "threat": "Insider Threat",  "user": "jdoe",            "target": "Workstation-04",  "status": "Investigating", "time": "15 mins ago"},
    {"id": "ALT-1040", "severity": "Medium",   "threat": "Ransomware",      "user": "admin",           "target": "DC-02",           "status": "Resolved",      "time": "45 mins ago"},
    {"id": "ALT-1039", "severity": "Low",      "threat": "Policy Violation","user": "mscott",          "target": "Workstation-09",  "status": "Resolved",      "time": "1 hour ago"},
    {"id": "ALT-1038", "severity": "High",     "threat": "Insider Threat",  "user": "service_account", "target": "Database-01",     "status": "Open",          "time": "2 hours ago"},
]

# ── Severity badge widget ─────────────────────────────────────────────────────
class SeverityBadge(QLabel):
    ICONS   = {"Critical": "󰻌", "High": "󰀦", "Medium": "󰂚", "Low": "󰣏"}
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
        "Critical": ("󰻌", SEV_CRITICAL),
        "High":     ("󰀪", SEV_HIGH),
        "Medium":   ("󰂚", SEV_MEDIUM),
        "Low":      ("󰣏", SEV_LOW),
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

class AlertDetailDialog(QDialog):
    def __init__(self, alert:dict, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"Alert Detail - {alert['id']}")
        self.setFixedSize(480, 360)
        self.setStyleSheet(f"""
             QDialog {{ background: {BG_CARD}; }}
             QLabel {{ background: transparent; color: {TEXT_WHITE}; }}
        """)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(28, 24, 28, 24)
        lay.setSpacing(12)

        #title
        title = QLabel(f"󰂜  {alert['id']} - {alert['threat']}")
        title.setStyleSheet(f"color:{TEXT_WHITE}; font-size: 16px; font-weight: 700;")
        lay.addWidget(title)

        #fields
        fields = [
            ("Severity", alert.get("severity", "-")),
            ("Threat Type",alert.get("threat",   "—")),
            ("Affected User", alert.get("user",  "—")),
            ("Target",     alert.get("target",   "—")),
            ("Status",     alert.get("status",   "—")),
            ("Time",       alert.get("time",     "—")),
        ]
        for label, value in fields:
            row = QHBoxLayout()
            k = QLabel(f"{label}:")
            k.setStyleSheet(f"color:{TEXT_MUTED};font-size:13px;min-width:130px;")
            v = QLabel(value)
            v.setStyleSheet(f"color:{TEXT_WHITE};font-size:13px;font-weight:600;")
            row.addWidget(k); row.addWidget(v); row.addStretch()
            lay.addLayout(row)

        lay.addStretch()
        # Mark Resolved button
        resolve_btn = QPushButton("󰄬  Mark as Resolved")
        resolve_btn.setStyleSheet(f"""
            QPushButton {{
                background: #00c853; border: none; border-radius: 8px;
                color: #000; font-size: 13px; font-weight: 700; padding: 10px;
            }}
            QPushButton:hover {{ background: #00e676; }}
        """)
        resolve_btn.clicked.connect(lambda: self._mark_resolved(alert))
        resolve_btn.clicked.connect(self.accept)
        lay.addWidget(resolve_btn)
    
    def _mark_resolved(self, alert: dict):
        """Update status in DB if available."""
        try:
            con = sqlite3.connect(_DB_PATH, check_same_thread=False)
            cur = con.cursor()
            cur.execute(
                "UPDATE alerts SET severity='LOW' WHERE rowid=?",
                (int(alert["id"].replace("ALT-", "")) - 1000,)
            )
            con.commit(); con.close()
        except Exception:
            pass


# ── Single alert row ──────────────────────────────────────────────────────────
class AlertRow(QFrame):
    alert_clicked = pyqtSignal(dict)

    def __init__(self, alert: dict, parent = None):
        super().__init__(parent)
        self._alert = alert
        self.setObjectName ("row_frame")
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.setFixedHeight(56)

        lay = QHBoxLayout(self)
        lay.setContentsMargins(16, 0, 12, 0)
        lay.setSpacing(0)

        def cell(w, stretch=0):
            lay.addWidget(w, stretch)
        
        id_lbl = QLabel(alert["id"]); id_lbl.setObjectName("alert_id")
        id_lbl.setFixedWidth(90); cell(id_lbl)

        badge = SeverityBadge(alert["severity"])
        badge.setFixedWidth(110); cell(badge)
        lay.addSpacing(8)

        tt = QLabel(alert["threat"]); tt.setObjectName("threat_type")
        tt.setFixedWidth(160); cell(tt)

        user_icon = QLabel(f"󰀄  {alert['user']}"); user_icon.setObjectName("affected_user")
        user_icon.setFixedWidth(170); cell(user_icon)

        tgt = QLabel(alert["target"]); tgt.setObjectName("target_proc")
        tgt.setFixedWidth(160); cell(tgt)

        st = StatusBadge(alert["status"])
        st.setFixedWidth(120); cell(st)

        tm = QLabel(alert["time"]); tm.setObjectName("target_proc")
        tm.setFixedWidth(110); cell(tm)

        arr = QPushButton("'"); arr.setObjectName("arrow_btn"); arr.setFixedSize(24, 24)
        arr.clicked.connect(lambda: self.alert_clicked.emit(self._alert))
        cell(arr)


#  Main Alerts page 
class AlertsPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("alerts_root")
        self.setStyleSheet(STYLE)
        print("[alerts] loading alerts...")
        self._all_alerts = _load_alerts()
        print(f"[alerts] loaded {len(self._all_alerts)} alerts")
        self._filter_sev = "All Severities"
        self._search_txt = ""
        self._build()
        # Live-update timer: bumps the first alert's time every 30s
        self._last_alert_count = len(self._all_alerts)
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._poll_alerts)
        self._timer.start(30_000)
    

    #  Build UI 

    def _build(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(32, 24, 32, 28)
        outer.setSpacing(20)
        outer.setAlignment(Qt.AlignmentFlag.AlignTop)

        #  Header row 
        hdr = QHBoxLayout(); hdr.setSpacing(0)

        titles = QVBoxLayout(); titles.setSpacing(3)
        page_title = QLabel("Alerts Management"); page_title.setObjectName("page_title")
        page_sub   = QLabel("Real-time incident monitoring and response"); page_sub.setObjectName("page_sub")
        titles.addWidget(page_title); titles.addWidget(page_sub)
        hdr.addLayout(titles); hdr.addStretch()

        export_btn = QPushButton("󰮓 Export Report"); export_btn.setObjectName("export_btn")
        export_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        export_btn.clicked.connect(self._export_report)
        hdr.addWidget(export_btn)
        outer.addLayout(hdr)

        # Severity summary cards 

        cards_row = QHBoxLayout(); cards_row.setSpacing(16)
        self._sev_counts = self._count_severities()
        self._sev_cards  = {}
        for sev in ("Critical", "High", "Medium", "Low"):
            card = SeverityCard(sev, self._sev_counts.get(sev, 0))
            self._sev_cards[sev] = card
            cards_row.addWidget(card, 1)
        outer.addLayout(cards_row)

        #  Table card
         
        table_card = QFrame(); table_card.setObjectName("table_wrap")
        tc_lay = QVBoxLayout(table_card)
        tc_lay.setContentsMargins(16, 16, 16, 16)
        tc_lay.setSpacing(10)

        # Search + filter bar

        sf_row = QHBoxLayout(); sf_row.setSpacing(12)
        self._search = QLineEdit()
        self._search.setObjectName("search_alert")
        self._search.setPlaceholderText(" 󰍉  Search alert ID, user, or target...")
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

    def _export_report(self):
        """Export the current alerts list to a file (CSV/PDF/etc.)."""
        default_name = f"alerts_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        fname, _ = QFileDialog.getSaveFileName(
            self, "Exports Alerts Report", default_name, "CSV Files (*.csv)"
        )
        if not fname:
            return # user cancelled
        
        try:
            rows = self._filtered()
            with open(fname, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(["Alert ID", "Severity", "Threat Type", "Affected User", "Target", "Status", "Time"])
                for a in rows:
                    writer.writerow([
                        a["id"], a["severity"], a["threat"],
                        a["user"], a["target"], a["status"], a["time"]
                    ])

            msg = QMessageBox(self)
            msg.setWindowTitle("Export Complete")
            msg.setText(f"󰄬  {len(rows)} alert(s) exported to:\n{fname}")   # ← also fixed: was `row`, should be `rows`
            msg.setStandardButtons(QMessageBox.StandardButton.Ok)
            msg.setStyleSheet(
                f"QWidget{{background:{BG_CARD}; color:{TEXT_WHITE};}}"
                f"QPushButton{{background:{CYAN};border:none;color:#000;"
                f"border-radius:6px;padding:6px 20px;font-weight:700;}}"
            )
            msg.exec()
        except Exception as e:
            QMessageBox.critical(self, "Export Failed", str(e))

    #  Data helpers 

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

        filtered = self._filtered()[:200]

        for alert in self._filtered():
            row = AlertRow(alert)
            row.alert_clicked.connect(self._show_alert_detail)
            self._rows_layout.addWidget(row)

        # Empty-state label
        if not self._filtered():
            empty = QLabel("No alerts match your search.")
            empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
            empty.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 14px; padding: 40px; background: transparent;")
            self._rows_layout.addWidget(empty)
    
    def _show_alert_detail(self, alert:dict):
        dlg = AlertDetailDialog(alert, self)
        dlg.exec()

        self._all_alerts = _load_alerts()
        self._populate_rows()
        
    def _refresh_sev_cards(self):
        counts = self._count_severities()
        for sev, card in self._sev_cards.items():
            # Update the count label (second widget in the left layout)
            left_lay = card.layout().itemAt(0).layout()
            count_lbl = left_lay.itemAt(1).widget()
            count_lbl.setText(str(counts.get(sev, 0)))

    #  Slots 
    def _on_search(self, text: str):
        self._search_txt = text
        self._populate_rows()

    def _on_filter(self, text: str):
        self._filter_sev = text
        self._populate_rows()

    def _poll_alerts(self):
        """Poll DB for new or changed alert records."""
        fresh = _load_alerts()
        if fresh != self._all_alerts:
            self._last_alert_count = len(fresh)
            self._all_alerts = fresh
            self._refresh_sev_cards()
            self._populate_rows()    

    # ── Called by NovaSphereWindow on tab switch ──────────────────────────────
    def reload(self):
        self._all_alerts = _load_alerts()
        self._last_alert_count = len(self._all_alerts)
        self._refresh_sev_cards()
        self._populate_rows()
