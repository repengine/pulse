"""
strategos_digest_builder.py

Combines symbolic arc, capital deltas, and confidence into a foresight digest report.
Supports user configuration for included fields.

Usage:
    from strategos_digest_builder import build_digest
    digest_md = build_digest(batch, fmt="markdown", config={"fields": ["trace_id", "confidence"]})

Author: Pulse AI Engine
"""

from typing import List, Dict, Any, Optional, Union
import json
from collections import defaultdict
import logging

try:
    from operator_interface.pulse_prompt_logger import get_prompt_hash
except ImportError:
    def get_prompt_hash(trace_id: str) -> Optional[str]:
        return None

logger = logging.getLogger("strategos_digest_builder")

DEFAULT_FIELDS = [
    "trace_id", "turn", "confidence", "fragility", "trust_label", "symbolic_tag", "overlays", "exposure_delta"
]

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
    """Compute summary statistics for the digest footer."""
    stats = {}
    confidences = [f.get("confidence", 0.0) for f in forecasts if isinstance(f.get("confidence", 0.0), (float, int))]
    ret_scores = [f.get("retrodiction_score", 0.0) for f in forecasts if isinstance(f.get("retrodiction_score", 0.0), (float, int))]
    sym_scores = [f.get("symbolic_score", 0.0) for f in forecasts if isinstance(f.get("symbolic_score", 0.0), (float, int))]
    ages = [f.get("age_hours", 0.0) for f in forecasts if isinstance(f.get("age_hours", 0.0), (float, int))]
    stats["avg_confidence"] = round(sum(confidences) / len(confidences), 3) if confidences else 0.0
    stats["avg_retrodiction"] = round(sum(ret_scores) / len(ret_scores), 3) if ret_scores else 0.0
    stats["avg_symbolic"] = round(sum(sym_scores) / len(sym_scores), 3) if sym_scores else 0.0
    stats["avg_age"] = round(sum(ages) / len(ages), 2) if ages else 0.0
    stats["max_age"] = max(ages) if ages else 0.0
    stats["total"] = len(forecasts)
    stats["confidence_sparkline"] = [round(c, 2) for c in confidences]
    return stats

