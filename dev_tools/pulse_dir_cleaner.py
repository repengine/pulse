"""
pulse_dir_cleaner.py

Scans your Pulse project for:
- Duplicate .py files
- Misplaced module files (outside canonical structure)

Keeps the most recently modified copy in the correct folder.
Moves older or misplaced duplicates into ./quarantine/ for review.

Author: Pulse v0.20

Usage:
    python dev_tools/pulse_dir_cleaner.py [--dry-run] [--quarantine <dir>] [--verbose]

- Add --dry-run to preview actions without moving files
- Add --quarantine to specify quarantine directory
- Add --verbose for more detailed output
- Prints a summary of files checked, duplicates found, and files moved
- Handles errors and logs warnings for file operations
"""

import os
import shutil
from collections import defaultdict
import argparse
from typing import Dict, List
from utils.log_utils import get_logger
from engine.path_registry import PATHS

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
    "pulse_forecast_test_suite.py": "dev_tools/",
}

DEFAULT_QUARANTINE_DIR = PATHS.get("QUARANTINE_DIR", "quarantine")


def find_files() -> Dict[str, List[str]]:
    """
    Find all .py files (excluding __init__) in the project.
    Returns:
        Dict[str, List[str]]: Mapping from filename to list of file paths.
    """
    found = defaultdict(list)
    for root, _, files in os.walk("."):
        for file in files:
            if file.endswith(".py") and not file.startswith("__"):
                full_path = os.path.join(root, file)
                found[file].append(full_path)
    return found


def move_to_quarantine(path: str, quarantine_dir: str, dry_run: bool = False) -> None:
    """
    Move a file to the quarantine directory (or print action if dry-run).
    Args:
        path (str): File path to move.
        quarantine_dir (str): Quarantine directory.
        dry_run (bool): If True, only print action.
    """
    os.makedirs(quarantine_dir, exist_ok=True)
    dest = os.path.join(quarantine_dir, os.path.basename(path))
    if dry_run:
        print(f"[DRY-RUN] Would move to quarantine: {path}")
    else:
        try:
            shutil.move(path, dest)
            print(f"🧼 Moved to quarantine: {path}")
        except Exception as e:
            logger.warning(f"[Cleaner] Failed to move {path} to quarantine: {e}")


def run_cleaner(
    dry_run: bool = False,
    quarantine_dir: str = DEFAULT_QUARANTINE_DIR,
    verbose: bool = False,
) -> None:
    """
    Run the directory cleaner to quarantine duplicates/misplaced files.
    Args:
        dry_run (bool): If True, only print actions.
        quarantine_dir (str): Directory to move quarantined files.
        verbose (bool): Print all files checked.
    """
    logger.info("🧹 Pulse Directory Auto-Cleaner\n")
    all_files = find_files()
    flagged = 0
    files_checked = 0

    for fname, paths in all_files.items():
        canonical_dir = CANONICAL_PATHS.get(fname)
        if not canonical_dir:
            continue
        sorted_paths = sorted(paths, key=lambda p: os.path.getmtime(p), reverse=True)
        newest = sorted_paths[0]
        expected_path = os.path.normpath(os.path.join(".", canonical_dir, fname))
        files_checked += len(paths)

        # Move all but the newest/canonical to quarantine
        for path in sorted_paths[1:]:
            if os.path.abspath(path) != os.path.abspath(expected_path):
                move_to_quarantine(path, quarantine_dir, dry_run)
                flagged += 1

        # If newest isn't in the expected location, move/copy it there
        if not os.path.abspath(newest).startswith(os.path.abspath(expected_path)):
            try:
                os.makedirs(os.path.join(".", canonical_dir), exist_ok=True)
                if dry_run:
                    print(f"[DRY-RUN] Would copy {newest} to {expected_path}")
                else:
                    shutil.copy2(newest, expected_path)
                move_to_quarantine(newest, quarantine_dir, dry_run)
                logger.info(f"📦 Copied most recent '{fname}' to {expected_path}")
                flagged += 1
            except Exception as e:
                logger.warning(f"[Cleaner] Failed to move/copy '{fname}': {e}")
        elif verbose:
            print(f"Checked: {newest}")

    print(
        f"\nSummary: {files_checked} files checked, {flagged} file(s) moved to quarantine."
    )
    if flagged == 0:
        logger.info("✅ No duplicates or misplaced files found.")
    else:
        logger.info(f"🔁 Auto-clean complete. {flagged} file(s) moved to quarantine.")


def parse_args():
    """
    Parse CLI arguments for dry-run, quarantine directory, and verbosity.
    Returns:
        (bool, str, bool): (dry_run, quarantine_dir, verbose)
    """
    parser = argparse.ArgumentParser(description="Pulse Directory Cleaner")
    parser.add_argument(
        "--dry-run", action="store_true", help="Preview actions without moving files"
    )
    parser.add_argument(
        "--quarantine",
        type=str,
        default=DEFAULT_QUARANTINE_DIR,
        help="Quarantine directory",
    )
    parser.add_argument(
        "--verbose", action="store_true", help="Print all files checked"
    )
    args = parser.parse_args()
    return args.dry_run, args.quarantine, args.verbose


if __name__ == "__main__":
    dry_run, quarantine_dir, verbose = parse_args()
    run_cleaner(dry_run=dry_run, quarantine_dir=quarantine_dir, verbose=verbose)
