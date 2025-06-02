"""
worldstate_monitor.py

Provides display and logging functions for Pulse simulation:
- Symbolic overlays
- Capital exposure
- Variable states
- Delta view vs prior state
- Optional logging to file

Author: Pulse v0.4
"""

from engine.worldstate import WorldState
import logging
from engine.variable_accessor import get_variable, get_overlay
from engine.path_registry import PATHS
import datetime
import os
from typing import Optional, List, Dict, Any

assert isinstance(PATHS, dict), f"PATHS is not a dict, got {type(PATHS)}"


# Import gravity explainer functionality
try:
    from diagnostics.gravity_explainer import (
        display_correction_explanation,
        plot_gravity_correction_details_html,
        export_gravity_explanation_json,
    )

    GRAVITY_EXPLAINER_AVAILABLE = True
except ImportError:
    GRAVITY_EXPLAINER_AVAILABLE = False
    print("Warning: Gravity Explainer module not available.")

    # Define fallback stub functions for type checking
    def display_correction_explanation(trace_data, variable_name):
        print("Gravity explainer module not available.")

    def plot_gravity_correction_details_html(
        trace_data, variable_name, output_path, max_steps=None
    ):
        print("Gravity explainer module not available.")
        return output_path  # Return the path to match original function's return type

    def export_gravity_explanation_json(trace_data, variable_name, output_path):
        print("Gravity explainer module not available.")
        return output_path  # Return the path to match original function's return type


logger = logging.getLogger(__name__)


def display_overlay_state(state: WorldState) -> None:
    """Prints symbolic overlays to the CLI."""
    for key in state.overlays.as_dict().keys():
        print(f"{key}: {get_overlay(state, key)}")


def display_capital_exposure(state: WorldState) -> None:
    """Prints capital exposure to the CLI."""
    print("\n💰 Capital Exposure:")
    for asset, val in state.capital.as_dict().items():
        print(f"  {asset.upper():<6} → ${val:,.2f}")


def display_variable_state(state: WorldState) -> None:
    """Prints worldstate variables to the CLI using variable accessor."""
    variables = state.variables
    if isinstance(variables, dict):
        for key in variables.keys():
            print(f"{key}: {get_variable(state, key)}")
    else:
        print(f"variables: {variables}")


def display_deltas(state: WorldState, prev_state: WorldState) -> None:
    """Prints overlay deltas vs previous state."""
    print("\n🔁 Overlay Change (Δ vs last turn):")
    for name, current in state.overlays.as_dict().items():
        prev = prev_state.overlays.as_dict().get(name, 0)
        delta = current - prev
        print(f"  {name:<8} → Δ {delta:+.3f}")


def display_all(
    state: WorldState, prev_state: Optional[WorldState] = None, log: bool = False
) -> None:
    """
    Displays all worldstate info and optionally logs to file.
    """
    stamp = f"TURN {state.turn}"
    print(f"\n=== {stamp} STATE ===")
    display_overlay_state(state)
    display_capital_exposure(state)
    display_variable_state(state)
    if prev_state:
        display_deltas(state, prev_state)
    print("=" * 35)

    if log:
        folder = PATHS["WORLDSTATE_LOG_DIR"]
        os.makedirs(folder, exist_ok=True)
        ts = datetime.datetime.utcnow().strftime("%Y-%m-%d_%H-%M")
        file = os.path.join(folder, f"state_{state.turn}_{ts}.txt")
        with open(file, "w", encoding="utf-8") as f:
            f.write(f"Turn {state.turn} Worldstate Snapshot\n")
            f.write(f"Overlays: {state.overlays.as_dict()}\n")
            f.write(f"Capital : {state.capital.as_dict()}\n")
            f.write(f"Vars    : {state.variables.as_dict()}\n")
            f.write("\n")
        print(f"📁 State saved to {file}")


