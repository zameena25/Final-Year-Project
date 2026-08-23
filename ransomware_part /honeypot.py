# ransomware_part/honeypot.py
import os
import json
from pathlib import Path
from datetime import datetime
from .config import MONITOR_PATH
from auth.app_paths import get_logs_dir

_HONEYPOT_JSON = get_logs_dir() / "honeypots.json"

class HoneypotManager:
    def __init__(self):
        self.honeypot_files = []
        self.setup_honeypots()
        self.save_honeypot_list()   

    def setup_honeypots(self):
        decoys = [
            "critical_business_data.xlsx",
            "database_backup.sql",
            "financial_records.pdf",
            "HR_employee_data.docx",
            "company_secrets.txt"
        ]
        honeypot_dir = os.path.join(MONITOR_PATH, "Documents", ".novasphere_decoys")
        os.makedirs(honeypot_dir, exist_ok=True)

        for decoy in decoys:
            path = os.path.join(honeypot_dir, decoy)
            if not os.path.exists(path):
                with open(path, 'w') as f:
                    f.write("[HONEYPOT - DO NOT MODIFY]\n")
                    f.write("This is a decoy file for ransomware detection\n")
                    f.write(f"Created by NOVASPHERE at {datetime.now()}\n")
            self.honeypot_files.append(path)

        hidden_dir = os.path.join(honeypot_dir, ".honeypot")
        os.makedirs(hidden_dir, exist_ok=True)
        print(f"Created {len(self.honeypot_files)} honeypot files")

    def is_honeypot(self, file_path):
        return (
            any(hp in file_path for hp in self.honeypot_files)
            or ".honeypot" in file_path
        )

    def save_honeypot_list(self):
        try:
            _HONEYPOT_JSON.parent.mkdir(parents=True, exist_ok=True)
            data = [{"path": str(p)} for p in self.honeypot_files]
            with open(_HONEYPOT_JSON, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
        except Exception:
            pass
