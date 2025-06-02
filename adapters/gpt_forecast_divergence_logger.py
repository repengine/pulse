"""
gpt_forecast_divergence_logger.py

Logs and tags types of divergence between Pulse and GPT outputs.
Supports curriculum learning and model diagnostics by categorizing divergences (e.g., strategic, narrative inconsistency, variable disagreement).

Core Functions:
- log_forecast_divergence: Logs divergence events with tags and metadata.
- tag_divergence_type: Classifies the type of divergence between Pulse and GPT outputs.
- load_divergence_log: Loads and parses the divergence log for analysis.

Author: [Your Name]
Date: 2025-04-24
"""

from typing import Dict, Any, List, Optional
import json
import datetime

DIVERGENCE_LOG_PATH = "gpt_forecast_divergence_log.jsonl"


def log_forecast_divergence(
    pulse_output: Dict[str, Any],
    gpt_output: Dict[str, Any],
    divergence_type: str,
    metadata: Optional[Dict[str, Any]] = None,
    log_path: str = DIVERGENCE_LOG_PATH,
) -> None:
    """
    Logs a divergence event between Pulse and GPT outputs.

    Args:
        pulse_output (Dict[str, Any]): Output from Pulse.
        gpt_output (Dict[str, Any]): Output from GPT.
        divergence_type (str): Tag for the type of divergence.
        metadata (Dict[str, Any], optional): Additional metadata.
        log_path (str): Path to the divergence log file.
    """
    entry = {
        "timestamp": datetime.datetime.utcnow().isoformat(),
        "pulse_output": pulse_output,
        "gpt_output": gpt_output,
        "divergence_type": divergence_type,
        "metadata": metadata or {},
    }
    with open(log_path, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")


def tag_divergence_type(
    pulse_output: Dict[str, Any], gpt_output: Dict[str, Any]
) -> str:
    """
    Classifies the type of divergence between Pulse and GPT outputs.
    """
    if pulse_output.get("symbolic_tag") != gpt_output.get("symbolic_tag"):
        return "narrative_inconsistency"
    if pulse_output.get("capital_outcome") != gpt_output.get("capital_outcome"):
        return "variable_disagreement"
    if pulse_output.get("rule_trace") != gpt_output.get("rule_trace"):
        return "rule_trace_divergence"
    if pulse_output.get("trust") != gpt_output.get("trust"):
        return "trust_divergence"
    return "strategic"


def load_divergence_log(log_path: str = DIVERGENCE_LOG_PATH) -> List[Dict[str, Any]]:
    """
    Loads the divergence log for analysis.

    Args:
        log_path (str): Path to the divergence log file.

    Returns:
        List[Dict[str, Any]]: List of logged divergence events.
    """
    entries = []
    try:
        with open(log_path, "r", encoding="utf-8") as f:
            for line in f:
                entries.append(json.loads(line))
    except FileNotFoundError:
        pass
    return entries


# Example usage (for testing)
if __name__ == "__main__":
    pulse = {"symbolic_tag": "hope", "capital_outcome": 100}
    gpt = {"symbolic_tag": "despair", "capital_outcome": 90}
    tag = tag_divergence_type(pulse, gpt)
    log_forecast_divergence(pulse, gpt, tag, metadata={"example": True})
    print("Logged divergence type:", tag)
    print("Divergence log entries:", load_divergence_log())
