"""
pulse_forecast_lineage.py

Tracks ancestry and influence of forecasts, detects drift, generates forecast trees, flags divergence.

Author: Pulse AI Engine
"""

from typing import List, Dict, Any, Optional
import logging
import argparse
import json

try:
    import graphviz
except ImportError:
    graphviz = None

logger = logging.getLogger("pulse_forecast_lineage")

def build_forecast_lineage(forecasts: List[Dict]) -> Dict[str, List[str]]:
    """
    Build a mapping from forecast_id to its children (descendants).

    Args:
        forecasts: List of forecast dicts (should include 'trace_id' and 'parent_id').

    Returns:
        Dict mapping parent_id to list of child trace_ids.

    Example:
        >>> build_forecast_lineage([
        ...   {"trace_id": "A", "parent_id": None},
        ...   {"trace_id": "B", "parent_id": "A"},
        ...   {"trace_id": "C", "parent_id": "A"}
        ... ])
        {'A': ['B', 'C']}
    """
    lineage = {}
    for f in forecasts:
        parent = f.get("parent_id")
        if parent:
            lineage.setdefault(parent, []).append(f.get("trace_id"))
    logger.info(f"Lineage built for {len(lineage)} parents.")
    return lineage

def detect_drift(forecasts: List[Dict], drift_key: str = "symbolic_tag") -> List[str]:
    """
    Detects drift in a specified key (default: symbolic_tag) over time.

    Args:
        forecasts: List of forecast dicts (chronologically ordered).
        drift_key: Key to check for drift (default: 'symbolic_tag').

    Returns:
        List of drift event strings.

    Example:
        >>> detect_drift([
        ...   {"trace_id": "A", "symbolic_tag": "Hope"},
        ...   {"trace_id": "B", "symbolic_tag": "Hope"},
        ...   {"trace_id": "C", "symbolic_tag": "Despair"}
        ... ])
        ['Drift: A → C [symbolic_tag: Hope → Despair]']
    """
    drifts = []
    for i in range(1, len(forecasts)):
        prev = forecasts[i-1]
        curr = forecasts[i]
        if prev.get(drift_key) != curr.get(drift_key):
            drifts.append(f"Drift: {prev.get('trace_id')} → {curr.get('trace_id')} [{drift_key}: {prev.get(drift_key)} → {curr.get(drift_key)}]")
    logger.info(f"Drift detection: {len(drifts)} drift events found for key '{drift_key}'.")
    return drifts

def flag_divergence(forecasts: List[Dict]) -> List[str]:
    """
    Flags divergence forks for operator review.

    Args:
        forecasts: List of forecast dicts (should include 'trace_id' and 'parent_id').

    Returns:
        List of divergence event strings.

    Example:
        >>> flag_divergence([
        ...   {"trace_id": "A", "parent_id": None},
        ...   {"trace_id": "B", "parent_id": "A"},
        ...   {"trace_id": "C", "parent_id": "A"}
        ... ])
        ['Divergence: C from parent A']
    """
    forks = []
    seen = set()
    for f in forecasts:
        parent = f.get("parent_id")
        if parent and parent in seen:
            forks.append(f"Divergence: {f.get('trace_id')} from parent {parent}")
        seen.add(f.get("trace_id"))
    logger.info(f"Divergence flagging: {len(forks)} forks found.")
    return forks

def fork_count(forecasts: List[Dict]) -> Dict[str, int]:
    """
    Count how many forks (children) exist from each parent.

    Args:
        forecasts: List of forecast dicts (should include 'trace_id' and 'parent_id').

    Returns:
        Dict mapping parent_id to fork count.

    Example:
        >>> fork_count([
        ...   {"trace_id": "A", "parent_id": None},
        ...   {"trace_id": "B", "parent_id": "A"},
        ...   {"trace_id": "C", "parent_id": "A"}
        ... ])
        {'A': 2}
    """
    counts = {}
    for f in forecasts:
        parent = f.get("parent_id")
        if parent:
            counts[parent] = counts.get(parent, 0) + 1
    return counts

