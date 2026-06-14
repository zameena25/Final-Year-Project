# NOVASPHERE — Login & Sign Up Screen
# Matches Figma design exactly
# Run: python login.py
#
# Install: pip install PyQt6

import sys
import socket
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QCheckBox, QFrame, QScrollArea,
    QStackedWidget, QSizePolicy, QGraphicsDropShadowEffect
)
from PyQt6.QtCore import Qt, QSize, QPropertyAnimation, QEvent, QEasingCurve, pyqtSignal
from PyQt6.QtGui import (
    QColor, QFont, QPalette, QPainter, QPen, QBrush,
    QLinearGradient, QFontDatabase, QCursor, QPainterPath, QPixmap, QIcon
)
from PyQt6.QtSvgWidgets import QSvgWidget
from auth import AuthService, init_db, session_manager
from auth.ui.two_factor_dialog import TwoFactorDialog 
import frontend.security_overview
from auth.session_manager import SessionManager 
from auth.ui.two_factor_dialog import TwoFactorDialog


# ─── Colors (from Figma) ──────────────────────────────────────────────────────
BG_DARK      = "#0d1117"   # outer background
BG_CARD      = "#161b27"   # card background
BG_INPUT     = "#1a2133"   # input field background
BG_NOTICE    = "#1a2133"   # notice box background
CYAN         = "#00bcd4"   # primary accent
CYAN_DARK    = "#0097a7"   # button hover
BORDER       = "#2a3548"   # input border
BORDER_FOCUS = "#00bcd4"   # focused input border
TEXT_WHITE   = "#e8eaf0"   # primary text
TEXT_MUTED   = "#6b7a99"   # placeholder / muted
TEXT_CYAN    = "#00bcd4"   # links / highlights
TEXT_ORANGE  = "#ffa726"   # warning icon color
TEXT_BLUE    = "#42a5f5"   # info icon color

# ─── Stylesheet ───────────────────────────────────────────────────────────────
STYLE = f"""
QWidget {{
    background-color: {BG_DARK};
    color: {TEXT_WHITE};
    font-family: 'Times New Romen', sans-serif;
}}

/* ── Scroll area ── */
QScrollArea {{ border: none; background: {BG_DARK}; }}
QScrollBar:vertical {{
    background: {BG_DARK}; width: 10px; border-radius: 3px;
}}
QScrollBar::handle:vertical {{
    background: #2a3548; border-radius: 3px;
}}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}

/* ── Card ── */
#card {{
    background: {BG_CARD};
    border: 2px solid {BORDER};
    border-radius: 20px;
    padding: 20px;
}}

/* ── Tab buttons ── */
QPushButton#tab_btn {{
    background: transparent;
    border: none;
    color: {TEXT_MUTED};
    font-size: 16px;
    padding: 8px 0;
    border-radius: 5px;
}}
QPushButton#tab_btn[active="true"] {{
    background: {CYAN};
    color: white;
    font-weight: bold;
}}
QPushButton#tab_btn:hover {{
    color: {CYAN};
}}
QPushButton#tab_btn[active="true"]:hover {{
    background: {CYAN_DARK};
    color: white;
}}

/* ── Input fields ── */
QLineEdit {{
    background: {BG_INPUT};
    border: 2px solid {BORDER};
    border-radius: 16px;
    color: {TEXT_WHITE};
    font-size: 30px;
    padding: 25px 40px 25px 40px;
    selection-background-color: {CYAN};
}}
QLineEdit:focus {{
    border: 2px solid {BORDER_FOCUS};
}}
QLineEdit::placeholder {{
    color: {TEXT_MUTED};
}}

/* ── Primary button (Sign In / Create Account) ── */
QPushButton#primary_btn {{
    background: qlineargradient(
        x1:0, y1:0, x2:1, y2:0,
        stop:0 #00bcd4, stop:1 #0097a7
    );
    color: white;
    border: none;
    border-radius: 8px;
    font-size: 15px;
    font-weight: bold;
    padding: 5px;
}}
QPushButton#primary_btn:hover {{
    background: qlineargradient(
        x1:0, y1:0, x2:1, y2:0,
        stop:0 #26c6da, stop:1 #00b3e0
    );
}}
QPushButton#primary_btn:pressed {{
    background: {CYAN_DARK};
}}

/* ── Guest button ── */
QPushButton#guest_btn {{
    background: {BG_CARD};
    color: {TEXT_WHITE};
    border: 1px solid {BORDER};
    border-radius: 8px;
    font-size: 13px;
    padding: 13px;
}}
QPushButton#guest_btn:hover {{
    border: 1px solid {CYAN};
    color: {CYAN};
}}

/* ── Checkbox ── */
QCheckBox {{
    color: {TEXT_WHITE};
    font-size: 12px;
    spacing: 8px;
}}
QCheckBox::indicator {{
    width: 16px; height: 16px;
    border: 2px solid {BORDER};
    border-radius: 3px;
    background: {BG_INPUT};
}}
QCheckBox::indicator:checked {{
    background: {CYAN};
    border-color: {CYAN};
    image: none;
}}

/* ── Notice boxes ── */
#notice_box {{
    background: {BG_INPUT};
    border: 1px solid {BORDER};
    border-radius: 8px;
    padding: 12px;
}}

/* ── Divider line ── */
#divider_line {{
    background: {BORDER};
    max-height: 1px;
    min-height: 1px;
}}

/* ── Links ── */
QPushButton#link_btn {{
    background: transparent;
    border: none;
    color: {TEXT_CYAN};
    font-size: 12px;
    padding: 0;
    text-decoration: underline;
}}
QPushButton#link_btn:hover {{
    color: #26c6da;
}}
"""

