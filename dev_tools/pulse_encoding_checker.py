"""
pulse_encoding_checker.py

Scans all Python files in the Pulse project for encoding issues.
Flags files that can't be read as UTF-8.

Author: Pulse v0.20
"""

import os
from utils.log_utils import get_logger

logger = get_logger(__name__)

SEARCH_PATHS = [
    "dev_tools",
    "simulation_engine/forecasting",
    "simulation_engine/rules",
    "simulation_engine",
]


def check_file_encoding(filepath):
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            f.read()
        return True
    except UnicodeDecodeError:
        return False
    except Exception:
        return False


def scan_for_encoding_issues():
    failed_files = []

    for base_path in SEARCH_PATHS:
        for root, _, files in os.walk(base_path):
            for fname in files:
                if fname.endswith(".py") and not fname.startswith("__"):
                    fpath = os.path.join(root, fname)
                    if not check_file_encoding(fpath):
                        failed_files.append(fpath)

    if not failed_files:
        logger.info("✅ All .py files passed UTF-8 encoding check.")
    else:
        logger.warning(f"⚠️ Found {len(failed_files)} file(s) with encoding issues:")
        for f in failed_files:
            logger.warning(f" - {f}")


if __name__ == "__main__":
    scan_for_encoding_issues()
