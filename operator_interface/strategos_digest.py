import logging
from typing import Optional, List, Dict, Any
from forecast_output.forecast_licenser import filter_licensed_forecasts

# from forecast_output.forecast_compressor import compress_forecasts  # Removed unused import
from forecast_output.strategos_tile_formatter import format_strategos_tile
from forecast_output.strategos_digest_builder import build_digest
from analytics.forecast_memory import ForecastMemory
from engine.path_registry import PATHS
from trust_system.alignment_index import compute_alignment_index
from trust_system.forecast_episode_logger import summarize_episodes
from trust_system.trust_engine import compute_symbolic_attention_score
from trust_system.forecast_licensing_shell import license_forecast
from engine.simulation_drift_detector import run_simulation_drift_analysis
from trust_system.license_enforcer import (
    annotate_forecasts,
    filter_licensed,
    summarize_license_distribution,
)
from forecast_output.mutation_compression_engine import (
    compress_episode_chain,
    plot_symbolic_trajectory,
)
from analytics.forecast_episode_tracer import build_episode_chain
from symbolic_system.symbolic_transition_graph import (
    build_symbolic_graph,
    visualize_symbolic_graph,
)

# from symbolic_system.pulse_symbolic_revision_planner import plan_revisions_for_fragmented_arcs  # Removed unused import
import matplotlib.pyplot as plt
import os
import json

# --- PATCH: Import resonance scanner ---
from forecast_output.forecast_resonance_scanner import generate_resonance_summary

# --- PATCH: Import forecast certification digest ---
from forecast_output.forecast_fidelity_certifier import generate_certified_digest

# --- PATCH: Import forecast prioritization engine ---
from forecast_output.forecast_prioritization_engine import select_top_forecasts

# --- PATCH: Import narrative cluster classifier ---
from forecast_output.forecast_cluster_classifier import (
    classify_forecast_cluster,
    summarize_cluster_counts,
)

from operator_interface.rule_cluster_digest_formatter import (
    format_cluster_digest_md,
)  # PATCH 2

assert isinstance(PATHS, dict), f"PATHS is not a dict, got {type(PATHS)}"

DIGEST_DIR = PATHS.get("DIGEST_DIR", PATHS["WORLDSTATE_LOG_DIR"])


def safe_save_plot(fig, path: str) -> bool:
    """Safely save a matplotlib figure to disk."""
    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        fig.savefig(path)
        return True
    except Exception as e:
        logging.error(f"Failed to save plot to {path}: {e}")
        return False


def group_by_confidence(
    forecasts: List[Dict[str, Any]],
) -> Dict[str, List[Dict[str, Any]]]:
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
    # Sort by priority_score, then confidence (descending)
    for label in groups:
        groups[label].sort(
            key=lambda f: (f.get("priority_score", 0.0), f.get("confidence", 0.0)),
            reverse=True,
        )
    return groups


def compute_arc_drift(prev_path: str, curr_path: str) -> Dict[str, int]:
    """
    Compute the drift in symbolic arcs between two episode logs.

    Args:
        prev_path (str): Path to previous episode log.
        curr_path (str): Path to current episode log.

    Returns:
        Dict[str, int]: Arc label to drift delta.
    """
    try:
        prev = summarize_episodes(prev_path)
        curr = summarize_episodes(curr_path)
    except Exception as e:
        print(f"⚠️ Error summarizing episodes: {e}")
        return {}
    # --- FIX: Add type conversion for values ---
    arcs_prev = {
        k.replace("arc_", ""): float(v) if isinstance(v, (int, float, str)) else 0
        for k, v in prev.items()
        if k.startswith("arc_")
    }
    arcs_curr = {
        k.replace("arc_", ""): float(v) if isinstance(v, (int, float, str)) else 0
        for k, v in curr.items()
        if k.startswith("arc_")
    }
    all_keys = set(arcs_prev) | set(arcs_curr)
    return {k: arcs_curr.get(k, 0) - arcs_prev.get(k, 0) for k in all_keys}


