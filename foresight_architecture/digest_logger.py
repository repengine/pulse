"""
digest_logger.py

Exports Strategos Digest foresight summaries to disk.

Author: Pulse v0.2
"""

import datetime
import os
from utils.log_utils import get_logger

logger = get_logger(__name__)

def save_digest_to_file(digest: str, tag: str = None):
    stamp = datetime.datetime.utcnow().strftime("%Y-%m-%d_%H-%M")
    filename = f"digest_{tag or stamp}.txt"
    
    folder = os.path.join("pulse", "digests")
    os.makedirs(folder, exist_ok=True)

    full_path = os.path.join(folder, filename)
    with open(full_path, "w", encoding="utf-8") as f:
        f.write(digest)

    logger.info(f"📁 Digest saved to: {full_path}")