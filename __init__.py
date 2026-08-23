#ransomware_part / __init__.py

"""
NOVASPHERE - Ransomware Detection Package
Re-exports the main public symbols so frontend pages can do:
   from ransomware_part import path_scores, process_event
   from ransomware_part.detector import RansomwareDetector
"""

from .detector import process_event, path_scores, reset_scores
from .prevention import take_action, suspend_process
from .honeypot import HoneypotManager
from .monitor import RansomwareMonitor

__all__ = [
    "process_event",
    "path_scores",
    "reset_scores",
    "take_action",
    "suspend_process",
    "HoneypotManager",
    "RansomwareMonitor",
]