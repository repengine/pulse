# forecast_output/mutation_compression_engine.py

"""
Mutation Compression Engine

Collapses a forecast episode chain (mutated versions) into:
- Best single candidate
- Drift summary
- Canonical symbolic outcome

Author: Pulse AI Engine
Version: v1.0.0
"""

import json
from typing import List, Dict, Optional
from memory.forecast_episode_tracer import summarize_lineage_drift
from symbolic_system.symbolic_flip_classifier import extract_transitions


def select_best_forecast(chain: List[Dict]) -> Dict:
    """
    Pick the most aligned and trusted forecast in a mutation chain.

    Returns:
        Dict: selected forecast
    """
    sorted_chain = sorted(
        chain,
        key=lambda fc: (
            fc.get("license_status") == "✅ Approved",
            fc.get("alignment_score", 0),
            fc.get("confidence", 0),
        ),
        reverse=True,
    )
    return sorted_chain[0] if sorted_chain else {}


def summarize_chain_arcs(chain: List[Dict]) -> Dict[str, int]:
    """
    Count arc label frequencies across the episode.

    Returns:
        Dict[str, int]: arc counts
    """
    arcs = {}
    for fc in chain:
        arc = fc.get("arc_label", "unknown")
        arcs[arc] = arcs.get(arc, 0) + 1
    return arcs


def tag_symbolic_instability(forecast_chain: List[Dict], forecast: Dict) -> None:
    """
    If the forecast chain shows high flip volatility or reversals, flag instability.

    Args:
        forecast_chain (List[Dict]): The full episode chain
        forecast (Dict): The final compressed forecast (will be tagged)
    """
    transitions = extract_transitions(forecast_chain)
    flip_counts = {}
    for a, b in transitions:
        flip_counts[(a, b)] = flip_counts.get((a, b), 0) + 1

    # Flipback detection
    reversals = [(b, a) for (a, b) in flip_counts if (b, a) in flip_counts]
    if reversals:
        forecast["unstable_symbolic_path"] = True
        forecast["symbolic_loops_detected"] = [f"{a} ↔ {b}" for (a, b) in reversals]


def compress_episode_chain(chain: List[Dict]) -> Dict:
    """
    Collapse a symbolic forecast lineage chain into a canonical version.

    Returns:
        Dict: compressed forecast + annotations
    """
    if not chain:
        return {}

    summary = summarize_lineage_drift(chain)
    best = select_best_forecast(chain)
    arc_freq = summarize_chain_arcs(chain)

    best["mutation_compressed_from"] = [fc.get("trace_id", "unknown") for fc in chain]
    best["arc_frequency_map"] = arc_freq
    best["symbolic_stability_score"] = summary["symbolic_stability_score"]
    best["tag_flips"] = summary["tag_flips"]
    best["arc_flips"] = summary["arc_flips"]
    best["total_versions"] = summary["total_versions"]

    tag_symbolic_instability(chain, best)

    return best


def export_compressed_episode(forecast: Dict, path: str) -> None:
    """

        Save compressed forecast to disk.
    Args:
        forecast: single forecast dict
        path: .jsonl destination
    """
    try:
        with open(path, "w") as f:
            f.write(json.dumps(forecast) + "\n")
        print(f"✅ Compressed forecast exported to {path}")
    except Exception as e:
        print(f"❌ Failed to export: {e}")


def plot_symbolic_trajectory(
    chain: List[Dict],
    title: str = "Symbolic Trajectory",
    export_path: Optional[str] = None,
):
    """
    Plot and optionally export symbolic arc + tag timeline across forecast chain.

    Args:
        chain (List[Dict])
        export_path (str): Optional path to save image (e.g. .png)
    """
    import matplotlib.pyplot as plt

    steps = list(range(len(chain)))
    arc_labels = [fc.get("arc_label", "unknown") for fc in chain]
    tags = [fc.get("symbolic_tag", "unknown") for fc in chain]

    plt.figure(figsize=(10, 4))
    plt.plot(
        steps,
        arc_labels,
        marker="o",
        linestyle="--",
        label="Arc Label",
        color="royalblue",
    )
    plt.plot(
        steps, tags, marker="x", linestyle="-", label="Symbolic Tag", color="firebrick"
    )
    plt.title(title)
    plt.xlabel("Forecast Version")
    plt.ylabel("Symbolic State")
    plt.legend()
    plt.xticks(steps)
    plt.tight_layout()

    if export_path:
        plt.savefig(export_path)
        print(f"📤 Symbolic trajectory plot saved to {export_path}")
    else:
        plt.show()


# Add this to mutation_compression_engine.py


def summarize_mutation_log(forecast_batch: List[Dict], fmt: str = "markdown") -> str:
    """
    Summarize mutation lineage for a batch of forecasts.

    Args:
        forecast_batch (List[Dict]): List of forecast episodes.
        fmt (str): Output format ("markdown" or "json").

    Returns:
        str: Mutation log as Markdown or JSON string.
    """
    compressed = []
    for forecast in forecast_batch:
        if (lineage := forecast.get("lineage", [])) and (
            compressed_forecast := compress_episode_chain(lineage)
        ):
            compressed.append(compressed_forecast)

    if not compressed:
        return "No mutation lineage data available."

    if fmt == "json":
        import json

        return json.dumps(compressed, indent=2)

    # Default: Markdown
    lines = ["## 🔧 Mutation Summary Log\n"]
    for fc in compressed:
        trace_id = fc.get("trace_id", "unknown")
        stability = fc.get("symbolic_stability_score", "N/A")
        flips = fc.get("arc_flips", "N/A")
        total_versions = fc.get("total_versions", "N/A")
        lines.extend(
            [
                f"### Forecast {trace_id}",
                f"- Symbolic Stability Score: {stability}",
                f"- Arc Flips: {flips}",
                f"- Total Versions: {total_versions}",
                "",
            ]
        )
    return "\n".join(lines)
