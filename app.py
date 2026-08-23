import sys

# Windows' default console codepage (cp1252) can't encode the emoji used in
# status prints (ransomware_part/monitor.py, alerting/alerting.py, etc.),
# which crashes the background monitoring thread before it starts watching.
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

from frontend.login import main

if __name__ == "__main__":
    main()