"""
digest_exporter.py

Exports strategos digest to Markdown, JSON, HTML, or PDF.

Usage:
    from digest_exporter import export_digest
    export_digest(digest_str, "out.md", fmt="markdown")
    export_digest(digest_str, "out.pdf", fmt="pdf")

Author: Pulse AI Engine
"""

import json
import logging

logger = logging.getLogger("digest_exporter")

def export_digest(digest_str: str, path: str, fmt: str = "markdown"):
    """
    Export digest string to file in the specified format.
    Supported formats: markdown, html, pdf (stub).
    """
    try:
        if fmt == "pdf":
            export_digest_pdf(digest_str, path)
        else:
            with open(path, "w", encoding="utf-8") as f:
                f.write(digest_str)
            logger.info(f"Digest exported to {path}")
    except Exception as e:
        logger.error(f"Export error: {e}")

def export_digest_json(forecast_batch, path: str):
    """
    Export forecast batch as JSON.
    """
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(forecast_batch, f, indent=2)
        logger.info(f"Digest JSON exported to {path}")
    except Exception as e:
        logger.error(f"Export error: {e}")

def export_digest_pdf(digest_str: str, path: str):
    """
    Export digest as PDF (stub).
    """
    try:
        # TODO: Integrate ReportLab or WeasyPrint for real PDF export
        with open(path, "w", encoding="utf-8") as f:
            f.write("PDF export not implemented.\n\n")
            f.write(digest_str)
        logger.info(f"Digest PDF (stub) exported to {path}")
    except Exception as e:
        logger.error(f"PDF export error: {e}")

# Example usage:
# export_digest("# Digest\n...", "digest.md", fmt="markdown")
# export_digest_json([{"trace_id": "t1"}], "digest.json")
