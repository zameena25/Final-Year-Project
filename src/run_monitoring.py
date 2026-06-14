#run_monitoring.py
import sys
from pathlib import Path
import threading
import time

sys.path.insert(0, str(Path(__file__).parent / "src"))

from monitoring.main import start_monitoring
from monitoring.process_monitor import process_monitor

if __name__ == "__main__":
    print("Starting NOVASPHERE Full Monitoring System... \n")

    file_thread = threading.Thread(target=start_monitoring, daemon=True)
    file_thread.start()

    #start monitoring
    process_monitor.start()

    print("Both file and Process Monitoring are Active!")
    print("Press Ctrl+C to stop everything. \n")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n Shutting down NOVASPHERE...") 
        process_monitor.stop()

        print("Shutdown complete.")
