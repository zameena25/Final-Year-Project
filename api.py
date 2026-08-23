# ransomware_part / api.py
"""
NOVASPHERE Flask API
Connects the Python backend to the React dashboard.
Run this instead of main.py when using the UI.
"""

import os
import re
import threading
from datetime import datetime
from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS

from . import config
from . import detector
from .monitor import start_monitoring
from .honeypot import HoneypotManager

app = Flask(__name__)
CORS(app)  # Allow React dev server to call this API

# ── Monitoring thread state ──────────────────────────────────────────────────
_monitor_thread   = None
_monitoring_active = False
_scan_start_time  = None
_files_scanned    = 0
_honeypot_mgr     = HoneypotManager()

# Initial scan progress tracking
_scan_progress = {
    "running":   False,   # initial scan in progress
    "done":      False,   # initial scan finished
    "current":   0,       # files checked so far
    "total":     0,       # total files to check
    "current_file": "",   # file being checked right now
    "found":     0,       # suspicious files found
}


# ── Helper: parse log file into alert objects ────────────────────────────────
def _parse_alerts():
    """
    Read the log file and turn each detection line into a structured alert dict.
    Returns newest-first list.
    """
    alerts = []
    alert_id = 1

    if not os.path.exists(config.LOG_FILE):
        return alerts

    # Patterns we care about
    patterns = {
        "CRITICAL": re.compile(r"HONEYPOT TRIGGERED"),
        "HIGH":     re.compile(r"HIGH RISK DETECTED.*Score:\s*([\d.]+).*File:\s*(.+)"),
        "MEDIUM":   re.compile(r"MEDIUM RISK.*?([\w._-]+\.?\w*)\s*\|\s*Score:\s*([\d.]+)"),
        "SCORE":    re.compile(r"\[SCORE\]\s*([\w._-]+)\s*\|\s*\+(\d+)\s*pts\s*\(([^)]+)\)"),
    }

    with open(config.LOG_FILE, "r", encoding="utf-8") as f:
        lines = f.readlines()

    for line in lines:
        line = line.strip()
        if not line:
            continue

        # Extract timestamp
        ts_match = re.match(r"\[(\d{2}:\d{2}:\d{2})\]", line)
        timestamp = ts_match.group(1) if ts_match else "00:00:00"

        alert = None

        if patterns["CRITICAL"].search(line):
            file_match = re.search(r"File:\s*(.+)", line)
            fname = os.path.basename(file_match.group(1)) if file_match else "Unknown"
            alert = {
                "id":        f"ALT-{alert_id:04d}",
                "severity":  "Critical",
                "type":      "Honeypot Triggered",
                "file":      fname,
                "rule":      "HONEYPOT",
                "score":     100,
                "timestamp": timestamp,
                "status":    "Open",
            }

        elif m := patterns["HIGH"].search(line):
            fname = os.path.basename(m.group(2).strip())
            alert = {
                "id":        f"ALT-{alert_id:04d}",
                "severity":  "High",
                "type":      "Ransomware",
                "file":      fname,
                "rule":      "HIGH_RISK",
                "score":     float(m.group(1)),
                "timestamp": timestamp,
                "status":    "Open",
            }

        elif m := patterns["MEDIUM"].search(line):
            alert = {
                "id":        f"ALT-{alert_id:04d}",
                "severity":  "Medium",
                "type":      "Suspicious Activity",
                "file":      m.group(1),
                "rule":      "MEDIUM_RISK",
                "score":     float(m.group(2)),
                "timestamp": timestamp,
                "status":    "Investigating",
            }

        elif m := patterns["SCORE"].search(line):
            alert = {
                "id":        f"ALT-{alert_id:04d}",
                "severity":  "Low",
                "type":      "Score Event",
                "file":      m.group(1),
                "rule":      m.group(3),
                "score":     int(m.group(2)),
                "timestamp": timestamp,
                "status":    "Resolved",
            }

        if alert:
            alerts.append(alert)
            alert_id += 1

    alerts.reverse()   # newest first
    return alerts