def run_batch_forecasts(
    count=5,
    domain="capital",
    min_conf=0.5,
    symbolic_block=None,
    verbose=True,
    export_summary=True,
):
    """
    Runs a batch of forecasts and logs summary to centralized path.
    """
    logs = []
    rejected = 0
    for i in range(count):
        forecast_id = f"forecast_{i}"
        metadata = {"confidence": 0.7}  # Example metadata
        accepted_condition = metadata.get("confidence", 0) >= min_conf and (
            symbolic_block is None or symbolic_block(metadata)
        )
        if accepted_condition:
            logs.append(
                {"forecast_id": forecast_id, "status": "accepted", "metadata": metadata}
            )
            if verbose:
                logger.info(f"✅ Accepted [{forecast_id}] | Metadata: {metadata}")
        else:
            rejected += 1
            reason = (
                "low_confidence"
                if metadata.get("confidence", 0) < min_conf
                else "blocked_symbolic"
            )
            logs.append(
                {
                    "forecast_id": forecast_id,
                    "status": "rejected",
                    "reason": reason,
                    "metadata": metadata,
                }
            )
            if verbose:
                logger.warning(
                    f"⛔ Rejected [{forecast_id}] ({reason}) | Metadata: {metadata}"
                )
    if export_summary:
        summary_file = PATHS["BATCH_FORECAST_SUMMARY"]
        os.makedirs(os.path.dirname(summary_file), exist_ok=True)
        with open(summary_file, "w", encoding="utf-8") as f:
            f.write("Batch Forecast Summary\n")
            f.write(f"Total forecasts: {count}\n")
            f.write(f"Rejected: {rejected}\n")
            f.write(f"Logs: {logs}\n")
        logger.info(f"📁 Summary saved to {summary_file}")


def display_gravity_correction_details(
    trace_data: List[Dict[str, Any]],
    variable_name: str,
    output_format: str = "text",
    output_dir: Optional[str] = None,
) -> Optional[str]:
    """
    Display gravity correction details for a specific variable.

    This function acts as an entry point to the gravity explanation features,
    supporting multiple output formats.

    Args:
        trace_data: Simulation trace data containing gravity correction details
        variable_name: Name of the variable to explain
        output_format: Format of the output ("text", "html", "json")
        output_dir: Directory for output files (for non-text formats)

    Returns:
        Path to the output file (for non-text formats) or None (for text)
    """
    if not GRAVITY_EXPLAINER_AVAILABLE:
        print("ERROR: Gravity Explainer module is required but not available.")
        return None

    # Check if trace contains gravity correction data
    has_gravity_data = False
    for step in trace_data:
        if "gravity_correction_details" in step:
            has_gravity_data = True
            break

    if not has_gravity_data:
        print(
            "No gravity correction data found in the trace. Was the simulation run with gravity enabled?"
        )
        return None

    # Display using the appropriate format
    if not GRAVITY_EXPLAINER_AVAILABLE:
        print("ERROR: Gravity Explainer module is required but not available.")
        return None

    if output_format == "text":
        # Call the display function directly
        display_correction_explanation(trace_data, variable_name)
        return None

    elif output_format in ["html", "json"]:
        # Create output directory if not provided
        if output_dir is None:
            default_dir = os.path.join(
                str(PATHS.get("VIZ_DIR", "visualizations")), "gravity_explanations"
            )
            output_dir = str(PATHS.get("GRAVITY_EXPLANATIONS_DIR", default_dir))

        # Ensure directory exists (with type checking)
        if output_dir is not None:
            os.makedirs(output_dir, exist_ok=True)

            # Generate timestamp
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")

            if output_format == "html":
                # Generate HTML visualization
                output_path = os.path.join(
                    output_dir, f"gravity_{variable_name}_{timestamp}.html"
                )
                # Call the function directly
                return plot_gravity_correction_details_html(
                    trace_data, variable_name, output_path
                )

            elif output_format == "json":
                # Export as JSON
                output_path = os.path.join(
                    output_dir, f"gravity_{variable_name}_{timestamp}.json"
                )
                # Call the function directly
                return export_gravity_explanation_json(
                    trace_data, variable_name, output_path
                )
        else:
            print("ERROR: Output directory is required for non-text formats")
            return None

    else:
        print(f"Unknown output format: {output_format}")
        print("Supported formats: text, html, json")
        return None