# ─── Shield SVG logo ──────────────────────────────────────────────────────────
SHIELD_SVG = b"""
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 80 90" fill="none">
  <path d="M40 2L6 16v26c0 22 14 40 34 46 20-6 34-24 34-46V16L40 2z"
        fill="#161b27" stroke="#00bcd4" stroke-width="2.5"/>
  <path d="M40 10L12 22v20c0 17 11 31 28 36 17-5 28-19 28-36V22L40 10z"
        fill="#1a2133" stroke="#00bcd4" stroke-width="1.5" opacity="0.7"/>
  <circle cx="40" cy="38" r="10" stroke="#00bcd4" stroke-width="2" fill="none"/>
  <rect x="36" y="44" width="8" height="10" rx="2"
        fill="#00bcd4" opacity="0.9"/>
  <circle cx="40" cy="38" r="4" fill="#00bcd4" opacity="0.8"/>
  <path d="M28 30 Q40 18 52 30" stroke="#00bcd4" stroke-width="1.5"
        fill="none" opacity="0.5"/>
</svg>
"""
class StyledLineEdit(QLineEdit):
    """Custom QLineEdit with focus signals."""
    focus_gained = pyqtSignal()
    focus_lost = pyqtSignal()
    
    def focusInEvent(self, event):
        super().focusInEvent(event)
        self.focus_gained.emit()
    
    def focusOutEvent(self, event):
        super().focusOutEvent(event)
        self.focus_lost.emit()

# ─── Reusable widgets ─────────────────────────────────────────────────────────

