"""
gpt_rule_fingerprint_extractor.py

Distills causal fingerprints from GPT rationales, matches them to Pulse rules, and archives unmatched fingerprints as "foreign causal logic."
Intended for use as part of the epistemic mirror system in Pulse.

Core Functions:
- extract_fingerprint_from_gpt_rationale: Parse GPT rationale to extract causal fingerprints.
- match_fingerprint_to_pulse_rules: Match extracted fingerprints to known Pulse rules.
- archive_foreign_fingerprint: Store unmatched fingerprints in a "foreign causal archive" for later review or integration.

Author: [Your Name]
Date: 2025-04-24
"""

from typing import List, Dict, Any, Optional


def extract_fingerprint_from_gpt_rationale(gpt_rationale: str) -> Dict[str, Any]:
    """
    Extracts a causal fingerprint from a GPT rationale/explanation.
    """
    # Naive extraction: look for variable, threshold, and consequence
    import re

    fingerprint = {}
    var_match = re.search(r"(\w+) variable", gpt_rationale)
    if var_match:
        fingerprint["variable"] = var_match.group(1)
    threshold_match = re.search(r"below the (\w+) threshold", gpt_rationale)
    if threshold_match:
        fingerprint["threshold"] = threshold_match.group(1)
    consequence_match = re.search(r"because (.+)", gpt_rationale)
    if consequence_match:
        fingerprint["consequence"] = consequence_match.group(1)
    fingerprint["rationale_text"] = gpt_rationale
    return fingerprint


def match_fingerprint_to_pulse_rules(
    fingerprint: Dict[str, Any], pulse_rules: List[Dict[str, Any]]
) -> Optional[Dict[str, Any]]:
    """
    Attempts to match a fingerprint to known Pulse rules.
    """
    for rule in pulse_rules:
        if (
            fingerprint.get("variable")
            and fingerprint.get("variable") in rule.get("condition", "")
        ) and (
            fingerprint.get("consequence")
            and fingerprint.get("consequence") in rule.get("consequence", "")
        ):
            return rule
    return None


def archive_foreign_fingerprint(
    fingerprint: Dict[str, Any], archive_path: str = "foreign_causal_archive.jsonl"
) -> None:
    """
    Archives an unmatched fingerprint in a foreign causal archive.

    Args:
        fingerprint (Dict[str, Any]): The unmatched fingerprint.
        archive_path (str): Path to the archive file.
    """
    import json

    with open(archive_path, "a", encoding="utf-8") as f:
        f.write(json.dumps(fingerprint) + "\n")


# Example usage (for testing)
if __name__ == "__main__":
    example_gpt_rationale = "The system failed because the trust variable dropped below the critical threshold after repeated negative feedback."
    pulse_rules = [
        {"condition": "trust < threshold", "consequence": "system failure"},
        # ... more rules ...
    ]
    fingerprint = extract_fingerprint_from_gpt_rationale(example_gpt_rationale)
    match = match_fingerprint_to_pulse_rules(fingerprint, pulse_rules)
    if match is None:
        archive_foreign_fingerprint(fingerprint)
        print("Archived foreign fingerprint:", fingerprint)
    else:
        print("Matched Pulse rule:", match)