# ── Routes ───────────────────────────────────────────────────────────────────

@app.route("/api/status")
def get_status():
    """Overall system status for the dashboard."""
    quarantine_count = 0
    quarantine_path = config.QUARANTINE_FOLDER
    if os.path.exists(quarantine_path):
        quarantine_count = len(os.listdir(quarantine_path))

    alerts = _parse_alerts()
    threats_detected = sum(
        1 for a in alerts if a["severity"] in ("Critical", "High")
    )

    return jsonify({
        "monitoring_active": _monitoring_active,
        "protection_status": "Active" if _monitoring_active else "Inactive",
        "files_scanned":     _files_scanned,
        "threats_detected":  threats_detected,
        "quarantine_count":  quarantine_count,
        "last_scan_time":    _scan_start_time,
        "monitor_path":      config.MONITOR_PATH,
        "settings": {
            "auto_quarantine":  config.SETTINGS["auto_quarantine"],
            "auto_kill_process": config.SETTINGS["auto_kill_process"],
        }
    })


@app.route("/api/scan/start", methods=["POST"])
def start_scan():
    """Start initial file scan then hand off to live monitor."""
    global _monitor_thread, _monitoring_active, _scan_start_time, _files_scanned

    if _monitoring_active:
        return jsonify({"success": False, "message": "Already monitoring"}), 400

    _scan_start_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    _monitoring_active = True
    _files_scanned = 0

    # Run initial scan + then start live monitor, all in one background thread
    def run_scan_then_monitor():
        global _files_scanned
        _scan_progress["running"]      = True
        _scan_progress["done"]         = False
        _scan_progress["current"]      = 0
        _scan_progress["found"]        = 0
        _scan_progress["current_file"] = ""

        # Collect all files in monitor folder
        all_files = []
        for root, _, files in os.walk(config.MONITOR_PATH):
            for f in files:
                all_files.append(os.path.join(root, f))

        _scan_progress["total"] = len(all_files)

        # Check each file — simulate scan with small delay per file
        import types, time as _time
        for i, fpath in enumerate(all_files):
            if not _monitoring_active:
                break

            _scan_progress["current"]      = i + 1
            _scan_progress["current_file"] = os.path.basename(fpath)
            _files_scanned = i + 1

            # Run through detector rules for existing files
            try:
                path_lower = fpath.lower()
                is_suspicious = any(
                    fpath.lower().endswith(ext)
                    for ext in detector.RANSOMWARE_EXTENSIONS
                )
                if is_suspicious:
                    _scan_progress["found"] += 1
                    # Fire a synthetic event through the detector
                    fake_event = types.SimpleNamespace(
                        src_path=fpath, is_directory=False
                    )
                    detector.process_event(fake_event, "created")
            except Exception:
                pass

            _time.sleep(0.08)   # small delay so progress is visible

        _scan_progress["running"]      = False
        _scan_progress["done"]         = True
        _scan_progress["current_file"] = ""

        # Now start live watchdog monitor
        start_monitoring()

    _monitor_thread = threading.Thread(target=run_scan_then_monitor, daemon=True)
    _monitor_thread.start()

    return jsonify({"success": True, "message": "Scan started", "started_at": _scan_start_time})


@app.route("/api/scan/progress")
def get_scan_progress():
    """Return current initial scan progress."""
    total   = _scan_progress["total"] or 1   # avoid div by zero
    current = _scan_progress["current"]
    pct     = round((current / total) * 100)
    return jsonify({
        "running":      _scan_progress["running"],
        "done":         _scan_progress["done"],
        "current":      current,
        "total":        _scan_progress["total"],
        "percent":      pct,
        "current_file": _scan_progress["current_file"],
        "found":        _scan_progress["found"],
    })


@app.route("/api/scan/stop", methods=["POST"])
def stop_scan():
    """Stop monitoring (marks as inactive; watchdog thread is daemon so it stops with app)."""
    global _monitoring_active
    _monitoring_active = False
    return jsonify({"success": True, "message": "Monitoring stopped"})


