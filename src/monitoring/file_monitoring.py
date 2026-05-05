import json
import time
from datetime import datetime
from pathlib import Path

import logging
from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer
from heuristic_engine import process_event 

# Config

IGNORE_FOLDERS = [".next", "node_modules", "__pycache__", ".git"]

SUSPICIOUS_EVENT_THRESHOLD = 10
SUSPICIOUS_TIME_WINDOW = 5

LOG_FILE = "event_logs.jsonl"

# Logger setup

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)


# Event Handler

class FolderMonitor(FileSystemEventHandler):
    """Watches a directory and logs + analyzes every file system event."""

    def __init__(self):
        super().__init__()
        self.event_count = 0
        self.window_start = time.time()
        self.alert_fired = False
        self.event_buffer = []


    # Core event router

    def log(self, event_type: str, path: str):
        """Called by every on_* method. Filters noise, logs, and runs detection."""

        # Skip noisy/irrelevant folders
        if any(folder in path for folder in IGNORE_FOLDERS):
            return

        # Build structured event record
        event_data = {
            "event_type": event_type,
            "file_path": path,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "file_extension": Path(path).suffix,
            "file_size": Path(path).stat().st_size if Path(path).is_file() else 0,
            "event_source": "file_monitor"
        }

        # Human-readable console output
        logger.info("[%s] %s - %s", event_data["timestamp"], event_type, path)

        # Persist to JSONL log
        self.save_event(event_data)

        self.event_buffer.append(event_data)

        if len(self.event_buffer) >= 5:
            process_event(self.event_buffer)
            self.event_buffer.clear()

        # Run behavioral detection on every event
        self._check_suspicious_activity(event_type, path)
    
    def _get_file_size(self, path):
        try:
            return Path(path).stat().st_size
        except:
            return 0
    

    # Watchdog callback

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
            # Showing the source and destination for renames
            self.log("RENAMED", f"{event.src_path} → {event.dest_path}")

    def process_event(self, event):
        print("Sending to heuristic engine:", event)

    
    # Suspicious activity detection

    def _check_suspicious_activity(self, event_type: str, path: str):
        """
        Sliding window burst detector.
        Counts events within SUSPICIOUS_TIME_WINDOW seconds.
        Resets the window once the window expires — AFTER checking, not before.
        """
        now = time.time()
        elapsed = now - self.window_start

        if elapsed <= SUSPICIOUS_TIME_WINDOW:
            # Still inside the current window — keep counting
            self.event_count += 1

            if self.event_count > SUSPICIOUS_EVENT_THRESHOLD:
                if not self.alert_fired:
                    self._raise_alert(event_type, path, self.event_count, elapsed)
                    self.alert_fired = True
        else:
            # Window expired — reset for the next window, THEN count this event
            self.event_count = 1
            self.window_start = now
            self.alert_fired = False

    def _raise_alert(self, event_type: str, path: str, count: int, elapsed: float):
        alert = {
            "alert": "RAPID_FILE_ACTIVITY",
            "event_count": count,
            "window_seconds": round(elapsed, 2),
            "trigger_event": event_type,
            "trigger_path": path,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }
        # Prominent console warning
        print(
            f"\n⚠  SUSPICIOUS ACTIVITY: {count} events in {round(elapsed, 2)}s"
            f"  |  trigger: {event_type} on {path}\n"
        )
        self.save_event(alert)

    # Persistence

    def save_event(self, event_data: dict):
        """Appends a JSON record to the log file. One record per line (JSONL)."""
        try:
            with open(LOG_FILE, "a", encoding="utf-8") as f:
                f.write(json.dumps(event_data) + "\n")
        except OSError as e:
            logger.error("Failed to write event log: %s", e)


# Entry point

def main():
    path = input("Enter folder path to monitor (or press Enter for current directory): ").strip()
    if not path:
        path = "."

    folder_path = Path(path)

    if not folder_path.exists():
        print(f"Path does not exist: {folder_path}")
        return

    print(f"Monitoring: '{folder_path.resolve()}'")   # FIX: was missing closing quote
    print("Press Ctrl+C to stop.\n")

    event_handler = FolderMonitor()
    observer = Observer()
    observer.schedule(event_handler, str(folder_path), recursive=True)

    try:
        observer.start()
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nStopping monitor...")
        observer.stop()

    observer.join()
    print("Monitor stopped.")


if __name__ == "__main__":
    main()