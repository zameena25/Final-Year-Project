# NovaSphere Testing Guide

## Before Testing

1. Close any running NovaSphere instances.
2. Start the application from the project root:

```powershell
python app.py
```

3. Wait for the dashboard to open. The startup output should include both monitoring services with no errors.
4. Do not use personal documents for attack tests. The included simulations use `test_folder` only.

## Automated Regression Tests

Run this after every code change that touches detection, alerts, scanning, or the dashboard:

```powershell
python -m unittest discover -s tests -v
```

The suite verifies that ransomware detections create structured alerts, the Alerts page can load them, and Live Monitoring can load high/critical findings.

## Manual Test Cases (Module-wise)

### Authentication Module (`auth/`)

| ID | Scenario | Steps | Expected Result | Evidence |
|---|---|---|---|---|
| TC-A1 | Valid login | Enter correct credentials and submit. | User reaches the dashboard. | Screenshot. |
| TC-A2 | Two-factor verification | Log in, then enter the TOTP code. | Access granted only after the correct code is entered. | Screenshot. |

### Monitoring & Detection Module (`src/monitoring/`, `ransomware_part/`)

| ID | Scenario | Steps | Expected Result | Evidence |
|---|---|---|---|---|
| TC-M1 | Application monitoring starts | Launch NovaSphere and leave it open. | Both file-system and ransomware monitoring start without errors. | Console startup output. |
| TC-M2 | Rapid file activity | With NovaSphere open, run `python src/simulate_attack.py`. | A `RAPID_FILE_ACTIVITY` alert is persisted after the configured burst threshold. | Alerts page and `python verify_alerts.py`. |
| TC-M3 | Ransomware extension detection | With NovaSphere open, run `python -m ransomware_part.simulator`. | `.locked` file activity creates a `RANSOMWARE_DETECTED` high-risk alert. | Alerts page, Live Monitoring feed, and database query. |
| TC-M4 | Honeypot detection | Modify one bait file listed in `logs/honeypots.json`. | A `HONEYPOT_TRIGGERED` critical alert appears. | Alerts page, Live Monitoring, and database query. |
| TC-M5 | False-positive control | Create one ordinary `.txt` file in `test_folder`. | No high/critical alert is created. | `python verify_alerts.py` before/after comparison. |

### Alerting Module (`alerting/`)

| ID | Scenario | Steps | Expected Result | Evidence |
|---|---|---|---|---|
| TC-AL1 | Alert persistence | Trigger any detection (e.g. TC-M3). | The alert row in `logs/novasphere.db` has a timestamp, alert type, severity, source, and affected file path. | Database query. |
| TC-AL2 | Manual scan integration | Run a scan from the dashboard. | Each suspicious file is persisted as an alert; Alerts and Live Monitoring refresh after completion. | Scan result and UI screenshots. |

### Dashboard Module (`frontend/`)

| ID | Scenario | Steps | Expected Result | Evidence |
|---|---|---|---|---|
| TC-D1 | Live Monitoring updates | Repeat TC-M3 while the Live Monitoring page is open. | Within 2 seconds, the event feed and high-risk counters update. | Screenshot or screen recording. |
| TC-D2 | Alerts page updates | Repeat TC-M3 while Alerts is open. | The new alert appears within 30 seconds; navigating away and back refreshes it immediately. | Screenshot and database query. |

## Commands and Expected Evidence

Run the general attack simulation:

```powershell
python src/simulate_attack.py
```

Run the ransomware-specific simulation:

```powershell
python -m ransomware_part.simulator
```

Inspect the ten most recent persisted alerts:

```powershell
python verify_alerts.py
```

Inspect only ransomware and honeypot alerts:

```powershell
python -c "import sqlite3; c=sqlite3.connect('logs/novasphere.db'); print(*c.execute(\"SELECT timestamp, alert_type, severity, file_path FROM alerts WHERE source='ransomware_detector' ORDER BY rowid DESC LIMIT 10\"), sep='\n')"
```

## Pass Criteria

- All test cases pass on a clean application restart.
- TC-M5 produces no high or critical alert.
- Every detected simulation event has a timestamp, alert type, severity, source, and affected file path in `logs/novasphere.db`.
- The same alert is visible on both Alerts and Live Monitoring.

## Test Record Template

Use this table in your project report for each execution.

| Test ID | Date | Tester | Build | Result | Notes / Evidence |
|---|---|---|---|---|---|
| TC-A1 | | | | Pass / Fail | |
| TC-A2 | | | | Pass / Fail | |
| TC-M1 | | | | Pass / Fail | |
| TC-M2 | | | | Pass / Fail | |
| TC-M3 | | | | Pass / Fail | |
| TC-M4 | | | | Pass / Fail | |
| TC-M5 | | | | Pass / Fail | |
| TC-AL1 | | | | Pass / Fail | |
| TC-AL2 | | | | Pass / Fail | |
| TC-D1 | | | | Pass / Fail | |
| TC-D2 | | | | Pass / Fail | |