def drift_score(forecasts: List[Dict], drift_key: str = "symbolic_tag") -> Dict[str, int]:
    """
    Quantify cumulative drift per parent (family).

    Args:
        forecasts: List of forecast dicts.
        drift_key: Key to check for drift.

    Returns:
        Dict mapping parent_id to drift count.

    Example:
        >>> drift_score([
        ...   {"trace_id": "A", "parent_id": None, "symbolic_tag": "Hope"},
        ...   {"trace_id": "B", "parent_id": "A", "symbolic_tag": "Hope"},
        ...   {"trace_id": "C", "parent_id": "A", "symbolic_tag": "Despair"}
        ... ])
        {'A': 1}
    """
    parent_map = {f["trace_id"]: f for f in forecasts}
    drift_counts = {}
    for f in forecasts:
        parent_id = f.get("parent_id")
        if parent_id and parent_id in parent_map:
            parent_val = parent_map[parent_id].get(drift_key)
            child_val = f.get(drift_key)
            if parent_val != child_val:
                drift_counts[parent_id] = drift_counts.get(parent_id, 0) + 1
    return drift_counts

def get_symbolic_arc(forecast: Dict) -> Optional[Dict]:
    """
    Extract symbolic arc (emotional overlays) from a forecast if present.

    Args:
        forecast: Forecast dict.

    Returns:
        Dict of symbolic arc values or None.

    Example:
        >>> get_symbolic_arc({"symbolic_arc": {"hope": 0.7}})
        {'hope': 0.7}
    """
    for key in ("symbolic_arc", "symbolic_change", "emotional_overlay"):
        if key in forecast:
            return forecast[key]
    overlays = {k: forecast[k] for k in ("hope", "despair", "rage", "fatigue") if k in forecast}
    return overlays if overlays else None

def get_confidence(forecast: Dict) -> Optional[float]:
    return forecast.get("confidence")

def get_prompt_hash(forecast: Dict) -> Optional[str]:
    for key in ("prompt_hash", "prompt_id", "origin_hash"):
        if key in forecast:
            return forecast[key]
    return None

def symbolic_color(symbolic_tag: Optional[str]) -> str:
    """
    Map symbolic_tag to a color for Graphviz.
    """
    color_map = {
        "Hope": "green",
        "Despair": "red",
        "Rage": "orange",
        "Fatigue": "gray",
        "Trust": "blue",
        None: "black"
    }
    return color_map.get(symbolic_tag, "black")

def confidence_color(conf: Optional[float]) -> str:
    """
    Map confidence to a color gradient (green to red).
    """
    if conf is None:
        return "black"
    if conf >= 0.8:
        return "green"
    elif conf >= 0.6:
        return "yellow"
    elif conf >= 0.4:
        return "orange"
    else:
        return "red"

def export_graphviz_dot(
    forecasts: List[Dict],
    filepath: str,
    color_by: str = "arc"
):
    """
    Export forecast lineage as a color-coded Graphviz .dot file.

    Args:
        forecasts: List of forecast dicts (should include 'trace_id' and 'parent_id').
        filepath: Output .dot file path.
        color_by: 'arc' (symbolic_tag), 'confidence', or 'none'.

    Example:
        >>> export_graphviz_dot([
        ...   {"trace_id": "A", "parent_id": None, "symbolic_tag": "Hope", "confidence": 0.9},
        ...   {"trace_id": "B", "parent_id": "A", "symbolic_tag": "Despair", "confidence": 0.5}
        ... ], "lineage.dot", color_by="arc")
    """
    if graphviz is None:
        raise ImportError("graphviz is not installed. Please install it to use --export-graph.")
    dot = graphviz.Digraph(comment="Forecast Lineage")
    ids = set()
    for f in forecasts:
        tid = f.get("trace_id")
        if not tid or tid in ids:
            continue
        label = tid
        arc = get_symbolic_arc(f)
        tag = f.get("symbolic_tag")
        conf = get_confidence(f)
        prompt_hash = get_prompt_hash(f)
        if arc:
            arc_str = ", ".join(f"{k}:{v:.2f}" for k, v in arc.items())
            label += f"\n{arc_str}"
        if prompt_hash:
            label += f"\nPrompt: {prompt_hash[:8]}"
        if color_by == "arc":
            color = symbolic_color(tag)
        elif color_by == "confidence":
            color = confidence_color(conf)
        else:
            color = "black"
        dot.node(tid, label=label, color=color, fontcolor=color)
        ids.add(tid)
    for f in forecasts:
        tid = f.get("trace_id")
        pid = f.get("parent_id")
        if tid and pid:
            dot.edge(pid, tid)
    dot.save(filepath)

