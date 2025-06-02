"""
gravity_explainer.py

This module provides explanations and visualizations for the symbolic gravity
corrections applied during simulations. It helps users understand why specific
corrections were applied to variables by showing the contribution of various
symbolic pillars and their underlying data points.

Features:
- Text-based explanations of gravity corrections
- HTML visualizations of correction details
- Drill-down into pillar contributions and source data points
- Comparison of causal vs. gravity deltas over time

Author: Pulse v3.5
"""

import logging
import json
import os
from typing import Dict, List, Optional
import numpy as np
from datetime import datetime
import matplotlib.pyplot as plt

# Try importing plotly with fallback to matplotlib
go = None
make_subplots = None
try:
    import plotly.graph_objects as go
    from plotly.subplots import make_subplots

    PLOTLY_AVAILABLE = True
except ImportError:
    PLOTLY_AVAILABLE = False
    # go and make_subplots remain None
    logging.warning("Plotly not available. Using matplotlib for visualizations.")

# Import necessary Pulse components

logger = logging.getLogger(__name__)


def display_correction_explanation(trace_data: List[Dict], variable_name: str) -> None:
    """
    Display a textual explanation of gravity corrections for a specific variable.

    Parameters
    ----------
    trace_data : List[Dict]
        Simulation trace data containing gravity correction details
    variable_name : str
        The name of the variable to explain corrections for

    Returns
    -------
    None
        Prints explanation to console
    """
    if not trace_data:
        print(f"No trace data provided for variable '{variable_name}'")
        return

    print(f"\n=== Gravity Correction Explanation for '{variable_name}' ===\n")

    # Track if we found any gravity correction data
    found_data = False

    for step_idx, step in enumerate(trace_data):
        turn = step.get("turn", step_idx)

        # Check if gravity correction details exist
        gravity_details = step.get("gravity_correction_details", {})
        if not gravity_details:
            continue

        # Check if details for this variable exist
        var_details = gravity_details.get(variable_name, {})
        if not var_details:
            continue

        found_data = True

        # Extract correction information
        gravity_delta = var_details.get("gravity_delta", 0.0)
        causal_delta = var_details.get("causal_delta", 0.0)

        # Get dominant pillars information
        dominant_pillars = var_details.get("dominant_pillars", [])

        # Print step information
        print(f"Turn {turn}:")
        print(f"  Causal Delta: {causal_delta:+.4f}")
        print(f"  Gravity Delta: {gravity_delta:+.4f}")

        # Calculate the net effect
        net_delta = causal_delta + gravity_delta
        print(f"  Net Effect: {net_delta:+.4f}")

        # Print dominant pillars information
        if dominant_pillars:
            print("\n  Dominant Symbolic Pillars:")
            for pillar_info in dominant_pillars:
                pillar_name = pillar_info.get("pillar_name", "Unknown")
                weight = pillar_info.get("weight", 0.0)

                # Calculate contribution percentage
                contribution_pct = 0
                if abs(gravity_delta) > 1e-10:  # Avoid division by zero
                    contribution_pct = (weight * 100) / abs(gravity_delta)

                print(
                    f"    {pillar_name}: weight={weight:+.4f} (contribution: {contribution_pct:.1f}%)"
                )

                # Print source data points if available
                source_points = pillar_info.get("source_data_points", [])
                if source_points:
                    print(f"      Based on {len(source_points)} data points:")
                    # Show up to 3 most influential data points
                    for i, point in enumerate(source_points[:3]):
                        point_id = point.get("id", "Unknown")
                        point_value = point.get("value", 0.0)
                        point_ts = point.get("timestamp", "Unknown")
                        print(f"      - {point_id}: value={point_value} @ {point_ts}")

                    if len(source_points) > 3:
                        print(
                            f"      ... and {len(source_points) - 3} more data points"
                        )

        print("\n" + "-" * 50)

    if not found_data:
        print(f"No gravity correction data found for variable '{variable_name}'")
        print(
            "Make sure simulation was run with '--explain-gravity' flag and variable exists in the simulation."
        )

    print("\n")


