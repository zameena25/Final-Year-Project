#monitoring/detector.py

import time
from datetime import datetime
from .config import config
from .logger import save_event
from alerting.alerting import send_alert
from pathlib import Path
from .false_positive_filter import FalsePositiveFilter

_BASE = Path(__file__).parent.parent.parent
ALERT_LOG = _BASE /"logs" /"alerts.jsonl"

class SuspiciousActivityDetector:
    """Sliding window burst detector — fires an alert if too many events hit too fast."""

    def __init__(self):
        self.event_count = 0
        self.window_start = time.time()
        self.alert_fired = False
        self.false_positive_filter = FalsePositiveFilter()

    def check(self, event_type:str, path: str):
        event = {"src_path": path, "event_type": event_type, "frequency": self.event_count}
        is_threat, score, reasons = self.false_positive_filter.is_genuine_threat(event)
        if not is_threat:
            return 
        self._last_fp_score = score
        self._last_fp_reasons = reasons

        now = time.time()
        elapsed = now - self.window_start
        
        if elapsed <= config["suspicious_time_window"]:
            self.event_count += 1
            if self.event_count > config["suspicious_event_threshold"] and not self.alert_fired:
                self._raise_alert(event_type, path, self.event_count, elapsed)
                self.alert_fired = True
        else:
            # Window expired — reset
            self.event_count = 1
            self.window_start = now
            self.alert_fired = False

    def _raise_alert(self, event_type: str, path: str, count: int, elapsed: float):
        alert = {
            "alert_type": "RAPID_FILE_ACTIVITY",
            "severity": "HIGH",
            "event_count": count,
            "threat_score": getattr(self, "_last_fp_score", 0),
            "threat_reasons": getattr(self, "_last_fp_reasons", []),
            "window_seconds": round(elapsed, 2),
            "trigger_event": event_type,
            "trigger_path": path,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "message": f"Rapid file activity detected: {count} events in {round(elapsed, 2)}s"
        }
        
        print(f"\n  SUSPICIOUS ACTIVITY DETECTED: {alert['message']}\n")
        save_event(alert, is_alert=True)
        send_alert("RAPID_FILE_ACTIVITY", alert)
