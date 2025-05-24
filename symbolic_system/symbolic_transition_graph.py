# symbolic/symbolic_transition_graph.py

"""
Symbolic Transition Graph

Builds a symbolic graph of arc/tag transitions across a forecast archive:
- Nodes = symbolic states
- Edges = observed transitions
- Edge weight = frequency
- Loops = symbolic instability

Author: Pulse AI Engine
Version: v1.0.0
"""

from typing import List, Dict
import networkx as nx
import matplotlib.pyplot as plt
from collections import Counter
from symbolic_system.symbolic_flip_classifier import extract_transitions


def build_symbolic_graph(forecasts: List[Dict]) -> nx.DiGraph:
    """
    Build a directed graph from symbolic transitions across all episodes.

    Returns:
        networkx.DiGraph
    """
    G = nx.DiGraph()
    transition_counts = Counter()

    for fc in forecasts:
        lineage = fc.get("lineage", {})
        if not lineage:
            continue
        history = lineage.get("ancestral_chain", [])
        if not history:
            continue
        chain = [fc] + history
        transitions = extract_transitions(chain)
        for a, b in transitions:
            transition_counts[(a, b)] += 1

    for (a, b), count in transition_counts.items():
        G.add_edge(a, b, weight=count)

    return G


def visualize_symbolic_graph(
    G: nx.DiGraph,
    title: str = "Symbolic Transition Graph",
    highlight_loops: bool = True,
):
    """
    Visualize the symbolic transition graph and return the matplotlib Figure.

    Args:
        G (networkx.DiGraph)
        title (str)
        highlight_loops (bool): bold cycle edges

    Returns:
        matplotlib.figure.Figure: The created figure object.
    """

    fig, ax = plt.subplots(figsize=(12, 8))
    pos = nx.spring_layout(G, seed=42)
    edge_weights = nx.get_edge_attributes(G, "weight")
    loop_edges = []

    if highlight_loops:
        for cycle in nx.simple_cycles(G):
            if len(cycle) > 1:
                for i in range(len(cycle)):
                    a = cycle[i]
                    b = cycle[(i + 1) % len(cycle)]
                    if G.has_edge(a, b):
                        loop_edges.append((a, b))

    nx.draw_networkx_nodes(G, pos, node_color="lightblue", node_size=1000, ax=ax)
    nx.draw_networkx_labels(G, pos, font_size=9, font_weight="bold", ax=ax)
    nx.draw_networkx_edges(G, pos, width=1.5, edge_color="gray", arrows=True, ax=ax)

    if loop_edges:
        nx.draw_networkx_edges(
            G, pos, edgelist=loop_edges, edge_color="crimson", width=2.5, ax=ax
        )

    nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_weights, font_size=7, ax=ax)
    ax.set_title(title)
    ax.axis("off")
    fig.tight_layout()
    # plt.show()  # Do not show in non-interactive/batch mode
    return fig


def export_graph_dot(G: nx.DiGraph, path: str):
    """
    Save the symbolic graph as a Graphviz .dot file.

    Args:
        G (networkx.DiGraph)
        path (str)
    """
    try:
        nx.drawing.nx_pydot.write_dot(G, path)
        print(f"✅ Graph exported to {path}")
    except Exception as e:
        print(f"❌ Export failed: {e}")