def plot_gravity_correction_details_html(
    trace_data: List[Dict],
    variable_name: str,
    output_path: str,
    max_steps: Optional[int] = None,
) -> str:
    """
    Generate an interactive HTML plot of gravity correction details.

    Parameters
    ----------
    trace_data : List[Dict]
        Simulation trace data containing gravity correction details
    variable_name : str
        The name of the variable to visualize corrections for
    output_path : str
        Path where the HTML output will be saved
    max_steps : Optional[int]
        Maximum number of steps to include (from the end of trace)

    Returns
    -------
    str
        Path to the generated HTML file
    """
    if not PLOTLY_AVAILABLE:
        return _plot_gravity_correction_details_matplotlib(
            trace_data, variable_name, output_path, max_steps
        )

    assert go is not None
    assert make_subplots is not None

    # Extract data for plotting
    steps = []
    causal_deltas = []
    gravity_deltas = []
    net_deltas = []
    pillar_weights = {}

    # Process the trace data
    relevant_trace = trace_data
    if max_steps is not None and len(trace_data) > max_steps:
        relevant_trace = trace_data[-max_steps:]

    for step in relevant_trace:
        turn = step.get("turn", len(steps))
        steps.append(turn)

        # Get gravity correction details
        gravity_details = step.get("gravity_correction_details", {})
        var_details = gravity_details.get(variable_name, {})

        # Add deltas
        causal_delta = var_details.get("causal_delta", 0.0)
        gravity_delta = var_details.get("gravity_delta", 0.0)
        causal_deltas.append(causal_delta)
        gravity_deltas.append(gravity_delta)
        net_deltas.append(causal_delta + gravity_delta)

        # Process pillar data for each step
        dominant_pillars = var_details.get("dominant_pillars", [])
        for pillar_info in dominant_pillars:
            pillar_name = pillar_info.get("pillar_name", "Unknown")
            weight = pillar_info.get("weight", 0.0)

            if pillar_name not in pillar_weights:
                pillar_weights[pillar_name] = [0] * len(steps)

            # Ensure the pillar weights list has enough entries
            while len(pillar_weights[pillar_name]) < len(steps):
                pillar_weights[pillar_name].append(0)

            pillar_weights[pillar_name][-1] = weight

    # Create figure
    fig = make_subplots(
        rows=2,
        cols=1,
        subplot_titles=("Simulation Deltas Over Time", "Pillar Contributions"),
        vertical_spacing=0.15,
        specs=[[{"type": "scatter"}], [{"type": "bar"}]],
    )

    # Add traces for deltas
    fig.add_trace(
        go.Scatter(
            x=steps,
            y=causal_deltas,
            mode="lines+markers",
            name="Causal Delta",
            line=dict(color="blue", width=2),
            hovertemplate="Step %{x}<br>Causal Delta: %{y:.4f}",
        ),
        row=1,
        col=1,
    )

    fig.add_trace(
        go.Scatter(
            x=steps,
            y=gravity_deltas,
            mode="lines+markers",
            name="Gravity Delta",
            line=dict(color="red", width=2),
            hovertemplate="Step %{x}<br>Gravity Delta: %{y:.4f}",
        ),
        row=1,
        col=1,
    )

    fig.add_trace(
        go.Scatter(
            x=steps,
            y=net_deltas,
            mode="lines+markers",
            name="Net Delta",
            line=dict(color="green", width=2, dash="dash"),
            hovertemplate="Step %{x}<br>Net Delta: %{y:.4f}",
        ),
        row=1,
        col=1,
    )

    # Add pillar weight traces for the last step
    if steps and pillar_weights:
        last_step = steps[-1]
        pillar_names = list(pillar_weights.keys())
        pillar_values = [pillar_weights[name][-1] for name in pillar_names]

        # Sort pillars by absolute weight for better visualization
        sorted_indices = np.argsort(np.abs(pillar_values))[::-1]
        sorted_names = [pillar_names[i] for i in sorted_indices]
        sorted_values = [pillar_values[i] for i in sorted_indices]

        # Take top 7 pillars for better readability
        top_names = sorted_names[:7]
        top_values = sorted_values[:7]

        # Use different colors for positive and negative values
        colors = ["green" if val >= 0 else "red" for val in top_values]

        fig.add_trace(
            go.Bar(
                x=top_names,
                y=top_values,
                marker_color=colors,
                name=f"Step {last_step} Pillar Weights",
                hovertemplate="%{x}<br>Weight: %{y:.4f}",
            ),
            row=2,
            col=1,
        )

    # Update layout
    fig.update_layout(
        title=f"Gravity Correction Analysis for Variable: {variable_name}",
        hovermode="closest",
        height=800,
        template="plotly_white",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        annotations=[
            dict(
                text="Click on a bar to see source data points (if available)",
                showarrow=False,
                xref="paper",
                yref="paper",
                x=0.5,
                y=0.25,
                font=dict(size=10),
            )
        ],
    )

    fig.update_xaxes(title_text="Simulation Step", row=1, col=1)
    fig.update_yaxes(title_text="Delta Value", row=1, col=1)

    fig.update_xaxes(title_text="Symbolic Pillars", row=2, col=1)
    fig.update_yaxes(title_text="Weight Contribution", row=2, col=1)

    # Add callback for bar click (this will be a JS function in the HTML)
    # This creates pop-up information about source data points when a pillar
    # bar is clicked
    fig.update_layout(clickmode="event+select")

    # Generate the HTML content
    html_content = fig.to_html(include_plotlyjs="cdn", full_html=True)

    # Add JavaScript for interactive features
    html_content = html_content.replace(
        "</head>",
        """
        <script>
        document.addEventListener('DOMContentLoaded', function() {
            var myPlot = document.getElementById('plotly-html-element');
            myPlot.on('plotly_click', function(data) {
                // Check if click was on a pillar bar
                if (data.points[0].data.type === 'bar') {
                    var pillarName = data.points[0].x;
                    var weight = data.points[0].y.toFixed(4);

                    // Get source data points (this would need to be added as a custom data attribute)
                    // For now, just show a placeholder message
                    var message = "Pillar: " + pillarName + "\\nWeight: " + weight;
                    message += "\\n\\nSource data points for this pillar are not available in this view.";
                    message += "\\nUse the CLI explanation for more detailed information.";

                    alert(message);
                }
            });
        });
        </script>
        </head>
        """,
    )

    # Save to file
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html_content)

    logger.info(f"Gravity correction visualization saved to {output_path}")
    return output_path


