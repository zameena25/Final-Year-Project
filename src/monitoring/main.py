#monitoring/main.py

import time
from pathlib import Path
from watchdog.observers import Observer
from .monitor import FolderMonitor
from .config import config

def start_monitoring():
    from frontend.ransomwarepage import launch_flask_thread
    launch_flask_thread()
    paths = config.get("monitored_paths", ["."])
    print(f"NOVASPHERE File Monitor Starting...")
    print(f"Monitoring paths: {paths}\n")

    event_handler = FolderMonitor()
    observer = Observer()

    for path in paths:
        p = Path(path)
        if p.exists():
            observer.schedule(event_handler, str(p), recursive=True)
            print(f"Monitoring: {p.resolve()}")
        else:
            print(f"Path not found: {path}")
                      
    try:
        observer.start()
        print("Monitoring is Active. Press Ctrl+C to stop.")
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nStopping Monitor...")
        observer.stop()
    finally: 
        observer.join()
        print("Monitor stopped.")

if __name__ == "__main__":
    start_monitoring()
    