def flag_drift_sensitive_forecasts(
    forecasts: List[Dict[str, Any]],
    drift_report: Dict[str, Any],
    threshold: float = 0.2,
) -> List[Dict[str, Any]]:
    """
    Flags forecasts if they belong to unstable arcs or drift-prone rule sets.

    Args:
        forecasts (List[Dict])
        drift_report (Dict): Output from run_simulation_drift_analysis()
        threshold (float): Drift cutoff for flagging

    Returns:
        List[Dict]: forecasts updated with 'drift_flag'
    """
    volatile_rules = {
        r
        for r, delta in drift_report.get("rule_trigger_delta", {}).items()
        if abs(delta) > threshold * 10
    }
    unstable_overlays = {
        k for k, v in drift_report.get("overlay_drift", {}).items() if v > threshold
    }

    for fc in forecasts:
        # arc = fc.get("arc_label", "unknown")  # Removed unused variable
        rules = fc.get("fired_rules", [])
        overlays = fc.get("forecast", {}).get("symbolic_change", {})

        flagged = False
        if any(r in volatile_rules for r in rules):
            fc["drift_flag"] = "⚠️ Rule Instability"
            flagged = True
        if any(k in unstable_overlays for k in overlays):
            fc["drift_flag"] = "⚠️ Overlay Volatility"
            flagged = True
        if not flagged:
            fc["drift_flag"] = "✅ Stable"
    return forecasts


def _extract_symbolic_flip_patterns(_: List[Dict[str, Any]]) -> List[str]:
    """
    Placeholder: Extract symbolic flip patterns from forecasts.
    """
    # TODO: Implement actual pattern detection
    return ["ARC: Despair → ARC: Rage (4x)", "TAG: Neutral → TAG: Collapse Risk (3x)"]


def _extract_detected_loops(_: List[Dict[str, Any]]) -> List[str]:
    """
    Placeholder: Extract detected loops from forecasts.
    """
    # TODO: Implement actual loop detection
    return ["TAG: Fatigue ↔ TAG: Despair", "ARC: Collapse Risk ↔ ARC: Stabilization"]


