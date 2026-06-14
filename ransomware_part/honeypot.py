# honey pot.py - Add to your project
"""
Honeypot decoy files that trigger immediate high alert
"""

import os
from config import MONITOR_PATH

class HoneypotManager:
    def __init__(self):
        self.honeypot_files = []
        self.setup_honeypots()
    
    def setup_honeypots(self):
        """Create decoy files that look attractive to ransomware"""
        decoys = [
            "critical_business_data.xlsx",
            "database_backup.sql",
            "financial_records.pdf",
            "HR_employee_data.docx",
            "company_secrets.txt"
        ]
        
        for decoy in decoys:
            path = os.path.join(MONITOR_PATH, decoy)
            if not os.path.exists(path):
                with open(path, 'w') as f:
                    f.write("[HONEYPOT - DO NOT MODIFY]\n")
                    f.write("This is a decoy file for ransomware detection\n")
                    f.write(f"Created by NOVASPHERE at {__import__('datetime').datetime.now()}\n")
            self.honeypot_files.append(path)
        
        # Create hidden .honeypot folder with more decoys
        hidden_dir = os.path.join(MONITOR_PATH, ".honeypot")
        os.makedirs(hidden_dir, exist_ok=True)
        
        print(f"🍯 Created {len(self.honeypot_files)} honeypot files + hidden decoys")
    
    def is_honeypot(self, file_path):
        """Check if touched file is a honeypot"""
        return any(hp in file_path for hp in self.honeypot_files) or ".honeypot" in file_path   