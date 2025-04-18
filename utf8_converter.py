""" 
utf8_converter.py

Scans and rewrites all .py files in the project to use UTF-8 encoding.
Ignores __init__.py and already valid files.

Author: Pulse v0.20
"""

import os
from utils.log_utils import get_logger

ROOTS = ["dev_tools", "simulation_engine"]

logger = get_logger(__name__)

def convert_to_utf8(filepath):
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            f.read()
        return False  # already UTF-8
    except UnicodeDecodeError:
        pass

    try:
        with open(filepath, 'r', encoding='cp1252', errors='ignore') as f:
            content = f.read()
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        return True
    except Exception as e:
        print(f"❌ Failed to convert {filepath}: {e}")
        return False

def run_conversion():
    converted = 0
    for root in ROOTS:
        for dirpath, _, files in os.walk(root):
            for file in files:
                if file.endswith(".py") and not file.startswith("__"):
                    full = os.path.join(dirpath, file)
                    if convert_to_utf8(full):
                        logger.info(f"✅ Converted to UTF-8: {full}")
                        converted += 1
    if converted == 0:
        logger.info("✅ All .py files already UTF-8 encoded.")
    else:
        logger.info(f"🔁 Total converted: {converted}")

if __name__ == "__main__":
    run_conversion()