def generate_strategos_digest(
    memory: ForecastMemory,
    n: int = 5,
    title: Optional[str] = None,
    previous_episode_log: Optional[str] = None,
    current_episode_log: Optional[str] = None,
    previous_trace_path: Optional[str] = None,
    current_trace_path: Optional[str] = None,
) -> str:
    """
    Generate a Strategos digest from forecast memory.

    Args:
        memory (ForecastMemory): Forecast memory instance.
        n (int, optional): Number of recent forecasts to include. Defaults to 5.
        title (Optional[str], optional): Title for the digest. Defaults to None.
        previous_episode_log (Optional[str], optional): Path to previous episode log.
        current_episode_log (Optional[str], optional): Path to current episode log.
        previous_trace_path (Optional[str], optional): Path to previous simulation trace.
        current_trace_path (Optional[str], optional): Path to current simulation trace.

    Returns:
        str: Strategos digest as a formatted string.
    """
    raw = memory.get_recent(n + 5)
    # --- PATCH: Validate input forecasts ---
    if not isinstance(raw, list):
        return "❌ Error: Forecast memory did not return a list."
    try:
        forecasts = filter_licensed_forecasts(raw, strict=True)
    except Exception as e:
        return f"❌ Error filtering licensed forecasts: {e}"

    # --- Trust enforcement logic ---
    original_count = len(forecasts)
    try:
        forecasts = annotate_forecasts(forecasts)
        forecasts = filter_licensed(forecasts)
        licensed_count = len(forecasts)
        drop_rate = round(100 * (1 - licensed_count / max(original_count, 1)), 2)
        license_summary = summarize_license_distribution(forecasts)
    except Exception as e:
        licensed_count = 0
        drop_rate = 100.0
        license_summary = f"❌ License enforcement error: {e}"

    # --- License loss warning logic ---
    digest = {}
    digest["license_loss_percent"] = drop_rate
    digest["warnings"] = []
    if digest.get("license_loss_percent", 0) > 40:
        warning_msg = "🔍 Triggering symbolic audit due to high license loss."
        digest["warnings"].append(warning_msg)
        logging.warning(warning_msg)
        # Optionally call symbolic audit system or arc drift scanner here

    # --- Alignment scoring integration ---
    for forecast in forecasts:
        try:
            alignment = compute_alignment_index(forecast)
            forecast["alignment_score"] = alignment.get("alignment_score", 0.0)
        except Exception as e:
            forecast["alignment_score"] = 0.0
            forecast["alignment_error"] = str(e)

    # --- Forecast Licensing Summary ---
    licensed = {"approved": 0, "rejected": 0, "low_alignment": 0}
    for fc in forecasts:
        try:
            license_status = license_forecast(fc)
        except Exception as e:
            license_status = f"❌ Licensing Error: {e}"
        fc["license_status"] = license_status
        if license_status == "✅ Approved":
            licensed["approved"] += 1
        else:
            licensed["rejected"] += 1
            if "Alignment" in license_status:
                licensed["low_alignment"] += 1

    # Build and compress symbolic lineages
    digest["compressed_episodes"] = []
    trace_ids = [f.get("trace_id") for f in forecasts if "lineage" in f]
    for root in trace_ids:
        if root is not None:
            chain = build_episode_chain(forecasts, root_id=root)
            if len(chain) > 1:
                compressed = compress_episode_chain(chain)
                digest["compressed_episodes"].append(compressed)

    # --- Symbolic learning profile integration ---
    from symbolic_system.pulse_symbolic_learning_loop import (
        generate_learning_profile,
        learn_from_tuning_log,
    )
    from symbolic_system.symbolic_upgrade_planner import propose_symbolic_upgrades

    tuning_log = "logs/tuning_results.jsonl"
    os.makedirs(os.path.dirname(tuning_log), exist_ok=True)
    if os.path.exists(tuning_log):
        results = learn_from_tuning_log(tuning_log)
        digest["symbolic_learning_profile"] = generate_learning_profile(results)

    # --- Symbolic upgrade plan integration ---
    results = learn_from_tuning_log(tuning_log)
    profile = generate_learning_profile(results)
    digest["symbolic_upgrade_plan"] = propose_symbolic_upgrades(profile)

    # --- Symbolic tuning summary integration ---
    from symbolic_system.symbolic_executor import rewrite_forecast_symbolics
    from trust_system.recovered_forecast_scorer import summarize_repair_quality

    digest["symbolic_tuning_summary"] = {}

    # Learn
    results = learn_from_tuning_log(tuning_log)
    profile = generate_learning_profile(results)
    digest["symbolic_tuning_summary"]["learning_profile"] = profile

    # Propose upgrade plan
    plan = propose_symbolic_upgrades(profile)
    digest["symbolic_tuning_summary"]["upgrade_plan"] = plan

    # Apply upgrade and score
    try:
        with open("forecasts/revision_candidates.jsonl", "r") as f:
            forecasts = [json.loads(line) for line in f if line.strip()]
        mutated = rewrite_forecast_symbolics(forecasts, plan)
        summary = summarize_repair_quality(mutated)
        digest["symbolic_tuning_summary"]["repair_quality"] = summary
        digest["symbolic_tuning_summary"]["total_mutations"] = len(mutated)
    except Exception as e:
        digest["symbolic_tuning_summary"]["repair_quality"] = f"Error: {e}"
        digest["symbolic_tuning_summary"]["total_mutations"] = 0

    # --- PATCH: Symbolic resonance summary ---
    digest["symbolic_resonance"] = generate_resonance_summary(
        forecasts, key="arc_label"
    )

    # --- PATCH: Add forecast certification summary to digest ---
    digest["forecast_certification"] = generate_certified_digest(forecasts)

    # --- PATCH: Narrative Cluster Classification ---
    # Tag forecasts with narrative cluster
    for fc in forecasts:
        fc["narrative_cluster"] = classify_forecast_cluster(fc)

    # Build summary
    digest["narrative_cluster_summary"] = summarize_cluster_counts(forecasts)

    # Optionally sort by alignment_score (top-N)
    forecasts = sorted(
        forecasts, key=lambda f: f.get("alignment_score", 0), reverse=True
    )

    # --- PATCH: Top Strategic Forecasts Integration ---
    top_forecasts = select_top_forecasts(forecasts, top_n=5)
    digest["strategic_top_forecasts"] = [
        {
            "trace_id": f.get("trace_id"),
            "arc": f.get("arc_label"),
            "tag": f.get("symbolic_tag"),
            "alignment": f.get("alignment_score"),
            "confidence": f.get("confidence"),
        }
        for f in top_forecasts
    ]

    groups = group_by_confidence(forecasts)
    header = title or "Strategos Forecast Digest"

    sections = [f"📘 {header}", ""]

    # --- PATCH: Markdown output for Top Strategic Forecasts ---
    if digest.get("strategic_top_forecasts"):
        sections.append("## 🧭 Top Strategic Forecasts\n")
        sections.append("| Trace ID | Arc | Tag | Alignment | Confidence |")
        sections.append("|----------|-----|-----|-----------|------------|")
        for fc in digest["strategic_top_forecasts"]:
            sections.append(
                f"| {fc.get('trace_id', '')} | {fc.get('arc', '')} | {fc.get('tag', '')} | {fc.get('alignment', '')} | {fc.get('confidence', '')} |"
            )
        sections.append("")

    # --- Trust Enforcement Report ---
    sections.append("## 🛡️ Trust Enforcement Report")
    sections.append(f"- Total forecasts: {original_count}")
    sections.append(f"- Approved: {licensed_count}")
    sections.append(f"- Rejected: {original_count - licensed_count}")
    sections.append(f"- License drop rate: {drop_rate:.2f}%")
    if isinstance(license_summary, dict):
        for k, v in license_summary.items():
            sections.append(f"- {k}: {v}")
    else:
        sections.append(str(license_summary))
    if drop_rate > 40:
        sections.append("⚠️ High license loss rate — trust coherence degraded.")
    sections.append("")

    # --- Licensing Summary Markdown Section ---
    sections.append("## ✅ Forecast Licensing Summary")
    sections.append(f"- Approved: {licensed['approved']}")
    sections.append(f"- Rejected: {licensed['rejected']}")
    sections.append(f"- Low Alignment: {licensed['low_alignment']}")
    sections.append("")

    # --- PATCH: Markdown output for forecast certification summary ---
    cert = digest.get("forecast_certification")
    if cert:
        sections.append("## ✅ Forecast Certification Summary")
        sections.append(f"- Certified: {cert.get('certified', 0)}")
        sections.append(f"- Uncertified: {cert.get('uncertified', 0)}")
        sections.append(f"- Certification Rate: {cert.get('certified_ratio', 'N/A')}")
        sections.append("")

    # --- PATCH: Markdown output for Narrative Cluster Breakdown ---
    cluster_summary = digest.get("narrative_cluster_summary")
    if cluster_summary:
        sections.append("## 🧠 Narrative Cluster Breakdown\n")
        sections.append("| Cluster             | Count |")
        sections.append("|---------------------|-------|")
        for cluster, count in cluster_summary.items():
            sections.append(f"| {cluster:<19} | {count:<5} |")
        sections.append("")

    # Arc drift summary
    arc_drift = {}
    if (
        previous_episode_log
        and current_episode_log
        and os.path.exists(previous_episode_log)
        and os.path.exists(current_episode_log)
    ):
        arc_drift = compute_arc_drift(previous_episode_log, current_episode_log)
        if arc_drift:
            sections.append("## 🌀 Arc Drift This Cycle")
            for arc, delta in arc_drift.items():
                sign = "+" if delta > 0 else ""
                sections.append(f"- {arc}: {sign}{delta}")
            sections.append("")

    # Simulation drift summary
    drift_report = None
    if (
        previous_trace_path
        and current_trace_path
        and os.path.exists(previous_trace_path)
        and os.path.exists(current_trace_path)
    ):
        try:
            drift_report = run_simulation_drift_analysis(
                previous_trace_path, current_trace_path
            )
            if "error" in drift_report:
                sections.append(
                    f"⚠️ Simulation drift analysis failed: {drift_report['error']}"
                )
            else:
                sections.append("## 🧪 Simulation Drift Summary")
                for k, v in drift_report.get("overlay_drift", {}).items():
                    sign = "+" if v > 0 else ""
                    sections.append(f"- Overlay Δ {k.capitalize()}: {sign}{v:.3f}")
                if drift_report.get("rule_trigger_delta"):
                    sections.append("- Rule trigger delta:")
                    for rule, delta in drift_report["rule_trigger_delta"].items():
                        sign = "+" if delta > 0 else ""
                        sections.append(f"  - {rule}: {sign}{delta}")
                if (
                    drift_report.get("structure_shift")
                    and "turn_diff" in drift_report["structure_shift"]
                ):
                    td = drift_report["structure_shift"]["turn_diff"]
                    sign = "+" if td > 0 else ""
                    sections.append(f"- Turn count changed by: {sign}{td}")
                sections.append("")
        except Exception as e:
            sections.append(f"⚠️ Simulation drift analysis failed: {e}")

    # Flag drift-sensitive forecasts if drift_report is available
    if drift_report and "error" not in drift_report:
        forecasts = flag_drift_sensitive_forecasts(forecasts, drift_report)

    # --- Drift-Flagged Forecasts Section ---
    drifted = [
        f
        for f in forecasts
        if f.get("drift_flag") in {"⚠️ Rule Instability", "⚠️ Overlay Volatility"}
    ]
    if drifted:
        sections.append("## 🔥 Drift-Flagged Forecasts")
        for fc in drifted[:10]:
            sections.append(f"- {fc.get('trace_id', 'unknown')} → {fc['drift_flag']}")
        sections.append("")

    # 🧪 Optional Digest Markdown Summary: Compressed Mutation Episodes
    if digest["compressed_episodes"]:
        sections.append("## 🔁 Compressed Mutation Episodes")
        for ce in digest["compressed_episodes"]:
            root_id = ce.get("root_id", "unknown")
            label = ce.get("label", "")
            versions = ce.get("version_count", len(ce.get("chain", [])))
            tag_flips = ce.get("tag_flips", 0)
            arc_status = ce.get("arc_status", "")
            summary = f"- {root_id} → {label} ({versions} versions"
            if tag_flips:
                summary += f", {tag_flips} tag flips"
            if arc_status:
                summary += f", {arc_status}"
            summary += ")"
            sections.append(summary)
            plot_path = os.path.join("plots", f"symbolic_trajectory_{root_id}.png")
            try:
                plot_symbolic_trajectory(
                    ce.get("mutation_compressed_from", []), export_path=plot_path
                )
                sections.append(f"![Trajectory]({plot_path})")
            except Exception as e:
                logging.error(f"Could not plot trajectory for {root_id}: {e}")
                sections.append(f"⚠️ Could not plot trajectory for {root_id}: {e}")
        sections.append("")

    # ➕ Symbolic Transition Graph Section
    try:
        symbolic_graph = build_symbolic_graph(forecasts)
        fig = visualize_symbolic_graph(symbolic_graph, title="Strategic Symbolic Map")
        plot_path = os.path.join("plots", "strategos_symbolic_graph.png")
        if safe_save_plot(fig, plot_path):
            digest["symbolic_graph_path"] = plot_path
            sections.append("## 🌐 Symbolic Transition Graph")
            sections.append(f"![Symbolic Graph]({plot_path})")
            sections.append("")
        plt.close(fig)
    except Exception as e:
        logging.error(f"Could not generate symbolic transition graph: {e}")
        sections.append(f"⚠️ Could not generate symbolic transition graph: {e}")
        sections.append("")

    # --- PATCH: Symbolic Resonance Markdown Output ---
    resonance = digest.get("symbolic_resonance")
    if resonance:
        sections.append("## 🔗 Symbolic Resonance")
        sections.append(f"- Resonance Score: {resonance.get('resonance_score', 'N/A')}")
        sections.append(f"- Dominant Arc: {resonance.get('dominant_arc', 'N/A')}")
        if resonance.get("top_themes"):
            sections.append(f"- Top Themes: {', '.join(resonance['top_themes'])}")
        if resonance.get("cluster_sizes"):
            sections.append("- Cluster Sizes:")
            for k, v in resonance["cluster_sizes"].items():
                sections.append(f"  - {k}: {v}")
        sections.append("")

    # --- Markdown output for symbolic tuning summary ---
    if "symbolic_tuning_summary" in digest:
        sts = digest["symbolic_tuning_summary"]
        sections.append("## 🧠 Symbolic Tuning Summary\n")
        # Learning Insights
        sections.append("### Learning Insights")
        lp = sts.get("learning_profile", {})
        if lp:
            strong = lp.get("strong_tags") or lp.get("strong", [])
            risky = lp.get("risky_tags") or lp.get("risky", [])
            if strong:
                sections.append(f"- Strong Tags: {', '.join(strong)}")
            if risky:
                sections.append(f"- Risky Tags: {', '.join(risky)}")
        # Upgrade Plan
        sections.append("\n### Upgrade Plan")
        up = sts.get("upgrade_plan", {})
        if up:
            boost = up.get("boost", []) or up.get("boost_tags", [])
            replace = (
                up.get("replace") or up.get("retune") or up.get("replace_retune") or []
            )
            if boost:
                sections.append(f"- Boost: {boost}")
            if replace:
                sections.append(f"- Replace/Retune: {replace}")
        # Results
        sections.append("\n### Results")
        total = sts.get("total_mutations", 0)
        rq = sts.get("repair_quality", {})
        stable = rq.get("stable_after_revision") if isinstance(rq, dict) else None
        unstable = rq.get("still_unstable") if isinstance(rq, dict) else None
        sections.append(f"- Total Rewritten: {total}")
        if stable is not None:
            sections.append(f"- Stable After Revision: {stable}")
        if unstable is not None:
            sections.append(f"- Still Unstable: {unstable}")
        if isinstance(rq, str):
            sections.append(f"- Repair Quality: {rq}")
        sections.append("")

    # ➕ Symbolic Flip Patterns and Loops Section (dynamic)
    sections.append("## ♻️ Symbolic Flip Patterns")
    for pattern in _extract_symbolic_flip_patterns(forecasts):
        sections.append(f"- {pattern}")
    sections.append("")
    sections.append("## 🔁 Detected Loops")
    for loop in _extract_detected_loops(forecasts):
        sections.append(f"- {loop}")
    sections.append("")

    for label in ["🟢 Trusted", "⚠️ Moderate", "🔴 Fragile", "🔘 Unscored"]:
        tiles = groups[label]
        if not tiles:
            continue
        sections.append(f"==== {label} ====")
        for tile in tiles:
            conf = tile.get("confidence", "N/A")
            align = tile.get("alignment_score", "N/A")
            drift_flag = tile.get("drift_flag", "")
            attention = ""
            if arc_drift:
                try:
                    attn_score = compute_symbolic_attention_score(tile, arc_drift)
                    if attn_score > 0.5:
                        attention = f" | ⚡️Attention: {attn_score}"
                    elif attn_score > 0:
                        attention = f" | Attention: {attn_score}"
                except Exception:
                    attention = " | ⚠️ Attention Error"
            drift_note = (
                f" | {drift_flag}" if drift_flag and drift_flag != "✅ Stable" else ""
            )
            try:
                tile_str = format_strategos_tile(tile)
            except Exception as e:
                tile_str = f"⚠️ Error formatting tile: {e}"
            sections.append(f"[Conf: {conf} | Align: {align}{attention}{drift_note}]")
            sections.append(tile_str)
        sections.append("")

    try:
        ret_scores = [
            f.get("retrodiction_score", 0.0)
            for f in forecasts
            if isinstance(f.get("retrodiction_score"), (float, int))
        ]
        sym_scores = [
            f.get("symbolic_score", 0.0)
            for f in forecasts
            if isinstance(f.get("symbolic_score"), (float, int))
        ]
        avg_r = round(sum(ret_scores) / len(ret_scores), 3) if ret_scores else 0.0
        avg_s = round(sum(sym_scores) / len(sym_scores), 3) if sym_scores else 0.0
        sections.append(f"🎯 Avg Retrodiction Score: {avg_r} | Symbolic Score: {avg_s}")
    except Exception as e:
        sections.append(f"⚠️ Retrodiction stats unavailable: {e}")

    try:
        sparkline = [round(f.get("confidence", 0.0), 2) for f in forecasts]
        sections.append(f"📊 Confidence Sparkline: {sparkline}")
    except Exception as e:
        sections.append(f"⚠️ Sparkline unavailable: {e}")

    try:
        ages = [f.get("age_hours", 0) for f in forecasts]
        if ages:
            avg_age = round(sum(ages) / len(ages), 2)
            oldest = max(ages)
            sections.append(f"🕓 Forecast Age: Avg {avg_age}h | Max: {oldest}h")
    except Exception as e:
        sections.append(f"⚠️ Age stats unavailable: {e}")

    sections.append(f"Total Forecasts: {len(forecasts)}")

    # --- PATCH: Rule Cluster Digest Section ---
    sections.append("\n## 🧩 Rule Cluster Digest\n")
    sections.append(format_cluster_digest_md(limit=3))

    return "\n".join(sections)


