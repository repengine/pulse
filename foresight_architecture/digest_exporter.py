"""
digest_exporter.py

Exports strategos digest to Markdown, JSON, or HTML.

Usage:
    from digest_exporter import export_digest
    export_digest(digest_str, "out.md", fmt="markdown")

Author: Pulse AI Engine
"""

import json
import logging

logger = logging.getLogger("digest_exporter")

def export_digest(digest_str: str, path: str, fmt: str = "markdown"):
    try:
        with open(path, "w", encoding="utf-8") as f:
            f.write(digest_str)
        logger.info(f"Digest exported to {path}")
    except Exception as e:
        logger.error(f"Export error: {e}")

def export_digest_json(forecast_batch, path: str):
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(forecast_batch, f, indent=2)
        logger.info(f"Digest JSON exported to {path}")
    except Exception as e:
        logger.error(f"Export error: {e}")