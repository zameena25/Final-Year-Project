# file_monitoring/config.py

IGNORE_FOLDER = [".next", "node_modules", "__pycache__", ".git"]
SUSPICIOUS_EVENT_THRESHOLD = 10
SUSPICIOUS_TIME_WINDOW = 5 #seconds
LOG_FILE = "event_logs.jsonl"
BUFFER_SIZE = 5 #events before flushing to heuristic engine

