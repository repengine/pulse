"""
forecast_pipeline_runner.py

Runs the full Pulse forecast processing pipeline:
- Trust scoring
- Fragility detection
- Symbolic overlays (optional)
- Trace linking
- Forecast compression
- Symbolic summarization
- Digest generation
- Export to memory or logs

Author: Pulse v0.23
"""

from typing import List, Dict, Optional, Any
from core.pulse_config import USE_SYMBOLIC_OVERLAYS
from forecast_output.forecast_compressor import compress_forecasts
from forecast_output.forecast_summary_synthesizer import summarize_forecasts
from forecast_output.strategos_digest_builder import build_digest
from trust_system.trust_engine import score_forecasts
from trust_system.fragility_detector import tag_fragility
from memory.trace_audit_engine import assign_trace_metadata, register_trace_to_memory
from memory.forecast_memory import ForecastMemory
from utils.log_utils import log_info
from forecast_output.forecast_prioritization_engine import select_top_forecasts
import os, json

# Add memory promoter imports
from memory.forecast_memory_promotor import select_promotable_forecasts, export_promoted

# --- Capital Layer Imports ---
from capital_engine.capital_layer import run_capital_forks, summarize_exposure, portfolio_alignment_tags

from forecast_output.forecast_confidence_gate import filter_by_confidence
from memory.trace_memory import TraceMemory

# Step 1: Import the Tracker
from memory.variable_performance_tracker import VariablePerformanceTracker

# Add contradiction detector import
from forecast_output.forecast_contradiction_detector import detect_forecast_contradictions
from core.pulse_learning_log import log_learning_event

