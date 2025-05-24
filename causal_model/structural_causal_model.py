"""
Structural Causal Model representation for Pulse.
Defines a causal graph and supports setting up relationships.
"""

from typing import List, Tuple
import networkx as nx


class StructuralCausalModel:
    """
    Represents an SCM as a directed acyclic graph.
    """

    def __init__(self):
        # Directed graph where edges indicate causal influence
        self.graph = nx.DiGraph()

    def add_variable(self, name: str):
        """Add a variable node to the graph."""
        self.graph.add_node(name)

    def add_causal_edge(self, cause: str, effect: str):
        """Add a directed edge from cause to effect."""
        self.graph.add_edge(cause, effect)

    def variables(self) -> List[str]:
        """List all variables in the model."""
        return list(self.graph.nodes)

    def edges(self) -> List[Tuple[str, str]]:
        """List all causal edges."""
        return list(self.graph.edges)

    def to_dot(self) -> str:
        """Export the SCM as Graphviz dot format."""
        return nx.nx_pydot.to_pydot(self.graph).to_string()

    def remove_variable(self, name: str):
        """Remove a variable node from the model."""
        self.graph.remove_node(name)

    def remove_causal_edge(self, cause: str, effect: str):
        """Remove a causal edge from cause to effect."""
        self.graph.remove_edge(cause, effect)

    def parents(self, variable: str):
        """Return parent variables of the given variable."""
        return list(self.graph.predecessors(variable))

    def children(self, variable: str):
        """Return child variables of the given variable."""
        return list(self.graph.successors(variable))

    def ancestors(self, variable: str):
        """Return all ancestors of the given variable."""
        return list(nx.ancestors(self.graph, variable))

    def descendants(self, variable: str):
        """Return all descendants of the given variable."""
        return list(nx.descendants(self.graph, variable))
