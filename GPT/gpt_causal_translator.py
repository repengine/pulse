"""
gpt_causal_translator.py

Extracts rules, symbolic arcs, and missing domains from GPT narrative outputs.
Intended for use as an epistemic mirror module in the Pulse simulation system.

Core Functions:
- extract_rules_from_gpt_output: Parse GPT output to extract (condition → consequence) rules.
- label_symbolic_arcs: Identify and label symbolic arcs from GPT narrative outputs.
- identify_missing_domains: Detect missing domains/variables in Pulse compared to GPT output.

Author: [Your Name]
Date: 2025-04-24
"""

from typing import List, Dict, Any, Tuple, Optional
import re

def extract_rules_from_gpt_output(gpt_output: str) -> List[Dict[str, Any]]:
    """
    Extracts explicit and implicit rules from GPT narrative output.
    """
    # Simple regex for 'If X, then Y.'
    pattern = re.compile(r"[Ii]f ([^.,]+),? then ([^.,]+)[.]")
    rules = []
    for match in pattern.finditer(gpt_output):
        condition, consequence = match.groups()
        rules.append({"condition": condition.strip(), "consequence": consequence.strip()})
    return rules

def label_symbolic_arcs(gpt_output: str) -> List[str]:
    """
    Identifies and labels symbolic arcs (e.g., hope, despair, reversal) in GPT narrative output.
    """
    arcs = []
    arc_keywords = ["hope", "despair", "rage", "fatigue", "trust", "reversal", "optimism", "collapse"]
    for arc in arc_keywords:
        if arc in gpt_output.lower():
            arcs.append(arc)
    return arcs

def identify_missing_domains(gpt_output: str, pulse_domains: List[str]) -> List[str]:
    """
    Identifies domains or variables present in GPT output but missing from Pulse's known domains.
    """
    words = set(re.findall(r"[a-zA-Z_]+", gpt_output.lower()))
    pulse_set = set([d.lower() for d in pulse_domains])
    missing = [w for w in words if w not in pulse_set and len(w) > 3]
    return list(set(missing))

# Example usage (for testing)
if __name__ == "__main__":
    example_gpt_output = "If the market crashes, then investor confidence will plummet. This triggers a wave of withdrawals, leading to systemic risk."
    pulse_domains = ["market", "investor_confidence", "withdrawals"]
    print("Extracted Rules:", extract_rules_from_gpt_output(example_gpt_output))
    print("Symbolic Arcs:", label_symbolic_arcs(example_gpt_output))
    print("Missing Domains:", identify_missing_domains(example_gpt_output, pulse_domains))