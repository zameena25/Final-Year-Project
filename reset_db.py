import sqlite3
from pathlib import Path

db_path = Path(__file__).parent / "logs" / "novasphere.db"
con = sqlite3.connect(db_path)
cur = con.cursor()

cur.execute("DELETE FROM events")
cur.execute("DELETE FROM alerts")

con.commit()
con.close()
print("Cleared events and alerts tables.")