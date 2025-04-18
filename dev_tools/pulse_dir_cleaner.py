""" 
pulse_dir_cleaner.py

Scans your Pulse project for:
- Duplicate .py files
- Misplaced module files (outside canonical structure)

Keeps the most recently modified copy in the correct folder.
Moves older or misplaced duplicates into ./quarantine/ for review.

Author: Pulse v0.20
"""

import os
import shutil
from collections import defaultdict
from utils.log_utils import get_logger

logger = get_logger(__name__)

CANONICAL_PATHS = {
    "rule_engine.py": "simulation_engine/",
    "rule_audit_layer.py": "simulation_engine/rules/",
    "forecast_tracker.py": "simulation_engine/forecasting/",
    "forecast_integrity_engine.py": "simulation_engine/forecasting/",
    "pulse_ui_shell.py": ".",
    "pulse_scan_hooks.py": "dev_tools/",
    "pulse_cli_dashboard.py": "dev_tools/",
    "pulse_cli_docgen.py": "dev_tools/",
    "rule_audit_viewer.py": "dev_tools/",
    "pulse_forecast_test_suite.py": "dev_tools/"
}

QUARANTINE_DIR = "quarantine"

def find_files():
    found = defaultdict(list)
    for root, _, files in os.walk("."):
        for file in files:
            if file.endswith(".py") and not file.startswith("__"):
                full_path = os.path.join(root, file)
                found[file].append(full_path)
    return found

def move_to_quarantine(path):
    os.makedirs(QUARANTINE_DIR, exist_ok=True)
    dest = os.path.join(QUARANTINE_DIR, os.path.basename(path))
    shutil.move(path, dest)
    print(f"🧼 Moved to quarantine: {path}")

def run_cleaner():
    logger.info("🧹 Pulse Directory Auto-Cleaner\n")
    all_files = find_files()
    flagged = 0

    for fname, paths in all_files.items():
        canonical_dir = CANONICAL_PATHS.get(fname)
        if not canonical_dir:
            continue

        sorted_paths = sorted(paths, key=lambda p: os.path.getmtime(p), reverse=True)
        newest = sorted_paths[0]
        expected_path = os.path.normpath(os.path.join(".", canonical_dir, fname))

        for path in sorted_paths[1:]:
            if os.path.abspath(path) != os.path.abspath(expected_path):
                move_to_quarantine(path)
                flagged += 1

        if not os.path.abspath(newest).startswith(os.path.abspath(expected_path)):
            try:
                os.makedirs(os.path.join(".", canonical_dir), exist_ok=True)
                shutil.copy2(newest, expected_path)
                move_to_quarantine(newest)
                logger.info(f"📦 Copied most recent '{fname}' to {expected_path}")
                flagged += 1
            except Exception as e:
                logger.warning(f"Failed to move/copy '{fname}': {e}")

    if flagged == 0:
        logger.info("✅ No duplicates or misplaced files found.")
    else:
        logger.info(f"🔁 Auto-clean complete. {flagged} file(s) moved to quarantine.")

if __name__ == "__main__":
    run_cleaner()