def run_forecast_pipeline(
    forecasts: List[Dict[str, Any]],
    batch_id: Optional[str] = None,
    enable_digest: bool = True,
    save_to_memory: bool = True
) -> Dict[str, Any]:
    """
    Executes the full forecast processing pipeline.

    Args:
        forecasts (List[Dict]): Raw forecast objects. Each should be a dict with at least 'confidence' and 'symbolic_tag'.
        batch_id (str, optional): Optional batch label.
        enable_digest (bool): Whether to generate digest output.
        save_to_memory (bool): Whether to write to memory.

    Returns:
        Dict: Final pipeline result bundle.
    """
    log_info("[PIPELINE] Starting forecast pipeline...")
    if not forecasts or not isinstance(forecasts, list):
        log_info("[PIPELINE] No forecasts provided or input is not a list.")
        return {"status": "no_forecasts"}

    # Validate forecast structure
    for i, f in enumerate(forecasts):
        if not isinstance(f, dict):
            log_info(f"[PIPELINE] Warning: Forecast at index {i} is not a dict. Skipping.")
            continue

    # Step 1: Score trust + fragility
    try:
        scored = score_forecasts(forecasts)
        scored = tag_fragility(scored)
        # Apply confidence + fragility filter
        scored = filter_by_confidence(scored)
        # OPTIONAL: Drop rejected forecasts from pipeline
        scored = [f for f in scored if f.get("confidence_status") != "❌ Rejected"]
    except Exception as e:
        log_info(f"[PIPELINE] Error during trust/fragility scoring: {e}")
        return {"status": "error", "error": str(e)}

    # --- Contradiction detection + learning log ---
    contradictions = detect_forecast_contradictions(scored)
    if contradictions:
        for tid1, tid2, reason in contradictions:
            log_learning_event("forecast_contradiction_detected", {
                "trace_id_1": tid1,
                "trace_id_2": tid2,
                "reason": reason
            })
        # Optionally flag involved forecasts as contradictory
        involved = {tid1 for tid1, _, _ in contradictions} | {tid2 for _, tid2, _ in contradictions}
        for f in scored:
            if f.get("trace_id") in involved:
                f["confidence_status"] = "❌ Contradictory"

    # --- Confidence gating: filter out low-confidence forecasts ---
    try:
        scored = filter_by_confidence(scored)
        log_info(f"[PIPELINE] Confidence gate applied: {len(scored)} forecasts retained.")
    except Exception as e:
        log_info(f"[PIPELINE] Confidence gating failed: {e}")

    # Initialize trace memory logger
    trace_logger = TraceMemory()

    # Step 2: Initialize VariablePerformanceTracker
    tracker = VariablePerformanceTracker()

    # Step 2: Apply symbolic overlays if enabled
    if USE_SYMBOLIC_OVERLAYS:
        try:
            from symbolic_system.pulse_symbolic_arc_tracker import compute_arc_label
        except ImportError as e:
            log_info(f"[PIPELINE] Could not import compute_arc_label: {e}")
            compute_arc_label = None

        for f in scored:
            try:
                if compute_arc_label:
                    arc = compute_arc_label(f)
                    f["arc_label"] = arc
                else:
                    f["arc_label"] = "arc_unknown"
            except Exception as e:
                f["arc_label"] = "arc_unknown"
                log_info(f"[PIPELINE] Arc label error: {e}")

    # Step 3: Assign trace IDs and register
    for f in scored:
        try:
            trace_meta = assign_trace_metadata({}, f)
            register_trace_to_memory(trace_meta)
            # Log to trace memory
            trace_logger.log_trace_entry(
                trace_id=f.get("trace_id", "unknown"),
                forecast=f,
                input_state={}  # Replace with state.to_dict() if state is available
            )
            # Log variable impact to performance tracker
            input_state = f.get("input_state", {})  # Replace with actual sim state if available
            tracker.log_variable_contribution(f, input_state)
        except Exception as e:
            log_info(f"[PIPELINE] Trace assignment/registration failed: {e}")

    # Step 4: Compress forecasts
    try:
        compressed = compress_forecasts(scored)
    except Exception as e:
        log_info(f"[PIPELINE] Compression failed: {e}")
        compressed = []

    # Step 5: Summarize symbolically
    try:
        summarize_forecasts(compressed)
    except Exception as e:
        log_info(f"[PIPELINE] Warning during summary: {e}")

    # Step 6: Digest
    digest_result = None
    if enable_digest:
        try:
            digest_result = build_digest(forecast_batch=compressed, tag="auto", export=True)
        except Exception as e:
            log_info(f"[PIPELINE] Digest failed: {e}")

    # Step 7: Memory store
    if save_to_memory:
        try:
            memory = ForecastMemory()
            for f in compressed:
                memory.store(f)
        except Exception as e:
            log_info(f"[PIPELINE] Memory store failed: {e}")

    # --- Select top forecasts and export ---
    top = []
    try:
        top = select_top_forecasts(compressed, top_n=5)
        prioritized_log = os.path.join("logs", "strategic_batch_output.jsonl")
        os.makedirs(os.path.dirname(prioritized_log), exist_ok=True)
        with open(prioritized_log, "w") as f:
            for fc in top:
                f.write(json.dumps(fc) + "\n")
        log_info(f"[PIPELINE] Top {len(top)} forecasts exported to {prioritized_log}")

        # --- Auto-promote strategic forecasts to memory ---
        promotable = select_promotable_forecasts(top)
        if promotable:
            export_promoted(promotable)
            log_info(f"[PIPELINE] {len(promotable)} top forecasts auto-promoted to memory.")
    except Exception as e:
        log_info(f"[PIPELINE] Top forecast selection/export/promote failed: {e}")

    # Log summary of rejected forecasts
    rejected = [f for f in scored if f.get("confidence_status") == "❌ Rejected"]
    log_info(f"[PIPELINE] {len(rejected)} forecasts rejected by confidence gate")

    # Print trace memory summary
    summary = trace_logger.summarize_memory()
    log_info(f"[TRACE MEMORY] Recent summary: {summary}")

    # Step 4 (Optional): Export Variable Scores at End of Pipeline
    tracker.export_variable_scores()

    log_info("[PIPELINE] Forecast pipeline complete.")
    result_bundle = {
        "status": "complete",
        "total": len(forecasts),
        "compressed": len(compressed),
        "digest": digest_result,
        "top_forecasts": top,
    }

    # --- Capital Layer: add exposure and alignment summaries if state is available ---
    # If you have a WorldState object, pass it here. Otherwise, adapt as needed.
    # result_bundle["capital_exposure"] = summarize_exposure(state)
    # result_bundle["capital_alignment"] = portfolio_alignment_tags(state)

    return result_bundle

def _test_pipeline():
    """Basic test for pipeline logic."""
    import json
    sample = [
        {"confidence": 0.71, "symbolic_tag": "hope", "drivers": ["AI rally"]},
        {"confidence": 0.43, "symbolic_tag": "fatigue", "drivers": ["media overload"]}
    ]
    result = run_forecast_pipeline(sample)
    print(json.dumps(result, indent=2))

# Example CLI trigger
if __name__ == "__main__":
    _test_pipeline()
