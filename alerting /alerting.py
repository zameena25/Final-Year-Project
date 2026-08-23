#alerting / alerting.py
"""
NOVASPHERE Unified Alerting System
Single source of truth for all alerts — file monitoring, detection, prevention, and API.

Usage across your system:
    from alerts import alert, get_alerts, filter_alerts, subscribe

    # Dispatch alert from any module (file_monitor, detector, prevention, etc.)
    alert("RAPID_FILE_ACTIVITY", {"username": "alice", "path": "/tmp"})
    
    # Query alerts from API or dashboard
    recent = get_alerts(limit=50)
    high_severity = filter_alerts(severity="HIGH")
    
    # Real-time updates (WebSocket, live dashboard)
    subscribe(callback_function)
"""

from datetime import datetime
from pathlib import Path
from typing import Optional, Callable, List
import json
import threading

# ============================================================================
# CONFIGURATION
# ============================================================================

_BASE = Path(__file__).parent
ALERT_LOG = _BASE / "logs" / "alerts.jsonl"

# Alert severity mapping
_SEVERITY_MAP = {
    "HIGH": [
        "RAPID_FILE_ACTIVITY",
        "MASS_EXTENSION_CHANGE",
        "RANSOMWARE_DETECTED",
        "CRITICAL_FILE_ACCESS"
    ],
    "MED": [
        "UNAUTHORIZED_ACCESS",
        "SUSPICIOUS_PROCESS",
        "PRIVILEGE_ESCALATION",
        "UNUSUAL_BEHAVIOR"
    ],
    "LOW": [
        "NORMAL_FILE_ACTIVITY",
        "INFO",
        "DEBUG"
    ]
}

# ============================================================================
# CORE ALERTING ENGINE
# ============================================================================

_SUBSCRIBERS = []
_LOCK = threading.RLock()  # Thread-safe alert dispatching


def _get_severity(alert_type: str) -> str:
    """Map alert type to severity level."""
    for severity, types in _SEVERITY_MAP.items():
        if alert_type in types:
            return severity
    return "LOW"


def _ensure_log_dir():
    """Create logs directory if it doesn't exist."""
    ALERT_LOG.parent.mkdir(parents=True, exist_ok=True)


def alert(
    alert_type: str,
    details: dict,
    source: str = "system"
) -> dict:
    """
    Send an alert from anywhere in the system.
    
    This is the ONLY function detection modules should call.
    Works for file_monitor, detector, prevention, and any other component.
    
    Args:
        alert_type (str): One of RAPID_FILE_ACTIVITY, MASS_EXTENSION_CHANGE,
                          UNAUTHORIZED_ACCESS, SUSPICIOUS_PROCESS, RANSOMWARE_DETECTED, etc.
        details (dict): Context dictionary (must include "username" and/or "path")
        source (str): Which module triggered this ("file_monitor", "detector", "prevention", etc.)
    
    Returns:
        alert_record (dict): The complete alert that was written
    
    Examples:
        # From file_monitor
        alert("RAPID_FILE_ACTIVITY", {"username": "alice", "path": "/home/alice/docs", "count": 45})
        
        # From detector
        alert("UNAUTHORIZED_ACCESS", {"username": "bob", "path": "/etc/passwd"}, source="detector")
        
        # From prevention
        alert("RANSOMWARE_DETECTED", {"username": "charlie", "process": "encrypt.exe"}, source="prevention")
    """
    
    with _LOCK:
        severity = _get_severity(alert_type)
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Build alert record
        alert_record = {
            "timestamp": timestamp,
            "alert_type": alert_type,
            "severity": severity,
            "source": source,
            "username": details.get("username", "System"),
            "path": details.get("path", ""),
            "details": details,
        }
        
        # Console output
        print(f"\n ⚠️  ALERT [{severity}] - {alert_type}")
        print(f"    Source: {source}")
        print(f"    User: {alert_record['username']}")
        if alert_record['path']:
            print(f"    Path: {alert_record['path']}")
        print(f"    Details: {details}")
        print(f"    Time: {timestamp}\n")
        
        # Write to JSONL log
        _ensure_log_dir()
        try:
            with open(ALERT_LOG, "a") as f:
                f.write(json.dumps(alert_record) + "\n")
        except OSError as e:
            print(f"❌ Failed to save alert to log: {e}")
        
        # Notify live subscribers (API WebSockets, dashboard, etc.)
        for callback in _SUBSCRIBERS:
            try:
                callback(alert_record)
            except Exception as e:
                print(f"❌ Subscriber error: {e}")
        
        return alert_record


# ============================================================================
# QUERY FUNCTIONS (FOR API & DASHBOARD)
# ============================================================================

def get_alerts(limit: int = 50) -> List[dict]:
    """
    Fetch the most recent alerts.
    
    Args:
        limit (int): Number of alerts to return (newest first)
    
    Returns:
        list of alert dicts
    
    Example:
        @app.route("/api/alerts")
        def get_dashboard_alerts():
            alerts = get_alerts(limit=100)
            return {"alerts": alerts}
    """
    if not ALERT_LOG.exists():
        return []
    
    alerts = []
    try:
        with open(ALERT_LOG, "r") as f:
            for line in f:
                if line.strip():
                    alerts.append(json.loads(line))
    except Exception as e:
        print(f"❌ Error reading alert log: {e}")
        return []
    
    # Return newest first
    return alerts[-limit:][::-1]


