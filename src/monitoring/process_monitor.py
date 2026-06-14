#monitoring/process_monitor.py
import psutil
import time
from datetime import datetime
import threading
from .logger import save_event

SAFE_PROCESS_NAMES = {
    #windows core 
    "system", "system idle process", "svchost.exe", "csrss.exe",
    "smss.exe", "wininit.exe", "services.exe", "lsass.exe",
    "spoolsv.exe", "taskhostw.exe", "explorer.exe", "dwm.exe",
    "winlogon.exe", "fontdrvhost.exe", "sihost.exe", "ctfmon.exe",
    "cmd.exe", #only suspicious with specific args
    "powersgell.exe", #only suspicious with -enc or -nop 
    "python.exe", "python3.exe",
    "code.exe", "node.exe",
    "chrome.exe", "msedge.exe", "firefox.exe", "brave.exe",
    "whatsapp.exe", "discord.exe", "slack.exe", "teams.exe",
    "taskmgr.exe", "notepad.exe", "mspaint.exe",
}

#Insider threat signals 
INSIDER_CMDLINE_PATTERNS = [
    # Privilege escalation
    "net localgroup administrators",
    "net user /add",
    "net user /active:yes",
 
    # Bulk data copying
    "xcopy /s",
    "robocopy",
    "copy /y",
 
    # Archiving / compression (exfil prep)
    "7z a",
    "winrar a",
    "compress-archive",
 
    # Registry export
    "reg export",
    "reg save",
 
    # Network data transfer
    "ftp ",
    "curl -t",
    "wget --post-file",
 
    # Log/evidence clearing
    "wevtutil cl system",
    "wevtutil cl security",
    "del /f /s /q",
]

CPU_SPIKE_THRESHOLD = 90.0
CPU_SPIKE_MIN_FILES = 100

class ProcessMonitor:
    """
    Background thread scanning all processes every 3 seconds.
    Detects ransomware and insider threat activity separately.
    cmd.exe, powershell.exe and common apps are whitelisted by name —
    they are only flagged when their COMMAND LINE arguments match known patterns.
    """
    def __init__(self):
        self.is_running = False
        self.thread = None
        self._alerted: dict = {} # { "ALERT_TYPE:PID": True } — fires once per PID
    
    def start(self):
        if self.is_running:
            return
        self.is_running = True
        self.thread = threading.Thread(
            target=self._monitor_loop,
            name="ProcessMonitor",
            daemon=True,
        )
        self.thread.start()
        print("Process Monitor started in background.")
    
    def stop(self):
        self.is_running = False
        print("Process Monitor stopped.")

    #Main loop
    def _monitor_loop(self):
        print("Process monitoring active...")
        while self.is_running:
            try:
                self._scan()
            except Exception as e:
                print(f"[ProcessMonitor] Scan error: {e}")
            time.sleep(3)

    def _scan(self):
        for proc in psutil.process_iter(["pid", "name","exe", "cmdline", "cpu_percent", "username"]):
            try:
                pid = proc.info["pid"]
                name = (proc.info["name"] or "").lower().strip()
                cmdline = " ".join(proc.info["cmdline"] or []).lower()
                username = proc.info.get("username", "unknown")

                if pid <=10:
                    continue

                if name in SAFE_PROCESS_NAMES in name not in ("cmd.exe", "powershell.exe"):
                    continue

                #insider threats checks 
                self._check_insider_cmdline(pid, name, cmdline, username)

            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                continue
            except Exception:
                continue

    def _check_insider_cmdline(self, pid, name, cmdline, username):
        matched = next((p for p in INSIDER_CMDLINE_PATTERNS if p in cmdline), None)
        if not matched:
            return
        self._alert(
            alert_type="INSIDER_THREAT_PROCESS",
            pid=pid,
            details={
                "pid": pid,
                "process_name": name,
                "matched_pattern":matched,
                "username": username,
                "cmdline": cmdline[:300],
                "message": (
                    f"Insider Threat activity: '{matched}"
                    f"run by {username} via {name} (PID {pid})"
                ),
            },
            severity = "High",
        )

    #alert dispatcher
    def _alert(self, alert_type: str, pid: int, details: dict, severity: str = "HIGH"):
        """Fires each alert only once per (alert_type, pid) - no log flooding."""
        key = f"{alert_type}:{pid}"
        if self._alerted.get(key):
            return
        self._alerted[key] = True

        alert={
            "alert_type": alert_type,
            "severity": severity,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "source": "process_monitor",
            **details,
        }
 
        tag = "CRITICAL" if severity == "CRITICAL" else "HIGH"
        print(f"\n[{tag}] [{alert_type}]")
        print(f"   {details.get('message', '')}")
        print(f"   Time: {alert['timestamp']}\n")
 
        save_event(alert, is_alert=True)

process_monitor = ProcessMonitor()

