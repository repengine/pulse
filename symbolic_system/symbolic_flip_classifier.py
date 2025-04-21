# symbolic/symbolic_flip_classifier.py

"""
Symbolic Flip Classifier

Analyzes symbolic arc and tag transitions across forecast chains to detect:
- Common arc shifts (e.g., Hope → Fatigue)
- Symbolic loops (e.g., Despair → Rage → Despair)
- Repair-resistant patterns for operator review

Author: Pulse AI Engine
Version: v1.0.0
"""

from typing import List, Dict
from collections import Counter


def extract_transitions(chain: List[Dict]) -> List[tuple]:
    """
    Extract arc and tag transitions from a forecast episode chain.

    Returns:
        List of (from → to) transitions
    """
    transitions = []
    for i in range(1, len(chain)):
        arc_prev = chain[i - 1].get("arc_label", "unknown")
        arc_curr = chain[i].get("arc_label", "unknown")
        tag_prev = chain[i - 1].get("symbolic_tag", "unknown")
        tag_curr = chain[i].get("symbolic_tag", "unknown")

        if arc_prev != arc_curr:
            transitions.append((f"ARC: {arc_prev}", f"ARC: {arc_curr}"))
        if tag_prev != tag_curr:
            transitions.append((f"TAG: {tag_prev}", f"TAG: {tag_curr}"))

    return transitions


def analyze_flip_patterns(chains: List[List[Dict]]) -> Dict:
    """
    Analyze all chains to find symbolic transitions and most common shifts.

    Returns:
        Dict: transition counts, common flips
    """
    all_flips = []

    for chain in chains:
        flips = extract_transitions(chain)
        all_flips.extend(flips)

    counter = Counter(all_flips)
    sorted_flips = sorted(counter.items(), key=lambda x: -x[1])

    return {
        "total_flips": len(all_flips),
        "unique_flips": len(counter),
        "top_flips": sorted_flips[:10],
        "all_flips": dict(counter)
    }


def detect_loops_or_cycles(flips: Dict[tuple, int]) -> List[str]:
    """
    Detect arcs or tags that commonly flip back to prior state.

    Returns:
        List[str]: tags/arcs in loop patterns
    """
    loop_candidates = []
    for (a, b), count in flips.items():
        if (b, a) in flips:
            loop_candidates.append(f"{a} ↔ {b}")
    return list(set(loop_candidates))
