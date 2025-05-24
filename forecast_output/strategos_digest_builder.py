"""
strategos_digest_builder.py

Combines symbolic arc, capital deltas, confidence, and retrodiction scoring from the unified simulate_forward function into a foresight digest report.
Supports user configuration for included fields.

Available digest templates:
    - "full": All default fields (trace_id, turn, confidence, fragility, trust_label, symbolic_tag, overlays, exposure_delta)
    - "short": Minimal fields (trace_id, confidence, symbolic_tag)
    - "symbolic_only": Symbolic tag and overlays only

UI integration: The digest builder supports template selection via the `template` argument in both CLI and UI (see live_digest_ui in strategos_digest.py).

Usage:
    from forecast_output.strategos_digest_builder import build_digest
    digest_md = build_digest(batch, fmt="markdown", config={"fields": ["trace_id", "confidence"]}, template="short")

Note:
    Retrodiction scores and related fields are expected to be included in the forecast data,
    produced by the unified simulate_forward function during simulation.

Author: Pulse AI Engine
"""

from typing import List, Dict, Any, Optional
import os
import json
from collections import defaultdict
import logging
from forecast_output.digest_trace_hooks import summarize_trace_for_digest
from forecast_output.pulse_forecast_lineage import get_prompt_hash

# Add import for divergence detector
from forecast_output.forecast_divergence_detector import (
    generate_divergence_report,
    group_conflicting_forecasts,
)

logger = logging.getLogger("strategos_digest_builder")

DEFAULT_FIELDS = [
    "trace_id",
    "turn",
    "confidence",
    "fragility",
    "trust_label",
    "symbolic_tag",
    "overlays",
    "exposure_delta",
]

# --- PATCH: Import learning summary, mutation logs, capital/symbolic trends ---
try:
    from symbolic_system.pulse_symbolic_learning_loop import (
        generate_learning_profile,
        learn_from_tuning_log,
    )
except ImportError:
    generate_learning_profile = None
    learn_from_tuning_log = None

try:
    from forecast_output.mutation_compression_engine import summarize_mutation_log
except ImportError:
    summarize_mutation_log = None

# ✅ PATCH B Step 1: Import contradiction digest formatter
try:
    from operator_interface.symbolic_contradiction_digest import (
        format_contradiction_cluster_md,
        load_symbolic_conflict_events,
    )
except ImportError:
    format_contradiction_cluster_md = None
    load_symbolic_conflict_events = None


def validate_forecast_schema(f: Dict) -> bool:
    """Basic schema validation for forecast objects."""
    required = ["trace_id", "confidence", "fragility", "symbolic_tag", "overlays"]
    return all(k in f for k in required)


def flatten_forecast(f: Dict) -> Dict:
    """If forecast is nested under 'forecast', flatten it into the parent dict."""
    if "forecast" in f and isinstance(f["forecast"], dict):
        merged = {**f, **f["forecast"]}
        del merged["forecast"]
        return merged
    return f


def cluster_by_key(forecasts: List[Dict], key: str) -> Dict[str, List[Dict]]:
    """Cluster forecasts by any key (e.g., symbolic_tag, trust_label, narrative_theme)."""
    clusters = defaultdict(list)
    for f in forecasts:
        label = f.get(key, "unknown")
        clusters[label].append(f)
    return clusters


def consensus_score(cluster: List[Dict], overlay_key: str = "hope") -> float:
    """Score consensus for a symbolic overlay (e.g., % with hope rising)."""
    count = 0
    for f in cluster:
        overlays = f.get("overlays", {})
        drift = overlays.get(overlay_key, 0.0) if isinstance(overlays, dict) else 0.0
        if drift > 0.0:
            count += 1
    return round(count / len(cluster), 2) if cluster else 0.0


