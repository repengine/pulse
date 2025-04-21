from forecast_output.forecast_licenser import filter_licensed_forecasts
from forecast_output.forecast_compressor import compress_forecasts
from forecast_output.strategos_tile_formatter import format_strategos_tile
from forecast_output.strategos_digest_builder import build_digest
from memory.forecast_memory import ForecastMemory
from typing import Optional, List, Dict
from core.path_registry import PATHS
from trust_system.alignment_index import compute_alignment_index
from trust_system.forecast_episode_logger import summarize_episodes
from trust_system.trust_engine import compute_symbolic_attention_score
import os
assert isinstance(PATHS, dict), f"PATHS is not a dict, got {type(PATHS)}"

DIGEST_DIR = PATHS.get("DIGEST_DIR", PATHS["WORLDSTATE_LOG_DIR"])

def group_by_confidence(forecasts: List[Dict]) -> Dict[str, List[Dict]]:
    """
    Group forecasts by confidence levels.

    Args:
        forecasts (List[Dict]): List of forecast dictionaries.

    Returns:
        Dict[str, List[Dict]]: Grouped forecasts by confidence levels.
    """
    groups = {"🟢 Trusted": [], "⚠️ Moderate": [], "🔴 Fragile": [], "🔘 Unscored": []}
    for f in forecasts:
        score = f.get("confidence", "unscored")
        if isinstance(score, float):
            if score >= 0.75:
                groups["🟢 Trusted"].append(f)
            elif score >= 0.5:
                groups["⚠️ Moderate"].append(f)
            else:
                groups["🔴 Fragile"].append(f)
        else:
            groups["🔘 Unscored"].append(f)
    for label in groups:
        groups[label].sort(key=lambda f: f.get("confidence", 0.0), reverse=True)
        groups[label].sort(key=lambda f: f.get('priority_score', 0.0), reverse=True)
    return groups

def compute_arc_drift(prev_path: str, curr_path: str) -> Dict[str, int]:
    """
    Compute the drift in symbolic arcs between two episode logs.
    """
    prev = summarize_episodes(prev_path)
    curr = summarize_episodes(curr_path)
    arcs_prev = {k.replace("arc_", ""): v for k, v in prev.items() if k.startswith("arc_")}
    arcs_curr = {k.replace("arc_", ""): v for k, v in curr.items() if k.startswith("arc_")}
    all_keys = set(arcs_prev) | set(arcs_curr)
    return {k: arcs_curr.get(k, 0) - arcs_prev.get(k, 0) for k in all_keys}

def generate_strategos_digest(
    memory: ForecastMemory,
    n: int = 5,
    title: Optional[str] = None,
    previous_episode_log: Optional[str] = None,
    current_episode_log: Optional[str] = None
) -> str:
    """
    Generate a Strategos digest from forecast memory.

    Args:
        memory (ForecastMemory): Forecast memory instance.
        n (int, optional): Number of recent forecasts to include. Defaults to 5.
        title (Optional[str], optional): Title for the digest. Defaults to None.
        previous_episode_log (Optional[str], optional): Path to previous episode log.
        current_episode_log (Optional[str], optional): Path to current episode log.

    Returns:
        str: Strategos digest as a formatted string.
    """
    raw = memory.get_recent(n + 5)
    forecasts = filter_licensed_forecasts(raw, strict=True)

    # --- Alignment scoring integration ---
    for forecast in forecasts:
        alignment = compute_alignment_index(forecast)
        forecast["alignment_score"] = alignment["alignment_score"]

    # Optionally sort by alignment_score (top-N)
    forecasts = sorted(forecasts, key=lambda f: f.get("alignment_score", 0), reverse=True)

    groups = group_by_confidence(forecasts)
    header = title or "Strategos Forecast Digest"

    sections = [f"📘 {header}", ""]

    # Arc drift summary
    arc_drift = {}
    if previous_episode_log and current_episode_log and os.path.exists(previous_episode_log) and os.path.exists(current_episode_log):
        arc_drift = compute_arc_drift(previous_episode_log, current_episode_log)
        if arc_drift:
            sections.append("## 🌀 Arc Drift This Cycle")
            for arc, delta in arc_drift.items():
                sign = "+" if delta > 0 else ""
                sections.append(f"- {arc}: {sign}{delta}")
            sections.append("")

    for label in ["🟢 Trusted", "⚠️ Moderate", "🔴 Fragile", "🔘 Unscored"]:
        tiles = groups[label]
        if not tiles:
            continue
        sections.append(f"==== {label} ====")
        for tile in tiles:
            # Display alignment alongside confidence
            conf = tile.get("confidence", "N/A")
            align = tile.get("alignment_score", "N/A")
            # Add attention score if arc_drift is available
            attention = ""
            if arc_drift:
                try:
                    attn_score = compute_symbolic_attention_score(tile, arc_drift)
                    if attn_score > 0.5:
                        attention = f" | ⚡️Attention: {attn_score}"
                    elif attn_score > 0:
                        attention = f" | Attention: {attn_score}"
                except Exception as e:
                    attention = " | ⚠️ Attention Error"
            sections.append(f"[Conf: {conf} | Align: {align}{attention}]")
            sections.append(format_strategos_tile(tile))
        sections.append("")

    # Footer: summary stats
    try:
        ret_scores = [f.get("retrodiction_score", 0.0) for f in forecasts if isinstance(f.get("retrodiction_score"), (float, int))]
        sym_scores = [f.get("symbolic_score", 0.0) for f in forecasts if isinstance(f.get("symbolic_score"), (float, int))]
        avg_r = round(sum(ret_scores) / len(ret_scores), 3) if ret_scores else 0.0
        avg_s = round(sum(sym_scores) / len(sym_scores), 3) if sym_scores else 0.0
        sections.append(f"🎯 Avg Retrodiction Score: {avg_r} | Symbolic Score: {avg_s}")
    except:
        sections.append("⚠️ Retrodiction stats unavailable.")

    try:
        sparkline = [round(f.get("confidence", 0.0), 2) for f in forecasts]
        sections.append(f"📊 Confidence Sparkline: {sparkline}")
    except:
        pass

    try:
        ages = [f.get("age_hours", 0) for f in forecasts]
        if ages:
            avg_age = round(sum(ages) / len(ages), 2)
            oldest = max(ages)
            sections.append(f"🕓 Forecast Age: Avg {avg_age}h | Max: {oldest}h")
    except:
        pass

    sections.append(f"Total Forecasts: {len(forecasts)}")

    return "\n".join(sections)

def live_digest_ui(memory: ForecastMemory, prompt: str = None, n: int = 10, export_fmt: str = "markdown", template: str = "full"):
    """
    Live UI hook: Build and display strategos digest, optionally filtered by prompt and template.

    Example:
        live_digest_ui(memory, prompt="AI", n=10, export_fmt="markdown", template="short")
    """
    raw = memory.get_recent(n + 10)
    if prompt:
        # Use digest builder's filter for prompt
        from forecast_output.strategos_digest_builder import filter_forecasts_by_prompt
        raw = filter_forecasts_by_prompt(raw, prompt)
    digest = build_digest(raw, fmt=export_fmt, config={"top_n": 3, "actionable_only": False}, template=template)
    print(digest)
    return digest