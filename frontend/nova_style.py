# nova_style.py
"""
Shared colours, card builders and data helpers for all NOVASPHERE pages.
Import this in every page file.
"""

import os
import re
import json
from pathlib import Path
from datetime import datetime

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QScrollArea
)
from PyQt6.QtCore import Qt

# ── Colours ───────────────────────────────────────────────────────────────────
BG_MAIN    = "#0b0f1a"
BG_CARD    = "#131929"
BG_CARD2   = "#161e30"
BG_ROW     = "#0f1520"
CYAN       = "#00bcd4"
CYAN_DIM   = "#007a8a"
BORDER     = "#1e2d45"
TEXT_WHITE = "#e8eaf0"
TEXT_MUTED = "#4a5a78"
TEXT_SUB   = "#6b7a99"
RED        = "#ff4757"
ORANGE     = "#ffa726"
GREEN      = "#26de81"
YELLOW     = "#fed330"
BLUE       = "#4fc3f7"

# ── Paths ─────────────────────────────────────────────────────────────────────
BASE_DIR        = Path(__file__).parent
LOG_FILE        = BASE_DIR / "logs" / "novasphere.log"
QUARANTINE_DIR  = BASE_DIR / "quarantine"
MONITOR_DIR     = BASE_DIR / "test_folder"


# ── Badge helper ──────────────────────────────────────────────────────────────
_SEV_COLOURS = {
    "CRITICAL": (RED,    "#1a0a0a"),
    "HIGH":     (ORANGE, "#1a100a"),
    "MEDIUM":   (CYAN,   "#0a1418"),
    "LOW":      (TEXT_SUB, BG_CARD2),
}

def badge(text: str, colour: str = CYAN) -> QLabel:
    lbl = QLabel(text)
    lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
    lbl.setStyleSheet(
        f"color:{colour};background:transparent;"
        f"border:1px solid {colour};border-radius:6px;"
        f"padding:2px 8px;font-size:11px;font-weight:600;"
    )
    return lbl


def severity_badge(sev: str) -> QLabel:
    fg, _ = _SEV_COLOURS.get(sev.upper(), (TEXT_SUB, BG_CARD2))
    return badge(sev.upper(), fg)


# ── Card builder ──────────────────────────────────────────────────────────────
def make_card(title: str = "", sub: str = "") -> tuple[QFrame, QVBoxLayout]:
    """Returns (frame, inner_layout). Use inner_layout to add content."""
    frame = QFrame()
    frame.setStyleSheet(
        f"QFrame{{background:{BG_CARD};border:1px solid {BORDER};"
        f"border-radius:16px;}}"
    )
    lay = QVBoxLayout(frame)
    lay.setContentsMargins(18, 16, 18, 16)
    lay.setSpacing(10)
    if title:
        t = QLabel(title)
        t.setStyleSheet(
            f"color:{TEXT_WHITE};font-size:15px;font-weight:700;"
            f"background:transparent;border:none;"
        )
        lay.addWidget(t)
    if sub:
        s = QLabel(sub)
        s.setStyleSheet(
            f"color:{TEXT_MUTED};font-size:11px;"
            f"background:transparent;border:none;"
        )
        lay.addWidget(s)
    return frame, lay


def stat_card(value: str, label: str, colour: str = CYAN) -> QFrame:
    frame = QFrame()
    frame.setStyleSheet(
        f"QFrame{{background:{BG_CARD};border:1px solid {BORDER};"
        f"border-radius:16px;}}"
    )
    lay = QVBoxLayout(frame)
    lay.setContentsMargins(18, 14, 18, 14)
    lay.setSpacing(4)
    v = QLabel(value)
    v.setStyleSheet(
        f"color:{colour};font-size:28px;font-weight:300;"
        f"background:transparent;border:none;"
    )
    l = QLabel(label.upper())
    l.setStyleSheet(
        f"color:{TEXT_MUTED};font-size:10px;letter-spacing:1px;"
        f"background:transparent;border:none;"
    )
    lay.addWidget(v)
    lay.addWidget(l)
    return frame