def _plot_gravity_correction_details_matplotlib(
    trace_data: List[Dict],
    variable_name: str,
    output_path: str,
    max_steps: Optional[int] = None,
) -> str:
    """
    Fallback matplotlib implementation when plotly is not available.

    Parameters
    ----------
    trace_data : List[Dict]
        Simulation trace data containing gravity correction details
    variable_name : str
        The name of the variable to visualize corrections for
    output_path : str
        Path where the HTML output will be saved
    max_steps : Optional[int]
        Maximum number of steps to include (from the end of trace)

    Returns
    -------
    str
        Path to the generated HTML file
    """
    # Extract data for plotting
    steps = []
    causal_deltas = []
    gravity_deltas = []
    net_deltas = []
    pillar_weights = {}

    # Process the trace data
    relevant_trace = trace_data
    if max_steps is not None and len(trace_data) > max_steps:
        relevant_trace = trace_data[-max_steps:]

    for step in relevant_trace:
        turn = step.get("turn", len(steps))
        steps.append(turn)

        # Get gravity correction details
        gravity_details = step.get("gravity_correction_details", {})
        var_details = gravity_details.get(variable_name, {})

        # Add deltas
        causal_delta = var_details.get("causal_delta", 0.0)
        gravity_delta = var_details.get("gravity_delta", 0.0)
        causal_deltas.append(causal_delta)
        gravity_deltas.append(gravity_delta)
        net_deltas.append(causal_delta + gravity_delta)

        # Process pillar data for the last step only
        if step == relevant_trace[-1]:
            dominant_pillars = var_details.get("dominant_pillars", [])
            for pillar_info in dominant_pillars:
                pillar_name = pillar_info.get("pillar_name", "Unknown")
                weight = pillar_info.get("weight", 0.0)
                pillar_weights[pillar_name] = weight

    # Create figure with two subplots
    fig, (ax1, ax2) = plt.subplots(
        2, 1, figsize=(10, 12), gridspec_kw={"height_ratios": [3, 2]}
    )

    # Plot deltas
    ax1.plot(steps, causal_deltas, "b-o", label="Causal Delta")
    ax1.plot(steps, gravity_deltas, "r-o", label="Gravity Delta")
    ax1.plot(steps, net_deltas, "g--o", label="Net Delta")

    ax1.set_title(f"Simulation Deltas Over Time for {variable_name}")
    ax1.set_xlabel("Simulation Step")
    ax1.set_ylabel("Delta Value")
    ax1.legend()
    ax1.grid(True, alpha=0.3)

    # Plot pillar weights
    if pillar_weights:
        names = list(pillar_weights.keys())
        values = list(pillar_weights.values())

        # Sort by absolute weight
        sorted_indices = np.argsort(np.abs(values))[::-1]
        sorted_names = [names[i] for i in sorted_indices]
        sorted_values = [values[i] for i in sorted_indices]

        # Take top 7 for readability
        top_names = sorted_names[:7]
        top_values = sorted_values[:7]

        # Use different colors for positive and negative
        colors = ["green" if val >= 0 else "red" for val in top_values]

        ax2.bar(top_names, top_values, color=colors)
        ax2.set_title(f"Pillar Contributions for Step {steps[-1]}")
        ax2.set_xlabel("Symbolic Pillars")
        ax2.set_ylabel("Weight Contribution")
        ax2.grid(True, alpha=0.3, axis="y")

        # Rotate x labels for better readability
        plt.setp(ax2.get_xticklabels(), rotation=45, ha="right")

    plt.tight_layout()

    # Change output path to PNG if it's HTML
    if output_path.endswith(".html"):
        output_path = output_path.replace(".html", ".png")

    # Save to file
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    plt.savefig(output_path)
    plt.close()

    logger.info(f"Gravity correction visualization saved to {output_path}")
    return output_path


