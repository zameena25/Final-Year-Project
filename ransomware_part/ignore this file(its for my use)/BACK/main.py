# main.py
"""
NOVASPHERE v1.4 - Main Entry Point with Working Toggles
"""

import threading
from monitor import start_monitoring
from commands import handle_command
from config import MONITOR_PATH

def print_banner():
    print("=" * 75)
    print("🔐 NOVASPHERE v1.4 - Ransomware Detection System")
    print("=" * 75)
    print(f"📍 Monitoring Folder : {MONITOR_PATH}")
    print("💡 Type 'help' for available commands")
    print("=" * 75)
    print()

if __name__ == "__main__":
    print_banner()
    
    # Start monitoring in background
    monitor_thread = threading.Thread(target=start_monitoring, daemon=True)
    monitor_thread.start()
    
    print("✅ Monitoring started successfully.\n")
    
    # Start interactive console
    while True:
        try:
            cmd = input("NOVASPHERE> ").strip()
            if not handle_command(cmd):
                break
        except KeyboardInterrupt:
            print("\n\n👋 Stopped by user.")
            break
        except Exception as e:
            print(f"Error: {e}")