def filter_alerts(
    severity: Optional[str] = None,
    source: Optional[str] = None,
    alert_type: Optional[str] = None,
    limit: int = 50
) -> List[dict]:
    """
    Filter alerts by severity, source, or type.
    
    Args:
        severity (str): "HIGH", "MED", "LOW" (optional)
        source (str): "file_monitor", "detector", "prevention", etc. (optional)
        alert_type (str): "RAPID_FILE_ACTIVITY", "RANSOMWARE_DETECTED", etc. (optional)
        limit (int): Max results to return
    
    Returns:
        list of matching alert dicts (newest first)
    
    Examples:
        # Get all HIGH severity alerts
        critical = filter_alerts(severity="HIGH", limit=50)
        
        # Get all ransomware alerts
        ransomware = filter_alerts(alert_type="RANSOMWARE_DETECTED")
        
        # Get all alerts from file_monitor
        file_alerts = filter_alerts(source="file_monitor", limit=100)
    """
    all_alerts = get_alerts(limit * 3)  # Over-fetch to ensure we get enough matches
    
    filtered = all_alerts
    
    if severity:
        filtered = [a for a in filtered if a.get("severity") == severity]
    if source:
        filtered = [a for a in filtered if a.get("source") == source]
    if alert_type:
        filtered = [a for a in filtered if a.get("alert_type") == alert_type]
    
    return filtered[:limit]


def get_alert_stats() -> dict:
    """
    Get summary statistics of all alerts.
    
    Returns:
        dict with counts by severity, source, and type
    
    Example:
        @app.route("/api/alert-stats")
        def stats():
            return get_alert_stats()
    """
    all_alerts = get_alerts(limit=10000)
    
    stats = {
        "total": len(all_alerts),
        "by_severity": {
            "HIGH": len([a for a in all_alerts if a.get("severity") == "HIGH"]),
            "MED": len([a for a in all_alerts if a.get("severity") == "MED"]),
            "LOW": len([a for a in all_alerts if a.get("severity") == "LOW"]),
        },
        "by_source": {},
        "by_type": {},
        "latest_timestamp": all_alerts[0].get("timestamp") if all_alerts else None,
    }
    
    for alert_rec in all_alerts:
        src = alert_rec.get("source", "unknown")
        typ = alert_rec.get("alert_type", "unknown")
        stats["by_source"][src] = stats["by_source"].get(src, 0) + 1
        stats["by_type"][typ] = stats["by_type"].get(typ, 0) + 1
    
    return stats


# ============================================================================
# REAL-TIME SUBSCRIPTIONS (FOR WEBSOCKETS, LIVE DASHBOARDS)
# ============================================================================

def subscribe(callback: Callable):
    """
    Register a callback to receive live alerts in real-time.
    
    The callback will be called synchronously each time an alert is dispatched.
    
    Args:
        callback: Callable that takes one argument (alert_record dict)
    
    Example (Flask + Server-Sent Events):
        from flask import Response
        
        def alert_stream():
            def on_alert(alert_record):
                yield f"data: {json.dumps(alert_record)}\\n\\n"
            
            alerts.subscribe(on_alert)
            while True:
                time.sleep(1)  # Keep connection alive
        
        @app.route("/stream/alerts")
        def stream_alerts():
            return Response(alert_stream(), mimetype="text/event-stream")
    """
    with _LOCK:
        if callback not in _SUBSCRIBERS:
            _SUBSCRIBERS.append(callback)


def unsubscribe(callback: Callable):
    """Unregister a callback."""
    with _LOCK:
        if callback in _SUBSCRIBERS:
            _SUBSCRIBERS.remove(callback)


def get_subscribers_count() -> int:
    """Get number of active subscribers (for monitoring)."""
    return len(_SUBSCRIBERS)


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def clear_logs():
    """
    DANGEROUS: Erase all alert logs. Use only for testing/development.
    """
    if ALERT_LOG.exists():
        ALERT_LOG.unlink()
        print("✓ Alert logs cleared.")


def export_alerts(filepath: str, format: str = "json") -> bool:
    """
    Export all alerts to a file.
    
    Args:
        filepath (str): Where to save exported alerts
        format (str): "json" (list) or "jsonl" (one per line)
    
    Returns:
        bool: Success status
    
    Example:
        export_alerts("/tmp/alerts.json", format="json")
    """
    try:
        all_alerts = get_alerts(limit=100000)
        
        with open(filepath, "w") as f:
            if format == "json":
                json.dump(all_alerts, f, indent=2)
            else:  # jsonl
                for alert_rec in all_alerts:
                    f.write(json.dumps(alert_rec) + "\n")
        
        print(f"✓ Exported {len(all_alerts)} alerts to {filepath}")
        return True
    except Exception as e:
        print(f"❌ Export failed: {e}")
        return False


# ============================================================================
# INITIALIZATION
# ============================================================================

_ensure_log_dir()

if __name__ == "__main__":
    # Demo/test
    alert("RAPID_FILE_ACTIVITY", {"username": "alice", "path": "/home/alice", "count": 100})
    alert("RANSOMWARE_DETECTED", {"username": "bob", "process": "encrypt.exe"})
    alert("LOW", {"username": "charlie"})
    
    print("\n--- Recent Alerts ---")
    for a in get_alerts(limit=10):
        print(f"  [{a['severity']}] {a['alert_type']} @ {a['timestamp']}")
    
    print("\n--- Stats ---")
    print(get_alert_stats())
