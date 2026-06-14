from datetime import datetime
import json
from pathlib import Path

_BASE = Path(__file__).parent.parent.parent
ALERT_LOG = _BASE /"logs"/"alerts.jsonl"

def _get_severity(alert_type: str) -> str:
    HIGH = ["RAPID_FILE_ACTIVITY", "MASS_EXTENSION_CHANGE"]
    MED  = ["UNAUTHORIZED_ACCESS", "SUSPICIOUS_PROCESS"]
    return "HIGH" if alert_type in HIGH else "MED" if alert_type in MED else "LOW"

def send_alert(alert_type: str, details: dict):
    alert = {
        "alert_type": alert_type,
        "details": details,
        "username": details.get("username", "System"),
        "file_path": details.get("path",""),
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "source": "file_monitor",
        "severity": _get_severity(alert_type),
    }
    print(f"\n ALERT [{alert['severity']}] - {alert_type}")
    print(f"   Details: {details}")
    print(f"   Time: {alert['timestamp']}\n")

    Path(_BASE / "logs").mkdir(exist_ok=True)
    try:
        with open(ALERT_LOG, "a") as f:
            f.write(json.dumps(alert) + "\n")
    except OSError as e:
        print(f"Failed to save alert: {e}")

    return alert