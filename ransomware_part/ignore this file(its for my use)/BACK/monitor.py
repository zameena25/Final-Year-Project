# monitor.py
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import time
from config import MONITOR_PATH
from detector import process_event

class RansomwareMonitor(FileSystemEventHandler):
    def on_created(self, event):
        process_event(event, "created")

    def on_modified(self, event):
        process_event(event, "modified")

    def on_deleted(self, event):
        process_event(event, "deleted")

    def on_moved(self, event):
        process_event(event, "moved", event.dest_path)


def start_monitoring():
    print("🚀 NOVASPHERE v1.0 Detection System Started...\n")
    
    event_handler = RansomwareMonitor()
    observer = Observer()
    observer.schedule(event_handler, MONITOR_PATH, recursive=False)
    observer.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
        print("\n👋 NOVASPHERE Stopped.")
    observer.join()