def divider() -> QFrame:
    line = QFrame()
    line.setFixedHeight(1)
    line.setStyleSheet(f"background:{BORDER};border:none;")
    return line


def scroll_page(content_widget: QWidget) -> QScrollArea:
    """Wrap a widget in a scroll area matching the app style."""
    sa = QScrollArea()
    sa.setWidgetResizable(True)
    sa.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
    sa.setStyleSheet("QScrollArea{border:none;background:transparent;}")
    sa.setWidget(content_widget)
    return sa


# ── Data helpers ──────────────────────────────────────────────────────────────
def load_log_lines(limit: int = 200) -> list[str]:
    if not LOG_FILE.exists():
        return []
    try:
        lines = LOG_FILE.read_text(encoding="utf-8").splitlines()
        return [l for l in lines if l.strip()][-limit:]
    except Exception:
        return []


def parse_log_alerts(lines: list[str]) -> list[dict]:
    """Turn log lines into structured alert dicts."""
    alerts = []
    aid = 1
    patterns = {
        "CRITICAL": re.compile(r"HONEYPOT TRIGGERED"),
        "HIGH":     re.compile(r"HIGH RISK DETECTED.*Score:\s*([\d.]+).*File:\s*(.+)"),
        "MEDIUM":   re.compile(r"MEDIUM RISK.*?([\w._-]+)\s*\|.*Score:\s*([\d.]+)"),
        "SCORE":    re.compile(r"\[SCORE\]\s*([\w._-]+)\s*\|\s*\+(\d+)\s*pts\s*\(([^)]+)\)"),
    }
    for line in reversed(lines):
        ts_m = re.match(r"\[(\d{2}:\d{2}:\d{2})\]", line)
        ts = ts_m.group(1) if ts_m else "--:--:--"

        if patterns["CRITICAL"].search(line):
            fm = re.search(r"File:\s*(.+)", line)
            alerts.append({"id": f"ALT-{aid:04d}", "severity": "CRITICAL",
                            "type": "Honeypot Triggered",
                            "file": Path(fm.group(1)).name if fm else "Unknown",
                            "rule": "HONEYPOT", "score": 100,
                            "timestamp": ts, "status": "Open"})
            aid += 1
        elif m := patterns["HIGH"].search(line):
            alerts.append({"id": f"ALT-{aid:04d}", "severity": "HIGH",
                            "type": "Ransomware",
                            "file": Path(m.group(2).strip()).name,
                            "rule": "HIGH_RISK", "score": float(m.group(1)),
                            "timestamp": ts, "status": "Open"})
            aid += 1
        elif m := patterns["MEDIUM"].search(line):
            alerts.append({"id": f"ALT-{aid:04d}", "severity": "MEDIUM",
                            "type": "Suspicious Activity",
                            "file": m.group(1), "rule": "MEDIUM_RISK",
                            "score": float(m.group(2)),
                            "timestamp": ts, "status": "Investigating"})
            aid += 1
    return alerts


def load_quarantine_files() -> list[dict]:
    if not QUARANTINE_DIR.exists():
        return []
    files = []
    for f in sorted(QUARANTINE_DIR.iterdir()):
        if f.is_file():
            st = f.stat()
            files.append({
                "name": f.name,
                "size": st.st_size,
                "modified": datetime.fromtimestamp(st.st_mtime)
                                   .strftime("%Y-%m-%d %H:%M:%S"),
            })
    return files


def try_import_detector():
    """Try to import live detector state. Returns path_scores dict or {}."""
    try:
        import sys
        sys.path.insert(0, str(BASE_DIR))
        from ransomware_part.detector import path_scores
        return dict(path_scores)
    except Exception:
        return {}


def try_import_honeypots():
    """Try to import honeypot manager. Returns list of dicts."""
    try:
        import sys
        sys.path.insert(0, str(BASE_DIR))
        from ransomware_part.honeypot import HoneypotManager
        hm = HoneypotManager()
        return [{"name": Path(p).name, "path": str(p),
                 "intact": Path(p).exists()} for p in hm.honeypot_files]
    except Exception:
        return []
