#src/monitoring/database.py
import sqlite3
from pathlib import Path
from datetime import datetime

DB_FILE = Path("logs/novasphere.db")

class Database:
    def __init__(self):
        DB_FILE.parent.mkdir(exist_ok=True)
        self.conn = sqlite3.connect(DB_FILE, check_same_thread=False)
        self.create_tables()

    def create_tables(self):
        cursor=self.conn.cursor()

        #file events table 
        cursor.execute('''
                       CREATE TABLE IF NOT EXISTS events (
                       id INTEGER PRIMARY KEY AUTOINCREMENT,
                       timestamp TEXT,
                       event_type TEXT,
                       file_path TEXT,
                       file_extension TEXT,
                       file_size INTEGER,
                       username TEXT,
                       source TEXT DEFAULT 'file_monitor'
                       )
                       ''')
        
        #alerts table 
        cursor.execute('''
                       CREATE TABLE IF NOT EXISTS alerts (
                       id INTEGER PRIMARY KEY AUTOINCREMENT,
                       timestamp TEXT,
                       alert_type TEXT,
                       severity TEXT,
                       message TEXT,
                       process_name TEXT,
                       pid INTEGER,
                       file_path TEXT,
                       source TEXT
                       )
                    ''')
        
        self.conn.commit()
    
    def log_event(self, event: dict):
        try:
            cursor = self.conn.cursor()
            cursor.execute('''
                           INSERT INTO events
                           (timestamp, event_type, file_path, file_extension, file_size, username, source)
                           VALUES (?, ?, ?, ?, ?, ?, ?)
                        ''', (
                            event.get('timestamp', datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
                            event.get('event_type'),
                            event.get('file_path'),
                            event.get('file_extension'),
                            event.get('file_size'),
                            event.get('username'),
                            event.get('source', 'file_monitor')
                        ) )
            self.conn.commit()
            
        except Exception as e:
            print(f"DB Event Error: {e}")
    
    def log_alert(self, alert:dict):
        try:
            cursor = self.conn.cursor()
            cursor.execute('''
                           INSERT INTO alerts
                           (timestamp, alert_type, severity, message, process_name, pid, file_path, source)
                           VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                        ''', (
                            alert.get('timestamp', datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
                            alert.get('alert_type'),
                            alert.get('severity', 'HIGH'),
                            alert.get('message'),
                            alert.get('process_name'),
                            alert.get('pid'),
                            alert.get('trigger_path') or alert.get('file_path'),
                            alert.get('source', 'monitor')
                        ))
            self.conn.commit()
        except Exception as e:
            print(f"DB Alert Error: {e}")
    
    def close(self):
        self.conn.close()

db = Database()
