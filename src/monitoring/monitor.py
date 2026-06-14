# src/monitoring/monitor.py

import getpass
import time
from datetime import datetime
from pathlib import Path

from watchdog.events import FileSystemEventHandler
from .config import config
from .models import FileEvent
from .logger import log_to_console, save_event
from .detector import SuspiciousActivityDetector


class FolderMonitor(FileSystemEventHandler):
    """Watches a directory and routes every file system event to logging + detection."""

    def __init__(self):
        super().__init__()
        self.detector = SuspiciousActivityDetector()
        self.event_buffer = []
        self.username = getpass.getuser()
        self.last_modified = {}      # Debounce rapid MODIFIED events on same file

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _should_ignore(self, path: str) -> bool:
        path_lower = path.lower()
        return any(folder in path_lower for folder in config["ignore_folders"])

    def _build_event(self, event_type: str, src_path: str) -> dict:
        p = Path(src_path)
        try:
            file_size = p.stat().st_size if p.is_file() else 0
        except OSError:
            file_size = 0

        return FileEvent(
            event_type=event_type,
            file_path=str(p),
            timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            file_extension=p.suffix.lower(),
            file_size=file_size,
            username=self.username,
        ).to_dict()

    def _process_event(self, event_data: dict):
        if self._should_ignore(event_data["file_path"]):
            return

        # Debounce: skip MODIFIED events on the same file within 1.5s
        if event_data["event_type"] == "MODIFIED":
            path = event_data["file_path"]
            now = time.time()
            if path in self.last_modified and now - self.last_modified[path] < 1.5:
                return
            self.last_modified[path] = now
        
        #skipped MODIFIED events on the same file within 1.5s
        if event_data["event_type"] == "RENAMED":
            self.detector.fp_filter.reset_rename_counts()
            
        # Log to console and persist to file + DB
        log_to_console(event_data)
        save_event(event_data)

        # Buffer events — flush when buffer is full
        self.event_buffer.append(event_data)
        if len(self.event_buffer) >= config["buffer_size"]:
            self.event_buffer.clear()

        # Run burst detection
        self.detector.check(event_data["event_type"], event_data["file_path"])

    #watchdog callbacks
    def on_created(self, event):
        if not event.is_directory:
            self._process_event(self._build_event("CREATED", event.src_path))

    def on_deleted(self, event):
        if not event.is_directory:
            self._process_event(self._build_event("DELETED", event.src_path))

    def on_modified(self, event):
        if not event.is_directory:
            self._process_event(self._build_event("MODIFIED", event.src_path))

    def on_moved(self, event):
        if not event.is_directory:
            self._process_event(self._build_event("RENAMED", event.src_path))