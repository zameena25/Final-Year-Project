# detector.py - Complete updated version
import time
import psutil
from collections import defaultdict, deque
from config import HIGH_THRESHOLD, MEDIUM_THRESHOLD, WINDOW_SECONDS, SETTINGS
import prevention
from honeypot import HoneypotManager
from file_buffer import FileBuffer

# Initialize advanced features
honeypot = HoneypotManager()
file_buffer = FileBuffer(buffer_seconds=5)

process_scores = defaultdict(int)
event_queues = defaultdict(lambda: deque(maxlen=200))
last_decay = defaultdict(lambda: time.time())

def log_event(message: str):
    timestamp = time.strftime("%H:%M:%S")
    log_message = f"[{timestamp}] {message}"
    print(log_message)
    try:
        with open("logs/novasphere.log", "a", encoding="utf-8") as f:
            f.write(log_message + "\n")
    except:
        pass

def process_event(event, event_type: str, dest_path=None):
    global process_scores, last_decay
    
    if event.is_directory:
        return

    # FEATURE 1: HONEYPOT CHECK (IMMEDIATE RESPONSE)
    if honeypot.is_honeypot(event.src_path):
        log_event(f"🍯 HONEYPOT TRIGGERED! File: {event.src_path}")
        
        # IMMEDIATE maximum response
        if SETTINGS.get("auto_kill_process", False):
            prevention.suspend_process(event)  # Use suspend for investigation
        
        if SETTINGS.get("auto_quarantine", True):
            prevention.take_action(event.src_path, "CRITICAL", "HONEYPOT")
        
        log_event("🔥 HONEYPOT: Attack detected before real damage!")
        return  # Don't continue scoring - immediate response

    # FEATURE 2: BUFFER FILES FOR POSSIBLE ROLLBACK
    if event_type in ["modified", "created"]:
        file_buffer.buffer_file(event.src_path)
    
    now = time.time()
    path_lower = event.src_path.lower()

    # Clean old events
    while event_queues["global"] and now - event_queues["global"][0][0] > WINDOW_SECONDS:
        event_queues["global"].popleft()

    event_queues["global"].append((now, event.src_path, event_type))
    recent_count = len(event_queues["global"])
    points = 0

    # Detection rules
    ransomware_exts = ['.locked', '.encrypted', '.crypt', '.enc', '.ransom', '.crypto']
    if any(ext in path_lower for ext in ransomware_exts):
        points += 55
        log_event(f"[EXTENSION] Ransomware extension detected! +55")

    if recent_count >= 6:
        points += 30
        log_event(f"[BULK] High activity detected! {recent_count} events +30")

    if event_type == "moved" and dest_path and any(ext in dest_path.lower() for ext in ransomware_exts):
        points += 45
        log_event(f"[RENAME] File renamed to ransomware extension! +45")
    
    # Honeypot protected mode - lower threshold
    if honeypot.is_honeypot(event.src_path):
        points += 100  # Instant max score

    process_scores["global"] += points

    # Score decay
    if now - last_decay["global"] > WINDOW_SECONDS:
        process_scores["global"] = max(0, process_scores["global"] - 30)
        last_decay["global"] = now

    current_score = process_scores["global"]

    # RESPONSE LEVELS
    if current_score >= HIGH_THRESHOLD:
        log_event(f"🚨 HIGH RISK DETECTED! Score: {current_score}")
        
        # FEATURE 3: ROLLBACK if possible
        rollback_success = file_buffer.rollback_file(event.src_path)
        if rollback_success:
            log_event("✅ Rollback successful - file restored to pre-attack state")
        
        # Response actions
        if SETTINGS.get("auto_kill_process", False):
            killed_pid = prevention.suspend_process(event)
            if killed_pid:
                log_event(f"🔪 Process suspended and terminated (PID: {killed_pid})")
        
        if SETTINGS.get("auto_quarantine", True):
            prevention.take_action(event.src_path, "HIGH")
        else:
            log_event("⚠️ Auto Quarantine OFF - Manual review required")
        
        # Clean up
        file_buffer.clear_buffer(event.src_path)
        process_scores["global"] = 0
        
        # Send alert (could add email/SMS here)
        log_event("📧 ALERT: Critical incident logged for admin review")

    elif current_score >= MEDIUM_THRESHOLD:
        log_event(f"⚠️ Medium Risk | Score: {current_score}")
        # For medium risk, just buffer and monitor
        log_event("   → File buffered, monitoring for escalation")