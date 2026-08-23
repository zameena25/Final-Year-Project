import sqlite3

conn = sqlite3.connect("logs/novasphere.db")
rows = conn.execute(
    "SELECT timestamp, alert_type, severity, file_path FROM alerts "
    "WHERE source='ransomware_detector' ORDER BY rowid DESC LIMIT 10"
)
for row in rows:
    print(row)
conn.close()