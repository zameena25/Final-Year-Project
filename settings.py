# ── settings.py — NovaSphere System Configuration Page ──────────────────
# froentend / settings.py

import sys
import json
from pathlib import Path
from auth.app_paths import get_app_data_dir
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QFrame, QScrollArea, QCheckBox, QSlider,
    QLineEdit, QComboBox, QSizePolicy, QStackedWidget, QGridLayout,
    QMessageBox, QInputDialog
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QColor, QCursor, QFont, QPainter, QPen, QBrush

_SETTINGS_FILE = get_app_data_dir() / "config" / "novasphere_settings.json"

# ── Colors ─────────────────────────────────────────────────────────────────────
from nova_style import (
    BG_MAIN, BG_CARD, BG_CARD2, BG_ROW, CYAN, CYAN_DIM,
    BORDER, TEXT_WHITE, TEXT_MUTED, TEXT_SUB,
    RED, ORANGE, GREEN, YELLOW, BLUE
)

def _load_settings() -> dict:
    if _SETTINGS_FILE.exists():
        try:
            with open(_SETTINGS_FILE, encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {}

def _save_settings(data: dict):
    try:
        _SETTINGS_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(_SETTINGS_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
    except Exception:
        pass

# Reusable widgets

def lbl(text="", size=12, color=TEXT_WHITE, bold=False) -> QLabel:
    l = QLabel(text)
    w = "700" if bold else "400"
    l.setStyleSheet(f"border:none; color:{color};font-size:{size}px;font-weight:{w};background:transparent;")
    return l

def hsep() -> QFrame:
    f = QFrame()
    f.setFrameShape(QFrame.Shape.HLine)
    f.setFixedHeight(1)
    f.setStyleSheet(f"border:none;")
    return f

def card_frame(red_tint=False) -> QFrame:
    bg = "#150d0d" if red_tint else BG_CARD
    border = RED if red_tint else BORDER
    f = QFrame()
    f.setStyleSheet(f"QFrame{{background:{bg};border:1px solid {BORDER};border-radius:12px;}}")
    return f


# Toggle switch

class ToggleSwitch(QWidget):
    toggled = pyqtSignal(bool)

    def __init__(self, checked=True, parent=None):
        super().__init__(parent)
        self._checked = checked
        self.setFixedSize(52, 28)
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))

    def isChecked(self): return self._checked
    def setChecked(self, v): self._checked = v; self.update()

    def mousePressEvent(self, _):
        self._checked = not self._checked
        self.toggled.emit(self._checked)
        self.update()

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        track = QColor(CYAN) if self._checked else QColor(BORDER)
        p.setBrush(QBrush(track)); p.setPen(Qt.PenStyle.NoPen)
        p.drawRoundedRect(0, 4, 52, 20, 10, 10)
        cx = 36 if self._checked else 16
        p.setBrush(QBrush(QColor(TEXT_WHITE))); p.drawEllipse(cx - 10, 2, 24, 24)
        p.end()


# Styled checkbox 

def styled_checkbox(text: str, checked: bool = True) -> QCheckBox:
    cb = QCheckBox(text)
    cb.setChecked(checked)
    cb.setStyleSheet(f"""
        QCheckBox {{ color:{TEXT_WHITE}; font-size:13px; background:transparent; spacing:10px; }}
        QCheckBox::indicator {{ width:18px; height:18px; border:1px;
            border-radius:4px; background:{BG_MAIN}; }}
        QCheckBox::indicator:checked {{ background:{CYAN}; border-color:{CYAN}; }}
    """)
    return cb


# Styled combobox 

def styled_combo(items: list, current=0) -> QComboBox:
    cb = QComboBox()
    cb.addItems(items)
    cb.setCurrentIndex(current)
    cb.setStyleSheet(f"""
        QComboBox {{ background:{BG_CARD2}; border:1px; border-radius:8px;
            color:{TEXT_WHITE}; font-size:15px; padding:8px 14px; min-height:36px; }}
        QComboBox::drop-down {{ border:none; width:24px; }}
        QComboBox::down-arrow {{ color:{CYAN}; }}
        QComboBox QAbstractItemView {{ background:{BG_CARD}; color:{TEXT_WHITE};
            border:1px; selection-background-color:{CYAN_DIM}; }}
    """)
    return cb


