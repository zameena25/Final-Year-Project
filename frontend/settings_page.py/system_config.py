import sys
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QSlider, QScrollArea, QFrame, QSizePolicy
)
from PyQt6.QtCore import Qt, QSize, QRect, QPoint, QPropertyAnimation, QEasingCurve, pyqtProperty
from PyQt6.QtGui import (
    QPainter, QColor, QPen, QBrush, QFont, QFontMetrics,
    QPainterPath, QLinearGradient, QPalette, QCursor
)


# ─── Color Constants ───────────────────────────────────────────────────────────
BG_BASE        = "#0d1117"
BG_SIDEBAR     = "#161b22"
BG_CARD        = "#1c2128"
BG_CARD_HOVER  = "#21262d"
BG_ACTIVE_NAV  = "#1a2d3a"
BG_HEADER      = "#0d1117"

CYAN           = "#22d3ee"
CYAN_DARK      = "#1aa8c0"
CYAN_SUBTLE    = "#0e2a33"
AMBER          = "#f59e0b"
RED_WARN       = "#ef4444"
ORANGE_WARN    = "#f97316"

TEXT_PRIMARY   = "#e6edf3"
TEXT_SECONDARY = "#8b949e"
TEXT_MUTED     = "#6e7681"
TEXT_CYAN      = "#22d3ee"

BORDER_COLOR   = "#30363d"
BORDER_CARD    = "#21262d"

TOGGLE_ON      = "#22d3ee"
TOGGLE_OFF     = "#30363d"


# ─── Toggle Switch ─────────────────────────────────────────────────────────────
class ToggleSwitch(QWidget):
    def __init__(self, checked=True, parent=None):
        super().__init__(parent)
        self._checked = checked
        self._thumb_x = 1.0 if checked else 0.0
        self.setFixedSize(44, 24)
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))

        self._anim = QPropertyAnimation(self, b"thumb_pos", self)
        self._anim.setDuration(150)
        self._anim.setEasingCurve(QEasingCurve.Type.InOutQuad)

    @pyqtProperty(float)
    def thumb_pos(self):
        return self._thumb_x

    @thumb_pos.setter
    def thumb_pos(self, value):
        self._thumb_x = value
        self.update()

    def isChecked(self):
        return self._checked

    def setChecked(self, checked):
        self._checked = checked
        target = 1.0 if checked else 0.0
        self._anim.stop()
        self._anim.setStartValue(self._thumb_x)
        self._anim.setEndValue(target)
        self._anim.start()

    def mousePressEvent(self, event):
        self.setChecked(not self._checked)

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)

        w, h = self.width(), self.height()
        radius = h / 2

        # Track
        track_color = QColor(TOGGLE_ON) if self._checked else QColor(TOGGLE_OFF)
        # Blend for animation
        if 0.0 < self._thumb_x < 1.0:
            on_c  = QColor(TOGGLE_ON)
            off_c = QColor(TOGGLE_OFF)
            r = int(off_c.red()   + (on_c.red()   - off_c.red())   * self._thumb_x)
            g = int(off_c.green() + (on_c.green() - off_c.green()) * self._thumb_x)
            b = int(off_c.blue()  + (on_c.blue()  - off_c.blue())  * self._thumb_x)
            track_color = QColor(r, g, b)

        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QBrush(track_color))
        p.drawRoundedRect(0, 0, w, h, radius, radius)

        # Thumb
        thumb_diameter = h - 4
        thumb_travel   = w - thumb_diameter - 4
        thumb_x        = 2 + int(thumb_travel * self._thumb_x)
        thumb_y        = 2

        p.setBrush(QBrush(QColor("#ffffff")))
        p.drawEllipse(thumb_x, thumb_y, thumb_diameter, thumb_diameter)
        p.end()


