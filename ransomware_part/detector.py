# detector.py
"""
NOVASPHERE - Detection Engine with Weighted Scoring System
Scoring is per-file-path to avoid false inflation from unrelated activity.
"""

import time
import psutil
from collections import defaultdict, deque
from config import HIGH_THRESHOLD, MEDIUM_THRESHOLD, WINDOW_SECONDS, SETTINGS, LOG_FILE
import prevention
from honeypot import HoneypotManager
from file_buffer import FileBuffer

# Initialize subsystems
honeypot_mgr = HoneypotManager()
file_buffer   = FileBuffer(buffer_seconds=5)

# Per-path scoring state
path_scores    = defaultdict(float)          # current risk score per file path
event_queues   = defaultdict(lambda: deque(maxlen=200))  # recent events per path
last_seen      = defaultdict(float)          # last event time per path
alerted_paths  = set()                       # paths already actioned (avoid double-trigger)

# Global bulk activity queue (across all paths, for mass-encryption detection)
global_event_queue = deque(maxlen=500)

# ---------------------------------------------------------------------------
# Detection rules — each returns (points, label) or (0, None)
# ---------------------------------------------------------------------------

RANSOMWARE_EXTENSIONS = {
    '.locked', '.encrypted', '.crypt', '.enc', '.ransom',
    '.crypto', '.crypted', '.ryk', '.ryuk', '.wncry',
    '.wannacry', '.cerber', '.zepto', '.locky'
}

SUSPICIOUS_PATTERNS = [
    'readme_to_decrypt', 'how_to_decrypt', 'decrypt_instructions',
    'your_files_are_encrypted', 'recovery_key', 'ransom_note'
]


def _rule_ransomware_extension(path_lower, event_type, dest_path):
    """File has or is renamed to a known ransomware extension."""
    if any(path_lower.endswith(ext) for ext in RANSOMWARE_EXTENSIONS):
        return 60, "RANSOMWARE_EXT"
    if event_type == "moved" and dest_path:
        dest_lower = dest_path.lower()
        if any(dest_lower.endswith(ext) for ext in RANSOMWARE_EXTENSIONS):
            return 70, "RENAME_TO_RANSOMWARE_EXT"
    return 0, None


def _rule_ransom_note(path_lower):
    """File name matches known ransom note patterns."""
    filename = path_lower.split("/")[-1].split("\\")[-1]
    if any(pattern in filename for pattern in SUSPICIOUS_PATTERNS):
        return 80, "RANSOM_NOTE_CREATED"
    return 0, None


def _rule_bulk_activity(path, now):
    """Many files modified in a short window — mass encryption signal."""
    # Count unique file paths changed in last WINDOW_SECONDS
    recent_paths = set()
    for ts, p in global_event_queue:
        if now - ts <= WINDOW_SECONDS:
            recent_paths.add(p)

    count = len(recent_paths)
    if count >= 20:
        return 50, f"BULK_ACTIVITY({count} files)"
    elif count >= 10:
        return 25, f"BULK_ACTIVITY({count} files)"
    return 0, None


def _rule_rapid_repeat(path, now):
    """Same file modified many times rapidly — encryption-in-progress signal."""
    queue = event_queues[path]
    recent = sum(1 for ts, _ in queue if now - ts <= 10)  # last 10 seconds
    if recent >= 5:
        return 35, f"RAPID_REPEAT({recent}x in 10s)"
    return 0, None


def _rule_file_extension_changed(path_lower, event_type, dest_path):
    """Original extension replaced entirely (e.g. .docx → .locked)."""
    if event_type == "moved" and dest_path:
        src_ext  = path_lower.rsplit(".", 1)[-1] if "." in path_lower else ""
        dest_ext = dest_path.lower().rsplit(".", 1)[-1] if "." in dest_path else ""
        if src_ext and dest_ext and src_ext != dest_ext:
            # Only flag if destination ext looks unusual (not a known safe rename)
            safe_renames = {"tmp", "bak", "log", "old"}
            if dest_ext not in safe_renames:
                return 20, f"EXT_CHANGED({src_ext}→{dest_ext})"
    return 0, None


def _rule_deletion_spike(now):
    """High number of delete events — wiping originals after encryption."""
    recent_deletes = sum(
        1 for ts, etype in list(global_event_queue)
        if etype == "deleted" and now - ts <= 30
    )
    if recent_deletes >= 8:
        return 40, f"DELETION_SPIKE({recent_deletes} deletes)"
    return 0, None


# ---------------------------------------------------------------------------
# Score decay — called on every event per path
# ---------------------------------------------------------------------------

