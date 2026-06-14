# simulate_attack.py
# Simulates ransomware + insider threat behavior to test the full pipeline
# Run WHILE run_monitoring.py is active

import os
import time
import random
from pathlib import Path

TEST_DIR = Path("test_folder")
TEST_DIR.mkdir(exist_ok=True)

print("=" * 55)
print("  NOVASPHERE — Attack Simulation Starting")
print("=" * 55)

# ── Test 1: Rapid file creation (triggers burst detector)
print("\n[1] Rapid file creation — 30 files in 2 seconds...")
for i in range(30):
    (TEST_DIR / f"document_{i}.txt").write_text(f"content {i}")
    time.sleep(0.05)
print("    ✓ Done")

time.sleep(2)

# ── Test 2: Mass extension rename (ransomware signature)
print("\n[2] Mass renaming to .enc (ransomware simulation)...")
for i in range(30):
    src = TEST_DIR / f"document_{i}.txt"
    dst = TEST_DIR / f"document_{i}.enc"
    if src.exists():
        src.rename(dst)
    time.sleep(0.03)
print("    ✓ Done")

time.sleep(2)

# ── Test 3: Mass delete
print("\n[3] Mass file deletion...")
for f in TEST_DIR.glob("*.enc"):
    f.unlink()
    time.sleep(0.02)
print("    ✓ Done")

time.sleep(2)

# ── Test 4: Suspicious file types
print("\n[4] Creating suspicious file types...")
suspicious = [
    "payload.exe", "backdoor.bat", "keylogger.vbs",
    "stealer.ps1", "ransom_note.txt", "decrypt_instructions.html"
]
for name in suspicious:
    (TEST_DIR / name).write_text("suspicious content")
    time.sleep(0.1)
print("    ✓ Done")

time.sleep(1)

# ── Test 5: Rapid modify (insider behavior)
print("\n[5] Rapid file modifications (insider behavior)...")
target = TEST_DIR / "ransom_note.txt"
for i in range(20):
    target.write_text(f"modified {i} times")
    time.sleep(0.05)
print("    ✓ Done")

print("\n" + "=" * 55)
print("  Simulation complete!")
print("  Check the UI — alerts should appear within 3 seconds")
print("  Check logs/alerts.jsonl for written alerts")
print("=" * 55)