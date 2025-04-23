import os
import tempfile
from output.digest_exporter import export_digest

def test_export_markdown():
    with tempfile.NamedTemporaryFile(delete=False) as f:
        export_digest("# Test", f.name, fmt="markdown")
        with open(f.name) as fin:
            assert "# Test" in fin.read()
    os.remove(f.name)

def test_export_html_fallback():
    with tempfile.NamedTemporaryFile(delete=False) as f:
        export_digest("# Test", f.name, fmt="html")
        with open(f.name) as fin:
            content = fin.read()
            assert "<pre>" in content or "<h1>" in content
    os.remove(f.name)