# ─── Custom Slider ─────────────────────────────────────────────────────────────
class CyanSlider(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._value = 58  # ~"Balanced" position (0–100)
        self._dragging = False
        self.setFixedHeight(36)
        self.setMinimumWidth(200)
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))

    def value(self):
        return self._value

    def _track_rect(self):
        m = 10
        cy = self.height() // 2
        return QRect(m, cy - 3, self.width() - 2 * m, 6)

    def _thumb_x(self):
        tr = self._track_rect()
        return tr.x() + int((self._value / 100) * tr.width())

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)

        tr = self._track_rect()
        tx = self._thumb_x()

        # Track background
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QBrush(QColor("#30363d")))
        p.drawRoundedRect(tr, 3, 3)

        # Filled portion
        filled = QRect(tr.x(), tr.y(), tx - tr.x(), tr.height())
        p.setBrush(QBrush(QColor(CYAN)))
        p.drawRoundedRect(filled, 3, 3)

        # Thumb
        thumb_r = 10
        cy = self.height() // 2
        p.setBrush(QBrush(QColor("#ffffff")))
        p.setPen(QPen(QColor("#c8ccd0"), 1))
        p.drawEllipse(QPoint(tx, cy), thumb_r, thumb_r)
        p.end()

    def _x_to_value(self, x):
        tr = self._track_rect()
        val = (x - tr.x()) / tr.width() * 100
        return max(0, min(100, int(val)))

    def mousePressEvent(self, e):
        if e.button() == Qt.MouseButton.LeftButton:
            self._dragging = True
            self._value = self._x_to_value(e.position().x())
            self.update()

    def mouseMoveEvent(self, e):
        if self._dragging:
            self._value = self._x_to_value(e.position().x())
            self.update()

    def mouseReleaseEvent(self, e):
        self._dragging = False


# ─── Nav Item ──────────────────────────────────────────────────────────────────
class NavItem(QWidget):
    def __init__(self, icon: str, label: str, active=False, parent=None):
        super().__init__(parent)
        self._active = active
        self.setFixedHeight(44)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))

        layout = QHBoxLayout(self)
        layout.setContentsMargins(14, 0, 14, 0)
        layout.setSpacing(12)

        icon_label = QLabel(icon)
        icon_label.setFixedSize(20, 20)
        icon_label.setFont(QFont("Segoe UI", 13))
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        text_label = QLabel(label)
        text_label.setFont(QFont("Segoe UI", 10))

        layout.addWidget(icon_label)
        layout.addWidget(text_label)
        layout.addStretch()

        self._icon_label = icon_label
        self._text_label = text_label
        self._apply_style()

    def _apply_style(self):
        if self._active:
            self.setStyleSheet(f"""
                NavItem {{
                    background: {BG_ACTIVE_NAV};
                    border-radius: 8px;
                }}
            """)
            self._text_label.setStyleSheet(f"color: {CYAN}; font-weight: 500;")
            self._icon_label.setStyleSheet(f"color: {CYAN};")
        else:
            self.setStyleSheet("NavItem { background: transparent; border-radius: 8px; }")
            self._text_label.setStyleSheet(f"color: {TEXT_SECONDARY};")
            self._icon_label.setStyleSheet(f"color: {TEXT_MUTED};")

    def enterEvent(self, e):
        if not self._active:
            self.setStyleSheet(f"NavItem {{ background: {BG_CARD_HOVER}; border-radius: 8px; }}")

    def leaveEvent(self, e):
        if not self._active:
            self.setStyleSheet("NavItem { background: transparent; border-radius: 8px; }")


# ─── Section Header ────────────────────────────────────────────────────────────
def make_section_header(icon: str, icon_color: str, title: str) -> QWidget:
    w = QWidget()
    lay = QHBoxLayout(w)
    lay.setContentsMargins(0, 0, 0, 0)
    lay.setSpacing(10)

    icon_lbl = QLabel(icon)
    icon_lbl.setFont(QFont("Segoe UI", 16))
    icon_lbl.setStyleSheet(f"color: {icon_color};")
    icon_lbl.setFixedWidth(26)

    title_lbl = QLabel(title)
    title_lbl.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
    title_lbl.setStyleSheet(f"color: {TEXT_PRIMARY};")

    lay.addWidget(icon_lbl)
    lay.addWidget(title_lbl)
    lay.addStretch()
    return w


# ─── Card wrapper ──────────────────────────────────────────────────────────────
def make_card(content_widget: QWidget, padding=(16, 16, 16, 16)) -> QWidget:
    card = QWidget()
    card.setObjectName("card")
    card.setStyleSheet(f"""
        QWidget#card {{
            background: {BG_CARD};
            border: 1px solid {BORDER_CARD};
            border-radius: 10px;
        }}
    """)
    layout = QVBoxLayout(card)
    layout.setContentsMargins(*padding)
    layout.setSpacing(0)
    layout.addWidget(content_widget)
    return card


# ─── Divider ──────────────────────────────────────────────────────────────────
def make_divider():
    line = QFrame()
    line.setFrameShape(QFrame.Shape.HLine)
    line.setFixedHeight(1)
    line.setStyleSheet(f"background: {BORDER_CARD}; border: none;")
    return line


