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

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Digest Exporter CLI")
    parser.add_argument("--input", type=str, required=True, help="Input digest file or string")
    parser.add_argument("--output", type=str, required=True, help="Output file")
    parser.add_argument("--fmt", type=str, default="markdown", choices=["markdown", "json", "html"], help="Export format")
    args = parser.parse_args()
    with open(args.input, "r", encoding="utf-8") as f:
        digest_str = f.read()
    export_digest(digest_str, args.output, fmt=args.fmt)