import time
from datetime import datetime
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import logging

#Setting up logging
logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)
IGNORE_FOLDER = [".next", "node_modules", "__pycache__"]
class FolderMonitor(FileSystemEventHandler):
    def __init__(self):
        self.event_count = 0
        self.start_time = time.time()

        # Count events
        self.event_count += 1

        current_time = time.time()
        time_diff = current_time - self.start_time

        # Suspicious detection
        if time_diff <= 5:
            if self.event_count >10:
                print(f" Suspicious Activity: {self.event_count} events in {round(time_diff,2)} seconds")
        else: 
            self.event_count = 0
            self.start_time = current_time
        
        # Structured event data
        event_data = {
            "event_type" : event_type,
            "file_path" : path,
            "timestamp" : datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }

        #Print clean Output 
        logger.info(f"[{event_data['timestamp']}] {event_data['event_type']} - {event_data['file_path']}")

        #Save to file
        self.save_event(event_data)
        
    """Simple file system event handler."""

    def log(self, event_type, path):
        # Ignore unneccessary folders
        if any(folder in path for folder in IGNORE_FOLDER):
            return
        timestamp = datetime.now().strftime('%H:%M:%S')
        logger.info(f"[{timestamp}] {event_type} - {path}")

    def on_created(self, event):
        if not event.is_directory:
            self.log("CREATED", event.src_path)
    
    def on_deleted(self,event):
        if not event.is_directory:
            self.log("DELETED", event.src_path)
    
    def on_modified(self,event):
        if not event.is_directory:
            self.log("MODIFIED", event.src_path)

    def on_moved(self, event):
        if not event.is_directory:
            self.log("RENAMED", f"{event.src_path} -> {event.dest_path}")

def main():
    path = input("Enter folder path to monitor (or press Enter for current directory): ").strip()
    if not path:
        path ="."
    
    folder_path = Path(path)

    if not folder_path.exists():
        print(f"Path does not exist: {folder_path}")
        return
    
    print (f"Monitoring '{folder_path.resolve()}")
    print ("Press Ctrl+C to stop\n")

    event_handler=FolderMonitor()
    observer = Observer()
    observer.schedule(event_handler, str(folder_path), recursive=True)

    try:
        observer.start()
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
        
    observer.join()
    
if __name__ == "__main__":
    main()
