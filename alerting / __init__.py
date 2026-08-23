# alerting/__init__.py

import time

try:
    from src.monitoring.logger import save_event
except ImportError:
    try:
        from monitoring.logger import save_event
    except ImportError:
        def save_event(event_data, is_alert=False):
            pass


def alerting(alert_type: str, details: dict) -> dict:
    severity  = details.get("severity", "MEDIUM")
    message   = details.get("message", f"{alert_type} detected")
    file_path = details.get("file_path", "")
    source    = details.get("source", "ransomware_detector")

    alert = {
        "timestamp":  time.strftime("%Y-%m-%d %H:%M:%S"),
        "alert_type": alert_type,
        "severity":   severity,
        "message":    message,
        "file_path":  file_path,
        "source":     source,
    }

    save_event(alert, is_alert=True)
    return alert