def summarize_stats(forecasts: List[Dict]) -> Dict[str, Any]:
    """Compute summary statistics for the digest footer.

    Retrodiction scores are expected to be included in the forecast data,
    produced by the unified simulate_forward function during simulation.
    """
    stats = {}
    confidences = [
        f.get("confidence", 0.0)
        for f in forecasts
        if isinstance(f.get("confidence", 0.0), (float, int))
    ]
    ret_scores = [
        f.get("retrodiction_score", 0.0)
        for f in forecasts
        if isinstance(f.get("retrodiction_score", 0.0), (float, int))
    ]
    sym_scores = [
        f.get("symbolic_score", 0.0)
        for f in forecasts
        if isinstance(f.get("symbolic_score", 0.0), (float, int))
    ]
    ages = [
        f.get("age_hours", 0.0)
        for f in forecasts
        if isinstance(f.get("age_hours", 0.0), (float, int))
    ]
    stats["avg_confidence"] = (
        round(sum(confidences) / len(confidences), 3) if confidences else 0.0
    )
    stats["avg_retrodiction"] = (
        round(sum(ret_scores) / len(ret_scores), 3) if ret_scores else 0.0
    )
    stats["avg_symbolic"] = (
        round(sum(sym_scores) / len(sym_scores), 3) if sym_scores else 0.0
    )
    stats["avg_age"] = round(sum(ages) / len(ages), 2) if ages else 0.0
    stats["max_age"] = max(ages) if ages else 0.0
    stats["total"] = len(forecasts)
    stats["confidence_sparkline"] = [round(c, 2) for c in confidences]
    return stats


def get_top_clusters(
    clusters: Dict[str, List[Dict]], n: int = 3, sort_by: str = "count"
) -> List[tuple]:
    """
    Return the top N clusters by count or average confidence.
    """
    if sort_by == "confidence":
        ranked = sorted(
            clusters.items(),
            key=lambda x: sum(f.get("confidence", 0) or 0 for f in x[1])
            / max(len(x[1]), 1),
            reverse=True,
        )
    else:
        ranked = sorted(clusters.items(), key=lambda x: len(x[1]), reverse=True)
    return ranked[:n]


def summarize_drivers(cluster: List[Dict], top_k: int = 3) -> List[str]:
    """
    Summarize top drivers in a cluster.
    """
    from collections import Counter

    drivers = []
    for f in cluster:
        ds = f.get("drivers") or f.get("driver") or []
        if isinstance(ds, str):
            ds = [ds]
        drivers.extend(ds)
    counter = Counter(drivers)
    return [d for d, _ in counter.most_common(top_k)]


def render_fields(f: Dict[str, Any], fields: List[str]) -> List[str]:
    """Render a forecast dict as lines for the digest."""
    lines = []
    for k in fields:
        v = f.get(k, "N/A")
        lines.append(f"{k.capitalize():<14}: {v}")
    return lines


from datetime import datetime


def log_prompt(
    prompt: str, config: dict, overlays: dict, path: str = "logs/prompt_log.jsonl"
):
    entry = {
        "timestamp": datetime.utcnow().isoformat(),
        "prompt": prompt,
        "config": config,
        "overlays": overlays,
    }
    try:
        with open(path, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry) + "\n")
        logger.info(f"Prompt logged to {path}")
    except Exception as e:
        logger.error(f"Prompt log error: {e}")


def process_forecasts(forecast_list):
    for forecast in forecast_list:
        forecast_output = forecast.get("output", "")
        trace_id = forecast.get("trace_id")
        if trace_id:
            trace_summary = summarize_trace_for_digest(trace_id)
            if trace_summary:
                forecast_output += f"\n[Trace {trace_id[:8]}] {trace_summary}"
        print(forecast_output)


