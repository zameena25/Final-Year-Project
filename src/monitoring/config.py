# file_monitoring/config.py
import json
from pathlib import Path
from typing import Dict

CONFIG_FILE = Path("config/monitoring_config.json")

DEFAULT_CONFIG = {
    "monitored_paths": ["test_folder", "C:/Users/User/Documents", "C:/Users/User/Downloads", "C:/Users/User/Desktop"],
    "critical_paths": ["Documents", "Downloads", "Desktop"],
    "ignore_folders": [".next", "node_modules", "__pycache__", ".git", ".venv", "venv", "env", "logs", ".lock", "tmp"],
    "suspicious_event_threshold": 12,
    "suspicious_time_window": 5,
    "buffer_size": 10,
    "log_file": "logs/events.jsonl",
    "alert_log_file": "logs/alerts.jsonl"
}

def load_config() -> Dict:
    CONFIG_FILE.parent.mkdir(exist_ok=True)
    Path("logs").mkdir(exist_ok=True)

    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                return { **DEFAULT_CONFIG, **json.load(f)}
        except Exception:
            pass
    
    #Creating the default config
    with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
        json.dump(DEFAULT_CONFIG, f, indent=2)
    return DEFAULT_CONFIG

config = load_config()
