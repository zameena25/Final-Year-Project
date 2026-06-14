import sqlite3
from pathlib import Path

db = Path("logs/novasphere.db")
print("DB exists:", db.exists())

c = sqlite3.connect(db)
cur = c.cursor()

cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
print("Tables:", cur.fetchall())

cur.execute("SELECT timestamp, alert_type, severity FROM alerts ORDER BY rowid DESC LIMIT 5")
print("Latest 5 alerts:")
for r in cur.fetchall():
    print(r)
