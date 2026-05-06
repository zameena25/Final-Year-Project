# file_monitoring/detector.py

import time
from datetime import datetime
from .config import SUSPICIOUS_EVENT_THRESHOLD, SUSPICIOUS_TIME_WINDOW
from .logger import save_event


class SuspiciousActivityDetector:
    """Sliding window burst detector — fires an alert if too many events hit too fast."""

    def __init__(self):
        self.event_count = 0
        self.window_start = time.time()
        self.alert_fired = False

    def check(self, event_type: str, path: str):
        now = time.time()
        elapsed = now - self.window_start

        if elapsed <= SUSPICIOUS_TIME_WINDOW:
            self.event_count += 1
            if self.event_count > SUSPICIOUS_EVENT_THRESHOLD and not self.alert_fired:
                self._raise_alert(event_type, path, self.event_count, elapsed)
                self.alert_fired = True
        else:
            # Window expired — reset
            self.event_count = 1
            self.window_start = now
            self.alert_fired = False

    def _raise_alert(self, event_type: str, path: str, count: int, elapsed: float):
        alert = {
            "alert": "RAPID_FILE_ACTIVITY",
            "event_count": count,
            "window_seconds": round(elapsed, 2),
            "trigger_event": event_type,
            "trigger_path": path,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }
        print(
            f"\n  SUSPICIOUS ACTIVITY DETECTED: {count} events in {round(elapsed, 2)}s"
            f"  |  trigger: {event_type} on {path}\n"
        )
        save_event(alert)