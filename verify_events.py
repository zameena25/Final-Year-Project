# verify_events.py — run from project root
from pathlib import Path

events_path = Path("logs/events.jsonl")
if events_path.exists():
    lines = events_path.read_text(encoding="utf-8").splitlines()
    print(f"Total events logged: {len(lines)}")
    print("Last 5 events:")
    for line in lines[-5:]:
        print(" ", line)
else:
    print("events.jsonl doesn't exist yet — background monitor likely never ran.")
    