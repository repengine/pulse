#!/usr/bin/env python3
"""
sync_module_markdowns.py  ─── READ-PHASE ONLY
• Scans docs/sprint0_module_analysis/<module>.md files listed in
  docs/pulse_inventory.md.
• Writes snapshot to .cache/sync_snapshot.json.
"""

from __future__ import annotations
import argparse
import json
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any
import frontmatter  # pip install python-frontmatter

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
MODULE_MD_DIR = DOCS / "sprint0_module_analysis"
INV_FILE = DOCS / "pulse_inventory.md"
CACHE_DIR = ROOT / ".cache"
CACHE_DIR.mkdir(exist_ok=True)
SNAPSHOT = CACHE_DIR / "sync_snapshot.json"


def parse_inventory() -> List[str]:
    if not INV_FILE.exists():
        return []
    pat = re.compile(r"^- \*\*(.+?)\\.py", re.MULTILINE)
    return sorted({m.group(1) for m in pat.finditer(INV_FILE.read_text())})


def load_module_md(name: str) -> Dict[str, str]:
    md_path = MODULE_MD_DIR / f"{name}.md"
    if not md_path.exists():
        return {}
    post = frontmatter.load(md_path)
    return {
        "purpose": post.get("Module Intent/Purpose", ""),
        "status": post.get("Operational Status/Completeness", ""),
        "gaps": post.get("Implementation Gaps / Unfinished Next Steps", ""),
    }


def build_snapshot() -> Dict[str, Any]:
    snap: Dict[str, Any] = {}
    for mod in parse_inventory():
        if data := load_module_md(mod):
            snap[mod] = data
    snap["_generated_at"] = datetime.utcnow().isoformat()
    return snap


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--ci", action="store_true")
    args = parser.parse_args()

    new_snap = build_snapshot()
    if args.ci and SNAPSHOT.exists():
        if json.loads(SNAPSHOT.read_text()) != new_snap:
            print("Docs & inventory drift detected", file=sys.stderr)
            sys.exit(1)
    SNAPSHOT.write_text(json.dumps(new_snap, indent=2))
    print(f"✅ snapshot written with {len(new_snap) - 1} modules.")


if __name__ == "__main__":
    main()
