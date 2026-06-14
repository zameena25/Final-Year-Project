#montoring/check_db.py
import sqlite3
from pathlib import Path

db_path = Path("logs/novasphere.db")

if not db_path.exists():
    print("Database file not found!")
    print("Make sure you have run the monitor for some time.")
else:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    print("Database found!")

    #checking events
    cursor.execute("SELECT COUNT (*) FROM EVENTS")
    events_count = cursor.fetchone()[0]
    print(f" Total Events saved: {events_count}")

    #showing the recent events
    cursor.execute("""
                   SELECT timestamp, event_type, file_path 
                   FROM events 
                   ORDER BY rowid DESC LIMIT 8
                   """)
    print("\n Last 8 Events: ")
    for row in cursor.fetchall():
        print(row)
    
    #checking alerts
    cursor.execute("SELECT COUNT(*) FROM alerts")
    alerts_count = cursor.fetchone()[0]
    print(f"\n Total Alerts saved: {alerts_count}")

    conn.close()
