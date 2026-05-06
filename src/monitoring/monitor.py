#file_monitor/monitor.py

from datetime import datetime
from pathlib import Path

from watchdog.events import FileSystemEventHandler
from heuristic_engine import process_event

from .config import IGNORE_FOLDERS, BUFFER_SIZE
from .logger import log_to_console, save_event
from .detector import SuspiciousActivityDetector

class FolderMonitor(FileSystemEventHandler):
    """Watches a directory and routes every file system event to logging + detection."""

    def __init__(self):
        super().__init__()
        self.detector = SuspiciousActivityDetector()
        self.event_buffer = []
    
    def _build_event(self, event_type: str, path: str):
        p = Path(path)
        return {
            "event_type": event_type,
            "file_path": path,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "file_extension": p.suffix,
            "file_size": p.stat().st_size if p.is_file() else 0,
            "event_source": "file_moniotr",
        }
    
    def log(self, event_type: str, path: str):
        if any(folder in path for folder in IGNORE_FOLDERS):
            return
        
        event_data = self._build_event(event_type, path)

        log_to_console(event_data["timestamp"], event_type, path)
        save_event(event_data)

        self.event_buffer.append(event_data)
        if len(self.event_buffer) >= BUFFER_SIZE:
            process_event(self.event_buffer)
            self.event_buffer.clear()
        
        self.detector.check(event_type, path)

    #watchdog callbacks
    def on_created(self, event):
        if not event.is_directory:
            self.log("CREATED", event.src_path)
    
    def on_deleted(self, event):
        if not event.is_directory:
            self.log("DELETED", event.src_path)
    
    def on_modified(self, event):
        if not event.is_directory:
            self.log("MODIFIED", event.src_path)
    
    def on_moved(self, event):
        if not event.is_directory:
            self.log("RENAMED", f"{event.src_path} → {event.dest_path}")    

