 # file_monitoring/logger.py

import json
import logging
from pathlib import Path
from .config import LOG_FILE

logging.basicConfig(level=logging.INFO, format="%(message)s")
_logger = logging.getLogger(__name__)


def log_to_console(timestamp: str, event_type: str, path: str):
    _logger.info("[%s] %s - %s", timestamp, event_type, path)


def save_event(event_data: dict):
    """Appends one JSON record to the JSONL log file."""
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(json.dumps(event_data) + "\n")
    except OSError as e:
        _logger.error("Failed to write event log: %s", e)
