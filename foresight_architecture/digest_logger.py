"""
digest_logger.py

Exports Strategos Digest foresight summaries to disk.

Author: Pulse v0.2
"""

import datetime
import os
from utils.log_utils import get_logger
from core.path_registry import PATHS

logger = get_logger(__name__)

def save_digest_to_file(digest: str, tag: str = None) -> None:
    folder = PATHS.get("DIGEST_DIR", os.path.dirname(PATHS["LOG_FILE"]))
    os.makedirs(folder, exist_ok=True)

    if not digest.strip():
        logger.info("No digest to save (empty input).")
        return

    stamp = datetime.datetime.utcnow().strftime("%Y-%m-%d_%H-%M")
    filename = f"digest_{tag or stamp}.txt"
    full_path = os.path.join(folder, filename)
    with open(full_path, "w", encoding="utf-8") as f:
        f.write(digest)

    logger.info(f"📁 Digest saved to: {full_path}")