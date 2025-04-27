"""
Iris Symbolism Engine

Handles symbolic overlay tagging for signals:
- Maps signals into symbolic categories (hope, despair, rage, fatigue, etc).
- Supports both heuristic and zero-shot inference modes.

Author: Pulse Development Team
Date: 2025-04-27
"""

import logging
from typing import Optional, List

logger = logging.getLogger(__name__)

# Core symbolic archetypes
SYMBOLIC_CATEGORIES = ["hope", "despair", "rage", "fatigue"]

# Attempt to load zero-shot model (optional)
try:
    from transformers import pipeline
    zero_shot_pipeline = pipeline("zero-shot-classification", model="facebook/bart-large-mnli")
except Exception:
    zero_shot_pipeline = None
    logger.warning("[IrisSymbolism] Zero-shot model unavailable. Using fallback tagging.")

class IrisSymbolismTagger:
    def __init__(self):
        """
        Initialize the Iris Symbolism Engine.
        """
        self.symbols = SYMBOLIC_CATEGORIES

    def infer_symbolic_tag(self, signal_name: str) -> str:
        """
        Infer symbolic tag from signal name.

        Args:
            signal_name (str): Name or short description of the signal.

        Returns:
            str: Symbolic category label.
        """
        name_lower = signal_name.lower()

        # Simple heuristic matching first
        for symbol in self.symbols:
            if symbol in name_lower:
                return symbol

        # If no match and zero-shot available, fallback to model
        if zero_shot_pipeline:
            try:
                result = zero_shot_pipeline(signal_name, self.symbols)
                if isinstance(result, dict) and "labels" in result and "scores" in result:
                    if result["scores"][0] > 0.5:
                        return str(result["labels"][0])
            except Exception as e:
                logger.warning("[IrisSymbolism] Zero-shot inference failed: %s", e)

        return "neutral"  # Fallback

    def list_available_symbols(self) -> List[str]:
        """
        List known symbolic categories.

        Returns:
            List[str]: Available symbolic tags.
        """
        return self.symbols
