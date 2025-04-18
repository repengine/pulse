""" 
pulse_autoscan_on_add.py

Monitors key directories for new modules and reruns hook scanner.
Should be run as a background watcher during development.

Author: Pulse v0.10
"""

import time
import os
import subprocess
import logging
from utils.log_utils import get_logger

logger = get_logger(__name__)

WATCH_PATHS = ["dev_tools", "simulation_engine/forecasting"]
CHECKPOINT_FILE = "dev_tools/.last_hook_scan_time"

def get_all_files(paths):
    files = []
    for path in paths:
        for root, _, filenames in os.walk(path):
            for fname in filenames:
                if fname.endswith(".py") and not fname.startswith("__"):
                    full = os.path.join(root, fname)
                    files.append((full, os.path.getmtime(full)))
    return dict(files)

def load_last_time():
    if os.path.exists(CHECKPOINT_FILE):
        with open(CHECKPOINT_FILE, "r", encoding="utf-8") as f:
            return float(f.read().strip())
    return 0.0

def update_checkpoint(now):
    with open(CHECKPOINT_FILE, "w", encoding="utf-8") as f:
        f.write(str(now))

if __name__ == "__main__":
    logger.info("👁️  Watching for new CLI modules... Ctrl+C to stop.")
    last_scan = load_last_time()

    while True:
        time.sleep(3)
        current_files = get_all_files(WATCH_PATHS)
        newest_change = max(current_files.values(), default=0)

        if newest_change > last_scan:
            logger.info("🔁 Detected new or modified file. Running hook scan...")
            subprocess.run(["python", "dev_tools/pulse_scan_hooks.py"])
            last_scan = newest_change
            update_checkpoint(last_scan)