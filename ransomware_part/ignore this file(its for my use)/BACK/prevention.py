# prevention.py
import os
import shutil
import psutil
from datetime import datetime
from config import QUARANTINE_FOLDER, BACKUP_FOLDER

def take_action(file_path: str, risk_level: str, process_name: str = "Unknown"):
    try:
        if not os.path.exists(file_path):
            return

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = os.path.basename(file_path)

        # Create backup first
        backup_path = os.path.join(BACKUP_FOLDER, f"{timestamp}_backup_{filename}")
        shutil.copy2(file_path, backup_path)
        print(f"💾 Backup created: {backup_path}")

        # Then quarantine
        quarantine_path = os.path.join(QUARANTINE_FOLDER, f"{timestamp}_{filename}")
        shutil.move(file_path, quarantine_path)

        print(f"🛡️ QUARANTINED [{risk_level}] | Process: {process_name}")
        print(f"   → {quarantine_path}\n")

    except Exception as e:
        print(f"❌ Quarantine failed: {e}")


def kill_process(event):
    """Kill the process that triggered the ransomware event"""
    try:
        # Try to find the process that modified the file
        for proc in psutil.process_iter(['pid', 'name', 'exe']):
            try:
                # Check if process has the file open
                for item in proc.open_files():
                    if event.src_path in item.path:
                        proc.kill()
                        print(f"🔪 KILLED suspicious process: {proc.info['name']} (PID: {proc.info['pid']})")
                        return
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                continue
        print("⚠️ Could not identify process to kill")
    except Exception as e:
        print(f"❌ Failed to kill process: {e}")
        
# Add to prevention.py
def suspend_process(event):
    """Suspend process instead of killing - gives time to backup"""
    try:
        for proc in psutil.process_iter(['pid', 'name', 'status']):
            try:
                for item in proc.open_files():
                    if event.src_path in item.path:
                        proc.suspend()
                        print(f"⏸️  SUSPENDED: {proc.info['name']} (PID: {proc.info['pid']})")
                        print(f"   Creating backup before termination...")
                        
                        # Now backup safely
                        create_emergency_backup(event.src_path)
                        
                        # Ask admin or auto-terminate after 10 seconds
                        time.sleep(10)
                        proc.terminate()
                        print(f"🔪 TERMINATED: {proc.info['name']}")
                        return proc.info['pid']
            except:
                continue
    except Exception as e:
        print(f"Failed to suspend: {e}")
    return None

def create_emergency_backup(file_path):
    """Emergency backup before process termination"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_name = f"emergency_{timestamp}_{os.path.basename(file_path)}"
    backup_path = os.path.join(BACKUP_FOLDER, backup_name)
    shutil.copy2(file_path, backup_path)
    print(f"💾 Emergency backup: {backup_path}")
    return backup_path