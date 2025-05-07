"""
visualization.py

Visualization utilities for the Symbolic Gravity Fabric system.

This module provides tools to visualize the symbolic pillars and their
interactions in the gravity fabric. It supports both terminal-based
and matplotlib-based visualizations.

Author: Pulse v3.5
"""

import numpy as np
import logging
from typing import Dict, List, Optional, Tuple, Any, Union
import json
import os
from datetime import datetime

# Define these for type checking
plt = None
mcolors = None
Rectangle = None
FancyArrowPatch = None
HAS_MATPLOTLIB = False

# Try to import matplotlib, but provide fallbacks if not available
try:
    import matplotlib.pyplot as plt
    import matplotlib.colors as mcolors
    from matplotlib.patches import Rectangle, FancyArrowPatch
    HAS_MATPLOTLIB = True
except ImportError:
    # Variables are already defined as None
    pass
    
logger = logging.getLogger(__name__)


def generate_ascii_visualization(pillar_data: List[Dict[str, Any]], 
                               max_height: int = 10) -> str:
    """
    Generate a simple ASCII art visualization of symbolic pillars.
    
    Parameters
    ----------
    pillar_data : List[Dict[str, Any]]
        Data for each pillar, including name, height, and intensity
    max_height : int, optional
        Maximum height of the ASCII art, by default 10
        
    Returns
    -------
    str
        ASCII art visualization
    """
    if not pillar_data:
        return "No pillars to visualize."
    
    lines = []
    
    # Header
    lines.append("SYMBOLIC PILLARS")
    lines.append("=" * 40)
    
    # Generate pillar visualization
    for pillar in pillar_data:
        name = pillar["name"]
        intensity = pillar.get("intensity", 0.0)
        growth_indicator = pillar.get("growth_indicator", 0)
        
        # Convert intensity to height
        height = int(intensity * max_height)
        if height < 1 and intensity > 0:
            height = 1  # Ensure non-zero intensity shows at least a height of 1
            
        # Add growth indicator
        growth_symbol = "↑" if growth_indicator > 0 else "↓" if growth_indicator < 0 else "→"
        
        # Create the pillar visualization
        pillar_vis = []
        pillar_vis.append(f"{name} ({intensity:.2f}) {growth_symbol}")
        pillar_vis.append("┌" + "─" * 8 + "┐")
        
        for i in range(max_height - height):
            pillar_vis.append("│" + " " * 8 + "│")
            
        for i in range(height):
            pillar_vis.append("│" + "█" * 8 + "│")
            
        pillar_vis.append("└" + "─" * 8 + "┘")
        
        # Add to lines
        lines.append("\n".join(pillar_vis))
        lines.append("")
    
    return "\n".join(lines)