def get_top_clusters(clusters: Dict[str, List[Dict]], n: int = 3, sort_by: str = "count") -> List[tuple]:
    """
    Return the top N clusters by count or average confidence.
    """
    if sort_by == "confidence":
        ranked = sorted(
            clusters.items(),
            key=lambda x: sum(f.get("confidence", 0) or 0 for f in x[1]) / max(len(x[1]), 1),
            reverse=True
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

def build_digest(
    forecast_batch: List[Dict[str, Any]],
    fmt: str = "markdown",
    config: Optional[dict] = None,
    template: str = "full"
) -> str:
    """
    Build a strategos digest from a batch of forecasts.

    Args:
        forecast_batch: List of forecast dicts.
        fmt: Output format ("markdown", "json", "html").
        config: Dict with customization options.
        template: Template type ("full", "short", "symbolic_only").
    Returns:
        Digest string in requested format.

    Example:
        build_digest(batch, fmt="markdown", config={"fields": ["trace_id", "confidence"]}, template="short")
    """
    if not forecast_batch:
        if fmt == "json":
            return "[]"
        if fmt == "html":
            return "<h1>Strategos Digest</h1><i>No forecasts available.</i>"
        return "# Strategos Digest\n\n_No forecasts available._"

    # Template support
    if template == "short":
        fields = ["trace_id", "confidence", "symbolic_tag"]
    elif template == "symbolic_only":
        fields = ["trace_id", "symbolic_tag", "overlays"]
    else:
        fields = config.get("fields") if config and "fields" in config else DEFAULT_FIELDS

    tag_filter = config.get("tag_filter") if config else None
    overlay_key = config.get("consensus_overlay", "hope") if config else "hope"
    cluster_key = config.get("cluster_key", "symbolic_tag") if config else "symbolic_tag"
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

    # Tag filter
    if tag_filter:
        flattened = [f for f in flattened if tag_filter in f.get("tags", [])]

    # Actionable only filter
    if actionable_only:
        flattened = [f for f in flattened if f.get("confidence_status") == "✅ Actionable"]

    # Prefer narrative_theme if present and requested
    if cluster_key == "narrative_theme" and not any("narrative_theme" in f for f in flattened):
        cluster_key = "symbolic_tag"

    clusters = cluster_by_key(flattened, cluster_key)

    # Top N clusters
    if top_n:
        clusters = dict(get_top_clusters(clusters, n=top_n, sort_by=sort_clusters_by))

    try:
        if fmt == "json":
            return json.dumps([{k: f.get(k) for k in fields} for f in flattened], indent=2)
        if fmt == "html":
            lines = ["<h1>Strategos Digest</h1>"]
            for label, cluster in clusters.items():
                lines.append(f"<h2>{label}</h2>")
                lines.append(f"<b>Consensus ({overlay_key} rising):</b> {consensus_score(cluster, overlay_key)*100:.0f}%<br>")
                if show_drivers:
                    drivers = summarize_drivers(cluster)
                    if drivers:
                        lines.append(f"<b>Top Drivers:</b> {', '.join(drivers)}<br>")
                for f in cluster:
                    prompt_hash = f.get("prompt_hash") or get_prompt_hash(f.get("trace_id", ""))
                    f["prompt_hash"] = prompt_hash
                    for k in fields:
                        v = f.get(k, "N/A")
                        lines.append(f"<b>{k}:</b> {v}<br>")
                lines.append("<hr>")
            if not clusters:
                lines.append("<i>No forecasts available.</i>")
            stats = summarize_stats(flattened)
            lines.append(f"<b>Avg Retrodiction Score:</b> {stats['avg_retrodiction']} | <b>Symbolic Score:</b> {stats['avg_symbolic']}<br>")
            lines.append(f"<b>Confidence Sparkline:</b> {stats['confidence_sparkline']}<br>")
            lines.append(f"<b>Forecast Age:</b> Avg {stats['avg_age']}h | Max: {stats['max_age']}h<br>")
            lines.append(f"<b>Total Forecasts:</b> {stats['total']}<br>")
            return "\n".join(lines)
        # Default: markdown
        lines = ["# Strategos Digest\n"]
        for label, cluster in clusters.items():
            lines.append(f"==== {label} ====")
            lines.append(f"Consensus ({overlay_key} rising): {consensus_score(cluster, overlay_key)*100:.0f}%")
            if show_drivers:
                drivers = summarize_drivers(cluster)
                if drivers:
                    lines.append(f"Top Drivers: {', '.join(drivers)}")
            for f in cluster:
                prompt_hash = f.get("prompt_hash") or get_prompt_hash(f.get("trace_id", ""))
                f["prompt_hash"] = prompt_hash
                lines.extend(render_fields(f, fields))
                lines.append("")
        if not clusters:
            lines.append("_No forecasts available._")
        stats = summarize_stats(flattened)
        lines.append(f"🎯 Avg Retrodiction Score: {stats['avg_retrodiction']} | Symbolic Score: {stats['avg_symbolic']}")
        lines.append(f"📊 Confidence Sparkline: {stats['confidence_sparkline']}")
        lines.append(f"🕓 Forecast Age: Avg {stats['avg_age']}h | Max: {stats['max_age']}h")
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
    parser.add_argument("--from-prompt", type=str, default=None, help="Filter forecasts by prompt substring")
    parser.add_argument("--input", type=str, default=PATHS.get("FORECAST_COMPRESSED", "logs/forecast_output_compressed.jsonl"), help="Input JSON file (compressed forecasts)")
    parser.add_argument("--export", type=str, default="markdown", choices=["markdown", "json", "html"], help="Export format")
    parser.add_argument("--output", type=str, default="digest.md", help="Output file")
    parser.add_argument("--top-n", type=int, default=None, help="Show only top N clusters")
    parser.add_argument("--cluster-key", type=str, default="symbolic_tag", help="Cluster key")
    parser.add_argument("--actionable-only", action="store_true", help="Only include actionable forecasts")
    parser.add_argument("--template", type=str, default="full", choices=["full", "short", "symbolic_only"], help="Digest template")
    args = parser.parse_args()

    # Load compressed forecasts
    import json
    try:
        with open(args.input, "r", encoding="utf-8") as f:
            try:
                forecasts = json.load(f)
            except Exception:
                # Try JSONL fallback
                forecasts = [json.loads(line) for line in f if line.strip()]
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
    digest = build_digest(forecasts, fmt=args.export, config=config, template=args.template)

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
            with open(args.output, "w", encoding="utf-8") as f:
                f.write(html)
            print(f"Digest HTML exported to {args.output}")
        except ImportError:
            with open(args.output, "w", encoding="utf-8") as f:
                f.write("<pre>\n" + digest + "\n</pre>")
            print(f"Digest HTML exported to {args.output} (preformatted, markdown2 not installed)")
    else:
        print("Unknown export format.")