# ─── Toggle Row ────────────────────────────────────────────────────────────────
def make_toggle_row(title: str, subtitle: str = "", checked: bool = True,
                    icon: str = "", warning: str = "",
                    indent: bool = False) -> tuple[QWidget, ToggleSwitch]:
    row = QWidget()
    row.setObjectName("toggleRow")
    layout = QHBoxLayout(row)
    left_margin = 32 if indent else 16
    layout.setContentsMargins(left_margin, 12, 16, 12)
    layout.setSpacing(0)

    left = QVBoxLayout()
    left.setSpacing(2)

    title_row = QHBoxLayout()
    title_row.setSpacing(8)
    title_row.setContentsMargins(0, 0, 0, 0)

    if icon:
        icon_lbl = QLabel(icon)
        icon_lbl.setFont(QFont("Segoe UI", 11))
        icon_lbl.setStyleSheet(f"color: {TEXT_SECONDARY};")
        title_row.addWidget(icon_lbl)

    title_lbl = QLabel(title)
    title_lbl.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
    title_lbl.setStyleSheet(f"color: {TEXT_PRIMARY};")
    title_row.addWidget(title_lbl)
    title_row.addStretch()

    left.addLayout(title_row)

    if subtitle:
        sub_lbl = QLabel(subtitle)
        sub_lbl.setFont(QFont("Segoe UI", 9))
        sub_lbl.setStyleSheet(f"color: {TEXT_SECONDARY};")
        left.addWidget(sub_lbl)

    if warning:
        warn_row = QHBoxLayout()
        warn_row.setSpacing(4)
        warn_row.setContentsMargins(0, 0, 0, 0)
        warn_icon = QLabel("⚠")
        warn_icon.setFont(QFont("Segoe UI", 9))
        warn_icon.setStyleSheet(f"color: {ORANGE_WARN};")
        warn_lbl = QLabel(warning)
        warn_lbl.setFont(QFont("Segoe UI", 9))
        warn_lbl.setStyleSheet(f"color: {ORANGE_WARN};")
        warn_row.addWidget(warn_icon)
        warn_row.addWidget(warn_lbl)
        warn_row.addStretch()
        left.addLayout(warn_row)

    layout.addLayout(left)

    toggle = ToggleSwitch(checked=checked)
    layout.addWidget(toggle)

    return row, toggle


