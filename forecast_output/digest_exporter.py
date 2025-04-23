"""
digest_exporter.py

Exports strategos digest to Markdown, JSON, HTML, or PDF.

Usage:
    from forecast_output.digest_exporter import export_digest
    export_digest(digest_str, "out.md", fmt="markdown")
    export_digest(digest_str, "out.pdf", fmt="pdf")
    export_digest(digest_str, "out.html", fmt="html", sanitize_html=True)

    # If exporting HTML, set sanitize_html=True to clean output (requires bleach)

Author: Pulse AI Engine
"""

import warnings
warnings.warn(
    "foresight_architecture.digest_exporter is deprecated. Use forecast_output.digest_exporter instead.",
    DeprecationWarning,
    stacklevel=2
)

import json
import logging

logger = logging.getLogger("digest_exporter")

def export_digest(digest_str: str, path: str, fmt: str = "markdown", sanitize_html: bool = False) -> None:
    """
    Export digest string to file in the specified format.
    Supported formats: markdown, html, pdf (stub).
    If exporting as HTML and markdown2 is available, will convert Markdown to HTML.
    If sanitize_html is True, will sanitize HTML output using bleach (if installed).
    """
    try:
        if fmt == "pdf":
            export_digest_pdf(digest_str, path)
        elif fmt == "html":
            try:
                import markdown2
                html = markdown2.markdown(digest_str)
                if sanitize_html:
                    try:
                        import bleach
                        html = bleach.clean(html, tags=bleach.sanitizer.ALLOWED_TAGS + ["h1", "h2", "h3"], strip=True)
                    except ImportError:
                        logger.warning("bleach not installed, HTML not sanitized.")
                with open(path, "w", encoding="utf-8") as f:
                    f.write(html)
                logger.info(f"Digest HTML exported to {path}")
            except ImportError:
                with open(path, "w", encoding="utf-8") as f:
                    f.write("<pre>\n" + digest_str + "\n</pre>")
                logger.info(f"Digest HTML exported to {path} (preformatted, markdown2 not installed)")
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
# export_digest("# Digest\n...", "digest.html", fmt="html", sanitize_html=True)