def extract_trace_data_for_variable(
    trace_data: List[Dict], variable_name: str
) -> List[Dict]:
    """
    Extract gravity correction data specific to a variable from the trace.

    Parameters
    ----------
    trace_data : List[Dict]
        Full simulation trace data
    variable_name : str
        Name of the variable to extract data for

    Returns
    -------
    List[Dict]
        Filtered trace data with only the relevant variable information
    """
    result = []

    for step in trace_data:
        step_copy = {"turn": step.get("turn", 0)}

        gravity_details = step.get("gravity_correction_details", {})
        if variable_name in gravity_details:
            step_copy["gravity_correction_details"] = {
                variable_name: gravity_details[variable_name]
            }
            result.append(step_copy)

    return result


def export_gravity_explanation_json(
    trace_data: List[Dict], variable_name: str, output_path: str
) -> str:
    """
    Export gravity correction explanation data to a JSON file.

    Parameters
    ----------
    trace_data : List[Dict]
        Simulation trace data containing gravity correction details
    variable_name : str
        The name of the variable to export data for
    output_path : str
        Path where the JSON file will be saved

    Returns
    -------
    str
        Path to the saved JSON file
    """
    # Extract relevant data
    variable_data = extract_trace_data_for_variable(trace_data, variable_name)

    if not variable_data:
        logger.warning(
            f"No gravity correction data found for variable '{variable_name}'"
        )
        return ""

    # Create metadata
    export_data = {
        "variable": variable_name,
        "exported_at": datetime.now().isoformat(),
        "steps_count": len(variable_data),
        "trace_data": variable_data,
    }

    # Save to file
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(export_data, f, indent=2)

    logger.info(f"Gravity explanation data exported to {output_path}")
    return output_path


def get_top_source_data_points_for_pillar(
    trace_data: List[Dict], variable_name: str, pillar_name: str, top_n: int = 5
) -> List[Dict]:
    """
    Get the top N most influential source data points for a specific pillar across the trace.

    Parameters
    ----------
    trace_data : List[Dict]
        Simulation trace data containing gravity correction details
    variable_name : str
        The name of the variable to analyze
    pillar_name : str
        The name of the pillar to get source data for
    top_n : int
        Number of top data points to return

    Returns
    -------
    List[Dict]
        List of top source data points with their metadata
    """
    all_data_points = []

    for step in trace_data:
        gravity_details = step.get("gravity_correction_details", {})
        var_details = gravity_details.get(variable_name, {})

        dominant_pillars = var_details.get("dominant_pillars", [])
        for pillar_info in dominant_pillars:
            if pillar_info.get("pillar_name") == pillar_name:
                source_points = pillar_info.get("source_data_points", [])
                for point in source_points:
                    # Add metadata about which step this came from
                    point_copy = point.copy()
                    point_copy["step"] = step.get("turn", 0)
                    all_data_points.append(point_copy)

    # Sort by value or weight if available
    sorted_points = sorted(
        all_data_points, key=lambda x: abs(x.get("value", 0.0)), reverse=True
    )

    # Return top N unique points
    unique_ids = set()
    result = []

    for point in sorted_points:
        point_id = point.get("id", "")
        if point_id not in unique_ids:
            unique_ids.add(point_id)
            result.append(point)

            if len(result) >= top_n:
                break

    return result
