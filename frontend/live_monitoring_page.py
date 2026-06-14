# live_monitoring_page.py
"""
NOVASPHERE — Live Monitoring Page
Shows real-time file activity and risk scores from detector.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QPainter, QPen, QColor, QBrush, QFont

from nova_style import (
    BG_CARD, BG_CARD2, BG_ROW, CYAN, BORDER,
    TEXT_WHITE, TEXT_MUTED, TEXT_SUB, RED, ORANGE, GREEN,
    badge, make_card, stat_card, scroll_page,
    load_log_lines, try_import_detector
)


class ScoreBar(QWidget):
    """Horizontal risk score progress bar."""

    def __init__(self, score: float, parent=None):
        super().__init__(parent)
        self._score = score
        self.setFixedHeight(8)
        self.setMinimumWidth(100)
        self.setStyleSheet("background:transparent;")

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h = self.width(), self.height()
        pct = min(self._score / 100.0, 1.0)
        col = QColor(RED) if self._score >= 80 else \
              QColor(ORANGE) if self._score >= 50 else QColor(CYAN)
        p.setBrush(QBrush(QColor(BORDER)))
        p.setPen(Qt.PenStyle.NoPen)
        p.drawRoundedRect(0, 0, w, h, 4, 4)
        p.setBrush(QBrush(col))
        p.drawRoundedRect(0, 0, int(w * pct), h, 4, 4)


def _score_row(filename: str, score: float) -> QFrame:
    row = QFrame()
    row.setStyleSheet(
        f"QFrame{{background:{BG_ROW};border:none;"
        f"border-bottom:1px solid {BORDER};}}"
        f"QFrame:hover{{background:#111827;}}"
    )
    lay = QHBoxLayout(row)
    lay.setContentsMargins(14, 10, 14, 10)
    lay.setSpacing(12)

    name = QLabel(filename)
    name.setStyleSheet(
        f"color:{TEXT_WHITE};font-size:12px;"
        f"font-family:Consolas,monospace;background:transparent;border:none;"
    )
    lay.addWidget(name, 1)

    bar_col = QVBoxLayout(); bar_col.setSpacing(2)
    score_top = QHBoxLayout()
    s_lbl = QLabel("Risk Score")
    s_lbl.setStyleSheet(
        f"color:{TEXT_MUTED};font-size:10px;background:transparent;border:none;"
    )
    score_col = RED if score >= 80 else ORANGE if score >= 50 else CYAN
    s_val = QLabel(str(int(score)))
    s_val.setStyleSheet(
        f"color:{score_col};font-size:11px;font-weight:700;"
        f"font-family:Consolas;background:transparent;border:none;"
    )
    score_top.addWidget(s_lbl); score_top.addStretch(); score_top.addWidget(s_val)
    bar_col.addLayout(score_top)
    bar_col.addWidget(ScoreBar(score))
    bar_w = QWidget(); bar_w.setLayout(bar_col); bar_w.setFixedWidth(160)
    lay.addWidget(bar_w)

    sev = "HIGH" if score >= 80 else "MEDIUM" if score >= 50 else "LOW"
    sev_col = RED if sev == "HIGH" else ORANGE if sev == "MEDIUM" else TEXT_SUB
    sev_badge = badge(sev, sev_col)
    sev_badge.setFixedWidth(70)
    lay.addWidget(sev_badge)
    return row


def _log_row(line: str) -> QFrame:
    row = QFrame()
    row.setStyleSheet(
        f"QFrame{{background:transparent;border:none;"
        f"border-bottom:1px solid {BORDER};}}"
    )
    lay = QHBoxLayout(row)
    lay.setContentsMargins(0, 4, 0, 4)

    col = (RED    if any(k in line for k in ["HIGH", "HONEYPOT", "CRITICAL"]) else
           ORANGE if any(k in line for k in ["MEDIUM", "WARN"])               else
           GREEN  if any(k in line for k in ["Rollback", "Reset", "success"]) else
           TEXT_SUB)
    lbl = QLabel(line)
    lbl.setStyleSheet(
        f"color:{col};font-size:11px;font-family:Consolas,monospace;"
        f"background:transparent;border:none;"
    )
    lbl.setWordWrap(True)
    lay.addWidget(lbl)
    return row


class LiveMonitoringPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._build_ui()
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._refresh_data)
        self._timer.start(2000)

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
        t = QLabel("Live Ransomware Monitoring")
        t.setStyleSheet(
            f"color:{TEXT_WHITE};font-size:22px;font-weight:700;background:transparent;"
        )
        s = QLabel("Real-time behavioural threat detection and file activity tracking")
        s.setStyleSheet(f"color:{TEXT_MUTED};font-size:12px;background:transparent;")
        col.addWidget(t); col.addWidget(s)
        hdr.addLayout(col); hdr.addStretch()

        self._status_dot = QLabel("● Monitoring Active")
        self._status_dot.setStyleSheet(
            f"color:{GREEN};font-size:12px;font-weight:600;background:transparent;"
        )
        hdr.addWidget(self._status_dot)
        root.addLayout(hdr)

        # Stat row
        stat_row = QHBoxLayout(); stat_row.setSpacing(12)
        self._stat_high   = stat_card("0", "High Risk Files",   RED)
        self._stat_medium = stat_card("0", "Medium Risk Files", ORANGE)
        self._stat_quar   = stat_card("0", "Quarantined Files", TEXT_SUB)
        self._stat_qfiles = stat_card("0", "Files Modified",    CYAN)
        for s in [self._stat_high, self._stat_medium, self._stat_quar, self._stat_qfiles]:
            stat_row.addWidget(s)
        stat_row.addStretch()
        root.addLayout(stat_row)

        # Two columns: scores left, log right
        cols = QHBoxLayout(); cols.setSpacing(16)

        # Risk scores
        score_frame, score_lay = make_card(
            "Active Risk Scores",
            "Files currently being tracked by the detection engine"
        )
        score_lay.setSpacing(0)
        score_lay.setContentsMargins(0, 8, 0, 0)
        self._score_body = QVBoxLayout()
        self._score_body.setSpacing(0)
        body_w = QWidget(); body_w.setLayout(self._score_body)
        score_lay.addWidget(body_w)
        cols.addWidget(score_frame, 1)

        # Recent log
        log_frame, log_lay = make_card(
            "Live Event Feed",
            "Last 30 log entries"
        )
        log_lay.setSpacing(0)
        log_lay.setContentsMargins(0, 8, 0, 0)
        self._log_body = QVBoxLayout()
        self._log_body.setSpacing(0)
        log_w = QWidget(); log_w.setLayout(self._log_body)
        log_lay.addWidget(log_w)
        cols.addWidget(log_frame, 1)

        root.addLayout(cols)
        root.addStretch()

        outer.addWidget(scroll_page(content))
        self._refresh_data()

    def _refresh_data(self):
        scores = try_import_detector()
        lines  = load_log_lines(30)

        from nova_style import load_quarantine_files
        qfiles = load_quarantine_files()

        high   = sum(1 for v in scores.values() if v >= 80)
        medium = sum(1 for v in scores.values() if 50 <= v < 80)

        self._update_stat(self._stat_high,   str(high),           RED if high else TEXT_SUB)
        self._update_stat(self._stat_medium, str(medium),         ORANGE if medium else TEXT_SUB)
        self._update_stat(self._stat_quar,   str(len(qfiles)),    TEXT_SUB)
        self._update_stat(self._stat_qfiles, str(len(scores)),    CYAN)

        # Rebuild score list
        self._clear(self._score_body)
        if scores:
            for fname, score in sorted(scores.items(), key=lambda x: -x[1]):
                self._score_body.addWidget(
                    _score_row(fname.split("/")[-1].split("\\")[-1], score)
                )
        else:
            empty = QLabel("No active threats")
            empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
            empty.setStyleSheet(
                f"color:{TEXT_MUTED};padding:32px;background:transparent;"
            )
            self._score_body.addWidget(empty)

        # Rebuild log
        self._clear(self._log_body)
        for line in reversed(lines):
            self._log_body.addWidget(_log_row(line))

    def _update_stat(self, card, value, colour):
        labels = card.findChildren(QLabel)
        if labels:
            labels[0].setText(value)
            labels[0].setStyleSheet(
                f"color:{colour};font-size:28px;font-weight:300;"
                f"background:transparent;border:none;"
            )

    def _clear(self, layout):
        while layout.count():
            item = layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

    def reload(self):
        self._refresh_data()