def build_digest(
    forecast_batch: List[Dict[str, Any]],
    fmt: str = "markdown",
    config: Optional[dict] = None,
    template: str = "full",
) -> str:
    """
    Build a strategos digest from a batch of forecasts.

    Args:
        forecast_batch: List of forecast dicts.
        fmt: Output format ("markdown", "json", "html").
        config: Dict with customization options.
        template: Digest template ("full", "short", "symbolic_only").
    Returns:
        Digest string in requested format.

    Example:
        build_digest(batch, fmt="markdown", config={"fields": ["trace_id", "confidence"]}, template="short")

    Available templates for UI:
        - "full"
        - "short"
        - "symbolic_only"
    """
    config = config or {}
    if not forecast_batch:
        if fmt == "json":
            return "[]"
        if fmt == "html":
            return "<h1>Strategos Digest</h1><i>No forecasts available.</i>"
        return "# Strategos Digest\n\n_No forecasts available._"

    # Template support
    # Ensure fields is always a list
    if template == "short":
        fields = ["trace_id", "confidence", "symbolic_tag"]
    elif template == "symbolic_only":
        fields = ["trace_id", "symbolic_tag", "overlays"]
    else:
        fields = (
            config.get("fields") if config.get("fields") is not None else DEFAULT_FIELDS
        )

    tag_filter = config.get("tag_filter") if config else None
    overlay_key = config.get("consensus_overlay", "hope") if config else "hope"
    cluster_key = (
        config.get("cluster_key", "symbolic_tag") if config else "symbolic_tag"
    )
    top_n = config.get("top_n", None) if config else None
    actionable_only = config.get("actionable_only", False) if config else False
    sort_clusters_by = config.get("sort_clusters_by", "count") if config else "count"
    show_drivers = config.get("show_drivers", True) if config else True

    # Flatten and validate
    flattened = []
    skipped = 0
    for f in forecast_batch:
        flat = flatten_forecast(f)
        if validate_forecast_schema(flat):
            flattened.append(flat)
        else:
            skipped += 1
    if skipped:
        logger.warning(f"Skipped {skipped} invalid forecasts in digest build.")

    # All downstream modules (divergence, dual narrative, memory, etc.) now operate on flattened, validated forecasts.

    # --- Symbolic Divergence Report ---
    divergence_report = generate_divergence_report(flattened, key="arc_label")
    conflict_groups = group_conflicting_forecasts(flattened, key="arc_label")
    divergent_ids = {
        f.get("trace_id") for flist in conflict_groups.values() for f in flist
    }
    for fc in flattened:
        if fc.get("trace_id") in divergent_ids:
            fc["divergent"] = True

    # Symbolic Fragmentation Summary
    from collections import Counter

    fragmented = [f for f in flattened if f.get("symbolic_fragmented")]
    fragment_summary = Counter(f.get("arc_label", "unknown") for f in fragmented)
    symbolic_fragmentation = {
        "total": len(fragmented),
        "by_arc": dict(fragment_summary),
    }

    # --- Most Evolved Forecasts by Cluster ---
    try:
        from memory.cluster_mutation_tracker import (
            track_cluster_lineage,
            select_most_evolved,
            summarize_mutation_depths,
        )

        cluster_map = track_cluster_lineage(flattened)
        lineage_leaders = select_most_evolved(cluster_map)
        mutation_depths = summarize_mutation_depths(cluster_map)
        most_evolved_digest = {
            "leaders": [
                {
                    "trace_id": fc.get("trace_id"),
                    "arc": fc.get("arc_label"),
                    "tag": fc.get("symbolic_tag"),
                    "depth": len(fc.get("lineage", {}).get("ancestors", [])),
                }
                for fc in lineage_leaders.values()
            ],
            "mutation_depths": mutation_depths,
        }
    except Exception as e:
        logger.warning(f"Could not compute most evolved forecasts: {e}")
        most_evolved_digest = {"leaders": [], "mutation_depths": {}}

    # --- Dual Narrative Scenarios ---
    try:
        from forecast_output.dual_narrative_compressor import generate_dual_scenarios
        from forecast_output.strategic_fork_resolver import resolve_all_forks

        dual_narrative_scenarios = generate_dual_scenarios(flattened)
        fork_decisions = resolve_all_forks(dual_narrative_scenarios)
    except Exception as e:
        logger.warning(f"Dual narrative scenario generation failed: {e}")
        dual_narrative_scenarios = []
        fork_decisions = []
    # Mark fork winners in forecasts
    decision_ids = {
        r["selected_trace_id"]
        for r in fork_decisions
        if r.get("decision") in {"A", "B"}
    }
    for fc in flattened:
        if fc.get("trace_id") in decision_ids:
            fc["fork_winner"] = True

    # --- Symbolic Entropy Report ---
    try:
        from memory.forecast_memory_entropy import generate_entropy_report

        # Optionally, load memory forecasts if available in config
        memory_forecasts = None
        if config and "memory_forecasts" in config:
            memory_forecasts = config["memory_forecasts"]
        else:
            # Try to load from default memory file if exists
            mem_path = (
                config.get("memory_path")
                if config and "memory_path" in config
                else None
            )
            if mem_path and os.path.exists(mem_path):
                with open(mem_path, "r", encoding="utf-8") as f:
                    memory_forecasts = [
                        json.loads(line.strip()) for line in f if line.strip()
                    ]
        if memory_forecasts:
            entropy_report = generate_entropy_report(flattened, memory_forecasts)
        else:
            entropy_report = None
    except Exception as e:
        logger.warning(f"Could not compute symbolic entropy report: {e}")
        entropy_report = None

    # --- PATCH: Learning Summary ---
    learning_summary_md = ""
    if generate_learning_profile and learn_from_tuning_log:
        try:
            tune_log = (
                config.get("tuning_log", "logs/tuning_results.jsonl")
                if config
                else "logs/tuning_results.jsonl"
            )
            if os.path.exists(tune_log):
                results = learn_from_tuning_log(tune_log)
                profile = generate_learning_profile(results)
                learning_summary_md = "## 🧠 Learning Summary\n"
                strong = profile.get("strong_tags") or profile.get("strong", [])
                risky = profile.get("risky_tags") or profile.get("risky", [])
                if strong:
                    learning_summary_md += f"- Strong Tags: {', '.join(strong)}\n"
                if risky:
                    learning_summary_md += f"- Risky Tags: {', '.join(risky)}\n"
                learning_summary_md += "\n"
        except Exception as e:
            learning_summary_md = f"## 🧠 Learning Summary\n- Error: {e}\n"

    # --- PATCH: Mutation Logs ---
    mutation_log_md = ""
    if summarize_mutation_log:
        try:
            mutation_log_md = summarize_mutation_log(forecast_batch, fmt="markdown")
            if mutation_log_md and not mutation_log_md.startswith("##"):
                mutation_log_md = "## 🔧 Mutation Log\n" + mutation_log_md
        except Exception as e:
            mutation_log_md = f"## 🔧 Mutation Log\n- Error: {e}\n"

    # Tag filter
    if tag_filter:
        flattened = [f for f in flattened if tag_filter in f.get("tags", [])]

    # Actionable only filter
    if actionable_only:
        flattened = [
            f for f in flattened if f.get("confidence_status") == "✅ Actionable"
        ]

    # Prefer narrative_theme if present and requested
    if cluster_key == "narrative_theme" and not any(
        "narrative_theme" in f for f in flattened
    ):
        cluster_key = "symbolic_tag"

    clusters = cluster_by_key(flattened, cluster_key)

    # Top N clusters
    if top_n:
        clusters = dict(get_top_clusters(clusters, n=top_n, sort_by=sort_clusters_by))

    # --- Compressed Cluster Memory Section ---
    from forecast_output.cluster_memory_compressor import compress_by_cluster

    compressed_cluster_forecasts = compress_by_cluster(flattened)

    try:
        if fmt == "json":
            # Include all keys from the flattened forecast dictionaries for comprehensive JSON output
            digest_json = flattened
            # Add most evolved section, divergence report, dual narrative scenarios, fork decisions, and entropy report
            return json.dumps(
                {
                    "forecasts": digest_json,
                    "most_evolved_per_cluster": most_evolved_digest,
                    "symbolic_divergence": divergence_report,
                    "dual_narrative_scenarios": dual_narrative_scenarios,
                    "fork_decisions": fork_decisions,
                    "symbolic_entropy_report": entropy_report,
                    "symbolic_fragmentation": symbolic_fragmentation,  # Include fragmentation summary
                    "compressed_cluster_memory": compressed_cluster_forecasts,  # Include compressed memory
                },
                indent=2,
            )
        if fmt == "html":
            lines = ["<h1>Strategos Digest</h1>"]
            # --- Symbolic Divergence Report (HTML) ---
            lines.append("<h2>⚔️ Symbolic Divergence Report</h2>")
            lines.append(
                f"<b>Divergence Score:</b> {divergence_report['divergence_score']}<br>"
            )
            if divergence_report["symbolic_conflicts"]:
                lines.append("<b>Conflicting Narratives Detected:</b><ul>")
                for a, b in divergence_report["symbolic_conflicts"]:
                    lines.append(f"<li>{a} vs {b}</li>")
                lines.append("</ul>")
            if divergence_report["cluster_sizes"]:
                lines.append("<b>Cluster Sizes:</b><ul>")
                for k, v in divergence_report["cluster_sizes"].items():
                    lines.append(f"<li>{k}: {v}</li>")
                lines.append("</ul>")
            # Fix clusters.items() usage for when clusters is a list
            if isinstance(clusters, dict):
                cluster_items = clusters.items()
            else:
                cluster_items = []
            # Ensure fields is not None before iteration
            if fields is None:
                fields = DEFAULT_FIELDS
            for label, cluster in cluster_items:
                lines.append(f"<h2>{label}</h2>")
                lines.append(
                    f"<b>Consensus ({overlay_key} rising):</b> {consensus_score(cluster, overlay_key) * 100:.0f}%<br>"
                )
                if show_drivers:
                    drivers = summarize_drivers(cluster)
                    if drivers:
                        lines.append(f"<b>Top Drivers:</b> {', '.join(drivers)}<br>")
                for f in cluster:
                    calculated_prompt_hash = f.get("prompt_hash") or get_prompt_hash(
                        f.get("trace_id", "")
                    )
                    f["prompt_hash"] = calculated_prompt_hash
                    for k in fields:
                        v = f.get(k, "N/A")
                        lines.append(f"<b>{k}:</b> {v}<br>")
                    # --- Causal Explanation (HTML) ---
                    if "causal_explanation" in f:
                        ce = f["causal_explanation"]
                        lines.append(
                            f"<b>Causal Explanation:</b> {ce.get('variable', '')} &rarr; Parents: {', '.join(ce.get('parents', []))}<br>"
                        )
                lines.append("<hr>")
            if not clusters:
                lines.append("<i>No forecasts available.</i>")
            stats = summarize_stats(flattened)
            lines.append(
                f"<b>Avg Retrodiction Score:</b> {stats['avg_retrodiction']} | <b>Symbolic Score:</b> {stats['avg_symbolic']}<br>"
            )
            lines.append(
                f"<b>Confidence Sparkline:</b> {stats['confidence_sparkline']}<br>"
            )
            lines.append(
                f"<b>Forecast Age:</b> Avg {stats['avg_age']}h | Max: {stats['max_age']}h<br>"
            )
            lines.append(f"<b>Total Forecasts:</b> {stats['total']}<br>")
            # Insert Most Evolved section in HTML
            lines.append("<h2>🧬 Most Evolved Forecasts by Cluster</h2>")
            lines.append(
                "<table><tr><th>Cluster</th><th>Trace ID</th><th>Arc Label</th><th>Depth</th></tr>"
            )
            for leader in most_evolved_digest["leaders"]:
                lines.append(
                    f"<tr><td>{leader['tag']}</td><td>{leader['trace_id']}</td><td>{leader['arc']}</td><td>{leader['depth']}</td></tr>"
                )
            lines.append("</table>")
            lines.append(
                f"<b>Mutation Depths:</b> {most_evolved_digest['mutation_depths']}<br>"
            )
            # Insert Symbolic Entropy Report (HTML)
            if entropy_report:
                lines.append("<h2>🌐 Symbolic Entropy Report</h2>")
                for k, v in entropy_report.items():
                    lines.append(f"<b>{k.replace('_', ' ').capitalize()}:</b> {v}<br>")
            # Optionally, insert dual narrative scenarios in HTML if desired
            if dual_narrative_scenarios:
                lines.append("<h2>🔀 Dual Narrative Scenarios</h2>")
                for pair in dual_narrative_scenarios:
                    a = pair.get("scenario_a", {})
                    b = pair.get("scenario_b", {})
                    lines.append(f"<h3>{a.get('arc', 'A')} vs {b.get('arc', 'B')}</h3>")
                    lines.append(f"<b>Scenario A ({a.get('arc', 'A')}):</b><br>")
                    lines.append(f"- Tag: {a.get('symbolic_tag', 'N/A')}<br>")
                    lines.append(f"- Alignment: {a.get('alignment_score', 'N/A')}<br>")
                    lines.append(f"- Confidence: {a.get('confidence', 'N/A')}<br>")
                    lines.append(f"<b>Scenario B ({b.get('arc', 'B')}):</b><br>")
                    lines.append(f"- Tag: {b.get('symbolic_tag', 'N/A')}<br>")
                    lines.append(f"- Alignment: {b.get('alignment_score', 'N/A')}<br>")
                    lines.append(f"- Confidence: {b.get('confidence', 'N/A')}<br>")
            # HTML Output: Fork Resolutions
            if fork_decisions:
                lines.append("<h2>🧭 Strategic Fork Resolutions</h2>")
                for d in fork_decisions:
                    a = d.get("scenario_a", {})
                    b = d.get("scenario_b", {})
                    winner = d.get("winner_label", "N/A")
                    winner_id = d.get("selected_trace_id", "N/A")
                    winner_align = d.get("winner_alignment", "N/A")
                    lines.append(
                        f"<b>{a.get('arc', 'A')} vs {b.get('arc', 'B')}</b> &rarr; ✅ {winner}<br>"
                    )
                    lines.append(
                        f"&nbsp;&nbsp;- Winner: {winner_id} (Align: {winner_align})<br>"
                    )
            return "\n".join(lines)
        # Default: markdown
        lines = ["# Strategos Digest\n"]

        # --- PATCH: Insert learning summary, mutation log, capital trends at top ---
        if learning_summary_md:
            lines.append(learning_summary_md)
        if mutation_log_md:
            lines.append(mutation_log_md)

        # ✅ PATCH B Step 2: Insert symbolic contradiction digest section
        if format_contradiction_cluster_md and load_symbolic_conflict_events:
            clusters = load_symbolic_conflict_events()
            if clusters:
                lines.append("## ♻️ Symbolic Contradiction Clusters\n")
                lines.append(format_contradiction_cluster_md(clusters))

        # --- Symbolic Divergence Report (Markdown) ---
        lines.append("## ⚔️ Symbolic Divergence Report\n")
        lines.append(f"- Divergence Score: {divergence_report['divergence_score']}")
        if divergence_report["symbolic_conflicts"]:
            lines.append("- Conflicting Narratives Detected:")
            for a, b in divergence_report["symbolic_conflicts"]:
                lines.append(f"  - {a} vs {b}")
        if divergence_report["cluster_sizes"]:
            lines.append("\n- Cluster Sizes:")
            for k, v in divergence_report["cluster_sizes"].items():
                lines.append(f"  - {k}: {v}")
        lines.append("")

        # Markdown Output: Symbolic Fragmentation Summary
        lines.append("## ⚠️ Symbolic Fragmentation Summary")
        lines.append(f"- Fragmented forecasts: {symbolic_fragmentation['total']}")
        lines.append("- Breakdown by arc:")
        for arc, count in symbolic_fragmentation["by_arc"].items():
            lines.append(f"  - {arc}: {count}")
        lines.append("")

        # Markdown Output: Compressed Cluster Memory
        lines.append("## 🧠 Compressed Cluster Memory\n")
        for c in compressed_cluster_forecasts:
            label = c.get("narrative_theme") or c.get("symbolic_tag") or "Unknown"
            trace_id = c.get("trace_id", "N/A")
            align = c.get("alignment", c.get("confidence", None))
            align_str = f"{align:.1f}" if isinstance(align, (float, int)) else "N/A"
            lines.append(f"- {label} → {trace_id} (Align: {align_str})")
        lines.append("")

        # Markdown Output: Most Evolved Forecasts by Cluster
        lines.append("## 🧬 Most Evolved Forecasts by Cluster\n")
        lines.append("| Cluster           | Trace ID | Arc Label     | Depth |")
        lines.append("|-------------------|----------|---------------|-------|")
        for leader in most_evolved_digest["leaders"]:
            lines.append(
                f"| {leader['tag']:<17} | {leader['trace_id']:<8} | {leader['arc'] or 'N/A':<13} | {leader['depth']}     |"
            )
        if not most_evolved_digest["leaders"]:
            lines.append("| _None found_      |          |               |       |")
        lines.append("")
        lines.append(f"**Mutation Depths:** {most_evolved_digest['mutation_depths']}\n")

        # --- Symbolic Entropy Report (Markdown) ---
        if entropy_report:
            lines.append("## 🌐 Symbolic Entropy Report\n")
            for k, v in entropy_report.items():
                lines.append(f"- {k.replace('_', ' ').capitalize()}: {v}")
            lines.append("")

        # Markdown Output: Dual Narrative Scenarios
        if dual_narrative_scenarios:
            lines.append("## 🔀 Dual Narrative Scenarios\n")
            for pair in dual_narrative_scenarios:
                a = pair.get("scenario_a", {})
                b = pair.get("scenario_b", {})
                lines.append(f"### {a.get('arc', 'A')} vs {b.get('arc', 'B')}\n")
                lines.append(f"**Scenario A ({a.get('arc', 'A')})**  ")
                lines.append(f"- Tag: {a.get('symbolic_tag', 'N/A')}  ")
                lines.append(f"- Alignment: {a.get('alignment_score', 'N/A')}  ")
                lines.append(f"- Confidence: {a.get('confidence', 'N/A')}\n")
                lines.append(f"**Scenario B ({b.get('arc', 'B')})**  ")
                lines.append(f"- Tag: {b.get('symbolic_tag', 'N/A')}  ")
                lines.append(f"- Alignment: {b.get('alignment_score', 'N/A')}  ")
                lines.append(f"- Confidence: {b.get('confidence', 'N/A')}\n")

        # Markdown Output: Fork Resolutions
        if fork_decisions:
            lines.append("## 🧭 Strategic Fork Resolutions\n")
            for d in fork_decisions:
                a = d.get("scenario_a", {})
                b = d.get("scenario_b", {})
                winner = d.get("winner_label", "N/A")
                winner_id = d.get("selected_trace_id", "N/A")
                winner_align = d.get("winner_alignment", "N/A")
                lines.append(
                    f"- {a.get('arc', 'A')} vs {b.get('arc', 'B')} → ✅ {winner}"
                )
                lines.append(f"  - Winner: {winner_id} (Align: {winner_align})\n")

        if isinstance(clusters, dict):
            cluster_items = clusters.items()
        elif isinstance(clusters, list):
            # If clusters is a list, treat each element as a cluster with a generated label
            cluster_items = [
                (f"Cluster {i + 1}", cluster) for i, cluster in enumerate(clusters)
            ]
        else:
            cluster_items = []
        for label, cluster in cluster_items:
            lines.append(f"==== {label} ====")
            # Ensure cluster is a list before passing to consensus_score
            cluster_list = cluster if isinstance(cluster, list) else []
            lines.append(
                f"Consensus ({overlay_key} rising): {consensus_score(cluster_list, overlay_key) * 100:.0f}%"
            )
            if show_drivers:
                drivers = summarize_drivers(cluster_list)
                if drivers and isinstance(drivers, list) and len(drivers) > 0:
                    lines.append(f"Top Drivers: {', '.join(drivers)}")
            for f in cluster_list:
                prompt_hash_value = f.get("prompt_hash") or get_prompt_hash(
                    f.get("trace_id", "")
                )
                f["prompt_hash"] = prompt_hash_value
                # Ensure fields is a list before passing to render_fields
                safe_fields = fields if isinstance(fields, list) else DEFAULT_FIELDS
                lines.extend(render_fields(f, safe_fields))
                # --- Causal Explanation (Markdown) ---
                if "causal_explanation" in f:
                    ce = f["causal_explanation"]
                    lines.append(
                        f"Causal Explanation: {ce.get('variable', '')} 2 Parents: {', '.join(ce.get('parents', []))}"
                    )
                lines.append("")
        if not clusters:
            lines.append("_No forecasts available._")
        stats = summarize_stats(flattened)
        lines.append(
            f"🎯 Avg Retrodiction Score: {stats['avg_retrodiction']} | Symbolic Score: {stats['avg_symbolic']}"
        )
        lines.append(f"📊 Confidence Sparkline: {stats['confidence_sparkline']}")
        lines.append(
            f"🕓 Forecast Age: Avg {stats['avg_age']}h | Max: {stats['max_age']}h"
        )
        lines.append(f"Total Forecasts: {stats['total']}")
        return "\n".join(lines)
    except Exception as e:
        logger.error(f"Digest build error: {e}")
        return f"⚠️ Digest build error: {e}"