class IconLineEdit(QWidget):
    """Input field with left icon and optional right eye toggle."""

    def __init__(self, placeholder: str, icon: str, is_password=False, parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Container with border
        self._container = QFrame()
        self._container.setStyleSheet(f"""
            QFrame {{
                background: {BG_INPUT};
                border: 0.8px solid {BORDER};
                border-radius: 20px;
            }}
        """)
        self._container.setFixedHeight(68)
        
        cl = QHBoxLayout(self._container)
        cl.setContentsMargins(0, 0, 0, 0)
        cl.setSpacing(8)

        # Left icon
        icon_lbl = QLabel(icon)
        icon_lbl.setStyleSheet(f"""
            color: {TEXT_MUTED}; 
            font-size: 20px; 
            background: transparent;
        """)
        icon_lbl.setFixedWidth(28)
        icon_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        cl.addWidget(icon_lbl)

        # Input field
        self._input = StyledLineEdit()
        self._input.setPlaceholderText(placeholder)
        self._input.setStyleSheet(f"""
            QLineEdit {{
                background: transparent;
                border: none;
                color: {TEXT_WHITE};
                font-size: 16px;
                padding: 0;
            }}
            QLineEdit::placeholder {{
                color: {TEXT_MUTED};
            }}
        """)
        self._input.setFixedHeight(56)
        
        if is_password:
            self._input.setEchoMode(QLineEdit.EchoMode.Password)

        cl.addWidget(self._input, 1)

        # Password toggle eye button
        if is_password:
            self._eye_btn = QPushButton("👁")
            self._eye_btn.setStyleSheet(f"""
                QPushButton {{
                    background: transparent;
                    border: none;
                    color: {TEXT_MUTED};
                    font-size: 18px;
                    padding: 0 4px;
                }}
                QPushButton:hover {{ color: {TEXT_CYAN}; }}
            """)
            self._eye_btn.setFixedWidth(32)
            self._eye_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
            self._eye_btn.setCheckable(True)
            self._eye_btn.toggled.connect(self._toggle_password_visibility)
            cl.addWidget(self._eye_btn)

        # Connect focus events properly
        self._input.focus_gained.connect(self._on_focus_in)
        self._input.focus_lost.connect(self._on_focus_out)

        layout.addWidget(self._container)

    def _on_focus_in(self):
        self._container.setStyleSheet(f"""
            QFrame {{
                background: {BG_INPUT};
                border: 1px solid {CYAN};
                border-radius: 100px;
            }}
        """)

    def _on_focus_out(self):
        self._container.setStyleSheet(f"""
            QFrame {{
                background: {BG_INPUT};
                border: 2px solid {BORDER};
                border-radius: 26px;
            }}
        """)

    def _toggle_password_visibility(self, checked):
        self._input.setEchoMode(
            QLineEdit.EchoMode.Normal if checked else QLineEdit.EchoMode.Password
        )

    def text(self) -> str:
        return self._input.text()

    def clear(self):
        self._input.clear()

class NoticeBox(QFrame):

    def __init__(self, icon: str, title: str, body: str,
                 icon_color: str = TEXT_ORANGE, parent=None):
        super().__init__(parent)
        self.setObjectName("notice_box")

        lay = QHBoxLayout(self)
        lay.setContentsMargins(9, 9, 9, 9)
        lay.setSpacing(5)
        lay.setAlignment(Qt.AlignmentFlag.AlignTop)

        icon_lbl = QLabel(icon)
        icon_lbl.setStyleSheet(
            f"color: {icon_color}; font-size: 30px; background: transparent;"
        )
        icon_lbl.setFixedWidth(30)
        icon_lbl.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignHCenter)

        text_col = QVBoxLayout()
        text_col.setSpacing(3)

        if title:
            t = QLabel(title)
            t.setStyleSheet(
                f"color: {icon_color}; font-size: 13px; "
                f"font-weight: bold; background: transparent;"
            )
            text_col.addWidget(t)

        b = QLabel(body)
        b.setStyleSheet(
            f"color: {TEXT_MUTED}; font-size: 12px; background: transparent;"
        )
        b.setWordWrap(True)
        text_col.addWidget(b)

        lay.addWidget(icon_lbl)
        lay.addLayout(text_col, 1)


def h_divider(label: str = "") -> QWidget:
    """Horizontal 'Or' divider."""
    w = QWidget()
    h = QHBoxLayout(w)
    h.setContentsMargins(0, 0, 0, 0)
    h.setSpacing(50)

    for _ in range(2):
        line = QFrame()
        line.setObjectName("divider_line")
        line.setFrameShape(QFrame.Shape.HLine)
        h.addWidget(line, 1)
        if _ == 0 and label:
            lbl = QLabel(label)
            lbl.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 13px; background: transparent;")
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            h.addWidget(lbl)

    return w

# ─── Login form ───────────────────────────────────────────────────────────────

