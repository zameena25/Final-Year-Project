# file_buffer.py
"""
Temporary buffer for file operations - enables rollback
"""

import os
import shutil
import tempfile
from datetime import datetime
from collections import defaultdict

class FileBuffer:
    def __init__(self, buffer_seconds=5):
        self.buffer = defaultdict(dict)
        self.buffer_seconds = buffer_seconds
    
    def buffer_file(self, file_path):
        """Create a temporary backup before modification"""
        if not os.path.exists(file_path):
            return
        
        # Create temp backup
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.backup')
        shutil.copy2(file_path, temp_file.name)
        
        self.buffer[file_path] = {
            'backup': temp_file.name,
            'timestamp': datetime.now(),
            'original_size': os.path.getsize(file_path)
        }
        
        return temp_file.name
    
    def rollback_file(self, file_path):
        """Restore file from buffer if ransomware detected"""
        if file_path in self.buffer:
            backup_path = self.buffer[file_path]['backup']
            if os.path.exists(backup_path):
                shutil.copy2(backup_path, file_path)
                print(f"🔄 ROLLBACK: Restored {file_path} from buffer")
                return True
        return False
    
    def clear_buffer(self, file_path):
        """Remove buffer after safe period"""
        if file_path in self.buffer:
            backup_path = self.buffer[file_path]['backup']
            if os.path.exists(backup_path):
                os.remove(backup_path)
            del self.buffer[file_path]