def filter_forecasts_by_prompt(forecasts: List[Dict], prompt: str) -> List[Dict]:
    """
    Filter forecasts by prompt substring match (in prompt_hash or tags).
    """
    result = []
    for f in forecasts:
        if prompt.lower() in (str(f.get("prompt_hash", "")).lower() or ""):
            result.append(f)
        elif any(prompt.lower() in str(tag).lower() for tag in f.get("tags", [])):
            result.append(f)
    return result


if __name__ == "__main__":
    import argparse
    from core.path_registry import PATHS

    parser = argparse.ArgumentParser(description="Strategos Digest Builder CLI")
    parser.add_argument(
        "--from-prompt",
        type=str,
        default=None,
        help="Filter forecasts by prompt substring",
    )
    parser.add_argument(
        "--input",
        type=str,
        default=PATHS.get(
            "FORECAST_COMPRESSED", "logs/forecast_output_compressed.jsonl"
        ),
        help="Input JSON file (compressed forecasts)",
    )
    parser.add_argument(
        "--export",
        type=str,
        default="markdown",
        choices=["markdown", "json", "html"],
        help="Export format",
    )
    parser.add_argument("--output", type=str, default="digest.md", help="Output file")
    parser.add_argument(
        "--top-n", type=int, default=None, help="Show only top N clusters"
    )
    parser.add_argument(
        "--cluster-key", type=str, default="symbolic_tag", help="Cluster key"
    )
    parser.add_argument(
        "--actionable-only",
        action="store_true",
        help="Only include actionable forecasts",
    )
    parser.add_argument(
        "--template",
        type=str,
        default="full",
        help="Digest template (full, short, symbolic_only)",
    )

    args = parser.parse_args()

    # Load input file
    forecasts = []
    try:
        with open(args.input, "r", encoding="utf-8") as f:
            if args.input.endswith(".json"):
                # Try JSON load
                forecasts = json.load(f)
            elif args.input.endswith(".jsonl"):
                # Try JSONL load
                forecasts = [json.loads(line) for line in f if line.strip()]
            else:
                print("Unsupported file format. Please provide a .json or .jsonl file.")
                exit(1)
    except Exception as e:
        print(f"Failed to load input file: {e}")
        exit(1)

    # If input is cluster summary, flatten examples
    if forecasts and isinstance(forecasts[0], dict) and "examples" in forecasts[0]:
        batch = []
        for c in forecasts:
            batch.extend(c.get("examples", []))
        forecasts = batch

    # Prompt filter
    if args.from_prompt:
        forecasts = filter_forecasts_by_prompt(forecasts, args.from_prompt)

    config = {
        "top_n": args.top_n,
        "cluster_key": args.cluster_key,
        "actionable_only": args.actionable_only,
    }
    digest = build_digest(
        forecasts, fmt=args.export, config=config, template=args.template
    )

    # Export
    if args.export == "markdown":
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(digest)
        print(f"Digest exported to {args.output}")
    elif args.export == "json":
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(digest)
        print(f"Digest JSON exported to {args.output}")
    elif args.export == "html":
        try:
            import markdown2

            html = markdown2.markdown(digest)
            try:
                import bleach

                allowed_tags = list(bleach.sanitizer.ALLOWED_TAGS) + ["h1", "h2", "h3"]
                html = bleach.clean(html, tags=allowed_tags, strip=True)
            except ImportError:
                print("Warning: bleach not installed, HTML not sanitized.")
            with open(args.output, "w", encoding="utf-8") as f:
                f.write(html)
            print(f"Digest HTML exported to {args.output}")
        except ImportError:
            with open(args.output, "w", encoding="utf-8") as f:
                f.write("<pre>\n" + digest + "\n</pre>")
            print(
                f"Digest HTML exported to {args.output} (preformatted, markdown2 not installed)"
            )
    else:
        print("Unknown export format.")
