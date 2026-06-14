# 🛡️ NOVASPHERE

> Real-time ransomware detection and insider threat prevention through behavioral file system analysis.

![Python](https://img.shields.io/badge/Python-3.10+-blue?style=flat-square&logo=python)
![Status](https://img.shields.io/badge/Status-In%20Development-orange?style=flat-square)
![License](https://img.shields.io/badge/License-MIT-green?style=flat-square)

---

## What is NOVASPHERE?

NOVASPHERE is a behavioral cybersecurity system designed to detect and prevent
ransomware attacks and insider threats in real time. Unlike traditional
signature-based antivirus tools, NOVASPHERE continuously monitors file
activities, user behavior, and system processes identifying suspicious
patterns before serious damage occurs.

---

## Core Features

| Feature | Description |
|---|---|
| 🔍 Real-time file monitoring | Tracks file creation, modification, deletion, and renaming |
| 🧠 Behavioral detection | Identifies ransomware-like activity through pattern analysis |
| ⚡ Burst alert system | Sliding window detector fires when rapid file activity is detected |
| 📋 JSONL event logging | Every event is persisted in structured logs for audit and review |
| 🔗 Heuristic engine integration | Event buffers are forwarded to the analysis engine automatically |
| 🚨 Insider threat detection | Flags abnormal access patterns and unauthorized activity |

---