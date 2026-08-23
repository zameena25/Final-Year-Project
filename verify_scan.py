# verify_scan.py
import os
from pathlib import Path

SKIP_DIRS = {
    "Windows", "System32", "$Recycle.Bin", "__pycache__", "node_modules",
    "AppData", ".git", ".cache", "venv", ".venv", "site-packages",
    "Library", "Application Data", "ProgramData",
}

scan_root = str(Path.home())
all_files = []
skipped_dirs = []
dir_count = 0

def _on_walk_error(err):
    skipped_dirs.append(str(err))

for root, dirs, files in os.walk(scan_root, onerror=_on_walk_error):
    dir_count += 1
    dirs[:] = [d for d in dirs if not d.startswith(".") and d not in SKIP_DIRS]
    for fname in files:
        all_files.append(os.path.join(root, fname))

print(f"Scan root: {scan_root}")
print(f"Directories visited: {dir_count}")
print(f"Total files found: {len(all_files)}")
print(f"Folders that errored: {len(skipped_dirs)}")
if skipped_dirs:
    print("First 10 errors:")
    for e in skipped_dirs[:10]:
        print(f"  - {e}")