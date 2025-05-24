# memory/forecast_episode_tracer.py

"""
Forecast Episode Tracer

Tracks symbolic lineage and mutations across forecast versions.
Useful for reconstructing memory chains, repair ancestry, or symbolic flip paths.

Author: Pulse AI Engine
Version: v1.0.0
"""

from typing import List, Dict


def trace_forecast_lineage(forecast: Dict) -> List[str]:
    """
    Return the list of trace IDs this forecast is derived from.

    Args:
        forecast (Dict): A forecast with ancestry metadata

    Returns:
        List[str]: List of ancestor trace IDs
    """
    return forecast.get("lineage", {}).get("ancestors", [])


def compare_forecast_versions(a: Dict, b: Dict) -> Dict:
    """
    Compare symbolic metadata across two forecast versions.

    Returns:
        Dict: Field-by-field differences
    """
    diffs = {}
    fields = [
        "symbolic_tag",
        "arc_label",
        "confidence",
        "alignment_score",
        "license_status",
    ]

    for f in fields:
        va, vb = a.get(f), b.get(f)
        if va != vb:
            diffs[f] = {"before": va, "after": vb}

    return diffs


def build_episode_chain(forecasts: List[Dict], root_id: str) -> List[Dict]:
    """
    Reconstruct an episode timeline starting from a given root forecast ID.

    Returns:
        List[Dict]: Forecasts ordered by ancestry (if possible)
    """
    id_map = {f.get("trace_id"): f for f in forecasts}
    chain = []
    current_id = root_id

    while current_id:
        fc = id_map.get(current_id)
        if not fc:
            break
        chain.append(fc)
        lineage = fc.get("lineage", {}).get("children", [])
        current_id = lineage[0] if lineage else None

    return chain


def summarize_lineage_drift(chain: List[Dict]) -> Dict:
    """
    Analyze symbolic mutation across a forecast episode chain.

    Returns:
        Dict: Drift metrics
    """
    tag_flips = 0
    arc_flips = 0
    total = len(chain)
    for i in range(1, total):
        if chain[i].get("symbolic_tag") != chain[i - 1].get("symbolic_tag"):
            tag_flips += 1
        if chain[i].get("arc_label") != chain[i - 1].get("arc_label"):
            arc_flips += 1

    return {
        "total_versions": total,
        "tag_flips": tag_flips,
        "arc_flips": arc_flips,
        "symbolic_stability_score": round(
            1 - ((tag_flips + arc_flips) / max(total - 1, 1)), 3
        ),
    }
