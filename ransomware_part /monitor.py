# ransomware_part/monitor.py
import time as _time
from collections import deque
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from .config import MONITOR_PATH


class RansomwareMonitor(FileSystemEventHandler):
    def on_created(self, event):
        from .detector import process_event
        process_event(event, "created")

    def on_modified(self, event):
        from .detector import process_event
        process_event(event, "modified")

    def on_deleted(self, event):
        from .detector import process_event
        process_event(event, "deleted")

    def on_moved(self, event):
        from .detector import process_event
        process_event(event, "moved", event.dest_path)


def start_monitoring():
    import time
    print("🚀 NOVASPHERE v1.0 Detection System Started...\n")
    event_handler = RansomwareMonitor()
    observer = Observer()
    observer.schedule(event_handler, MONITOR_PATH, recursive=True)
    observer.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
        print("\n👋 NOVASPHERE Stopped.")
    observer.join()


class FileSystemMonitor:
    _event_log: deque = deque(maxlen=500)

    def __init__(self):
        self._observer = None

    def start(self, paths: list, recursive: bool = True):
        handler = _TrackingHandler(self._event_log)
        self._observer = Observer()
        for path in paths:
            self._observer.schedule(handler, path, recursive=recursive)
        self._observer.start()

    def stop(self):
        if self._observer:
            self._observer.stop()
            self._observer.join()

    def get_activity(self) -> dict:
        now = _time.time()
        writes = 0
        deletes = 0
        for ts, etype in self._event_log:
            if now - ts <= 60:
                if etype in ("created", "modified"):
                    writes += 1
                elif etype == "deleted":
                    deletes += 1
        return {"reads": writes, "writes": writes, "deletes": deletes}


class _TrackingHandler(RansomwareMonitor):
    def __init__(self, log: deque):
        super().__init__()
        self._log = log

    def on_created(self, event):
        self._log.append((_time.time(), "created"))
        super().on_created(event)

    def on_modified(self, event):
        self._log.append((_time.time(), "modified"))
        super().on_modified(event)

    def on_deleted(self, event):
        self._log.append((_time.time(), "deleted"))
        super().on_deleted(event)
