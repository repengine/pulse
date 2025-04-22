"""
trace_audit_engine.py

Core audit and replay functionality for Pulse simulation traces.

- Assigns and validates trace IDs
- Provides trace replay and summary logic
- Audits memory for fork integrity and overlay coherence

Author: Pulse v0.21
"""

import uuid
import json
import os
from typing import Any, Dict, Optional, List
from core.path_registry import PATHS
from memory.forecast_memory import ForecastMemory
from utils.log_utils import get_logger
from core.pulse_config import TRACE_OUTPUT_DIR

logger = get_logger(__name__)

def generate_trace_id() -> str:
    """Generates a unique UUID for a trace."""
    return str(uuid.uuid4())

def overlay_to_dict(overlay):
    """Convert SymbolicOverlay or dict to dict for JSON serialization."""
    if hasattr(overlay, "as_dict"):
        return overlay.as_dict()
    return dict(overlay)

def assign_trace_metadata(sim_input: Dict[str, Any], sim_output: Dict[str, Any]) -> Dict[str, Any]:
    """Attaches trace ID and metadata to a simulation output."""
    trace_id = generate_trace_id()
    # Ensure overlays are serializable
    if "overlays" in sim_output:
        sim_output["overlays"] = overlay_to_dict(sim_output["overlays"])
    metadata = {
        "trace_id": trace_id,
        "input": sim_input,
        "output": sim_output,
    }
    save_trace_to_disk(metadata)
    return metadata

def save_trace_to_disk(metadata: Dict[str, Any]) -> None:
    """Saves the full trace record to disk in JSON format."""
    os.makedirs(TRACE_OUTPUT_DIR, exist_ok=True)
    filepath = os.path.join(TRACE_OUTPUT_DIR, f"{metadata['trace_id']}.json")
    try:
        # Ensure overlays are serializable
        if "output" in metadata and "overlays" in metadata["output"]:
            metadata["output"]["overlays"] = overlay_to_dict(metadata["output"]["overlays"])
        # PATCH: Recursively convert overlays in forks if present
        if "output" in metadata and "forks" in metadata["output"]:
            for fork in metadata["output"]["forks"]:
                if "overlays" in fork:
                    fork["overlays"] = overlay_to_dict(fork["overlays"])
        with open(filepath, "w") as f:
            json.dump(metadata, f, indent=2)
        logger.info(f"[TRACE] Saved trace to {filepath}")
    except Exception as e:
        logger.error(f"[TRACE] Failed to save trace: {e}")

def load_trace(trace_id: str) -> Optional[Dict[str, Any]]:
    """Loads a trace from disk by trace ID."""
    filepath = os.path.join(TRACE_OUTPUT_DIR, f"{trace_id}.json")
    if not os.path.exists(filepath):
        logger.warning(f"[TRACE] Trace not found: {trace_id}")
        return None
    try:
        with open(filepath, "r") as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"[TRACE] Failed to load trace: {e}")
        return None

def replay_trace(trace_id: str) -> None:
    """Attempts to replay a simulation from stored inputs."""
    trace = load_trace(trace_id)
    if not trace:
        return
    try:
        from main import run_simulation  # local call to Pulse engine
        logger.info(f"[TRACE] Replaying trace: {trace_id}")
        result = run_simulation(config_override=trace["input"])
        logger.info(f"[TRACE] Replay completed. (New trust: {result.get('trust', 'n/a')})")
    except Exception as e:
        logger.error(f"[TRACE] Failed to replay trace: {e}")

def summarize_trace(trace_id: str) -> None:
    """Prints summary statistics of a trace."""
    trace = load_trace(trace_id)
    if not trace:
        return
    overlays = trace["output"].get("overlays", {})
    trust = trace["output"].get("trust", "N/A")
    forks = trace["output"].get("forks", [])
    print(f"Trace ID: {trace_id}")
    print(f"Overlays: {overlays}")
    print(f"Trust Score: {trust}")
    print(f"Fork Count: {len(forks)}")

def audit_all_traces() -> None:
    """Runs a basic integrity audit across all saved traces."""
    issues = 0
    if not os.path.exists(TRACE_OUTPUT_DIR):
        logger.warning("[AUDIT] Trace directory does not exist.")
        return
    for fname in os.listdir(TRACE_OUTPUT_DIR):
        if fname.endswith(".json"):
            path = os.path.join(TRACE_OUTPUT_DIR, fname)
            try:
                with open(path, "r") as f:
                    trace = json.load(f)
                if "trace_id" not in trace or "output" not in trace:
                    logger.error(f"[AUDIT] Corrupt or incomplete trace: {fname}")
                    issues += 1
                if not trace["output"].get("trust"):
                    logger.warning(f"[AUDIT] Missing trust score in: {fname}")
            except Exception as e:
                logger.error(f"[AUDIT] Failed to audit {fname}: {e}")
                issues += 1
    logger.info(f"[AUDIT] Completed with {issues} issue(s).")

def register_trace_to_memory(trace_metadata: Dict[str, Any]) -> None:
    """Registers a trace to the forecast memory layer."""
    try:
        # Ensure overlays are serializable
        if "output" in trace_metadata and "overlays" in trace_metadata["output"]:
            trace_metadata["output"]["overlays"] = overlay_to_dict(trace_metadata["output"]["overlays"])
        # PATCH: Recursively convert overlays in forks if present
        if "output" in trace_metadata and "forks" in trace_metadata["output"]:
            for fork in trace_metadata["output"]["forks"]:
                if "overlays" in fork:
                    fork["overlays"] = overlay_to_dict(fork["overlays"])
        memory = ForecastMemory()
        memory.store(trace_metadata)
        logger.info(f"[TRACE] Trace {trace_metadata['trace_id']} added to memory.")
    except Exception as e:
        logger.error(f"[TRACE] Failed to register trace to memory: {e}")