# Styled line edit

def styled_input(text: str, placeholder="") -> QLineEdit:
    le = QLineEdit(text)
    le.setPlaceholderText(placeholder)
    le.setStyleSheet(f"""
        QLineEdit {{ background:{BG_CARD2}; border:1px; border-radius:8px;
            color:{TEXT_WHITE}; font-size:15px; padding:8px 14px; min-height:36px; }}
        QLineEdit:focus {{ border-color:{CYAN}; }}
    """)
    return le


# Section title

def section_title(icon: str, title: str, icon_color=CYAN) -> QHBoxLayout:
    row = QHBoxLayout(); row.setSpacing(10)
    row.addWidget(lbl(icon, 18, icon_color))
    row.addWidget(lbl(title, 16, TEXT_WHITE, bold=True))
    row.addStretch()
    return row


# Settings group panels

class DetectionResponsePanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        root = QVBoxLayout(self)
        root.setContentsMargins(32,28,32,32)
        root.setSpacing(28)
        root.setAlignment(Qt.AlignmentFlag.AlignTop)

        root.addLayout(section_title("󱐋", "Heuristic Sensitivity", YELLOW))
        root.addWidget(lbl("Adjust the aggression level of the behavioral analysis engine.", 14, TEXT_MUTED))

        sens_card = card_frame()
        sl = QVBoxLayout(sens_card)
        sl.setContentsMargins(20, 18, 20, 18)
        sl.setSpacing(10)

        th_row = QHBoxLayout()
        th_row.addWidget(lbl("Detection Threshold", 15, TEXT_WHITE, bold=True))
        th_row.addStretch()
        self._thresh_lbl = lbl("Balanced (Recommended)", 15, CYAN, bold=True)
        th_row.addWidget(self._thresh_lbl)
        sl.addLayout(th_row)

        self._slider = QSlider(Qt.Orientation.Horizontal)
        self._slider.setRange(0,100)
        self._slider.setValue(50)
        sl.addWidget(self._slider)

        hint_row = QHBoxLayout()
        hint_row.addWidget(lbl("Low False Positives", 13, TEXT_MUTED))
        hint_row.addStretch()
        hint_row.addWidget(lbl("Maximum Protection", 13, TEXT_MUTED))
        sl.addLayout(hint_row)
        root.addWidget(sens_card)
        root.addWidget(hsep())

        root.addLayout(section_title("󰌾", "Automated Response", RED))

        ade_card = card_frame()
        al = QVBoxLayout(ade_card)
        al.setContentsMargins(20, 16, 20, 0)
        al.setSpacing(0)

        ade_row = QHBoxLayout()
        col = QVBoxLayout()
        col.setSpacing(2)
        col.addWidget(lbl("Active Defense Engine", 15, TEXT_WHITE, bold=True))
        col.addWidget(lbl("Automatically take action when critical threats are detected", 13, TEXT_MUTED))
        ade_row.addLayout(col)
        ade_row.addStretch()
        self._ade_toggle = ToggleSwitch(checked=True)
        ade_row.addWidget(self._ade_toggle)
        al.addLayout(ade_row)
        al.addSpacing(12)
        al.addWidget(hsep())

        self._sub_options = []
        sub_items = [
            ("󱐋", "Kill Suspicious Processes", True, None),
            ("󰍛", "Isolate Compromised Hosts", False, "⚠  Warning: Disconnects network"),
            ("󰏒", "Block Ransomware File Writes", True, None),
        ]

        for i, (icon, title, checked, warning) in enumerate(sub_items):
            row = QHBoxLayout()
            row.setContentsMargins(0, 12, 0, 12)
            left = QHBoxLayout()
            left.setSpacing(10)
            left.addWidget(lbl(icon, 17, TEXT_MUTED))
            col2 = QVBoxLayout()
            col2.setSpacing(2)
            col2.addWidget(lbl(title, 16, TEXT_WHITE))
            if warning:
                col2.addWidget(lbl(warning, 12, ORANGE))
            left.addLayout(col2)
            row.addLayout(left)
            row.addStretch()
            tog = ToggleSwitch(checked=checked)
            self._sub_options.append(tog)
            row.addWidget(tog)
            al.addLayout(row)
            if i < len(sub_items) - 1:
                al.addWidget(hsep())

        al.addSpacing(4)
        root.addWidget(ade_card)
        root.addStretch()

        # --- Connect signals AFTER all widgets are built ---
        self._ade_toggle.toggled.connect(self._on_ade_toggle)
        if self._sub_options:
            self._sub_options[0].toggled.connect(self._on_kill_toggle)
        self._slider.valueChanged.connect(self._on_slider)

        # --- Restore saved settings AFTER widgets exist ---
        saved = _load_settings()
        if "auto_quarantine" in saved:
            self._ade_toggle.setChecked(saved["auto_quarantine"])
        if "auto_kill_process" in saved and self._sub_options:
            self._sub_options[0].setChecked(saved["auto_kill_process"])
        if "slider_value" in saved:
            self._slider.setValue(saved["slider_value"])
    
    def _on_ade_toggle(self, checked: bool):
        from ransomware_part import config as rs_config
        rs_config.SETTINGS["auto_qurantine"] = checked
        print(f"[settings] auto_quarantine -> {checked}")
        
    def _on_kill_toggle(self, checked: bool):
        try:
            import config
            config.SETTINGS["auto_kill_process"] = checked
        except Exception:
            pass

    def _on_slider(self, v):
        if v < 30:   label = "Low (Permissive)"
        elif v < 50: label = "Conservative"
        elif v < 70: label = "Balanced (Recommended)"
        elif v < 85: label = "Aggressive"
        else:        label = "Maximum Protection"
        self._thresh_lbl.setText(label)
        try:
            import config
            if v < 30:
                config.HIGH_THRESHOLD, config.MEDIUM_THRESHOLD = 120, 80
            elif v < 70:
                config.HIGH_THRESHOLD, config.MEDIUM_THRESHOLD = 80, 50
            else:
                config.HIGH_THRESHOLD, config.MEDIUM_THRESHOLD = 60, 35
        except Exception:
            pass

class FileMonitoringPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        root = QVBoxLayout(self)
        root.setContentsMargins(32, 28, 32, 32)
        root.setSpacing(24)
        root.setAlignment(Qt.AlignmentFlag.AlignTop)

        # Monitored Directories 
        hdr = QHBoxLayout()
        hdr.addLayout(section_title("󰛐", "Monitored Directories"))
        add_btn = QPushButton("+ Add Path")
        add_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        add_btn.setStyleSheet(f"""
            QPushButton {{ background:transparent; border:1px;
                color:{TEXT_WHITE}; border-radius:8px; padding:6px 14px; font-size:15px; }}
            QPushButton:hover {{ border-color:{CYAN}; color:{CYAN}; }}
        """)
        add_btn.clicked.connect(self._add_path)
        hdr.addWidget(add_btn)
        root.addLayout(hdr)
        root.addWidget(lbl("Paths subjected to real-time ransomware scanning.", 13, TEXT_MUTED))

        self._paths_card = card_frame()
        self._paths_layout = QVBoxLayout(self._paths_card)
        self._paths_layout.setContentsMargins(4, 4, 4, 4)
        self._paths_layout.setSpacing(0)

        self._paths = ["/srv/finance/data", "/home/users/documents", "/etc/config/critical"]
        self._rebuild_paths()
        root.addWidget(self._paths_card)

        root.addWidget(hsep())

        #  Deception System 

        dec_hdr = QHBoxLayout()
        dec_hdr.addWidget(lbl("󰀪", 16, YELLOW))
        dec_hdr.addWidget(lbl("Deception System", 18, TEXT_WHITE, bold=True))
        dec_hdr.addStretch()
        self._dec_toggle = ToggleSwitch(checked=True)
        dec_hdr.addWidget(self._dec_toggle)
        root.addLayout(dec_hdr)

        bait_card = card_frame()
        bl = QVBoxLayout(bait_card); bl.setContentsMargins(20, 18, 20, 18); bl.setSpacing(14)
        bl.addWidget(lbl("Bait File Configuration", 13, CYAN, bold=True))

        bait_files = [
            (".xlsx (Excel)", True), (".docx (Word)", True),
            (".pdf (Document)", True), (".bak (Backup)", True),
            (".pem (Keys)", True),
        ]
        grid = QGridLayout(); grid.setSpacing(10)
        for i, (name, chk) in enumerate(bait_files):
            cb_frame = QFrame()
            cb_frame.setStyleSheet(f"QFrame{{background:{BG_CARD2};border:1px;"
                                   f"border-radius:8px;}}")
            fl = QHBoxLayout(cb_frame); fl.setContentsMargins(12, 10, 12, 10)
            fl.addWidget(styled_checkbox(name, chk))
            r, c = divmod(i, 2)
            grid.addWidget(cb_frame, r, c)
        bl.addLayout(grid)
        bl.addWidget(lbl("󰀪  Honeyfiles are placed in hidden directories. "
                         "Do not manually interact with them.", 13, YELLOW))
        root.addWidget(bait_card)
        root.addStretch()

    def _rebuild_paths(self):
        while self._paths_layout.count():
            item = self._paths_layout.takeAt(0)
            if item.widget(): item.widget().deleteLater()

        for i, path in enumerate(self._paths):
            row = QWidget()
            row.setStyleSheet(f"background:{BG_CARD};border-radius:8px;")
            rl = QHBoxLayout(row); rl.setContentsMargins(16, 12, 16, 12)
            rl.addWidget(lbl("󰂺", 13, TEXT_MUTED))
            rl.addSpacing(10)
            rl.addWidget(lbl(path, 13, TEXT_WHITE))
            rl.addStretch()
            rm = QPushButton("X")
            rm.setFixedSize(22, 22)
            rm.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
            rm.setStyleSheet(f"QPushButton{{background:transparent;border:none;color:{TEXT_MUTED};"
                             f"font-size:12px;}}QPushButton:hover{{color:{RED};}}")
            idx = i
            rm.clicked.connect(lambda _, x=idx: self._remove_path(x))
            rl.addWidget(rm)
            self._paths_layout.addWidget(row)
            if i < len(self._paths) - 1:
                self._paths_layout.addWidget(hsep())

    def _add_path(self):
        text, ok = QInputDialog.getText(self, "Add Monitored Path", "Enter directory path:")
        if ok and text.strip():
            self._paths.append(text.strip())
            self._rebuild_paths()

    def _remove_path(self, idx):
        if 0 <= idx < len(self._paths):
            self._paths.pop(idx)
            self._rebuild_paths()


class UserManagementPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        root = QVBoxLayout(self)
        root.setContentsMargins(32, 28, 32, 32)
        root.setSpacing(24)
        root.setAlignment(Qt.AlignmentFlag.AlignTop)

        #  MFA 
        root.addLayout(section_title("󰦝", "Multi-Factor Authentication (MFA)"))

        mfa_card = card_frame()
        ml = QHBoxLayout(mfa_card); ml.setContentsMargins(20, 18, 20, 18)

        lock_icon = lbl("󰌾", 22, TEXT_MUTED)
        lock_icon.setFixedWidth(36)
        ml.addWidget(lock_icon)
        ml.addSpacing(12)

        mc = QVBoxLayout(); mc.setSpacing(3)
        mfa_row = QHBoxLayout(); mfa_row.setSpacing(10)
        mfa_row.addWidget(lbl("Enable Two-Factor Authentication (2FA)", 15, TEXT_WHITE, bold=True))
        self._mfa_badge = QLabel("DISABLED")
        self._mfa_badge.setFixedSize(72, 20)
        self._mfa_badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._mfa_badge.setStyleSheet(f"color:{TEXT_MUTED};"
                                       f"border-radius:4px;font-size:11px;font-weight:700;")
        mfa_row.addWidget(self._mfa_badge)
        mc.addLayout(mfa_row)
        mc.addWidget(lbl("Require an additional verification step during login for enhanced security.",
                         13, TEXT_MUTED))
        ml.addLayout(mc); ml.addStretch()

        self._mfa_toggle = ToggleSwitch(checked=False)
        self._mfa_toggle.toggled.connect(self._on_mfa)
        ml.addWidget(self._mfa_toggle)
        root.addWidget(mfa_card)

        #  Authorized Users 
        uhdr = QHBoxLayout()
        uhdr.addWidget(lbl("Authorized Users", 18, TEXT_WHITE, bold=True))
        uhdr.addStretch()
        add_user = QPushButton("+ Add User")
        add_user.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        add_user.setStyleSheet(f"""
            QPushButton {{ background:{CYAN}; border:none; color:#000;
                border-radius:8px; padding:8px 18px; font-size:13px; font-weight:700; }}
            QPushButton:hover {{ background:{CYAN_DIM}; }}
        """)
        add_user.clicked.connect(self._add_user)
        uhdr.addWidget(add_user)
        root.addLayout(uhdr)

        users_card = card_frame()
        ul = QVBoxLayout(users_card); ul.setContentsMargins(20, 16, 20, 16); ul.setSpacing(0)

        # Table header
        th = QHBoxLayout()
        for col, stretch in [("Name", 2), ("Role", 2), ("Email", 3), ("Status", 2), ("Actions", 2)]:
            th.addWidget(lbl(col, 12, TEXT_MUTED, bold=True), stretch)
        ul.addLayout(th)
        ul.addSpacing(8)
        ul.addWidget(hsep())
        ul.addSpacing(8)

        self._users = [
            ("Admin User", "Super Admin", "admin@novasphere.sec", "Active"),
            ("John Doe", "Security Analyst", "j.doe@novasphere.sec", "Active"),
            ("Audit Service", "Viewer", "audit@novasphere.sec", "Inactive"),
        ]
        self._users_layout = QVBoxLayout(); self._users_layout.setSpacing(12)
        ul.addLayout(self._users_layout)
        self._rebuild_users()
        root.addWidget(users_card)
        root.addStretch()

    def _rebuild_users(self):
        while self._users_layout.count():
            item = self._users_layout.takeAt(0)
            if item.widget(): item.widget().deleteLater()
            elif item.layout():
                while item.layout().count():
                    sub = item.layout().takeAt(0)
                    if sub.widget(): sub.widget().deleteLater()

        for name, role, email, status in self._users:
            row = QHBoxLayout()
            row.addWidget(lbl(name, 13, TEXT_WHITE, bold=True), 2)
            row.addWidget(lbl(role, 13, TEXT_SUB), 2)
            row.addWidget(lbl(email, 12, TEXT_SUB), 3)

            badge = QLabel(status)
            badge.setFixedSize(64, 22)
            badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
            color = GREEN if status == "Active" else TEXT_MUTED
            badge.setStyleSheet(f"background:{'#0a2e20' if status == 'Active' else BG_CARD2};"
                                f"color:{color};border-radius:11px;font-size:11px;font-weight:700;")
            act_row = QHBoxLayout(); act_row.setSpacing(8)
            act_row.addWidget(badge)

            actions = QHBoxLayout(); actions.setSpacing(14)
            for atxt in ["Edit", "Revoke"]:
                ab = QPushButton(atxt)
                ab.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
                ab.setStyleSheet(f"QPushButton{{background:transparent;border:none;"
                                 f"color:{CYAN};font-size:12px;font-weight:600;}}"
                                 f"QPushButton:hover{{color:{TEXT_WHITE};}}")
                actions.addWidget(ab)

            row.addLayout(act_row, 2)
            row.addLayout(actions, 2)
            self._users_layout.addLayout(row)

    def _on_mfa(self, checked):
        self._mfa_badge.setText("ENABLED" if checked else "DISABLED")
        color = GREEN if checked else TEXT_MUTED
        self._mfa_badge.setStyleSheet(
            f"background:{'#0a2e20' if checked else BORDER};color:{color};"
            f"border-radius:4px;font-size:10px;font-weight:700;")

    def _add_user(self):
        name, ok = QInputDialog.getText(self, "Add User", "Enter username:")
        if ok and name.strip():
            self._users.append((name.strip(), "Viewer", f"{name.lower()}@novasphere.sec", "Active"))
            self._rebuild_users()


class AlertsNotificationsPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        root = QVBoxLayout(self)
        root.setContentsMargins(32, 28, 32, 32)
        root.setSpacing(24)
        root.setAlignment(Qt.AlignmentFlag.AlignTop)

        root.addLayout(section_title("󰂚", "Alert Channels", "#c084fc"))

        channels = [
            ("󰠠", "Desktop Notifications", "Show pop-up alerts on admin workstation", True),
            ("󰇰", "Email Alerts", "Send critical incident reports to admin team", True),
        ]
        for icon, title, sub, checked in channels:
            ch_card = card_frame()
            cl = QHBoxLayout(ch_card); cl.setContentsMargins(20, 16, 20, 16)
            cl.addWidget(lbl(icon, 18, TEXT_MUTED))
            cl.addSpacing(14)
            col = QVBoxLayout(); col.setSpacing(3)
            col.addWidget(lbl(title, 15, TEXT_WHITE, bold=True))
            col.addWidget(lbl(sub, 13, TEXT_MUTED))
            cl.addLayout(col); cl.addStretch()
            cl.addWidget(ToggleSwitch(checked=checked))
            root.addWidget(ch_card)

        root.addWidget(hsep())
        root.addWidget(lbl("CONFIGURATION", 14, TEXT_MUTED, bold=True))
        root.addSpacing(4)

        cfg_row = QHBoxLayout(); cfg_row.setSpacing(20)
        sev_col = QVBoxLayout(); sev_col.setSpacing(8)
        sev_col.addWidget(lbl("Minimum Severity for Email", 13, TEXT_MUTED))
        sev_col.addWidget(styled_combo(["Critical Only", "High & Above",
                                        "Medium & Above", "All Alerts"]))
        cfg_row.addLayout(sev_col, 1)

        cool_col = QVBoxLayout(); cool_col.setSpacing(8)
        cool_col.addWidget(lbl("Alert Cooldown (minutes)", 13, TEXT_MUTED))
        cool_col.addWidget(styled_input("15", "Minutes"))
        cfg_row.addLayout(cool_col, 1)
        root.addLayout(cfg_row)
        root.addStretch()


class SystemPerformancePanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        root = QVBoxLayout(self)
        root.setContentsMargins(32, 28, 32, 32)
        root.setSpacing(24)
        root.setAlignment(Qt.AlignmentFlag.AlignTop)

        # Data Retention

        root.addWidget(lbl("Data Retention", 18, TEXT_WHITE, bold=True))

        ret_row = QHBoxLayout(); ret_row.setSpacing(20)

        log_col = QVBoxLayout(); log_col.setSpacing(8)
        log_col.addWidget(lbl("Incident Log Retention", 14, TEXT_MUTED))
        self._retention_combo = styled_combo(["7 Days", "14 Days", "30 Days",
                                              "60 Days", "90 Days", "1 Year"], current=2)
        log_col.addWidget(self._retention_combo)
        ret_row.addLayout(log_col, 1)

        enc_col = QVBoxLayout(); enc_col.setSpacing(8)
        enc_col.addWidget(lbl("Log Encryption", 14, TEXT_MUTED))
        enc_badge = QLabel(" 󰂚  AES-256 Enabled")
        enc_badge.setStyleSheet(f"color:{GREEN};font-size:14px;background:transparent;"
                                f"padding:10px 0;")
        enc_col.addWidget(enc_badge)
        ret_row.addLayout(enc_col, 1)
        root.addLayout(ret_row)

        root.addWidget(hsep())

        # Danger Zone 

        root.addWidget(lbl("Danger Zone", 18, TEXT_WHITE, bold=True))

        danger_card = card_frame(red_tint=True)
        dl = QHBoxLayout(danger_card); dl.setContentsMargins(20, 18, 20, 18)

        dc = QVBoxLayout(); dc.setSpacing(4)
        dc.addWidget(lbl("Factory Reset", 15, TEXT_WHITE, bold=True))
        dc.addWidget(lbl("Restore all settings to default and clear local logs", 13, RED))
        dl.addLayout(dc); dl.addStretch()

        reset_btn = QPushButton("Reset System")
        reset_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        reset_btn.setStyleSheet(f"""
            QPushButton {{ background:{RED}; border:none; color:#fff;
                border-radius:8px; padding:10px 20px; font-size:13px; font-weight:700; }}
            QPushButton:hover {{ background:#cc2200; }}
        """)
        reset_btn.clicked.connect(self._confirm_reset)
        dl.addWidget(reset_btn)
        root.addWidget(danger_card)
        root.addStretch()

    def get_retention_days(self) -> int:
        mapping = {"7 Days": 7, "14 Days": 14, "30 Days": 30,
                   "60 Days": 60, "90 Days": 90, "1 Year": 365}
        return mapping.get(self._retention_combo.currentText(), 30)

    def _confirm_reset(self):
        msg = QMessageBox(self)
        msg.setWindowTitle("Confirm Factory Reset")
        msg.setText("This will erase ALL settings and logs.\nThis action cannot be undone.")
        msg.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.Cancel)
        msg.setDefaultButton(QMessageBox.StandardButton.Cancel)
        msg.setStyleSheet(f"QWidget{{background:{BG_CARD};color:{TEXT_WHITE};}}"
                          f"QPushButton{{background: {BORDER}; border:none;color:{TEXT_WHITE};"
                          f"border-radius:6px;padding:6px 16px;}}")
        if msg.exec() == QMessageBox.StandardButton.Yes:
            pass  # Hook real reset logic here

