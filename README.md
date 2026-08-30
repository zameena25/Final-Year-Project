# NOVASPHERE

**Offline Ransomware Detection & Insider Threat Prevention System**

NOVASPHERE is a Windows-based security system built to solve a problem most modern tools ignore — what happens when there's no internet? Signature-based antivirus struggles against new ransomware variants, most security tools rely heavily on cloud connectivity and insider misuse often slips past traditional perimeter defenses.

NOVASPHERE runs entirely offline. It watches file and process activity in real time, scores suspicious behavior using weighted heuristics, and automatically responds — no internet or cloud dependency required.

This was built as our final year capstone project (NIT3004) by a team of 4.

---

## Key Features

- **Behavioral Ransomware Detection** — weighted scoring engine using extension checks, ransom note pattern matching, burst activity, deletion spikes, and rapid repeat edits
- **Insider Threat Detection** — process/command inspection and honeypot decoy files to catch misuse early
- **Automated Response** — quarantine and rollback triggered the moment a threat is confirmed
- **Live Monitoring Dashboard** — real-time visibility into system activity and alerts
- **Role-Based Access Control (RBAC)**
- **100% Offline** — zero reliance on cloud threat intelligence

---

## Testing & Results

- Tested against 50 simulated attack scenarios (extension rename, ransom note drop, deletion spikes, insider command patterns)
- **48/50** attacks correctly detected
- **1.5%** false positive rate (after tuning)
- **< 1.2 seconds** average detection response time

---

## Tech Stack

`Python` · `PyQt6` · `Flask` · `SQLite`

---

## Future Work

- Machine Learning-based anomaly scoring
- Cross-platform support (Linux/Mac)
- Optional cloud threat-intelligence sync for hybrid deployments

---

## Team

Built by Team J as part of our final year capstone.
