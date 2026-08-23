# verify_alerts.py
import sqlite3
from pathlib import Path

conn = sqlite3.connect(Path("logs/novasphere.db"))
cur = conn.execute(
    "SELECT timestamp, alert_type, severity, source FROM alerts ORDER BY rowid DESC LIMIT 10"
)
print("10 most recent alerts:")
for row in cur.fetchall():
    print(" ", row)

cur = conn.execute("SELECT COUNT(*) FROM alerts")
print("\nTotal alerts in table:", cur.fetchone()[0])
conn.close()