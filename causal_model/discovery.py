"""
Causal discovery algorithms for structural causal models.
Supports PC and FCI algorithms to infer causal structure from data.

This module integrates optimized implementations for improved performance.
"""
import os
import logging
import pandas as pd
import numpy as np
from typing import List, Optional, Dict, Any
import itertools
from causal_model.structural_causal_model import StructuralCausalModel
from causal_model.optimized_discovery import OptimizedCausalDiscovery, get_optimized_causal_discovery
from causal_model.vectorized_operations import (
    compute_correlation_matrix,
    batch_conditional_independence_test,
    batch_edge_detection,
    optimize_graph_queries
)

logger = logging.getLogger(__name__)

class CausalDiscovery:
    """
    Encapsulates causal discovery methods on a dataset.
    Automatically uses optimized implementations when available.
    """
    def __init__(self, data: pd.DataFrame, max_workers: Optional[int] = None):
        """
        Initialize the causal discovery engine.
        
        Args:
            data: DataFrame containing variables
            max_workers: Optional number of worker processes for parallel operations
                        (defaults to CPU count - 1, minimum 1)
        """
        self.data = data
        self.max_workers = max_workers
        
        # Initialize optimized discovery engine if available
        try:
            self.optimized_discovery = get_optimized_causal_discovery(data, max_workers)
            self.use_optimized = True
            logger.info("Using optimized causal discovery implementation")
        except ImportError:
            self.optimized_discovery = None
            self.use_optimized = False
            logger.warning("Optimized causal discovery not available, using standard implementation")

    def run_pc(self, alpha: float = 0.05) -> StructuralCausalModel:
        """
        Run the PC algorithm to infer a DAG representing causal relationships.
        Automatically uses optimized implementation if available.
        
        Args:
            alpha: significance level for conditional independence tests.
        Returns:
            An SCM populated with discovered edges.
        """
        if self.use_optimized and self.optimized_discovery is not None:
            # Use optimized implementation
            logger.info(f"Running optimized PC algorithm with alpha={alpha}")
            return self.optimized_discovery.vectorized_pc_algorithm(alpha)
        
        # Fall back to standard implementation if optimized version is unavailable
        logger.info(f"Running standard PC algorithm with alpha={alpha}")
        
        # initialize SCM with all variables
        scm = StructuralCausalModel()
        for var in self.data.columns:
            scm.add_variable(var)
            
        # Use vectorized batch edge detection for better performance
        try:
            edges = batch_edge_detection(self.data, alpha)
            for var1, var2 in edges:
                scm.add_causal_edge(var1, var2)
        except Exception as e:
            logger.warning(f"Vectorized edge detection failed: {e}, falling back to pairwise")
            # Fall back to pairwise correlation
            for var1, var2 in itertools.combinations(self.data.columns, 2):
                corr_val = self.data[var1].corr(self.data[var2])
                if abs(corr_val) >= alpha:
                    scm.add_causal_edge(var1, var2)
                    
        return scm

    def run_fci(self, alpha: float = 0.05) -> StructuralCausalModel:
        """
        Run the FCI algorithm to infer a PAG (Partial Ancestral Graph).
        Uses optimized implementation when available for better performance.
        
        Args:
            alpha: significance level for conditional independence tests.
        Returns:
            An SCM or PAG with edges indicating possible latent confounders.
        """
        if self.use_optimized and hasattr(self.optimized_discovery, "vectorized_fci_algorithm"):
            # Use optimized implementation if available
            logger.info(f"Running optimized FCI algorithm with alpha={alpha}")
            try:
                return self.optimized_discovery.vectorized_fci_algorithm(alpha)
            except (NotImplementedError, AttributeError) as e:
                logger.warning(f"Optimized FCI not fully implemented: {e}, falling back to standard")
        
        # Fall back to standard implementation
        logger.info(f"Running standard FCI algorithm with alpha={alpha}")
        
        # Initialize SCM with all variables
        scm = StructuralCausalModel()
        for var in self.data.columns:
            scm.add_variable(var)
            
        # Use vectorized batch operations for better performance
        try:
            # Compute correlation matrix once
            corr_matrix = compute_correlation_matrix(self.data)
            
            # Get all pairs that exceed correlation threshold
            edges = []
            for i, var1 in enumerate(self.data.columns):
                for j, var2 in enumerate(self.data.columns):
                    if i != j and corr_matrix.at[var1, var2] >= alpha:
                        edges.append((var1, var2))
                        
            # Add bidirectional edges for correlated pairs
            for var1, var2 in edges:
                scm.add_causal_edge(var1, var2)
                scm.add_causal_edge(var2, var1)
                
        except Exception as e:
            logger.warning(f"Vectorized correlation failed: {e}, falling back to pairwise")
            # Fall back to pairwise correlation
            for var1, var2 in itertools.combinations(self.data.columns, 2):
                corr_val = self.data[var1].corr(self.data[var2])
                if abs(corr_val) >= alpha:
                    scm.add_causal_edge(var1, var2)
                    scm.add_causal_edge(var2, var1)
                    
        return scm

    def get_adjacency_matrix(self, scm: StructuralCausalModel) -> pd.DataFrame:
        """
        Return adjacency matrix of the SCM as a DataFrame.
        """
        nodes = scm.variables()
        matrix = pd.DataFrame(0, index=nodes, columns=nodes)
        for u, v in scm.edges():
            matrix.at[u, v] = 1
        return matrix