""" 
utf8_converter.py

Scans and rewrites all .py files in the project to use UTF-8 encoding.
Ignores __init__.py and already valid files.

Author: Pulse v0.20

Usage:
    python utf8_converter.py [--dry-run] [--roots folder1 folder2 ...]

Options:
    --dry-run   Preview files that would be converted, but do not write changes.
    --roots     Specify root folders to scan (default: dev_tools simulation_engine)
"""

import os
import sys
from typing import List
from utils.log_utils import get_logger

ROOTS = ["dev_tools", "simulation_engine"]
logger = get_logger(__name__)

def convert_to_utf8(filepath: str, dry_run: bool = False) -> bool:
    """
    Convert a file to UTF-8 encoding if not already encoded.
    Args:
        filepath (str): Path to the file.
        dry_run (bool): If True, do not write changes.
    Returns:
        bool: True if conversion was performed, False otherwise.
    """
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            f.read()
        return False  # already UTF-8
    except UnicodeDecodeError:
        pass

    try:
        with open(filepath, 'r', encoding='cp1252', errors='ignore') as f:
            content = f.read()
        if not dry_run:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
        return True
    except Exception as e:
        logger.error(f"❌ Failed to convert {filepath}: {e}")
        return False

def run_conversion(roots: List[str] = None, dry_run: bool = False) -> None:
    """
    Scan and convert all .py files in the given roots to UTF-8 encoding.
    Args:
        roots (List[str]): List of root directories to scan.
        dry_run (bool): If True, only preview files to convert.
    """
    if roots is None:
        roots = ROOTS
    converted = 0
    scanned = 0
    for root in roots:
        for dirpath, _, files in os.walk(root):
            for file in files:
                if file.endswith(".py") and not file.startswith("__"):
                    full = os.path.join(dirpath, file)
                    scanned += 1
                    if convert_to_utf8(full, dry_run=dry_run):
                        logger.info(f"✅ Would convert to UTF-8: {full}" if dry_run else f"✅ Converted to UTF-8: {full}")
                        converted += 1
    logger.info(f"🔎 Scanned {scanned} .py files.")
    if converted == 0:
        logger.info("✅ All .py files already UTF-8 encoded.")
    else:
        logger.info(f"🔁 {'Would convert' if dry_run else 'Total converted'}: {converted}")

def parse_args():
    """
    Parse CLI arguments for dry-run and custom roots.
    Returns:
        (List[str], bool): (roots, dry_run)
    """
    import argparse
    parser = argparse.ArgumentParser(description="Pulse UTF-8 Converter")
    parser.add_argument("--dry-run", action="store_true", help="Preview files to convert, do not write changes.")
    parser.add_argument("--roots", nargs="*", default=None, help="Root folders to scan (default: dev_tools simulation_engine)")
    args = parser.parse_args()
    return args.roots, args.dry_run

if __name__ == "__main__":
    roots, dry_run = parse_args()
    run_conversion(roots=roots, dry_run=dry_run)