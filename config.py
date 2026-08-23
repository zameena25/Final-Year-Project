# ransomware_part / config.py
import os
import json
from datetime import datetime
from pathlib import Path
from auth.app_paths import get_logs_dir, get_app_data_dir

_APP_DIR = get_app_data_dir()
_SETTINGS_FILE = _APP_DIR / "config" / "novasphere_settings.json"
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Paths
PROJECT_ROOT = Path(__file__).resolve().parent.parent
MONITOR_PATH = str(PROJECT_ROOT / "test_folder")  # Monitor the user's home directory
QUARANTINE_FOLDER = str(_APP_DIR / "quarantine")
BACKUP_FOLDER = str(_APP_DIR / "backup")
LOG_FOLDER = str(get_logs_dir())

os.makedirs(QUARANTINE_FOLDER, exist_ok=True)
os.makedirs(BACKUP_FOLDER, exist_ok=True)
os.makedirs(LOG_FOLDER, exist_ok=True)

SETTINGS = {"auto_quarantine": False, "auto_kill_process": False}
HIGH_THRESHOLD = 80
MEDIUM_THRESHOLD = 50
WINDOW_SECONDS = 10

if _SETTINGS_FILE.exists():
    try:
        with open(_SETTINGS_FILE, "r", encoding="utf-8") as f:
            _saved = json.load(f)
        SETTINGS["auto_quarantine"] = _saved.get("auto_quarantine", SETTINGS["auto_quarantine"])
        SETTINGS["auto_kill_process"] = _saved.get("auto_kill_process", SETTINGS["auto_kill_process"])
        v = _saved.get("slider_value")
        if v is not None:
            if v < 30: HIGH_THRESHOLD, MEDIUM_THRESHOLD = 120, 80
            elif v < 70: HIGH_THRESHOLD, MEDIUM_THRESHOLD = 80, 50
            else: HIGH_THRESHOLD, MEDIUM_THRESHOLD = 60, 35
    except Exception:
        pass

HONEYPOT_FILENAMES = {
    "importnant_passowrds.docx",
    "financial_report_2024.xlsx",
    "backup_credentials.txt",
    "system_keys.dat",
}
RUN_TIMESTAMP = datetime.now().strftime("%Y%m%d_%H%M%S")
LOG_FILE = os.path.join(LOG_FOLDER, f"novasphere_{RUN_TIMESTAMP}.log")

# Only print once when config is first loaded
if not globals().get("_config_loaded"):
    _config_loaded = True
    print(" NOVASPHERE v1.5 Loaded")
    print(f" Monitoring : {MONITOR_PATH}")
    print(f" Auto Quarantine : {'ON' if SETTINGS['auto_quarantine'] else 'OFF'}")
    print(f" Auto Kill      : {'ON' if SETTINGS['auto_kill_process'] else 'OFF'}")