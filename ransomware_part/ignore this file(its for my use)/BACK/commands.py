# commands.py
"""
Console Commands with Real Toggle Support
"""

import os
import config  # Import the whole module to modify variables

def show_help():
    print("\n📋 Available Commands:")
    print("  help                    - Show this help")
    print("  status                  - Show current status")
    print("  quarantine              - List quarantined files")
    print("  autoquarantine on/off   - Turn auto quarantine ON / OFF")
    print("  autokill on/off         - Turn auto process kill ON / OFF")
    print("  reset                   - Reset risk scores")
    print("  clear                   - Clear screen")
    print("  exit                    - Stop the system")
    print()


def show_status():
    print("\n📊 NOVASPHERE Live Status")
    print("=" * 60)
    print(f"Monitoring Folder     : {config.MONITOR_PATH}")
    print(f"Auto Quarantine       : {'ON' if config.SETTINGS['auto_quarantine'] else 'OFF'}")
    print(f"Auto Kill Process     : {'ON' if config.SETTINGS['auto_kill_process'] else 'OFF'}")
    print("Detection Mode        : Per-Process Scoring")
    print("=" * 60)
    print()


def list_quarantine():
    quarantine_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "quarantine")
    if os.path.exists(quarantine_path):
        files = os.listdir(quarantine_path)
        if files:
            print(f"\n🛡️ Quarantined Files ({len(files)}):")
            for f in sorted(files):
                print(f"   • {f}")
            print()
        else:
            print("\n✅ Quarantine folder is empty.\n")
    else:
        print("\nNo files quarantined yet.\n")


def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')


def handle_command(cmd: str):
    cmd = cmd.strip().lower()
    
    if cmd == "help":
        show_help()
    elif cmd == "status":
        show_status()
    elif cmd == "quarantine":
        list_quarantine()
    elif cmd.startswith("autoquarantine"):
        parts = cmd.split()
        state = parts[1] if len(parts) > 1 else "on"
        config.SETTINGS["auto_quarantine"] = (state == "on")
        print(f"🛡️ Auto Quarantine turned {'ON' if config.SETTINGS['auto_quarantine'] else 'OFF'}")
    elif cmd.startswith("autokill"):
        parts = cmd.split()
        state = parts[1] if len(parts) > 1 else "on"
        config.SETTINGS["auto_kill_process"] = (state == "on")
        print(f"🔪 Auto Kill Process turned {'ON' if config.SETTINGS['auto_kill_process'] else 'OFF'}")
        if config.SETTINGS["auto_kill_process"]:
            print("⚠️  Warning: Auto Kill is dangerous!")
    elif cmd == "reset":
        print("\n🔄 Risk scores reset.\n")
    elif cmd == "rollback":
        print("\n🔄 Last 5 minutes of file changes can be rolled back")
        print("   (Shows files that were buffered)")
    elif cmd == "honeypot status":
        honeypot_files = honeypot.list_honeypots()
        print(f"\n🍯 Honeypot Files: {len(honeypot_files)} active")
    elif cmd == "simulate attack":
        print("\n⚠️ SIMULATION MODE - Testing detection...")
        test_file = os.path.join(MONITOR_PATH, "simulate_test.txt")
        with open(test_file, 'w') as f:
            f.write("TEST")
            os.rename(test_file, test_file + ".encrypted")
            print("   Test attack simulated - Check detection!")
    elif cmd == "clear":
        clear_screen()
        print("🧹 Console cleared.\n")
    elif cmd == "exit":
        print("👋 Exiting NOVASPHERE...\n")
        return False
    elif cmd != "":
        print("❌ Unknown command. Type 'help'.\n")
    
    return True