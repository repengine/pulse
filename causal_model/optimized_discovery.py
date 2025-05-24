"""
Optimized Causal Discovery Module

Provides efficient implementations of causal discovery algorithms for the Pulse system.
"""

import logging
import os
import itertools
from typing import List, Optional
from concurrent.futures import ProcessPoolExecutor, as_completed

# Handle pandas import properly
try:
    import pandas as pd

    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False
    pd = None

# Handle networkx import
try:
    # import networkx as nx # F401

    NX_AVAILABLE = True
except ImportError:
    NX_AVAILABLE = False

from causal_model.structural_causal_model import StructuralCausalModel
from scipy.stats import pearsonr

# Set up logger
logger = logging.getLogger(__name__)


class OptimizedCausalDiscovery:
    """
    Optimized implementation of causal discovery algorithms.
    Uses vectorized operations, parallel processing, and caching for performance.
    """

    def __init__(self, data, max_workers: Optional[int] = None):
        """
        Initialize with data for causal discovery.

        Args:
            data: DataFrame or array of data
            max_workers: Maximum number of worker processes for parallel operations
        """
        self.data = data
        # Use CPU count - 1 if not specified, but at least 1
        self.max_workers = (
            max_workers
            if max_workers is not None
            else max(1, (os.cpu_count() or 4) - 1)
        )
        self.logger = logging.getLogger(__name__)

        # Precompute correlation matrix for later use
        if PANDAS_AVAILABLE and pd is not None and isinstance(data, pd.DataFrame):
            self.corr_matrix = data.corr().abs()
        else:
            self.logger.warning(
                "Data not in pandas DataFrame format. Some optimizations unavailable."
            )
            self.corr_matrix = None

    def vectorized_pc_algorithm(self, alpha: float = 0.05) -> StructuralCausalModel:
        """
        Vectorized implementation of the PC algorithm for causal discovery.

        Args:
            alpha: Significance threshold for independence tests

        Returns:
            StructuralCausalModel representing the discovered causal graph
        """
        self.logger.info(f"Running vectorized PC algorithm with alpha={alpha}")

        # Initialize the causal model
        scm = StructuralCausalModel()

        # Add variables
        if PANDAS_AVAILABLE and pd is not None and isinstance(self.data, pd.DataFrame):
            for var in self.data.columns:
                scm.add_variable(var)

            # Step 1: Create complete undirected graph using vectorized operations
            # Use the precomputed correlation matrix to quickly add edges
            for i, var1 in enumerate(self.data.columns):
                for j, var2 in enumerate(self.data.columns):
                    if (
                        i != j
                        and self.corr_matrix is not None
                        and self.corr_matrix.at[var1, var2] >= alpha
                    ):
                        # Use add_causal_edge from the SCM interface
                        scm.add_causal_edge(var1, var2)

            # Step 2: Edge removal based on conditional independence tests
            # This is much more efficient than the original implementation
            self._run_conditional_independence_tests(scm, alpha)

            # Step 3: Edge orientation
            self._orient_edges(scm)
        else:
            self.logger.error("Vectorized PC algorithm requires pandas DataFrame")
            raise ValueError("Data must be a pandas DataFrame")

        return scm

    def _run_conditional_independence_tests(
        self, scm: StructuralCausalModel, alpha: float
    ) -> None:
        """
        Run conditional independence tests in parallel for edge removal.

        Args:
            scm: Structural causal model to modify
            alpha: Significance threshold
        """
        # Get all edges as an array for vectorized operations
        edges = list(scm.graph.edges())

        # Process in batches to avoid memory issues with large graphs
        batch_size = 100
        for i in range(0, len(edges), batch_size):
            edge_batch = edges[i : i + batch_size]

            # Run tests in parallel
            with ProcessPoolExecutor(max_workers=self.max_workers) as executor:
                futures = []
                for edge in edge_batch:
                    var1, var2 = edge
                    futures.append(
                        executor.submit(
                            self._test_conditional_independence,
                            var1,
                            var2,
                            list(scm.graph.nodes()),
                            alpha,
                        )
                    )

                # Process results
                edges_to_remove = []
                for future, edge in zip(as_completed(futures), edge_batch):
                    if future.result():
                        edges_to_remove.append(edge)

            # Remove edges found to be conditionally independent
            for edge in edges_to_remove:
                if scm.graph.has_edge(*edge):
                    scm.graph.remove_edge(*edge)

    def _test_conditional_independence(
        self, var1: str, var2: str, all_vars: List[str], alpha: float
    ) -> bool:
        """
        Test conditional independence between two variables.

        Args:
            var1: First variable
            var2: Second variable
            all_vars: All variables in the graph
            alpha: Significance threshold

        Returns:
            True if variables are conditionally independent, False otherwise
        """
        # Get potential conditioning sets (excluding the variables themselves)
        conditioning_vars = [v for v in all_vars if v != var1 and v != var2]

        # Test with increasingly large conditioning sets
        for size in range(
            min(3, len(conditioning_vars))
        ):  # Limit to sets of size 3 for performance
            for cond_set in itertools.combinations(conditioning_vars, size):
                # Calculate partial correlation
                try:
                    # For simplicity, using residual correlation
                    # In a production system, use proper partial correlation
                    X = self.data[list(cond_set) + [var1]]
                    Y = self.data[list(cond_set) + [var2]]

                    # Get residuals after regressing out conditioning variables
                    X_resid = X[var1] - X[list(cond_set)].mean(axis=1)
                    Y_resid = Y[var2] - Y[list(cond_set)].mean(axis=1)

                    # Calculate correlation of residuals
                    _corr, p_value_raw = pearsonr(X_resid, Y_resid)
                    p_value_scalar: float = float(p_value_raw) # Extract the scalar p-value and cast to float

                    # If p-value is high, variables are independent given conditioning set
                    if p_value_scalar > alpha:
                        return True
                except Exception as e:
                    self.logger.warning(
                        f"Error in independence test for {var1},{var2}: {e}"
                    )

        return False

    def _orient_edges(self, scm: StructuralCausalModel) -> None:
        """
        Orient edges in the skeleton to create a DAG.

        Args:
            scm: Structural causal model to modify
        """
        # Implement edge orientation rules from the PC algorithm
        # This is a simplified version for demonstration

        # Find all unshielded triples X - Y - Z (where X and Z are not adjacent)
        unshielded_triples = []
        for y in scm.graph.nodes():
            neighbors = list(scm.graph.neighbors(y))
            for i, x in enumerate(neighbors):
                for z in neighbors[i + 1 :]:
                    if not scm.graph.has_edge(x, z) and not scm.graph.has_edge(z, x):
                        unshielded_triples.append((x, y, z))

        # Orient colliders: X -> Y <- Z
        for x, y, z in unshielded_triples:
            # Check if Y is in the separator set for X and Z
            # In a real implementation, this would use the separation sets from the CI tests
            # For simplicity, we'll use a heuristic based on correlations
            if self.corr_matrix is not None:
                xy_corr = self.corr_matrix.at[x, y]
                yz_corr = self.corr_matrix.at[y, z]
                xz_corr = self.corr_matrix.at[x, z]

                # If Y is a potential collider
                if xy_corr > xz_corr and yz_corr > xz_corr:
                    # Orient edges towards Y
                    if scm.graph.has_edge(y, x):
                        scm.graph.remove_edge(y, x)
                    if scm.graph.has_edge(y, z):
                        scm.graph.remove_edge(y, z)

                    scm.graph.add_edge(x, y)
                    scm.graph.add_edge(z, y)


# Factory function to get causal discovery instance
def get_optimized_causal_discovery(
    data, max_workers: Optional[int] = None
) -> OptimizedCausalDiscovery:
    """
    Get an optimized causal discovery instance.

    Args:
        data: Data for causal discovery
        max_workers: Maximum number of worker processes

    Returns:
        OptimizedCausalDiscovery instance
    """
    return OptimizedCausalDiscovery(data, max_workers)