class LoginForm(QWidget):
    login_success = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        lay = QVBoxLayout(self)
        self.auth_svc = AuthService()
        self.session_mgr = SessionManager()
        lay.setContentsMargins(28, 24, 28, 28)
        lay.setSpacing(16)

        title = QLabel("Sign In to Your Account")
        title.setStyleSheet(
            f"color: {TEXT_WHITE}; font-size: 20px; font-weight: bold; background: transparent;"
        )
        lay.addWidget(title)

        # Email
        email_lbl = QLabel("Email Address")
        email_lbl.setStyleSheet(f"color: {TEXT_WHITE}; font-size: 15px; font-weight: 600; background: transparent; padding: 0;")
        self._email = IconLineEdit("Enter your email", "✉")
        lay.addWidget(email_lbl)
        lay.addWidget(self._email)

        # Password
        pass_lbl = QLabel("Password")
        pass_lbl.setStyleSheet(f"color: {TEXT_WHITE}; font-size: 15px; font-weight: 600; background: transparent;")
        self._password = IconLineEdit("Enter your password", "🔒", is_password=True)
        lay.addWidget(pass_lbl)
        lay.addWidget(self._password)

        # Keep signed in + Forgot
        row = QHBoxLayout()
        self._keep = QCheckBox("Keep me signed in")
        forgot = QPushButton("Forgot password?")
        forgot.setObjectName("link_btn")
        forgot.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        row.addWidget(self._keep)
        row.addStretch()
        row.addWidget(forgot)
        lay.addLayout(row)

        # Sign In button
        sign_in = QPushButton("Sign In")
        sign_in.setObjectName("primary_btn")
        sign_in.setFixedHeight(50)
        sign_in.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        sign_in.clicked.connect(self._do_login)
        lay.addWidget(sign_in)

        # Notice boxes
        lay.addWidget(NoticeBox("🛡", "Authorized Access Only",
            "This system is restricted to authorized users. "
            "All activities are monitored and logged.",
            icon_color="#ffa726"))

        lay.addWidget(NoticeBox("🔒", "",
            "Two-factor authentication can be enabled in Settings "
            "for additional protection.",
            icon_color=TEXT_MUTED))

        lay.addStretch()

    def _do_login(self):
        email = self._email.text().strip()
        password = self._password.text()
        remember = self._keep.isChecked()
        if not email or not password:
            return
        result = self.auth_svc.login(email, password)
        if not result["success"]:
            print ("Login Failed:", result["error"])
            return
        user = result["user"]

        if result["requires_2fa"]:
            dialog = TwoFactorDialog(user["id"], email, parent=self)
            if dialog.exec() != TwoFactorDialog.DialogCode.Accepted or not dialog.verified:
                return
            
        token = self.session_mgr.create_session(user["id"], remember=remember)
        if remember:
            self.session_mgr.save_token_to_disk(token)

        self.login_success.emit(email)

# ─── Sign Up form ─────────────────────────────────────────────────────────────

class SignUpForm(QWidget):
    signup_success = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        lay = QVBoxLayout(self)
        self.auth_svc = AuthService()
        lay.setContentsMargins(25, 15, 25, 25)
        lay.setSpacing(14)

        title = QLabel("Create New Account")
        title.setStyleSheet(
            f"color: {TEXT_WHITE}; font-size: 20px; font-weight: bold; background: transparent;"
        )
        lay.addWidget(title)

        # Email
        email_lbl = QLabel("Email Address")
        email_lbl.setStyleSheet(f"color: {TEXT_WHITE}; font-size: 15px; font-weight: 600; background: transparent;")
        self._email = IconLineEdit("Enter your email", "✉")
        hint = QLabel("ℹ  Email is used to send urgent security alerts to your mobile and inbox.")
        hint.setStyleSheet(f"color: {TEXT_BLUE}; font-size: 12px; background: transparent;")
        hint.setWordWrap(True)
        lay.addWidget(email_lbl)
        lay.addWidget(self._email)
        lay.addWidget(hint)

        # Password
        pass_lbl = QLabel("Password")
        pass_lbl.setStyleSheet(f"color: {TEXT_WHITE}; font-size: 15px; font-weight: 600; background: transparent;")
        self._password = IconLineEdit("Create a password", "🔒", is_password=True)
        lay.addWidget(pass_lbl)
        lay.addWidget(self._password)

        # Confirm Password
        conf_lbl = QLabel("Confirm Password")
        conf_lbl.setStyleSheet(f"color: {TEXT_WHITE}; font-size: 15px; font-weight: 600; background: transparent;")
        self._confirm = IconLineEdit("Confirm your password", "🔒", is_password=True)
        lay.addWidget(conf_lbl)
        lay.addWidget(self._confirm)

        # Create Account button
        create_btn = QPushButton("Create Account")
        create_btn.setObjectName("primary_btn")
        create_btn.setFixedHeight(48)
        create_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        create_btn.clicked.connect(self._do_signup)
        lay.addWidget(create_btn)

        # Notice boxes
        lay.addWidget(NoticeBox("✉", "Email Notifications",
            "Your email will be used to send real-time security alerts, "
            "threat notifications, and attack warnings.",
            icon_color=TEXT_CYAN))

        lay.addWidget(NoticeBox("🔒", "",
            "Two-factor authentication can be enabled in Settings "
            "for additional protection.",
            icon_color=TEXT_MUTED))

        lay.addStretch()

    def _do_signup(self):
        email = self._email.text().strip()
        password = self._password.text()
        confirm = self._confirm.text()

        if not email or not password:
            return
        if password != confirm:
            print("Passwords do not match.")
            return
        result = self.auth_svc.register(email, password)
        if result["success"]:
            self.signup_success.emit()
        else:
            print("Sign Up Failed:", result["error"])
    
