"""
pulse_autoscan_on_add.py

Monitors key directories for new modules and reruns hook scanner.
Should be run as a background watcher during development.

Author: Pulse v0.10

Usage:
    python dev_tools/pulse_autoscan_on_add.py [--interval SECONDS] [--paths path1 path2 ...]

- Specify watch interval and paths via CLI arguments.
- Prints a summary when a scan is triggered.
- Handles errors in subprocess and file I/O.
"""

import time
import os
import subprocess
import argparse
from typing import List, Dict
from utils.log_utils import get_logger
from engine.path_registry import PATHS

assert isinstance(PATHS, dict), f"PATHS is not a dict, got {type(PATHS)}"

logger = get_logger(__name__)

DEFAULT_WATCH_DIR = PATHS.get("WATCH_DIR", "src")
DEFAULT_WATCH_PATHS = [DEFAULT_WATCH_DIR, "simulation_engine/forecasting"]
CHECKPOINT_FILE = "dev_tools/.last_hook_scan_time"


def get_all_files(paths: List[str]) -> Dict[str, float]:
    """
    Get all .py files (excluding __init__) and their modification times in the given paths.
    Args:
        paths (List[str]): List of directories to scan.
    Returns:
        Dict[str, float]: Mapping from file path to last modified time.
    """
    files = []
    for path in paths:
        for root, _, filenames in os.walk(path):
            for fname in filenames:
                if fname.endswith(".py") and not fname.startswith("__"):
                    full = os.path.join(root, fname)
                    try:
                        files.append((full, os.path.getmtime(full)))
                    except Exception as e:
                        logger.warning(f"[Watcher] Could not stat {full}: {e}")
    return dict(files)


def load_last_time() -> float:
    """
    Load the last scan time from the checkpoint file.
    Returns:
        float: Last scan timestamp, or 0.0 if not found.
    """
    if os.path.exists(CHECKPOINT_FILE):
        try:
            with open(CHECKPOINT_FILE, "r", encoding="utf-8") as f:
                return float(f.read().strip())
        except Exception as e:
            logger.warning(f"[Watcher] Could not read checkpoint: {e}")
    return 0.0


def update_checkpoint(now: float) -> None:
    """
    Update the checkpoint file with the latest scan time.
    Args:
        now (float): Timestamp to write.
    """
    try:
        with open(CHECKPOINT_FILE, "w", encoding="utf-8") as f:
            f.write(str(now))
    except Exception as e:
        logger.warning(f"[Watcher] Could not update checkpoint: {e}")


def parse_args():
    """
    Parse CLI arguments for watch interval and paths.
    Returns:
        (List[str], int): (watch_paths, interval)
    """
    parser = argparse.ArgumentParser(description="Pulse Autoscan On Add")
    parser.add_argument(
        "--interval", type=int, default=3, help="Watch interval in seconds"
    )
    parser.add_argument(
        "--paths", nargs="*", default=DEFAULT_WATCH_PATHS, help="Directories to watch"
    )
    args = parser.parse_args()
    return args.paths, args.interval


if __name__ == "__main__":
    watch_paths, interval = parse_args()
    logger.info(
        f"👁️  Watching for new CLI modules in: {watch_paths} (interval: {interval}s). Ctrl+C to stop."
    )
    last_scan = load_last_time()

    while True:
        time.sleep(interval)
        current_files = get_all_files(watch_paths)
        newest_change = max(current_files.values(), default=0)

        if newest_change > last_scan:
            logger.info(
                f"🔁 Detected new or modified file at {
                    time.ctime(newest_change)}. Running hook scan...")
            try:
                result = subprocess.run(
                    ["python", "dev_tools/pulse_scan_hooks.py"],
                    capture_output=True,
                    text=True,
                )
                if result.returncode == 0:
                    logger.info("[Watcher] Hook scan completed successfully.")
                else:
                    logger.warning(f"[Watcher] Hook scan failed: {result.stderr}")
            except Exception as e:
                logger.warning(f"[Watcher] Error running hook scan: {e}")
            last_scan = newest_change
            update_checkpoint(last_scan)
