# deception_page.py
"""
NOVASPHERE — Deception System Page
Shows honeypot bait file status and trigger history.
"""

import math
from pathlib import Path
from datetime import datetime

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QFrame, QSizePolicy
)
from PyQt6.QtCore import Qt, QTimer, QRect
from PyQt6.QtGui import QPainter, QPen, QColor, QFont, QBrush

from nova_style import (
    BG_MAIN, BG_CARD, BG_CARD2, BG_ROW, CYAN, BORDER,
    TEXT_WHITE, TEXT_MUTED, TEXT_SUB, RED, ORANGE, GREEN,
    badge, make_card, stat_card, scroll_page,
    try_import_honeypots, load_log_lines
)


class ActivityGraph(QWidget):
    """Simple bar chart showing honeypot access attempts per hour."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._data = [0] * 24
        self.setMinimumHeight(120)
        self.setStyleSheet("background:transparent;")

    def set_data(self, data: list):
        self._data = data[-24:]
        self.update()

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h = self.width(), self.height()
        pad = 20
        bar_w = max(4, (w - pad * 2) // max(len(self._data), 1) - 2)
        mx = max(self._data) or 1

        for i, v in enumerate(self._data):
            x = pad + i * ((w - pad * 2) // len(self._data))
            bar_h = int((v / mx) * (h - pad * 2))
            col = QColor(RED) if v > 0 else QColor(BORDER)
            p.setBrush(QBrush(col))
            p.setPen(Qt.PenStyle.NoPen)
            p.drawRoundedRect(x, h - pad - bar_h, bar_w, bar_h, 2, 2)

        # x-axis labels every 6 hours
        p.setPen(QPen(QColor(TEXT_MUTED)))
        font = QFont("Segoe UI", 8)
        p.setFont(font)
        for i in range(0, 24, 6):
            x = pad + i * ((w - pad * 2) // 24)
            p.drawText(x - 10, h - 2, f"{i:02d}:00")


def _honeypot_row(hp: dict) -> QFrame:
    row = QFrame()
    intact = hp.get("intact", True)
    bg = BG_ROW if intact else "#1a0a0a"
    row.setStyleSheet(
        f"QFrame{{background:{bg};border:none;"
        f"border-bottom:1px solid {BORDER};}}"
        f"QFrame:hover{{background:#111827;}}"
    )
    lay = QHBoxLayout(row)
    lay.setContentsMargins(14, 12, 14, 12)
    lay.setSpacing(12)

    icon = QLabel("🍯" if intact else "⚠️")
    icon.setStyleSheet("font-size:18px;background:transparent;border:none;")
    icon.setFixedWidth(28)
    lay.addWidget(icon)

    info = QVBoxLayout()
    name = QLabel(hp.get("name", ""))
    name.setStyleSheet(
        f"color:{TEXT_WHITE};font-size:13px;font-weight:600;"
        f"font-family:Consolas,monospace;background:transparent;border:none;"
    )
    path = QLabel(hp.get("path", ""))
    path.setStyleSheet(
        f"color:{TEXT_MUTED};font-size:11px;background:transparent;border:none;"
    )
    info.addWidget(name); info.addWidget(path)
    lay.addLayout(info); lay.addStretch()

    status_text = "Active" if intact else "Triggered / Missing"
    status_col  = GREEN if intact else RED
    lay.addWidget(badge(status_text, status_col))
    return row


class DeceptionPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._honeypots = []
        self._hourly = [0] * 24
        self._build_ui()
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._refresh_data)
        self._timer.start(5000)

    def _build_ui(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)

        content = QWidget()
        root = QVBoxLayout(content)
        root.setContentsMargins(28, 24, 28, 28)
        root.setSpacing(18)
        root.setAlignment(Qt.AlignmentFlag.AlignTop)

        # Header
        hdr = QHBoxLayout()
        col = QVBoxLayout()
        t = QLabel("Deception System")
        t.setStyleSheet(
            f"color:{TEXT_WHITE};font-size:22px;font-weight:700;background:transparent;"
        )
        s = QLabel("Advanced Honeypot and Bait File Management")
        s.setStyleSheet(f"color:{TEXT_MUTED};font-size:12px;background:transparent;")
        col.addWidget(t); col.addWidget(s)
        hdr.addLayout(col); hdr.addStretch()

        defense_badge = QLabel("● Active Defense Enabled")
        defense_badge.setStyleSheet(
            f"color:{GREEN};font-size:12px;font-weight:600;background:transparent;"
        )
        hdr.addWidget(defense_badge)
        root.addLayout(hdr)

        # Stat row
        stat_row = QHBoxLayout(); stat_row.setSpacing(12)
        self._stat_active   = stat_card("0", "Active Bait Files", CYAN)
        self._stat_triggered = stat_card("0", "Traps Triggered", RED)
        self._stat_total    = stat_card("0", "Total Honeypots", TEXT_SUB)
        for s in [self._stat_active, self._stat_triggered, self._stat_total]:
            stat_row.addWidget(s)
        stat_row.addStretch()
        root.addLayout(stat_row)

        # Activity chart
        chart_frame, chart_lay = make_card(
            "Honeypot Activity Levels",
            "Access attempts per hour today"
        )
        self._chart = ActivityGraph()
        chart_lay.addWidget(self._chart)
        root.addWidget(chart_frame)

        # Bait file list
        list_frame, list_lay = make_card(
            "Strategic Bait Files",
            "Any access to these files triggers an immediate CRITICAL alert"
        )
        list_lay.setSpacing(0)
        list_lay.setContentsMargins(0, 8, 0, 0)

        self._list_body = QVBoxLayout()
        self._list_body.setSpacing(0)
        body_w = QWidget(); body_w.setLayout(self._list_body)
        list_lay.addWidget(body_w)
        root.addWidget(list_frame)
        root.addStretch()

        outer.addWidget(scroll_page(content))
        self._refresh_data()

    def _refresh_data(self):
        self._honeypots = try_import_honeypots()

        # Count activity from log
        lines = load_log_lines(500)
        hourly = [0] * 24
        for line in lines:
            if "HONEYPOT" in line:
                import re
                m = re.match(r"\[(\d{2}):", line)
                if m:
                    hourly[int(m.group(1))] += 1

        active    = sum(1 for h in self._honeypots if h.get("intact"))
        triggered = sum(1 for h in self._honeypots if not h.get("intact"))
        total     = len(self._honeypots)

        self._update_stat(self._stat_active,    str(active),    "Active Bait Files",  CYAN)
        self._update_stat(self._stat_triggered, str(triggered), "Traps Triggered",    RED if triggered else GREEN)
        self._update_stat(self._stat_total,     str(total),     "Total Honeypots",    TEXT_SUB)

        self._chart.set_data(hourly)
        self._rebuild_list()

    def _update_stat(self, card, value, label, colour):
        labels = card.findChildren(QLabel)
        if labels:
            labels[0].setText(value)
            labels[0].setStyleSheet(
                f"color:{colour};font-size:28px;font-weight:300;"
                f"background:transparent;border:none;"
            )

    def _rebuild_list(self):
        while self._list_body.count():
            item = self._list_body.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        if not self._honeypots:
            empty = QLabel("No honeypot files configured")
            empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
            empty.setStyleSheet(
                f"color:{TEXT_MUTED};padding:32px;background:transparent;"
            )
            self._list_body.addWidget(empty)
            return

        for hp in self._honeypots:
            self._list_body.addWidget(_honeypot_row(hp))

    def reload(self):
        self._refresh_data()