# ─── Full auth screen ─────────────────────────────────────────────────────────

class AuthScreen(QWidget):
    login_success = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._build_ui()

    def _build_ui(self):
        # Outer scroll (in case window is small)
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        outer.addWidget(scroll)

        content = QWidget()
        scroll.setWidget(content)
        root = QVBoxLayout(content)
        root.setContentsMargins(0, 30, 0, 30)
        root.setSpacing(0)
        root.setAlignment(Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignTop)

        # ── Shield logo
        logo_label = QLabel()
        logo_path = Path("novasphere.png")
        if logo_path.exists():
            pixmap = QPixmap(str(logo_path))
            pixmap = pixmap.scaled(200, 200, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            logo_label.setPixmap(pixmap)
        else:
            logo_label.setText("")
            logo_label.setStyleSheet("font-size: 90px; color: #00bcd4;")

        logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        root.addWidget(logo_label)


        # ── NOVASPHERE title
        title_row = QHBoxLayout()
        title_row.setSpacing(0)
        title_row.setAlignment(Qt.AlignmentFlag.AlignHCenter)

        nova = QLabel("NOVA")
        nova.setStyleSheet(
            f"color: {TEXT_WHITE}; font-size: 40px; font-weight: 900; "
            f"letter-spacing: 2px; background: transparent;"
        )
        sphere = QLabel("SPHERE")
        sphere.setStyleSheet(
            f"color: {CYAN}; font-size: 40px; font-weight: 900; "
            f"letter-spacing: 2px; background: transparent;"
        )
        title_row.addWidget(nova)
        title_row.addWidget(sphere)
        root.addLayout(title_row)
        root.addSpacing(6)

        tagline = QLabel("Unified Threat Detection & Prevention")
        tagline.setStyleSheet(
            f"color: {TEXT_MUTED}; font-size: 20px; background: transparent;"
        )
        tagline.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        root.addWidget(tagline)
        root.addSpacing(28)

        # ── Card
        card = QFrame()
        card.setObjectName("card")
        card.setFixedWidth(550)
        card_lay = QVBoxLayout(card)
        card_lay.setContentsMargins(0, 0, 0, 0)
        card_lay.setSpacing(0)

        # Tab row
        tab_frame = QFrame()
        tab_frame.setStyleSheet(
            f"background: {BG_CARD}; border-radius: 10px 10px 0 0;"
        )
        tab_row = QHBoxLayout(tab_frame)
        tab_row.setContentsMargins(8, 8, 8, 8)
        tab_row.setSpacing(4)

        self._login_tab = QPushButton("Login")
        self._login_tab.setObjectName("tab_btn")
        self._login_tab.setFixedHeight(35)
        self._login_tab.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))

        self._signup_tab = QPushButton("Sign Up")
        self._signup_tab.setObjectName("tab_btn")
        self._signup_tab.setFixedHeight(35)
        self._signup_tab.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))

        tab_row.addWidget(self._login_tab)
        tab_row.addWidget(self._signup_tab)
        card_lay.addWidget(tab_frame)

        # Stacked forms
        self._forms = QStackedWidget()
        self._login_form  = LoginForm()
        self._signup_form = SignUpForm()
        self._forms.addWidget(self._login_form)
        self._forms.addWidget(self._signup_form)
        card_lay.addWidget(self._forms)

        root.addWidget(card, alignment=Qt.AlignmentFlag.AlignHCenter)
        root.addSpacing(20)

        # ── "Or" divider + guest button
        div_wrap = QWidget()
        div_wrap.setFixedWidth(400)
        div_lay = QVBoxLayout(div_wrap)
        div_lay.setContentsMargins(0, 0, 0, 0)
        div_lay.setSpacing(12)
        div_lay.addWidget(h_divider("Or"))

        guest_btn = QPushButton()
        guest_btn.setObjectName("guest_btn")
        guest_btn.setFixedHeight(48)
        guest_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))

        # Guest button inner layout
        gb_lay = QHBoxLayout(guest_btn)
        gb_lay.setContentsMargins(16, 0, 16, 0)
        icon_l = QLabel("⊞")
        icon_l.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 25px; background: transparent;")
        txt_l  = QLabel("Continue without account")
        txt_l.setStyleSheet(f"color: {TEXT_WHITE}; font-size: 16px; background: transparent;")
        trial_l = QLabel("3 trials left")
        trial_l.setStyleSheet(f"color: {CYAN}; font-size: 16px; font-weight: bold; background: transparent;")
        gb_lay.addWidget(icon_l)
        gb_lay.addWidget(txt_l)
        gb_lay.addStretch()
        gb_lay.addWidget(trial_l)

        div_lay.addWidget(guest_btn)

        hint2 = QLabel("Guest access limited to Security Scan and basic overview")
        hint2.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 11px; background: transparent;")
        hint2.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        div_lay.addWidget(hint2)

        root.addWidget(div_wrap, alignment=Qt.AlignmentFlag.AlignHCenter)
        root.addSpacing(20)

        # ── Footer
        footer = QLabel("© 2026 NOVASPHERE Security System. All rights reserved.")
        footer.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 10px; background: transparent;")
        footer.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        root.addWidget(footer)

        # ── Wire up tabs
        self._login_tab.clicked.connect(lambda: self._switch_tab(0))
        self._signup_tab.clicked.connect(lambda: self._switch_tab(1))
        self._login_form.login_success.connect(self.login_success.emit)
        self._switch_tab(0)

        # Guest access also opens dashboard
        guest_btn.clicked.connect(self._on_guest)

    def _switch_tab(self, idx: int):
        self._forms.setCurrentIndex(idx)
        self._login_tab.setProperty("active",  "true" if idx == 0 else "false")
        self._signup_tab.setProperty("active", "true" if idx == 1 else "false")
        for btn in [self._login_tab, self._signup_tab]:
            btn.style().unpolish(btn)
            btn.style().polish(btn)
    
    
    def _on_guest(self):
        machine_id = socket.gethostname()
        result = AuthService().guest_login(machine_id)
        if result["success"]:
            self.login_success.emit("Guest")
        else:
            print("Guest denied:", result["error"])

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("NOVASPHERE — Security System")
        self.setMinimumSize(1100, 900)
        self.resize(1200, 750)
        self._show_auth()

    def _show_auth(self):
        session_mgr = SessionManager()
        token = session_mgr.load_token_from_disk()
        if token:
            user_info = session_mgr.validate_session(token)
            if user_info:
                self._on_login(user_info["username"])
                return
            
        auth = AuthScreen()
        auth.login_success.connect(self._on_login)
        self.setCentralWidget(auth)

    def _on_login(self, user: str):
        # After login — launch the main dashboard
        # Import here to avoid circular issues
        try:
            self.hide()
            self._dashboard = frontend.security_overview.SecurityOverview()
            self._dashboard.show()
        except ImportError:
            # If dashboard.py not found, show a placeholder
            placeholder = QWidget()
            lay = QVBoxLayout(placeholder)
            lbl = QLabel(f"✅  Logged in as: {user}\n\nDashboard loading...")
            lbl.setStyleSheet(
                f"color: {CYAN}; font-size: 20px; text-align: center; background: transparent;"
            )
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            lay.addWidget(lbl)
            self.setCentralWidget(placeholder)

# ─── Entry point ──────────────────────────────────────────────────────────────

def main():
    app = QApplication(sys.argv)
    init_db()
    app.setStyleSheet(STYLE)

    palette = QPalette()
    palette.setColor(QPalette.ColorRole.Window,      QColor(BG_DARK))
    palette.setColor(QPalette.ColorRole.WindowText,  QColor(TEXT_WHITE))
    palette.setColor(QPalette.ColorRole.Base,        QColor(BG_INPUT))
    palette.setColor(QPalette.ColorRole.Text,        QColor(TEXT_WHITE))
    palette.setColor(QPalette.ColorRole.Button,      QColor(BG_CARD))
    palette.setColor(QPalette.ColorRole.ButtonText,  QColor(TEXT_WHITE))
    palette.setColor(QPalette.ColorRole.Highlight,   QColor(CYAN))
    palette.setColor(QPalette.ColorRole.HighlightedText, QColor("#000000"))
    app.setPalette(palette)

    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
