import time
from datetime import datetime
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import logging

#Setting up logging
logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

class FolderMonitor(FileSystemEventHandler):

    """Simple file system event handler."""

    def log(self, event_type, path):
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
