# ransomware_part / simulator.py
"""
Ransomware Simulator - Used ONLY for testing NOVASPHERE.
Creates dummy files and simulates ransomware behavior (renaming to .locked).
"""

import os
import time
import random
from .config import MONITOR_PATH

def create_dummy_files(count=15):
    """Create normal looking files for testing"""
    os.makedirs(MONITOR_PATH, exist_ok=True)
    print(f"Creating {count} dummy files...")
    
    for i in range(count):
        filename = f"project_report_{i+1}.docx"
        filepath = os.path.join(MONITOR_PATH, filename)
        
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(f"This is a test document number {i+1}. " * 30)
        
        print(f"   Created: {filename}")
        time.sleep(0.1)  # Small delay to look natural


def simulate_attack():
    """Simulate ransomware behavior"""
    print("\nStarting Simulated Ransomware Attack...")
    print("This will create files and rename them to look like ransomware.\n")
    
    create_dummy_files(12)
    time.sleep(1.5)
    
    files = [f for f in os.listdir(MONITOR_PATH) if f.endswith(('.docx', '.txt'))]
    random.shuffle(files)
    
    for i, filename in enumerate(files[:8]):        # Encrypt only some files
        old_path = os.path.join(MONITOR_PATH, filename)
        new_path = old_path + ".locked"
        
        try:
            os.rename(old_path, new_path)
            print(f"Simulated Encryption: {filename} → {filename}.locked")
            time.sleep(0.5)   # Realistic delay
        except Exception as e:
            print(f"Error with {filename}: {e}")
    
    print("\nSimulation Completed. Check if NOVASPHERE detected it!\n")


if __name__ == "__main__":
    simulate_attack()