def plot_symbolic_pillars(pillar_data: List[Dict[str, Any]],
                         interactions: Optional[List[Dict[str, Any]]] = None,
                         save_path: Optional[str] = None,
                         title: str = "Symbolic Pillars & Gravity Fabric",
                         fabric_metrics: Optional[Dict[str, float]] = None) -> Optional[Any]:
    """
    Create a matplotlib visualization of symbolic pillars and their interactions.
    
    Parameters
    ----------
    pillar_data : List[Dict[str, Any]]
        Data for each pillar
    interactions : Optional[List[Dict[str, Any]]], optional
        Data for pillar interactions, by default None
    save_path : Optional[str], optional
        Path to save the visualization, by default None
    title : str, optional
        Title for the visualization, by default "Symbolic Pillars"
    fabric_metrics : Optional[Dict[str, float]], optional
        Additional metrics to display, by default None
        
    Returns
    -------
    Optional[Any]
        Matplotlib figure if matplotlib is available, otherwise None
    """
    # This entire function requires matplotlib
    if not HAS_MATPLOTLIB or plt is None or mcolors is None or Rectangle is None or FancyArrowPatch is None:
        logger.warning("Matplotlib not available for visualization. Using ASCII visualization.")
        return None
    
    if not pillar_data:
        logger.warning("No pillar data provided for visualization.")
        return None
    
    # Create figure and axis
    fig, ax = plt.subplots(figsize=(12, 8))
    
    # Define colors for pillars
    # Use perceptually distinct colors
    colors = list(mcolors.TABLEAU_COLORS.values())
    
    # Basic metrics for positioning
    pillar_count = len(pillar_data)
    pillar_width = 0.8
    spacing = 1.0
    
    # Position data
    x_positions = {}
    
    # Plot pillars
    for i, pillar in enumerate(pillar_data):
        name = pillar["name"]
        intensity = pillar.get("intensity", 0.0)
        height = pillar.get("height", intensity * 100)  # Default to scaled intensity
        
        # Position
        x_pos = i * (pillar_width + spacing)
        x_positions[name] = x_pos + pillar_width / 2  # Store center position
        
        # Color based on pillar type
        color_idx = i % len(colors)
        color = colors[color_idx]
        
        # Draw pillar
        rect = Rectangle((x_pos, 0), pillar_width, height, 
                        facecolor=color, edgecolor='black', alpha=0.7)
        ax.add_patch(rect)
        
        # Add name label
        ax.text(x_pos + pillar_width/2, -10, name, 
               ha='center', va='top', fontsize=10, rotation=45)
        
        # Add value label
        ax.text(x_pos + pillar_width/2, height + 5, f"{intensity:.2f}", 
               ha='center', va='bottom', fontsize=9)
        
        # Add growth indicator
        growth_indicator = pillar.get("growth_indicator", 0)
        if growth_indicator > 0:
            ax.text(x_pos + pillar_width/2, height + 15, "↑", 
                  ha='center', va='bottom', fontsize=12, color='green')
        elif growth_indicator < 0:
            ax.text(x_pos + pillar_width/2, height + 15, "↓", 
                  ha='center', va='bottom', fontsize=12, color='red')
    
    # Draw interactions if provided
    if interactions:
        for interaction in interactions:
            source = interaction.get("source")
            target = interaction.get("target")
            strength = interaction.get("strength", 0.0)
            interaction_type = interaction.get("type", "neutral")
            
            if source in x_positions and target in x_positions:
                # Determine source and target positions
                x1 = x_positions[source]
                x2 = x_positions[target]
                
                # Get heights for source and target
                source_height = next(p["height"] for p in pillar_data if p["name"] == source)
                target_height = next(p["height"] for p in pillar_data if p["name"] == target)
                
                # Determine y positions (start from middle of pillar)
                y1 = source_height / 2
                y2 = target_height / 2
                
                # Calculate control point for curved arrow
                control_y = max(source_height, target_height) + 20
                
                # Determine color and style based on interaction type
                if interaction_type == "opposing":
                    color = 'red'
                    style = 'dashed'
                    alpha = 0.6
                elif interaction_type == "enhancing":
                    color = 'green'
                    style = 'solid'
                    alpha = 0.6
                else:
                    color = 'gray'
                    style = 'dotted'
                    alpha = 0.4
                
                # Adjust line width based on strength
                line_width = min(3.0, abs(strength) * 5)
                
                # Create arrow
                arrow = FancyArrowPatch(
                    (x1, y1), (x2, y2),
                    connectionstyle=f"arc3,rad=0.3",
                    arrowstyle="->",
                    linewidth=line_width,
                    linestyle=style,
                    color=color,
                    alpha=alpha
                )
                ax.add_patch(arrow)
                
                # Add interaction strength text
                mid_x = (x1 + x2) / 2
                mid_y = (y1 + y2) / 2 + 10
                ax.text(mid_x, mid_y, f"{strength:.2f}", 
                       ha='center', va='center', fontsize=8, 
                       bbox=dict(facecolor='white', alpha=0.7, edgecolor='none'))
    
    # Add fabric metrics if provided
    if fabric_metrics:
        metrics_text = []
        for key, value in fabric_metrics.items():
            # Format the key for display
            display_key = key.replace('_', ' ').title()
            
            # Format the value based on type
            if isinstance(value, float):
                display_value = f"{value:.2f}"
            else:
                display_value = str(value)
                
            metrics_text.append(f"{display_key}: {display_value}")
        
        # Add metrics as text box
        text_box = '\n'.join(metrics_text)
        props = dict(boxstyle='round', facecolor='white', alpha=0.7)
        ax.text(0.02, 0.98, text_box, transform=ax.transAxes, fontsize=9,
               verticalalignment='top', bbox=props)
    
    # Set axis limits and labels
    ax.set_xlim(-1, pillar_count * (pillar_width + spacing))
    
    # Set appropriate y limit
    max_height = max([p.get("height", 0) for p in pillar_data], default=100)
    ax.set_ylim(-20, max_height * 1.2)
    
    # Set title and labels
    ax.set_title(title, fontsize=14)
    ax.set_xlabel("Symbolic Pillars", fontsize=12)
    ax.set_ylabel("Intensity (Height)", fontsize=12)
    
    # Remove ticks for cleaner look
    ax.set_xticks([])
    
    # Add timestamp
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    plt.figtext(0.99, 0.01, f"Generated: {timestamp}", fontsize=8, ha='right')
    
    # Add fabric schematic at the bottom
    fabric_y = -20
    ax.plot([-1, pillar_count * (pillar_width + spacing)], [fabric_y, fabric_y], 
           color='blue', linestyle='-', linewidth=2, alpha=0.5)
    ax.text(pillar_count * (pillar_width + spacing) / 2, fabric_y - 5, 
           "Symbolic Gravity Fabric", ha='center', va='top', fontsize=10, 
           bbox=dict(facecolor='white', alpha=0.7, edgecolor='none'))
    
    # Make layout tight
    plt.tight_layout()
    
    # Save if path provided
    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        logger.info(f"Saved symbolic pillar visualization to {save_path}")
    
    return fig


