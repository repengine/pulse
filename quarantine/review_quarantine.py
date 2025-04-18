"""
Script to review and optionally restore files from the quarantine directory.
"""

import os
import shutil

QUARANTINE_DIR = os.path.dirname(__file__)
RESTORE_DIR = os.path.abspath(os.path.join(QUARANTINE_DIR, '..'))

def list_quarantined_files():
    return [f for f in os.listdir(QUARANTINE_DIR) if f.endswith('.py')]

def restore_file(filename: str):
    src = os.path.join(QUARANTINE_DIR, filename)
    dst = os.path.join(RESTORE_DIR, filename)
    shutil.move(src, dst)
    print(f"Restored {filename} to {RESTORE_DIR}")

if __name__ == "__main__":
    files = list_quarantined_files()
    print("Quarantined files:")
    for f in files:
        print(f)
    to_restore = input("Enter filename to restore (or blank to skip): ").strip()
    if to_restore in files:
        restore_file(to_restore)
    else:
        print("No file restored.")