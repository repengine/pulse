#!/usr/bin/env python3
"""Builds/refreshes a symbol‑level index for the Pulse codebase.

The index is stored in two artefacts:
  1.  `vstore/` ‑ Chroma vector DB holding embeddings
  2.  `symbol_index.json` ‑ fast fallback / human‑readable listing

Requires:  pip install tree_sitter_python chromadb openai tqdm

Usage (from repo root):
    python scripts/build_symbol_index.py \
        --repo-path . \
        --db-path vstore \
        --openai-key $OPENAI_API_KEY
"""

from __future__ import annotations
import argparse
import ast
import json
import os
import re
import textwrap
from pathlib import Path
from typing import Dict, List

from tqdm import tqdm
import chromadb
from chromadb.utils.embedding_functions import OpenAIEmbeddingFunction

PY_EXT = re.compile(r"\.py$", re.I)

# --------------------------- AST utilities --------------------------- #


def extract_symbols(path: Path) -> List[Dict]:
    """Return a flat list of symbol dicts from <path>."""
    with path.open("r", encoding="utf8", errors="ignore") as f:
        source = f.read()
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return []
    symbols = []
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            doc = ast.get_docstring(node) or ""
            summ = textwrap.shorten(doc.replace("\n", " "), 120) or "No docstring."
            symbols.append(
                {
                    "name": node.name,
                    "kind": node.__class__.__name__,
                    "path": str(path.relative_to(Path.cwd())),
                    "lineno": node.lineno,
                    "summary": summ,
                }
            )
    return symbols


# --------------------------- Main script ----------------------------- #

ALLOWED_DIRS = {
    "capital_engine",
    "causal_model",
    "core",
    "forecast_engine",
    "intelligence",
    "iris",
    "learning",
    "memory",
    "operator_interface",
    "pipeline",
    "pulse",
    "simulation_engine",
    "symbolic_system",
    "trust_system",
    "utils",
}


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--repo-path", type=str, default=".")
    p.add_argument("--db-path", type=str, default="vstore")
    p.add_argument("--openai-key", type=str, default=os.getenv("OPENAI_API_KEY"))
    p.add_argument("--batch", type=int, default=128)
    args = p.parse_args()

    repo = Path(args.repo_path).resolve()
    files = [
        f
        for f in repo.rglob("*.py")
        if PY_EXT.search(str(f))
        and not any(part.startswith(".") for part in f.parts)
        and any(part in ALLOWED_DIRS for part in f.parts)
    ]

    print(f"📚 Scanning {len(files)} Python files …")
    all_symbols: List[Dict] = []
    for file in tqdm(files):
        all_symbols.extend(extract_symbols(file))

    # Save lightweight JSON for quick grep/debug
    Path("symbol_index.json").write_text(json.dumps(all_symbols, indent=2))
    print(f"✅ Wrote symbol_index.json  ({len(all_symbols)} symbols)")

    # --- vector DB ----------------------------------------------------------------
    if not args.openai_key:
        print("⚠️  OPENAI_API_KEY missing; skipping embedding step.")
        return

    chroma_client = chromadb.Client()
    collection = chroma_client.get_or_create_collection(
        name="pulse-code-index",
        embedding_function=OpenAIEmbeddingFunction(api_key=args.openai_key),
    )

    # Perform a full refresh by deleting and recreating the collection
    chroma_client.delete_collection(name="pulse-code-index")
    collection = chroma_client.get_or_create_collection(
        name="pulse-code-index",
        embedding_function=OpenAIEmbeddingFunction(api_key=args.openai_key),
    )

    for i in range(0, len(all_symbols), args.batch):
        batch = all_symbols[i : i + args.batch]
        texts = [f"{s['kind']} {s['name']} — {s['summary']}" for s in batch]
        ids = [f"{s['path']}:{s['lineno']}" for s in batch]
        metadata = batch
        collection.add(documents=texts, metadatas=metadata, ids=ids)
    print(f"✅ Embedded {len(all_symbols)} symbols into Chroma @ {args.db_path}")


if __name__ == "__main__":
    main()
