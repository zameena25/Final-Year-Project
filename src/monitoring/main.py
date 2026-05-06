# file_monitoring/main.py

import time
from pathlib import Path
from watchdog.observers import Observer
from .monitor import FolderMonitor

def main():
    path = input("Enter the folder path to monitor (or press Enter for the current directory): ").strip()
    if not path:
        path = "."
    
    folder_path = Path(path)
    if not folder_path.exists():
        print(f"Path does not exist: {folder_path}")
        return
    
    print (f"Monitoring: '{folder_path.resolve()}'")
    print("Press Ctrl+C to stop.\n")

    event_handler = FolderMonitor()
    observer = Observer()
    observer.schedule(event_handler, str(folder_path), recursive=True)
                      
    try:
        observer.start()
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nStopping Monitor...")
        observer.stop()
    
    observer.join()
    print("Monitor stopped.")

if __name__ == "__main__":
    main()
    