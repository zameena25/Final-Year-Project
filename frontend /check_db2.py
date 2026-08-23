# frontend / check_db2.py

import sqlite3
from pathlib import Path
from datetime import datetime, date
from collections import defaultdict

db = Path("logs/novasphere.db")
c = sqlite3.connect(db)
cur = c.cursor()

# Date range
cur.execute("SELECT MIN(timestamp), MAX(timestamp), COUNT(*) FROM alerts")
mn, mx, total = cur.fetchone()
print(f"Total alerts: {total}")
print(f"Oldest: {mn}")
print(f"Newest: {mx}")

# Count per day
cur.execute("SELECT timestamp FROM alerts")
today = date.today()
day_counts = defaultdict(int)
out_of_range = 0
for (ts,) in cur.fetchall():
    try:
        d = datetime.strptime(ts, "%Y-%m-%d %H:%M:%S").date()
        delta = (today - d).days
        if 0 <= delta < 7:
            day_counts[d] += 1
        else:
            out_of_range += 1
    except:
        pass

print(f"\nAlerts within last 7 days (today={today}):")
for d in sorted(day_counts):
    print(f"  {d}: {day_counts[d]} alerts")
print(f"Alerts older than 7 days: {out_of_range}")