def live_digest_ui(
    memory: ForecastMemory,
    prompt: Optional[str] = None,
    n: int = 10,
    export_fmt: str = "markdown",
    template: str = "full",
) -> str:
    """
    Live UI hook: Build and display strategos digest, optionally filtered by prompt and template.

    Args:
        memory (ForecastMemory): Forecast memory instance.
        prompt (Optional[str]): Filter prompt.
        n (int): Number of forecasts.
        export_fmt (str): Output format.
        template (str): Digest template.

    Returns:
        str: Digest forecast_output.
    """
    raw = memory.get_recent(n + 10)
    if prompt:
        try:
            from forecast_output.strategos_digest_builder import (
                filter_forecasts_by_prompt,
            )

            raw = filter_forecasts_by_prompt(raw, prompt)
        except Exception as e:
            print(f"⚠️ Error filtering by prompt: {e}")
    try:
        digest = build_digest(
            raw,
            fmt=export_fmt,
            config={"top_n": 3, "actionable_only": False},
            template=template,
        )
    except Exception as e:
        digest = f"❌ Error building digest: {e}"
    print(digest)
    return digest


# --- Simple test function for manual validation ---
def _test_digest():
    """Basic test for strategos digest generation."""
    import unittest

    class DummyMemory(ForecastMemory):
        def get_recent(self, n, domain=None, default=None):
            # Add a malformed entry for robustness
            return [
                {
                    "confidence": 0.8,
                    "alignment_score": 80,
                    "trust_label": "🟢 Trusted",
                    "priority_score": 1,
                    "retrodiction_score": 0.9,
                    "symbolic_score": 0.8,
                    "age_hours": 2,
                },
                {
                    "confidence": 0.6,
                    "alignment_score": 60,
                    "trust_label": "⚠️ Moderate",
                    "priority_score": 0.5,
                    "retrodiction_score": 0.7,
                    "symbolic_score": 0.6,
                    "age_hours": 5,
                },
                {
                    "confidence": 0.4,
                    "alignment_score": 40,
                    "trust_label": "🔴 Fragile",
                    "priority_score": 0.2,
                    "retrodiction_score": 0.5,
                    "symbolic_score": 0.4,
                    "age_hours": 10,
                },
                {},  # malformed
            ]

    class StrategosDigestTest(unittest.TestCase):
        def test_digest_runs(self):
            digest = generate_strategos_digest(DummyMemory(), n=3, title="Test Digest")
            self.assertIn("Test Digest", digest)
            self.assertIn("🛡️ Trust Enforcement Report", digest)
            self.assertIn("Strategos Forecast Digest", digest or "")

    unittest.TextTestRunner().run(
        unittest.TestLoader().loadTestsFromTestCase(StrategosDigestTest)
    )


if __name__ == "__main__":
    _test_digest()