def print_summary(forecasts: List[Dict]):
    """
    Print summary statistics of the forecast list.

    Args:
        forecasts: List of forecast dicts.

    Example:
        >>> print_summary([
        ...   {"trace_id": "A", "parent_id": None},
        ...   {"trace_id": "B", "parent_id": "A"}
        ... ])
        Forecasts: 2
        Unique parents: 1
    """
    print(f"Forecasts: {len(forecasts)}")
    parents = set(f.get("parent_id") for f in forecasts if f.get("parent_id"))
    print(f"Unique parents: {len(parents)}")

def save_output(obj: Any, filepath: str):
    """
    Save object as JSON to file.

    Args:
        obj: Object to save.
        filepath: Output file path.

    Example:
        >>> save_output({'a': 1}, 'out.json')
    """
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(obj, f, indent=2)

def parse_args():
    """
    Parse command-line arguments.

    Example:
        python pulse_forecast_lineage.py --forecasts forecasts.json --summary --export-graph lineage.dot --color-by arc --save output.json
    """
    parser = argparse.ArgumentParser(description="Pulse Forecast Lineage CLI")
    parser.add_argument("--forecasts", type=str, required=True, help="Path to forecasts JSON file")
    parser.add_argument("--drift-key", type=str, default="symbolic_tag", help="Key to check for drift")
    parser.add_argument("--lineage", action="store_true", help="Show forecast lineage")
    parser.add_argument("--drift", action="store_true", help="Detect drift events")
    parser.add_argument("--divergence", action="store_true", help="Flag divergence forks")
    parser.add_argument("--fork-count", action="store_true", help="Show fork count per parent")
    parser.add_argument("--drift-score", action="store_true", help="Show drift score per parent")
    parser.add_argument("--summary", action="store_true", help="Print summary statistics")
    parser.add_argument("--export-graph", type=str, help="Export lineage as Graphviz .dot file")
    parser.add_argument("--color-by", type=str, default="arc", choices=["arc", "confidence", "none"], help="Color nodes by arc, confidence, or none")
    parser.add_argument("--save", type=str, help="Save output JSON to file")
    return parser.parse_args()

def main():
    """
    Main entry point.

    Example:
        python pulse_forecast_lineage.py --forecasts forecasts.json --summary --export-graph lineage.dot --color-by arc --save output.json
    """
    args = parse_args()
    logging.basicConfig(level=logging.INFO)
    with open(args.forecasts, "r", encoding="utf-8") as f:
        forecasts = json.load(f)

    output = {}

    if args.lineage:
        lineage = build_forecast_lineage(forecasts)
        output["lineage"] = lineage
        print(json.dumps(lineage, indent=2))
    if args.drift:
        drifts = detect_drift(forecasts, drift_key=args.drift_key)
        output["drift"] = drifts
        print(json.dumps(drifts, indent=2))
    if args.divergence:
        forks = flag_divergence(forecasts)
        output["divergence"] = forks
        print(json.dumps(forks, indent=2))
    if args.fork_count:
        fc = fork_count(forecasts)
        output["fork_count"] = fc
        print(json.dumps(fc, indent=2))
    if args.drift_score:
        ds = drift_score(forecasts, drift_key=args.drift_key)
        output["drift_score"] = ds
        print(json.dumps(ds, indent=2))
    if args.summary:
        print_summary(forecasts)
    if args.export_graph:
        export_graphviz_dot(forecasts, args.export_graph, color_by=args.color_by)
        print(f"Graph exported to {args.export_graph}")
    if args.save:
        save_output(output, args.save)
        print(f"Output saved to {args.save}")

if __name__ == "__main__":
    main()
