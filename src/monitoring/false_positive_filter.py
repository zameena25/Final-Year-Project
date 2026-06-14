#monitoring/false_positive_filter.py

import re
from pathlib import Path

WHITELISTED_EXTENSIONS = {
    ".tmp", ".log", ".bak", '.swp", ".lock", ".pyc", ".pyo", ".pyd", ".cache",'
}

WHITELISTED_PATH_FRAGMENTS = [
    "__pycache__",
    ".git",
    "node_modules",
    "venv",
    ".venv",
    "site-packages",
]

RANSOMWARE_EXTENSIONS = {
    ".locked", ".encrypted", ".enc", ".crypto",
    ".crypted", ".crypt", ".wnry", ".wncry",
    ".locky", ".cerber", ".zepto", ".thor",
    ".pays", ".darkness", ".noob", ".xdata",
}

RANSOMWARE_FILENAME_PATTERNS = [
    re.compile(r"readme.*ransom", re.IGNORECASE),
    re.compile(r"how.to.decrypt", re.IGNORECASE),
    re.compile(r"recover.files", re.IGNORECASE),
    re.compile(r"your.files.are.encrypted", re.IGNORECASE),
    re.compile(r"!+decrypt", re.IGNORECASE),
]

# ──────────────────────────────────────────────
# SCORING WEIGHTS
# ──────────────────────────────────────────────
WEIGHT_RANSOMWARE_EXT      = 5   # high confidence indicator
WEIGHT_RANSOMWARE_FILENAME = 4   # ransom note pattern
WEIGHT_HIGH_FREQUENCY      = 3   # many events in short burst
WEIGHT_BULK_RENAME         = 3   # mass rename activity
WEIGHT_SENSITIVE_PATH      = 2   # targeting Documents/Desktop etc.
THREAT_SCORE_THRESHOLD     = 4   # minimum score to flag as real threat


SENSITIVE_PATH_FRAGMENTS = [
    "documents", "desktop", "downloads",
    "pictures", "onedrive", "dropbox",
]


class FalsePositiveFilter:
    """
    Evaluates a file event and returns whether it is a genuine threat.
    Uses whitelist checks, ransomware signatures, and weighted scoring.
    """

    def __init__(self, high_frequency_threshold: int = 20):
        # ADDED: track recent event counts for frequency scoring
        self.high_frequency_threshold = high_frequency_threshold
        self._event_counts: dict[str, int] = {}   # path → count in window
        self._rename_counts: dict[str, int] = {}  # directory → rename count

    # ──────────────────────────────────────────
    # PUBLIC INTERFACE
    # ──────────────────────────────────────────

    def is_genuine_threat(self, event: dict) -> tuple[bool, int, list[str]]:
        """
        Returns (is_threat, score, reasons).

        event dict keys expected:
            src_path  : str  — full file path
            event_type: str  — 'created' | 'modified' | 'renamed' | 'deleted'
            frequency : int  — number of similar events seen recently (optional)
        """
        src_path = event.get("src_path", "")
        event_type = event.get("event_type", "")
        frequency = event.get("frequency", 0)

        reasons: list[str] = []
        score = 0

        # ── Step 1: whitelist short-circuit ──────────────────────────────
        if self._is_whitelisted(src_path):
            return False, 0, ["whitelisted path or extension"]

        # ── Step 2: ransomware extension check ───────────────────────────
        ext = Path(src_path).suffix.lower()
        if ext in RANSOMWARE_EXTENSIONS:
            score += WEIGHT_RANSOMWARE_EXT
            reasons.append(f"ransomware extension detected: {ext}")

        # ── Step 3: ransomware filename pattern ──────────────────────────
        filename = Path(src_path).name
        for pattern in RANSOMWARE_FILENAME_PATTERNS:
            if pattern.search(filename):
                score += WEIGHT_RANSOMWARE_FILENAME
                reasons.append(f"ransom note filename pattern: {filename}")
                break

        # ── Step 4: high-frequency burst ─────────────────────────────────
        if frequency >= self.high_frequency_threshold:
            score += WEIGHT_HIGH_FREQUENCY
            reasons.append(f"high-frequency burst: {frequency} events")

        # ── Step 5: bulk rename detection ────────────────────────────────
        if event_type == "renamed":
            parent = str(Path(src_path).parent)
            self._rename_counts[parent] = self._rename_counts.get(parent, 0) + 1
            if self._rename_counts[parent] >= 10:
                score += WEIGHT_BULK_RENAME
                reasons.append(f"bulk rename in directory: {parent}")

        # ── Step 6: sensitive path targeting ─────────────────────────────
        lower_path = src_path.lower()
        if any(frag in lower_path for frag in SENSITIVE_PATH_FRAGMENTS):
            score += WEIGHT_SENSITIVE_PATH
            reasons.append("activity in sensitive user directory")

        is_threat = score >= THREAT_SCORE_THRESHOLD
        return is_threat, score, reasons

    def reset_rename_counts(self):
        # ADDED: call this at the start of each monitoring window/interval
        self._rename_counts.clear()

    # ──────────────────────────────────────────
    # PRIVATE HELPERS
    # ──────────────────────────────────────────

    def _is_whitelisted(self, path: str) -> bool:
        """Returns True if the path should be silently ignored."""
        ext = Path(path).suffix.lower()
        if ext in WHITELISTED_EXTENSIONS:
            return True
        for fragment in WHITELISTED_PATH_FRAGMENTS:
            if fragment in path:
                return True
        return False

