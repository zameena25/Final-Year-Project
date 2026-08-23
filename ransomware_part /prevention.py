# ransomware_part/prevention.py
import os
import shutil
import time
import psutil
import threading
from datetime import datetime
from .config import QUARANTINE_FOLDER, BACKUP_FOLDER, LOG_FILE

_LOCKDOWN_ACTIVE = False
_LOCKDOWN_LOCK = threading.Lock()


def take_action(file_path: str, risk_level: str, process_name: str = "Unknown"):
    try:
        if not os.path.exists(file_path):
            return
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = os.path.basename(file_path)

        backup_path = os.path.join(BACKUP_FOLDER, f"{timestamp}_backup_{filename}")
        shutil.copy2(file_path, backup_path)
        print(f"Backup created: {backup_path}")

        quarantine_path = os.path.join(QUARANTINE_FOLDER, f"{timestamp}_{filename}")
        shutil.move(file_path, quarantine_path)
        print(f"QUARANTINED [{risk_level}] | Process: {process_name}")
        print(f" -> {quarantine_path}\n")
    except Exception as e:
        print(f"Quarantine failed: {e}")


def suspend_process(event):
    try:
        for proc in psutil.process_iter(['pid', 'name', 'status']):
            try:
                for item in proc.open_files():
                    if event.src_path in item.path:
                        proc.suspend()
                        print(f"SUSPENDED: {proc.info['name']} (PID: {proc.info['pid']})")
                        create_emergency_backup(event.src_path)
                        time.sleep(10)
                        proc.terminate()
                        print(f"TERMINATED: {proc.info['name']}")
                        return proc.info['pid']
            except Exception:
                continue
    except Exception as e:
        print(f"Failed to suspend: {e}")
    return None


def create_emergency_backup(file_path):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_name = f"emergency_{timestamp}_{os.path.basename(file_path)}"
    backup_path = os.path.join(BACKUP_FOLDER, backup_name)
    shutil.copy2(file_path, backup_path)
    print(f"Emergency backup: {backup_path}")
    return backup_path


def _log_lockdown_event():
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            f.write(f"[{ts}] EMERGENCY LOCKDOWN ACTIVATED\n")
    except Exception:
        pass


class PreventionEngine:
    def __init__(self):
        self._suspicious_pids: set = set()

    def quarantine(self, file_path: str, risk_level: str = "HIGH"):
        take_action(file_path, risk_level)

    def suspend(self, event):
        pid = suspend_process(event)
        if pid:
            self._suspicious_pids.add(pid)
        return pid

    def emergency_lockdown(self):
        global _LOCKDOWN_ACTIVE
        with _LOCKDOWN_LOCK:
            _LOCKDOWN_ACTIVE = True
        print("EMERGENCY LOCKDOWN ACTIVATED - all file monitoring halted.")
        _log_lockdown_event()
        for pid in list(self._suspicious_pids):
            try:
                proc = psutil.Process(pid)
                proc.suspend()
                print(f"Suspended suspicious PID: {pid}")
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass

    @staticmethod
    def is_lockdown_active() -> bool:
        return _LOCKDOWN_ACTIVE

    @staticmethod
    def lift_lockdown():
        global _LOCKDOWN_ACTIVE
        with _LOCKDOWN_LOCK:
            _LOCKDOWN_ACTIVE = False
        print("Lockdown lifted - monitoring resumed.")
