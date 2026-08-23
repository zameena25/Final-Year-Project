"""
NOVASPHERE ransomware-monitoring console entry point.
Run from the project root with:
    python -m ransomware_part.main
"""

import threading

from .monitor import start_monitoring
from .commands import handle_command
from .config import MONITOR_PATH


def print_banner():
    print("=" * 75)
    print("NOVASPHERE - Ransomware Detection System")
    print("=" * 75)
    print(f"Monitoring Folder: {MONITOR_PATH}")
    print("Type 'help' for available commands")
    print("=" * 75)
    print()


def main():
    print_banner()

    monitor_thread = threading.Thread(target=start_monitoring, daemon=True)
    monitor_thread.start()
    print("Monitoring started successfully.\n")

    while True:
        try:
            if not handle_command(input("NOVASPHERE> ").strip()):
                break
        except KeyboardInterrupt:
            print("\nStopped by user.")
            break
        except Exception as exc:
            print(f"Error: {exc}")


if __name__ == "__main__":
    main()