# Main settings page

class SettingsPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._build()

    def _build(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setStyleSheet(
            f"QScrollArea{{border:none;background:transparent;}}"
            f"QScrollBar:vertical{{background:{BG_MAIN};width:5px;border-radius:2px;}}"
            f"QScrollBar::handle:vertical{{background:{BORDER};border-radius:2px;min-height:30px;}}"
            f"QScrollBar::add-line:vertical,QScrollBar::sub-line:vertical{{height:0;}}"
        )

        container = QWidget()
        scroll.setWidget(container)
        root = QVBoxLayout(container)
        root.setContentsMargins(28, 22, 28, 28)
        root.setSpacing(0)
        root.setAlignment(Qt.AlignmentFlag.AlignTop)

        #  Top bar 

        tb = QHBoxLayout()
        icon_lbl = lbl("󰒓", 24, TEXT_MUTED)
        title_col = QVBoxLayout(); title_col.setSpacing(2)
        title_col.addWidget(lbl("System Configuration", 20, TEXT_WHITE, bold=True))
        title_col.addWidget(lbl("Manage security policies, users, and system preferences", 15, TEXT_MUTED))
        tb.addWidget(icon_lbl); tb.addSpacing(10); tb.addLayout(title_col); tb.addStretch()

        reset_btn = QPushButton("↺  Reset Defaults")
        reset_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        reset_btn.setStyleSheet(
            f"QPushButton{{background:transparent;border:none;color:{TEXT_MUTED};"
            f"font-size:14px;padding:8px 16px;}}"
            f"QPushButton:hover{{color:{TEXT_WHITE};}}")

        save_btn = QPushButton(" 󰠘  Save Changes")
        save_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        save_btn.setStyleSheet(
            f"QPushButton{{background:{CYAN};border:none;color:#000;"
            f"border-radius:8px;padding:10px 22px;font-size:14px;font-weight:700;}}"
            f"QPushButton:hover{{background:{CYAN_DIM};}}")
        save_btn.clicked.connect(self._save)

        tb.addWidget(reset_btn); tb.addSpacing(8); tb.addWidget(save_btn)
        root.addLayout(tb)
        root.addSpacing(20)

        # Body: sidebar + content

        body = QHBoxLayout(); body.setSpacing(16)

        # Sidebar
        sidebar = QFrame()
        sidebar.setFixedWidth(230)
        sidebar.setStyleSheet(f"QFrame{{background:{BG_CARD};border:1px;"
                              f"border-radius:14px;}}")
        sbl = QVBoxLayout(sidebar); sbl.setContentsMargins(12, 20, 12, 20); sbl.setSpacing(4)
        sbl.addWidget(lbl("SETTINGS GROUPS", 13, TEXT_MUTED, bold=True))
        sbl.addSpacing(8)

        self._nav_buttons = []
        self._panels = QStackedWidget()

        groups = [
            ("󰒙", "Detection & Response", DetectionResponsePanel()),
            ("󰂺", "File Monitoring",       FileMonitoringPanel()),
            ("󰀓", "User Management",      UserManagementPanel()),
            ("󰂜", "Alerts & Notifications", AlertsNotificationsPanel()),
            ("󱪳", "System & Performance", SystemPerformancePanel()),
        ]
        for icon, title, panel in groups:
            btn = QPushButton(f"  {icon}  {title}")
            btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
            btn.setObjectName("settings_nav")
            btn.setStyleSheet(self._nav_style(False))
            self._nav_buttons.append(btn)
            self._panels.addWidget(panel)
            sbl.addWidget(btn)

        sbl.addStretch()

        for i, btn in enumerate(self._nav_buttons):
            btn.clicked.connect(lambda _, idx=i: self._nav(idx))
        self._nav(0)

        # Content area
        content_frame = QFrame()
        content_frame.setStyleSheet(f"QFrame{{background:{BG_CARD};border:1px;"
                                    f"border-radius:14px;}}")
        cf = QVBoxLayout(content_frame)
        cf.setContentsMargins(0, 0, 0, 0)
        cf.addWidget(self._panels)

        body.addWidget(sidebar)
        body.addWidget(content_frame, 1)
        root.addLayout(body)

        outer.addWidget(scroll)

    def _nav_style(self, active: bool) -> str:
        if active:
            return (f"QPushButton{{background:{BG_CARD2};border:none;"
                    f"color:{CYAN};text-align:left;padding:11px 14px;"
                    f"font-size:13px;border-radius:8px;font-weight:600;}}")
        return (f"QPushButton{{background:transparent;border:none;"
                f"color:{TEXT_MUTED};text-align:left;padding:11px 14px;"
                f"font-size:13px;border-radius:8px;}}"
                f"QPushButton:hover{{color:{TEXT_WHITE};background:#111827;}}")

    def _nav(self, idx: int):
        self._panels.setCurrentIndex(idx)
        for i, btn in enumerate(self._nav_buttons):
            btn.setStyleSheet(self._nav_style(i == idx))

    def _save(self):
        """Persist all settings to JSON."""
        # Collect from Detection panel (index 0)
        det_panel = self._panels.widget(0)
        data = {}
        if hasattr(det_panel, "_ade_toggle"):
           data["auto_quarantine"] = det_panel._ade_toggle.isChecked()
        if hasattr(det_panel, "_sub_options") and det_panel._sub_options:
           data["auto_kill_process"] = det_panel._sub_options[0].isChecked()
        if hasattr(det_panel, "_slider"):
           data["slider_value"] = det_panel._slider.value()

        perf_panel = self._panels.widget(4)
        if hasattr(perf_panel, "get_retention_days"):
            data["retention_days"] = perf_panel.get_retention_days()
        
        _save_settings(data)

        msg = QMessageBox(self)
        msg.setWindowTitle("Settings Saved")
        msg.setText("Configuration saved successfully.")
        msg.setStandardButtons(QMessageBox.StandardButton.Ok)
        msg.setStyleSheet(f"QWidget{{background:{BG_CARD};color:{TEXT_WHITE};}}"
                      f"QPushButton{{background:{CYAN};border:none;color:#000;"
                      f"border-radius:6px;padding:6px 20px;font-weight:700;}}")
        msg.exec()

        saved = _load_settings()
        if saved:
            det_panel = self._panels.widget(0)
            if hasattr(det_panel, "_ade_toggle") and "auto_quarantine" in saved:
                det_panel._ade_toggle.setChecked(saved["auto_quarantine"])
            if hasattr(det_panel, "_sub_options") and "auto_kill_process" in saved:
                det_panel._sub_options[0].setChecked(saved["auto_kill_process"])
            if hasattr(det_panel, "_slider") and "slider_value" in saved:
                det_panel._slider.setValue(saved["slider_value"])


    def reload(self):
        pass  # Called by dashboard on tab switch — nothing to refresh here

# Standalone test 

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyleSheet(f"* {{font-family:'Segoe UI',sans-serif;}}"
                      f"QWidget{{background:{BG_MAIN};color:{TEXT_WHITE};}}")
    w = SettingsPage()
    w.setWindowTitle("NovaSphere — System Configuration")
    w.resize(1280, 820)
    w.show()
    sys.exit(app.exec())