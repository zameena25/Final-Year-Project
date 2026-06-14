#monitoring/models.py
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

@dataclass
class FileEvent:
    event_type: str
    file_path:str
    timestamp: str
    file_extension: str
    file_size: int
    username: Optional[str] = None
    process_name: Optional[str] = None
    event_source: str = "file_monitor"

    def to_dict(self):
        return self.__dict__
    
