# verify_db.py — run from project root
import sqlite3, os
from pathlib import Path

db_path = Path("logs/novasphere.db")
print("DB exists:", db_path.exists())
print("Full path:", db_path.resolve())
print("Last modified:", os.path.getmtime(db_path) if db_path.exists() else "N/A")

conn = sqlite3.connect(db_path)
cur = conn.execute("SELECT COUNT(*) FROM alerts")
print("Alert count:", cur.fetchone()[0])
cur = conn.execute("SELECT timestamp, alert_type, source FROM alerts ORDER BY rowid DESC LIMIT 5")
print("Most recent alerts:")
for row in cur.fetchall():
    print(" ", row)
conn.close()
