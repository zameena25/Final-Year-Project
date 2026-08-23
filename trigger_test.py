# trigger_test.py — run while the app is open and monitoring is active
from pathlib import Path
import time

folder = Path.home() / "Desktop"
for i in range(15):
    (folder / f"burst_test_{i}.txt").write_text("test")
    time.sleep(0.1)
print("Done — check verify_alerts.py in ~10 seconds")