@app.route("/api/alerts")
def get_alerts():
    """Return parsed alerts from the log file."""
    alerts = _parse_alerts()

    # Summary counts
    counts = {"Critical": 0, "High": 0, "Medium": 0, "Low": 0}
    for a in alerts:
        if a["severity"] in counts:
            counts[a["severity"]] += 1

    return jsonify({
        "alerts":  alerts,
        "summary": counts,
        "total":   len(alerts),
    })


@app.route("/api/quarantine")
def get_quarantine():
    """List files currently in quarantine."""
    files = []
    if os.path.exists(config.QUARANTINE_FOLDER):
        for fname in sorted(os.listdir(config.QUARANTINE_FOLDER)):
            fpath = os.path.join(config.QUARANTINE_FOLDER, fname)
            stat = os.stat(fpath)
            files.append({
                "name":     fname,
                "size":     stat.st_size,
                "modified": datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M:%S"),
            })
    return jsonify({"files": files, "count": len(files)})


@app.route("/api/scores")
def get_scores():
    """Live risk scores from the detector — for Live Monitoring page."""
    scores = dict(detector.path_scores)
    # Only return non-zero scores
    active = {
        os.path.basename(k): round(v, 1)
        for k, v in scores.items() if v > 0
    }
    return jsonify({
        "active_scores": active,
        "high_threshold":   config.HIGH_THRESHOLD,
        "medium_threshold": config.MEDIUM_THRESHOLD,
        "total_active":     len(active),
    })


@app.route("/api/honeypots")
def get_honeypots():
    """Honeypot file list — for Deception System page."""
    files = []
    for fpath in _honeypot_mgr.honeypot_files:
        exists = os.path.exists(fpath)
        files.append({
            "name":    os.path.basename(fpath),
            "path":    fpath,
            "status":  "Active" if exists else "Triggered/Missing",
            "intact":  exists,
        })
    return jsonify({
        "honeypots":    files,
        "total":        len(files),
        "active_count": sum(1 for f in files if f["intact"]),
    })


@app.route("/api/settings", methods=["POST"])
def update_settings():
    """Toggle auto_quarantine or auto_kill_process."""
    data = request.get_json()
    if not data:
        return jsonify({"success": False, "message": "No data"}), 400

    changed = []
    if "auto_quarantine" in data:
        config.SETTINGS["auto_quarantine"] = bool(data["auto_quarantine"])
        changed.append(f"auto_quarantine = {config.SETTINGS['auto_quarantine']}")

    if "auto_kill_process" in data:
        config.SETTINGS["auto_kill_process"] = bool(data["auto_kill_process"])
        changed.append(f"auto_kill_process = {config.SETTINGS['auto_kill_process']}")

    return jsonify({
        "success":  True,
        "changed":  changed,
        "settings": config.SETTINGS,
    })


@app.route("/api/reset", methods=["POST"])
def reset():
    """Reset all risk scores."""
    detector.reset_scores()
    return jsonify({"success": True, "message": "All scores reset"})


@app.route("/api/logs")
def get_logs():
    """Return last N log lines — for Logs page."""
    limit = int(request.args.get("limit", 100))
    lines = []
    if os.path.exists(config.LOG_FILE):
        with open(config.LOG_FILE, "r", encoding="utf-8") as f:
            lines = f.readlines()
    return jsonify({
        "lines": [l.strip() for l in lines[-limit:]],
        "total": len(lines),
    })


# ── Entry point ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("=" * 60)
    print("🔐 NOVASPHERE API Server")
    print("=" * 60)
    print(f"📍 API running at : http://localhost:5000")
    print(f"📁 Monitoring     : {config.MONITOR_PATH}")
    print("💡 Open your React UI and connect to this API")
    print("=" * 60)
    app.run(debug=True, port=5000, use_reloader=False)

# ── Serve dashboard HTML ──────────────────────────────────────────────────────
STATIC_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")

@app.route("/")
def serve_dashboard():
    """Serve the dashboard HTML — pywebview loads this directly."""
    return send_from_directory(STATIC_DIR, "dashboard.html")