DECAY_RATE   = 15   # points removed per decay tick
DECAY_AFTER  = 20   # seconds of inactivity before decay kicks in

def _apply_decay(path, now):
    idle_time = now - last_seen.get(path, now)
    if idle_time >= DECAY_AFTER:
        ticks = int(idle_time / DECAY_AFTER)
        path_scores[path] = max(0.0, path_scores[path] - DECAY_RATE * ticks)


# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

def log_event(message: str):
    timestamp = time.strftime("%H:%M:%S")
    log_message = f"[{timestamp}] {message}"
    print(log_message)
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(log_message + "\n")
    except Exception:
        pass


def reset_scores():
    """Called by the 'reset' console command."""
    path_scores.clear()
    alerted_paths.clear()
    global_event_queue.clear()
    log_event("🔄 All risk scores reset by administrator.")


# ---------------------------------------------------------------------------
# Main event handler
# ---------------------------------------------------------------------------

def process_event(event, event_type: str, dest_path=None):
    if event.is_directory:
        return

    src_path   = event.src_path
    path_lower = src_path.lower()
    now        = time.time()

    # --- HONEYPOT CHECK (highest priority, immediate response) ---
    if honeypot_mgr.is_honeypot(src_path):
        log_event(f"🍯 HONEYPOT TRIGGERED! File: {src_path}")
        log_event("🔥 Immediate response — attack caught before real damage!")

        if SETTINGS.get("auto_kill_process", False):
            prevention.suspend_process(event)

        if SETTINGS.get("auto_quarantine", True):
            prevention.take_action(src_path, "CRITICAL", "HONEYPOT")

        return

    # --- BUFFER FILE for rollback ---
    if event_type in ["modified", "created"]:
        file_buffer.buffer_file(src_path)

    # --- UPDATE EVENT QUEUES ---
    event_queues[src_path].append((now, event_type))
    global_event_queue.append((now, src_path) if event_type != "deleted"
                               else (now, "deleted"))  # track deletes separately
    # Rebuild global queue to store (timestamp, event_type) for deletion spike rule
    # (re-append correctly)
    global_event_queue.pop()
    global_event_queue.append((now, event_type))

    # --- APPLY DECAY before adding new points ---
    _apply_decay(src_path, now)
    last_seen[src_path] = now

    # --- RUN ALL DETECTION RULES ---
    points = 0
    triggered = []

    rules = [
        _rule_ransomware_extension(path_lower, event_type, dest_path),
        _rule_ransom_note(path_lower),
        _rule_bulk_activity(src_path, now),
        _rule_rapid_repeat(src_path, now),
        _rule_file_extension_changed(path_lower, event_type, dest_path),
        _rule_deletion_spike(now),
    ]

    for rule_points, label in rules:
        if rule_points > 0:
            points += rule_points
            triggered.append(label)

    if points > 0:
        path_scores[src_path] += points
        rules_str = ", ".join(triggered)
        log_event(f"[SCORE] {src_path.split('/')[-1]} | +{points} pts "
                  f"({rules_str}) | Total: {path_scores[src_path]:.0f}")

    current_score = path_scores[src_path]

    # --- RESPONSE LEVELS ---
    if current_score >= HIGH_THRESHOLD:
        if src_path not in alerted_paths:
            alerted_paths.add(src_path)
            _respond_high(event, src_path, current_score)

    elif current_score >= MEDIUM_THRESHOLD:
        log_event(f"⚠️  MEDIUM RISK | {src_path.split('/')[-1]} | "
                  f"Score: {current_score:.0f} — monitoring closely")
        file_buffer.buffer_file(src_path)  # ensure buffered for possible rollback


def _respond_high(event, src_path, score):
    """Handle a HIGH risk detection."""
    log_event(f"🚨 HIGH RISK DETECTED | Score: {score:.0f} | File: {src_path}")

    # Attempt rollback first
    if file_buffer.rollback_file(src_path):
        log_event("✅ Rollback successful — file restored to pre-attack state")
    else:
        log_event("ℹ️  No buffer available for rollback")

    if SETTINGS.get("auto_kill_process", False):
        pid = prevention.suspend_process(event)
        if pid:
            log_event(f"🔪 Process suspended/terminated (PID: {pid})")

    if SETTINGS.get("auto_quarantine", True):
        prevention.take_action(src_path, "HIGH")
    else:
        log_event("⚠️  Auto Quarantine OFF — manual review required")

    file_buffer.clear_buffer(src_path)
    path_scores[src_path] = 0

    log_event("📧 ALERT: High-risk incident logged for administrator review")
    log_event("-" * 60)
