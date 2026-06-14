# config.py
import os
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Paths
TEST_FOLDER = "test_folder"
MONITOR_PATH = os.path.join(BASE_DIR, TEST_FOLDER)
QUARANTINE_FOLDER = os.path.join(BASE_DIR, "quarantine")
BACKUP_FOLDER = os.path.join(BASE_DIR, "backup")
LOG_FOLDER = os.path.join(BASE_DIR, "logs")

os.makedirs(MONITOR_PATH, exist_ok=True)
os.makedirs(QUARANTINE_FOLDER, exist_ok=True)
os.makedirs(BACKUP_FOLDER, exist_ok=True)
os.makedirs(LOG_FOLDER, exist_ok=True)

# Scoring
HIGH_THRESHOLD = 80
MEDIUM_THRESHOLD = 50
WINDOW_SECONDS = 60

# Toggles - Using a dictionary for mutable settings
SETTINGS = {
    "auto_quarantine": True,
    "auto_kill_process": False
}

RUN_TIMESTAMP = datetime.now().strftime("%Y%m%d_%H%M%S")
LOG_FILE = os.path.join(LOG_FOLDER, f"novasphere_{RUN_TIMESTAMP}.log")

# Only print once when config is first loaded
if not globals().get("_config_loaded"):
    _config_loaded = True
    print("✅ NOVASPHERE v1.5 Loaded")
    print(f"📁 Monitoring : {MONITOR_PATH}")
    print(f"🛡️ Auto Quarantine : {'ON' if SETTINGS['auto_quarantine'] else 'OFF'}")
    print(f"🔪 Auto Kill      : {'ON' if SETTINGS['auto_kill_process'] else 'OFF'}")