# symbolic/pulse_symbolic_learning_loop.py

"""
Pulse Symbolic Learning Loop

Learns symbolic strategy preferences based on revision logs and repair outcomes.
Tracks which arcs/tags are recoverable, risky, or should be revised faster.

Author: Pulse AI Engine
Version: v1.0.0
"""

import json
import os
import logging
from typing import Dict, List

LEARNING_LOG_PATH = "logs/symbolic_learning_log.jsonl"

logger = logging.getLogger("pulse_symbolic_learning_loop")
logging.basicConfig(level=logging.INFO)


def learn_from_tuning_log(path: str) -> List[Dict]:
    """
    Load tuning results and return raw entries.

    Args:
        path: JSONL log file from tuning engine

    Returns:
        List of dicts
    """
    if not isinstance(path, str):
        logger.warning("Input path is not a string.")
        return []
    if not path.endswith(".jsonl"):
        logger.warning(f"Input file {path} does not have .jsonl extension.")
    if not os.path.exists(path):
        logger.warning(f"Tuning log file not found: {path}")
        return []
    results = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
                if isinstance(obj, dict):
                    results.append(obj)
                else:
                    logger.warning(f"Non-dict entry in {path}: {obj}")
            except json.JSONDecodeError as e:
                logger.error(f"Malformed JSON in {path}: {e}")
    return results


def score_symbolic_paths(results: List[Dict]) -> Dict[str, Dict[str, int]]:
    """
    Return symbolic tag/arc success vs failure counts.

    Args:
        results: List of tuning result dicts

    Returns:
        {
            "arc_label": {"success": x, "fail": y},
            "symbolic_tag": {...}
        }
    """
    if not isinstance(results, list):
        logger.warning("Input results is not a list.")
        return {"arc_label": {}, "symbolic_tag": {}}
    arc_scores = {}
    tag_scores = {}

    for r in results:
        if not isinstance(r, dict):
            continue
        plan = r.get("symbolic_revision_plan", {})
        arc = plan.get("arc_label")
        tag = plan.get("symbolic_tag")
        success = r.get("revised_license") == "✅ Approved"

        if arc:
            arc_scores.setdefault(arc, {"success": 0, "fail": 0})
            arc_scores[arc]["success" if success else "fail"] += 1

        if tag:
            tag_scores.setdefault(tag, {"success": 0, "fail": 0})
            tag_scores[tag]["success" if success else "fail"] += 1

    return {"arc_label": arc_scores, "symbolic_tag": tag_scores}


def generate_learning_profile(results: List[Dict]) -> Dict:
    """
    Output symbolic strengths and weaknesses for future tuning.

    Args:
        results: List of tuning result dicts

    Returns:
        Dict profile with high-confidence upgrades and risk flags
    """
    if not isinstance(results, list):
        logger.warning("Input results is not a list.")
        return {}
    if not results:
        logger.warning("No tuning results provided to generate_learning_profile.")
        return {
            "arc_performance": {},
            "tag_performance": {},
            "last_updated": None,
            "total_records": 0,
        }
    scores = score_symbolic_paths(results)

    def rank(entries):
        ranked = {}
        for k, v in entries.items():
            total = v["success"] + v["fail"]
            win_rate = round(v["success"] / total, 2) if total else 0.0
            ranked[k] = {"rate": win_rate, "total": total}
        return dict(sorted(ranked.items(), key=lambda x: -x[1]["rate"]))

    return {
        "arc_performance": rank(scores["arc_label"]),
        "tag_performance": rank(scores["symbolic_tag"]),
        "last_updated": results[-1].get("timestamp") if results else None,
        "total_records": len(results),
    }


def log_symbolic_learning(profile: Dict, path: str = LEARNING_LOG_PATH):
    """
    Save the learning profile to disk.

    Args:
        profile: learning profile dict
        path: output file path
    """
    if not isinstance(profile, dict):
        logger.error("Profile is not a dict, cannot log.")
        return
    try:
        with open(path, "a", encoding="utf-8") as f:
            f.write(json.dumps(profile, ensure_ascii=False) + "\n")
        logger.info(f"📚 Symbolic learning profile saved to {path}")
    except Exception as e:
        logger.error(f"Failed to log learning profile: {e}")


def _test_symbolic_learning_loop():
    """Basic test for symbolic learning loop."""
    # Simulate a few tuning results
    dummy_results = [
        {
            "symbolic_revision_plan": {
                "arc_label": "Hope Surge",
                "symbolic_tag": "optimism",
            },
            "revised_license": "✅ Approved",
            "timestamp": "2024-06-01T12:00:00",
        },
        {
            "symbolic_revision_plan": {
                "arc_label": "Hope Surge",
                "symbolic_tag": "optimism",
            },
            "revised_license": "❌ Rejected",
            "timestamp": "2024-06-01T12:01:00",
        },
        {
            "symbolic_revision_plan": {
                "arc_label": "Collapse Risk",
                "symbolic_tag": "fear",
            },
            "revised_license": "❌ Rejected",
            "timestamp": "2024-06-01T12:02:00",
        },
        {
            "symbolic_revision_plan": {
                "arc_label": "Collapse Risk",
                "symbolic_tag": "fear",
            },
            "revised_license": "✅ Approved",
            "timestamp": "2024-06-01T12:03:00",
        },
        # Edge cases
        {
            "symbolic_revision_plan": {"arc_label": "Fatigue Loop"},
            "revised_license": "❌ Rejected",
            "timestamp": "2024-06-01T12:04:00",
        },
        {
            "symbolic_revision_plan": {},
            "revised_license": "✅ Approved",
            "timestamp": "2024-06-01T12:05:00",
        },
        {},  # malformed
    ]
    profile = generate_learning_profile(dummy_results)
    assert "arc_performance" in profile and "Hope Surge" in profile["arc_performance"]
    assert isinstance(profile["arc_performance"], dict)
    assert isinstance(profile["tag_performance"], dict)
    assert profile["total_records"] == len(dummy_results)
    logger.info("✅ Symbolic learning loop test passed.")


if __name__ == "__main__":
    _test_symbolic_learning_loop()