def visualize_gravity_fabric(
    pillar_system_or_data: Any,
    output_path: Optional[str] = None,
    format_type: str = "auto"
) -> str:
    """
    Visualize the gravity fabric based on pillar system or data.
    
    Parameters
    ----------
    pillar_system_or_data : Any
        SymbolicPillarSystem instance or visualization data
    output_path : Optional[str], optional
        Path to save the visualization, by default None
    format_type : str, optional
        Format type ('auto', 'matplotlib', 'ascii', 'json'), by default "auto"
        
    Returns
    -------
    str
        Path to saved visualization or ASCII visualization
    """
    # Extract visualization data
    if hasattr(pillar_system_or_data, "generate_visualization_data"):
        # It's a SymbolicPillarSystem instance
        try:
            data = pillar_system_or_data.generate_visualization_data()
        except Exception as e:
            logger.error(f"Error generating visualization data: {e}")
            return f"Visualization error: {e}"
    else:
        # Assume it's already visualization data
        data = pillar_system_or_data
    
    # Extract components
    pillar_data = data.get("pillars", [])
    interactions = data.get("interactions", [])
    fabric_metrics = data.get("fabric_metrics", {})
    
    # Determine format
    if format_type == "auto":
        format_type = "matplotlib" if HAS_MATPLOTLIB else "ascii"
    
    # Generate visualization
    if format_type == "matplotlib" and HAS_MATPLOTLIB and plt is not None:
        fig = plot_symbolic_pillars(
            pillar_data,
            interactions=interactions,
            save_path=output_path,
            fabric_metrics=fabric_metrics
        )
        
        if fig is None:
            # Fallback to ASCII if plot function failed
            format_type = "ascii"
            # Continue to ASCII case below
        elif output_path:
            return output_path
        else:
            # Create a default path if none provided
            default_path = os.path.join(
                os.getcwd(),
                f"symbolic_gravity_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
            )
            plt.savefig(default_path, dpi=300, bbox_inches='tight')
            plt.close(fig)
            return default_path
            
    # If we get here and format_type is "matplotlib", we either don't have
    # matplotlib or the previous attempt to use it failed, so use ASCII
    if format_type == "ascii" or not HAS_MATPLOTLIB:
        ascii_vis = generate_ascii_visualization(pillar_data)
        
        if output_path:
            with open(output_path, 'w') as f:
                f.write(ascii_vis)
            return output_path
        else:
            return ascii_vis
            
    elif format_type == "json":
        if output_path:
            with open(output_path, 'w') as f:
                json.dump(data, f, indent=2)
            return output_path
        else:
            return json.dumps(data, indent=2)
    
    else:
        return f"Unsupported format type: {format_type}"


# CLI interface
if __name__ == "__main__":
    import argparse
    import importlib.util
    
    parser = argparse.ArgumentParser(description="Symbolic Gravity Fabric Visualization")
    parser.add_argument("--input", type=str, help="Path to JSON data file (optional)")
    parser.add_argument("--output", type=str, help="Path to save visualization")
    parser.add_argument("--format", type=str, default="auto", 
                       choices=["auto", "matplotlib", "ascii", "json"],
                       help="Visualization format")
    args = parser.parse_args()
    
    # Load data or create example
    if args.input:
        with open(args.input, 'r') as f:
            data = json.load(f)
    else:
        # Try to import from symbolic system
        try:
            from symbolic_system.gravity.symbolic_pillars import SymbolicPillarSystem
            from symbolic_system.gravity.gravity_config import ResidualGravityConfig
            
            config = ResidualGravityConfig()
            system = SymbolicPillarSystem(config=config)
            
            # Add example data
            system.update_pillar("hope", intensity=0.7)
            system.update_pillar("despair", intensity=0.3)
            system.update_pillar("rage", intensity=0.5)
            system.update_pillar("calm", intensity=0.4)
            
            # Generate data
            data = system.generate_visualization_data()
        except ImportError:
            # Use example data
            data = {
                "pillars": [
                    {"name": "hope", "intensity": 0.7, "height": 70, "growth_indicator": 1},
                    {"name": "despair", "intensity": 0.3, "height": 30, "growth_indicator": -1},
                    {"name": "rage", "intensity": 0.5, "height": 50, "growth_indicator": 0},
                    {"name": "calm", "intensity": 0.4, "height": 40, "growth_indicator": 0}
                ],
                "interactions": [
                    {"source": "hope", "target": "despair", "strength": -0.3, "type": "opposing"},
                    {"source": "rage", "target": "calm", "strength": -0.2, "type": "opposing"},
                    {"source": "hope", "target": "calm", "strength": 0.2, "type": "enhancing"}
                ],
                "fabric_metrics": {
                    "total_support": 1.9,
                    "symbolic_tension": 0.4,
                    "fabric_stability": 0.6
                }
            }
    
    # Generate visualization
    result = visualize_gravity_fabric(data, args.output, args.format)
    
    # Print result
    if args.output:
        print(f"Visualization saved to: {result}")
    else:
        print(result)