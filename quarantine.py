# NOVASPHERE — Quarantine Management Page
# frontend / qurantine.py

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QFrame, QScrollArea, QMessageBox
)
from PyQt6.QtCore import Qt, QTimer, QSize
from PyQt6.QtGui import QColor, QPainter, QPen, QBrush
from ransomware_part.config import QUARANTINE_FOLDER, BACKUP_FOLDER, MONITOR_PATH

from nova_style import (
    BG_MAIN, BG_CARD, BG_CARD2, BG_ROW, CYAN, CYAN_DIM,
    BORDER, TEXT_WHITE, TEXT_MUTED, TEXT_SUB,
    RED, ORANGE, GREEN, YELLOW, BLUE
)

# ── Custom shield widget ──────────────────────────────────────────────────────
class ShieldWidget(QWidget):
    """Draws a filled shield that is green when secure, red when threats exist."""

    def __init__(self, secure=True, parent=None):
        super().__init__(parent)
        self._secure = secure
        self.setFixedSize(QSize(72, 82))
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

    def set_secure(self, secure: bool):
        if self._secure != secure:
            self._secure = secure
            self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)

        color = QColor("#2ecc71") if self._secure else QColor("#ff5252")
        glow  = QColor("#1a5c38" if self._secure else "#5c1a1a")

        w, h = self.width(), self.height()

        # Glow background circle
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QBrush(glow))
        p.drawEllipse(w//2 - 36, h//2 - 36, 72, 72)

        # Shield path
        pen = QPen(color, 3)
        pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
        p.setPen(pen)
        p.setBrush(QBrush(QColor(0, 0, 0, 0)))

        cx = w // 2
        # Shield outline points
        from PyQt6.QtGui import QPainterPath
        path = QPainterPath()
        path.moveTo(cx, 8)
        path.lineTo(cx + 28, 20)
        path.lineTo(cx + 28, 44)
        path.quadTo(cx + 28, 66, cx, 74)
        path.quadTo(cx - 28, 66, cx - 28, 44)
        path.lineTo(cx - 28, 20)
        path.closeSubpath()

        p.setBrush(QBrush(QColor(color.red(), color.green(), color.blue(), 40)))
        p.drawPath(path)

        # Checkmark (secure) or X (threat)
        p.setPen(QPen(color, 3, Qt.PenStyle.SolidLine,
                      Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin))
        if self._secure:
            p.drawLine(cx - 10, 42, cx - 2, 52)
            p.drawLine(cx - 2,  52, cx + 14, 34)
        else:
            p.drawLine(cx - 10, 34, cx + 10, 54)
            p.drawLine(cx + 10, 34, cx - 10, 54)

        p.end()


# ── Quarantine page ───────────────────────────────────────────────────────────
class QuarantinePage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._build()
        self._poll_timer = QTimer(self)
        self._poll_timer.timeout.connect(self.reload)
        self._poll_timer.start(3000)

    #  Layout 

    def _build(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(32, 28, 32, 32)
        outer.setSpacing(0)
        outer.setAlignment(Qt.AlignmentFlag.AlignTop)

        title = QLabel("Quarantine Management")
        title.setStyleSheet(
            f"color:{TEXT_WHITE};font-size:20px;font-weight:700;background:transparent;"
        )
        sub = QLabel("Isolated files blocked due to ransomware or suspicious behavior")
        sub.setStyleSheet(f"color:{TEXT_MUTED};font-size:15px;background:transparent;")

        outer.addWidget(title)
        outer.addSpacing(4)
        outer.addWidget(sub)
        outer.addSpacing(22)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setStyleSheet("border:none;background:transparent;")

        self._content = QWidget()
        self._content.setStyleSheet("background:transparent;")
        self._content_layout = QVBoxLayout(self._content)
        self._content_layout.setContentsMargins(0, 0, 0, 0)
        self._content_layout.setSpacing(10)
        self._content_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        scroll.setWidget(self._content)
        outer.addWidget(scroll, 1)

        self.reload()

    #  Data 

    def _load_files(self):
        """Return list of dicts for each file in the quarantine folder."""
        entries = []
        if not os.path.isdir(QUARANTINE_FOLDER):
            return entries
        for fname in sorted(os.listdir(QUARANTINE_FOLDER), reverse=True):
            fpath = os.path.join(QUARANTINE_FOLDER, fname)
            if not os.path.isfile(fpath):
                continue
            stat = os.stat(fpath)
            # Filename format from prevention.py: YYYYMMDD_HHMMSS_originalname
            parts = fname.split("_", 2)
            if len(parts) == 3:
                try:
                    ts = datetime.strptime(f"{parts[0]}_{parts[1]}", "%Y%m%d_%H%M%S")
                    original = parts[2]
                except ValueError:
                    ts = datetime.fromtimestamp(stat.st_mtime)
                    original = fname
            else:
                ts = datetime.fromtimestamp(stat.st_mtime)
                original = fname

            entries.append({
                "display_name": original,
                "quarantine_path": fpath,
                "timestamp": ts,
                "size": stat.st_size,
            })
        return entries

    #  Refresh

    def reload(self):
        while self._content_layout.count():
            item = self._content_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        entries = self._load_files()
        secure  = len(entries) == 0

        if secure:
            self._content_layout.addWidget(self._empty_state())
        else:
            self._content_layout.addWidget(self._summary_row(len(entries)))
            self._content_layout.addSpacing(8)
            for entry in entries:
                self._content_layout.addWidget(self._entry_row(entry))
            self._content_layout.addStretch()

    # ── Empty / secure state ──────────────────────────────────────────────────
    def _empty_state(self):
        card = QFrame()
        card.setStyleSheet(
            f"background:{BG_CARD};border:1px;border-radius:20px;"
        )
        card.setMinimumHeight(300)

        lay = QVBoxLayout(card)
        lay.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lay.setSpacing(14)

        shield = ShieldWidget(secure=True)
        shield_wrap = QHBoxLayout()
        shield_wrap.setAlignment(Qt.AlignmentFlag.AlignCenter)
        shield_wrap.addWidget(shield)

        msg = QLabel("No files currently in quarantine.")
        msg.setAlignment(Qt.AlignmentFlag.AlignCenter)
        msg.setStyleSheet(
            f"color:{TEXT_WHITE};font-size:22px;font-weight:700;background:transparent;"
        )
        hint = QLabel("System is secure.")
        hint.setAlignment(Qt.AlignmentFlag.AlignCenter)
        hint.setStyleSheet(
            f"color:{TEXT_MUTED};font-size:15px;background:transparent;"
        )

        lay.addLayout(shield_wrap)
        lay.addWidget(msg)
        lay.addWidget(hint)
        return card

    #  Threat state — summary row 

    def _summary_row(self, count):
        row = QWidget()
        row.setStyleSheet("background:transparent;")
        lay = QHBoxLayout(row)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(14)

        shield = ShieldWidget(secure=False)
        shield.setFixedSize(QSize(36, 42))   # smaller inline version
        lay.addWidget(shield)

        lbl = QLabel(f"{count} file{'s' if count != 1 else ''} in quarantine")
        lbl.setStyleSheet(
            f"color:#ff5252;font-size:15px;font-weight:700;background:transparent;"
        )
        lay.addWidget(lbl)
        lay.addStretch()

        clear_btn = QPushButton("Clear All")
        clear_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        clear_btn.setStyleSheet(
            "background:transparent;border:1px solid #ff5252;color:#ff5252;"
            "border-radius:8px;padding:6px 18px;font-size:13px;font-weight:600;"
        )
        clear_btn.clicked.connect(self._clear_all)
        lay.addWidget(clear_btn)
        return row

    #  Single file row 

    def _entry_row(self, entry):
        card = QFrame()
        card.setStyleSheet(
            f"background:{BG_CARD};border:1px;border-radius:12px;"
        )

        lay = QHBoxLayout(card)
        lay.setContentsMargins(20, 14, 20, 14)
        lay.setSpacing(16)

        icon = QLabel("󰂺")
        icon.setFixedWidth(28)
        icon.setStyleSheet("font-size:20px;background:transparent;")
        lay.addWidget(icon)

        info = QVBoxLayout()
        info.setSpacing(2)
        fname = QLabel(entry["display_name"])
        fname.setStyleSheet(
            f"color:{TEXT_WHITE};font-size:14px;font-weight:600;background:transparent;"
        )
        fpath = QLabel(entry["quarantine_path"])
        fpath.setStyleSheet(
            f"color:{TEXT_MUTED};font-size:11px;background:transparent;"
        )
        fpath.setWordWrap(True)
        info.addWidget(fname)
        info.addWidget(fpath)
        lay.addLayout(info, 1)

        # File size
        size_lbl = QLabel(self._fmt_size(entry["size"]))
        size_lbl.setStyleSheet(
            f"color:{TEXT_SUB};font-size:11px;background:transparent;min-width:60px;"
        )
        size_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lay.addWidget(size_lbl)

        # Timestamp
        ts_lbl = QLabel(entry["timestamp"].strftime("%Y-%m-%d  %H:%M"))
        ts_lbl.setStyleSheet(
            f"color:{TEXT_SUB};font-size:11px;background:transparent;min-width:120px;"
        )
        ts_lbl.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        lay.addWidget(ts_lbl)

        # Quarantined badge
        badge = QLabel("QUARANTINED")
        badge.setStyleSheet(
            "background:#1a0a0a;color:#ff5252;border:1px solid #ff5252;"
            "border-radius:6px;padding:3px 10px;font-size:10px;font-weight:700;"
            "letter-spacing:1px;"
        )
        lay.addWidget(badge)

        # Restore button

        restore_btn = QPushButton("Restore")
        restore_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        restore_btn.setStyleSheet(
            f"background:transparent;border:1px;color:{TEXT_MUTED};"
            "border-radius:7px;padding:5px 14px;font-size:12px;"
        )
        restore_btn.clicked.connect(lambda _, e=entry: self._restore(e))
        lay.addWidget(restore_btn)

        return card

    #  Actions 

    def _clear_all(self):
        count = len(self._load_files())
        msg = QMessageBox(self)
        msg.setWindowTitle("Confirm Delete")
        msg.setText(
            f"Are you sure? This permenently delete {count}"
            f"quarantined file{'s' if count != 1 else ''}.\n\n"
            f"This action cannot be undone."
        )
        msg.setStandardButtons(
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.Cancel
        )
        msg.setDefaultButton(QMessageBox.StandardButton.Cancel)
        msg.setStyleSheet(
            f"QWidget{{background:{BG_CARD}; color:{TEXT_WHITE}; }}"
            f"QPushButton{{background:{BORDER}; border:none; color:{TEXT_WHITE};"
            f"border-radius:6px; padding: 6px 16px;}}"
        )
        if msg.exec() != QMessageBox.StandardButton.Yes:
            return
        if not os.path.isdir(QUARANTINE_FOLDER):
            return
        for fname in os.listdir(QUARANTINE_FOLDER):
            fpath = os.path.join(QUARANTINE_FOLDER, fname)
            if os.path.isfile(fpath):
                try:
                    os.remove(fpath)
                except OSError:
                    pass
        self.reload()

    def _restore(self, entry: dict):
        """Restore file to original monitored location, stripping the timestamp prefix."""
        from ransomware_part.config import MONITOR_PATH

        src = entry["quarantine_path"]
        if not os.path.basename(src):
            self.reload()
            return
        
        fname = os.path.basename(src)
        parts=fname.split("_", 2)
        original_name = parts[2] if len(parts) == 3 else fname

        dest = os.path.join(MONITOR_PATH, original_name)

        if os.path.exists(dest):
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.warning(
                self,
                "Restore Failed",
                f"File already exists at destination: \n{dest}\n\nRename or remove it first.",
            )
            return
        try:
            import shutil
            shutil.move(src, dest)
            print(f"󰄬 Restored: {original_name} -> {dest}")
        except OSError as e:
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.critical(self, "Restore Error", str(e))
        
        self.reload()

    # ── Helpers ───────────────────────────────────────────────────────────────
    def _fmt_size(self, size_bytes):
        if size_bytes < 1024:
            return f"{size_bytes} B"
        elif size_bytes < 1024 ** 2:
            return f"{size_bytes/1024:.1f} KB"
        else:
            return f"{size_bytes/1024**2:.1f} MB"