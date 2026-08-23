#severity_dropdown.py including ransomwarepage 
# frontend / severity_dropdown.py

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton, QApplication
from PyQt6.QtCore import Qt, pyqtSignal, QPoint
from PyQt6.QtGui import QCursor, QPainter, QColor, QPen, QBrush, QPainterPath

BG_CARD = "#131929"
BG_SEL   = "#1a2e40"
BORDER   = "#1e2d45"
CYAN     = "#00bcd4"
TEXT_WHITE = "#e8eaf0"
TEXT_MUTED = "#4a5a78"

SEVERITIES = ["All Severities", "Critical", "High", "Medium", "Low"]

class SeverityDropdown(QWidget):
    """Floating dropdown panel - parented to top-level window so it overlays everything."""

    selectionChanged = pyqtSignal(str)  #emits chosen severity
    def __init__(self, anchor:QPushButton, parent: QWidget):
        super().__init__(parent, Qt.WindowType.Popup)
        self._anchor = anchor
        self._current = "All Severities"
        self.setFixedWidth(200)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setStyleSheet("background: transparent;")

        layout=QVBoxLayout(self)
        layout.setContentsMargins(0,0,0,0)
        layout.setSpacing(0)

        self._inner = QWidget()
        self._inner.setStyleSheet(
            f"QWidget#{self._inner.objectName()}{{}}"   # let items control own bg
        )
        self._inner.setObjectName("dropdown_inner")
        inner_layout = QVBoxLayout(self._inner)
        inner_layout.setContentsMargins(0, 6, 0, 6)
        inner_layout.setSpacing(0)
 
        self._buttons: list[QPushButton] = []
        for sev in SEVERITIES:
            btn = QPushButton(sev)
            btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
            btn.setFixedHeight(36)
            self._style_item(btn, selected=(sev == self._current))
            btn.clicked.connect(lambda _, s=sev: self._pick(s))
            inner_layout.addWidget(btn)
            self._buttons.append(btn)
 
        layout.addWidget(self._inner)
 
    # ── paint the rounded card border ────────────────────────────────────────
    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        path = QPainterPath()
        path.addRoundedRect(0, 0, self.width(), self.height(), 10, 10)
        p.fillPath(path, QBrush(QColor(BG_CARD)))
        p.setPen(QPen(QColor(BORDER), 1))
        p.drawPath(path)
        p.end()
 
    # ── helpers ───────────────────────────────────────────────────────────────
    def _style_item(self, btn: QPushButton, selected: bool):
        bg   = BG_SEL  if selected else "transparent"
        col  = CYAN    if selected else TEXT_WHITE
        btn.setStyleSheet(
            f"QPushButton{{"
            f"  background:{bg}; border:none; color:{col};"
            f"  text-align:left; padding:0 18px;"
            f"  font-size:13px; font-weight:{'700' if selected else '400'};"
            f"}}"
            f"QPushButton:hover{{"
            f"  background:{BG_SEL}; color:{CYAN};"
            f"}}"
        )
 
    def _pick(self, severity: str):
        self._current = severity
        for btn in self._buttons:
            self._style_item(btn, selected=(btn.text() == severity))
        self.selectionChanged.emit(severity)
        self.hide()
 
    def current(self) -> str:
        return self._current
 
    # ── position just below the anchor button ─────────────────────────────────
    def show_below(self):
        anchor_global = self._anchor.mapToGlobal(
            QPoint(0, self._anchor.height() + 4)
        )
        parent_local  = self.parent().mapFromGlobal(anchor_global)
        self.move(parent_local)
        self.adjustSize()
        self.show()
        self.raise_()
