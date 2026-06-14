 # file_monitoring/logger.py

import json
from .database import db
import logging
from pathlib import Path

LOG_FILE = "logs/events.jsonl"
ALERT_FILE = "logs/alerts.jsonl"

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)

def log_to_console(event: dict):
    logger.info(
        "[%s] %s - %s",
        event.get("timestamp", "N/A"),
        event.get("event_type", event.get("alert_type", "UNKNOWN")),
        event.get("file_path", event.get("trigger_path", "N/A")),
    )

def save_event(event_data: dict, is_alert=False):
    Path("logs").mkdir(exist_ok=True)
    file_path = ALERT_FILE if is_alert else LOG_FILE

    try:
        with open(file_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(event_data) + "\n")
        if is_alert:
            db.log_alert(event_data)
            print(f"ALERT SAVED: {event_data.get('message')}")
        else:
            db.log_event(event_data)

    except OSError as e:
        logger.error("Failed to write to log: %s", e)