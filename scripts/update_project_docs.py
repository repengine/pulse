#!/usr/bin/env python3
"""
update_project_docs.py  ─── WRITE-PHASE
• Consumes .cache/sync_snapshot.json
• Updates docs/sprint0_module_analysis/<module>.md front-matter
• Ensures docs/pulse_inventory.md lists every module
• Regenerates module_deps.dot via scripts/mk_deps.py (if present)
"""
from __future__ import annotations
import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict
import frontmatter

ROOT   = Path(__file__).resolve().parents[1]
DOCS   = ROOT / "docs"
MODULE_MD_DIR = DOCS / "sprint0_module_analysis"
INV_FILE      = DOCS / "pulse_inventory.md"
DOT_FILE      = ROOT / "module_deps.dot"
CACHE_FILE    = ROOT / ".cache" / "sync_snapshot.json"
PLANNING_DIR  = DOCS / "planning"

def ts() -> str:
    return datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")

def ensure_module_md(name: str, data: Dict[str, str]) -> None:
    MODULE_MD_DIR.mkdir(parents=True, exist_ok=True)
    md_path = MODULE_MD_DIR / f"{name}.md"
    post = frontmatter.load(md_path) if md_path.exists() else frontmatter.Post("")
    post["Module Intent/Purpose"] = data["purpose"] or post.get("Module Intent/Purpose", "")
    post["Operational Status/Completeness"] = data["status"] or post.get("Operational Status/Completeness", "")
    post["Implementation Gaps / Unfinished Next Steps"] = data["gaps"] or post.get("Implementation Gaps / Unfinished Next Steps", "")
    post["last_updated"] = ts()
    md_path.write_text(frontmatter.dumps(post))

def ensure_inventory(modules: list[str]) -> None:
    lines = INV_FILE.read_text().splitlines() if INV_FILE.exists() else ["# Pulse Module Inventory\n"]
    existing = {line.split("**")[1].split(".py")[0] for line in lines if line.startswith("- **")}
    with INV_FILE.open("a") as f:
        for m in modules:
            if m not in existing:
                f.write(f"- **{m}.py**  — added {ts()}\n")

def regenerate_dot() -> None:
    mk_deps = ROOT / "scripts" / "mk_deps.py"
    if mk_deps.exists():
        subprocess.run([sys.executable, str(mk_deps)], check=False)
    else:
        DOT_FILE.write_text("// placeholder: mk_deps.py not found\n")

def main() -> None:
    if not CACHE_FILE.exists():
        print("Snapshot missing; run sync_module_markdowns.py first", file=sys.stderr)
        sys.exit(1)
    snap: Dict[str, Dict[str, str]] = json.loads(CACHE_FILE.read_text())
    modules = [m for m in snap if not m.startswith("_")]

    for mod in modules:
        ensure_module_md(mod, snap[mod])
    ensure_inventory(modules)
    regenerate_dot()

    print(f"✅ docs & inventory updated for {len(modules)} modules.")

if __name__ == "__main__":
    main()