# ─── Left Sidebar ─────────────────────────────────────────────────────────────
class LeftSidebar(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedWidth(240)
        self.setObjectName("sidebar")
        self.setStyleSheet(f"""
            QWidget#sidebar {{
                background: {BG_SIDEBAR};
                border-right: 1px solid {BORDER_COLOR};
                border-radius: 12px;
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 20, 12, 20)
        layout.setSpacing(4)

        group_label = QLabel("SETTINGS GROUPS")
        group_label.setFont(QFont("Segoe UI", 8, QFont.Weight.Bold))
        group_label.setStyleSheet(f"color: {TEXT_MUTED}; letter-spacing: 1px;")
        group_label.setContentsMargins(8, 0, 0, 8)
        layout.addWidget(group_label)

        nav_items = [
            ("🛡", "Detection & Response", True),
            ("🗄", "File Monitoring",       False),
            ("👥", "User Management",       False),
            ("🔔", "Alerts & Notifications", False),
            ("⚙", "System & Performance",  False),
        ]

        for icon, label, active in nav_items:
            item = NavItem(icon, label, active)
            layout.addWidget(item)

        layout.addStretch()


# ─── Content Panel ─────────────────────────────────────────────────────────────
class ContentPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("contentPanel")
        self.setStyleSheet(f"QWidget#contentPanel {{ background: transparent; }}")

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setStyleSheet(f"""
            QScrollArea {{ background: transparent; border: none; }}
            QScrollBar:vertical {{
                background: {BG_BASE};
                width: 6px;
                border-radius: 3px;
            }}
            QScrollBar::handle:vertical {{
                background: {BORDER_COLOR};
                border-radius: 3px;
                min-height: 30px;
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
        """)

        inner = QWidget()
        inner.setStyleSheet("background: transparent;")
        inner_layout = QVBoxLayout(inner)
        inner_layout.setContentsMargins(32, 28, 32, 40)
        inner_layout.setSpacing(32)

        # ── Section 1: Heuristic Sensitivity ──────────────────────────────────
        section1 = QWidget()
        s1_layout = QVBoxLayout(section1)
        s1_layout.setContentsMargins(0, 0, 0, 0)
        s1_layout.setSpacing(16)

        # Header
        s1_header = make_section_header("⚡", AMBER, "Heuristic Sensitivity")
        s1_layout.addWidget(s1_header)

        sub_lbl = QLabel("Adjust the aggression level of the behavioral analysis engine.")
        sub_lbl.setFont(QFont("Segoe UI", 10))
        sub_lbl.setStyleSheet(f"color: {TEXT_SECONDARY};")
        s1_layout.addWidget(sub_lbl)

        # Slider card
        slider_card_inner = QWidget()
        slider_inner_layout = QVBoxLayout(slider_card_inner)
        slider_inner_layout.setContentsMargins(0, 0, 0, 0)
        slider_inner_layout.setSpacing(10)

        # Threshold row
        thresh_row = QWidget()
        thresh_layout = QHBoxLayout(thresh_row)
        thresh_layout.setContentsMargins(0, 0, 0, 0)
        thresh_layout.setSpacing(0)

        thresh_title = QLabel("Detection Threshold")
        thresh_title.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        thresh_title.setStyleSheet(f"color: {TEXT_PRIMARY};")

        thresh_value = QLabel("Balanced (Recommended)")
        thresh_value.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        thresh_value.setStyleSheet(f"color: {CYAN};")

        thresh_layout.addWidget(thresh_title)
        thresh_layout.addStretch()
        thresh_layout.addWidget(thresh_value)

        slider_inner_layout.addWidget(thresh_row)

        # The slider itself
        self._slider = CyanSlider()
        slider_inner_layout.addWidget(self._slider)

        # Labels row
        labels_row = QWidget()
        labels_layout = QHBoxLayout(labels_row)
        labels_layout.setContentsMargins(0, 0, 0, 0)
        lbl_low = QLabel("Low False Positives")
        lbl_low.setFont(QFont("Segoe UI", 9))
        lbl_low.setStyleSheet(f"color: {TEXT_MUTED};")
        lbl_high = QLabel("Maximum Protection")
        lbl_high.setFont(QFont("Segoe UI", 9))
        lbl_high.setStyleSheet(f"color: {TEXT_MUTED};")
        labels_layout.addWidget(lbl_low)
        labels_layout.addStretch()
        labels_layout.addWidget(lbl_high)
        slider_inner_layout.addWidget(labels_row)

        slider_card = make_card(slider_card_inner, padding=(20, 20, 20, 20))
        s1_layout.addWidget(slider_card)

        inner_layout.addWidget(section1)

        # Horizontal separator
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setFixedHeight(1)
        sep.setStyleSheet(f"background: {BORDER_COLOR}; border: none;")
        inner_layout.addWidget(sep)

        # ── Section 2: Automated Response ─────────────────────────────────────
        section2 = QWidget()
        s2_layout = QVBoxLayout(section2)
        s2_layout.setContentsMargins(0, 0, 0, 0)
        s2_layout.setSpacing(16)

        s2_header = make_section_header("🔒", "#ef4444", "Automated Response")
        s2_layout.addWidget(s2_header)

        # ── Active Defense Engine card ─────────────────────────────────────────
        ade_card_inner = QWidget()
        ade_layout = QVBoxLayout(ade_card_inner)
        ade_layout.setContentsMargins(0, 0, 0, 0)
        ade_layout.setSpacing(0)

        # Main toggle row
        ade_row, self._ade_toggle = make_toggle_row(
            title="Active Defense Engine",
            subtitle="Automatically take action when critical threats are detected",
            checked=True,
            indent=False
        )
        ade_layout.addWidget(ade_row)

        # Sub-items
        divider1 = make_divider()
        ade_layout.addWidget(divider1)

        ksp_row, self._ksp_toggle = make_toggle_row(
            title="Kill Suspicious Processes",
            checked=True,
            icon="〜",
            indent=True
        )
        ade_layout.addWidget(ksp_row)

        divider2 = make_divider()
        ade_layout.addWidget(divider2)

        ich_row, self._ich_toggle = make_toggle_row(
            title="Isolate Compromised Hosts",
            checked=False,
            icon="⊟",
            indent=True,
            warning="Warning: Disconnects network"
        )
        ade_layout.addWidget(ich_row)

        ade_card = make_card(ade_card_inner, padding=(0, 0, 0, 0))
        s2_layout.addWidget(ade_card)

        inner_layout.addWidget(section2)
        inner_layout.addStretch()

        scroll.setWidget(inner)
        outer.addWidget(scroll)


# ─── Top Header Bar ────────────────────────────────────────────────────────────
class TopHeader(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(70)
        self.setObjectName("topHeader")
        self.setStyleSheet(f"""
            QWidget#topHeader {{
                background: {BG_HEADER};
                border-bottom: 1px solid {BORDER_COLOR};
            }}
        """)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(28, 0, 28, 0)
        layout.setSpacing(14)

        # Gear icon + titles
        gear = QLabel("⚙")
        gear.setFont(QFont("Segoe UI", 22))
        gear.setStyleSheet(f"color: {TEXT_PRIMARY};")

        titles = QVBoxLayout()
        titles.setSpacing(1)
        title_lbl = QLabel("System Configuration")
        title_lbl.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        title_lbl.setStyleSheet(f"color: {TEXT_PRIMARY};")
        sub_lbl = QLabel("Manage security policies, users, and system preferences")
        sub_lbl.setFont(QFont("Segoe UI", 9))
        sub_lbl.setStyleSheet(f"color: {TEXT_SECONDARY};")
        titles.addWidget(title_lbl)
        titles.addWidget(sub_lbl)

        layout.addWidget(gear)
        layout.addLayout(titles)
        layout.addStretch()

        # Reset button
        reset_btn = QPushButton("↺  Reset Defaults")
        reset_btn.setFont(QFont("Segoe UI", 10))
        reset_btn.setFixedHeight(36)
        reset_btn.setStyleSheet(f"""
            QPushButton {{
                color: {TEXT_SECONDARY};
                background: transparent;
                border: none;
                padding: 0 12px;
            }}
            QPushButton:hover {{
                color: {TEXT_PRIMARY};
            }}
        """)
        reset_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))

        # Save button
        save_btn = QPushButton("💾  Save Changes")
        save_btn.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        save_btn.setFixedHeight(36)
        save_btn.setStyleSheet(f"""
            QPushButton {{
                color: #0d1117;
                background: {CYAN};
                border: none;
                border-radius: 8px;
                padding: 0 18px;
            }}
            QPushButton:hover {{
                background: {CYAN_DARK};
            }}
            QPushButton:pressed {{
                background: #178fa5;
            }}
        """)
        save_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))

        layout.addWidget(reset_btn)
        layout.addWidget(save_btn)


# ─── Main Window ──────────────────────────────────────────────────────────────
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("System Configuration")
        self.setMinimumSize(900, 620)
        self.resize(1100, 720)

        # Global stylesheet
        self.setStyleSheet(f"""
            QMainWindow {{
                background: {BG_BASE};
            }}
            QWidget {{
                font-family: "Segoe UI", "SF Pro Display", "Helvetica Neue", sans-serif;
                background: transparent;
            }}
        """)

        # Root widget
        root = QWidget()
        root.setObjectName("root")
        root.setStyleSheet(f"QWidget#root {{ background: {BG_BASE}; }}")
        self.setCentralWidget(root)

        root_layout = QVBoxLayout(root)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        # Top header
        header = TopHeader()
        root_layout.addWidget(header)

        # Body: sidebar + content
        body = QWidget()
        body.setStyleSheet(f"background: {BG_BASE};")
        body_layout = QHBoxLayout(body)
        body_layout.setContentsMargins(24, 24, 24, 24)
        body_layout.setSpacing(20)

        sidebar = LeftSidebar()
        body_layout.addWidget(sidebar)

        content = ContentPanel()
        body_layout.addWidget(content, stretch=1)

        root_layout.addWidget(body, stretch=1)


# ─── Entry Point ──────────────────────────────────────────────────────────────
if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")

    # Force dark palette
    palette = QPalette()
    palette.setColor(QPalette.ColorRole.Window,          QColor(BG_BASE))
    palette.setColor(QPalette.ColorRole.WindowText,      QColor(TEXT_PRIMARY))
    palette.setColor(QPalette.ColorRole.Base,            QColor(BG_CARD))
    palette.setColor(QPalette.ColorRole.AlternateBase,   QColor(BG_SIDEBAR))
    palette.setColor(QPalette.ColorRole.Text,            QColor(TEXT_PRIMARY))
    palette.setColor(QPalette.ColorRole.Button,          QColor(BG_CARD))
    palette.setColor(QPalette.ColorRole.ButtonText,      QColor(TEXT_PRIMARY))
    palette.setColor(QPalette.ColorRole.Highlight,       QColor(CYAN))
    palette.setColor(QPalette.ColorRole.HighlightedText, QColor("#0d1117"))
    app.setPalette(palette)

    window = MainWindow()
    window.show()
    sys.exit(app.exec())
