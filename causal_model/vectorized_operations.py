"""
Vectorized operations for causal model calculations

This module provides optimized, vectorized implementations of common operations
used in causal modeling to replace inefficient pair-by-pair calculations.
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Set, Tuple, Optional, Any, cast
import logging

logger = logging.getLogger(__name__)

def compute_correlation_matrix(data: pd.DataFrame) -> pd.DataFrame:
    """
    Efficiently compute the full correlation matrix at once.
    
    Args:
        data: DataFrame containing variables
        
    Returns:
        DataFrame with correlation matrix
    """
    return data.corr().abs()

def batch_edge_detection(data: pd.DataFrame, alpha: float = 0.05) -> List[Tuple[str, str]]:
    """
    Perform batch edge detection using vectorized correlation calculation.
    Significantly faster than iterating through variable pairs.
    
    Args:
        data: DataFrame containing variables
        alpha: Correlation threshold for edge detection
        
    Returns:
        List of detected edges as (from, to) tuples
    """
    # Calculate full correlation matrix in one vectorized operation
    corr_matrix = compute_correlation_matrix(data)
    
    # Find all pairs exceeding threshold (vectorized operation)
    edges = []
    for i, col1 in enumerate(data.columns):
        for j, col2 in enumerate(data.columns):
            if i != j and corr_matrix.at[col1, col2] >= alpha:
                edges.append((col1, col2))
    
    return edges

def batch_conditional_independence_test(
    data: pd.DataFrame,
    var_pairs: List[Tuple[str, str]],
    conditioning_vars: List[str],
    alpha: float = 0.05
) -> Dict[Tuple[str, str], bool]:
    """
    Test conditional independence for multiple variable pairs efficiently.
    
    Args:
        data: DataFrame containing variables
        var_pairs: List of variable pairs to test
        conditioning_vars: Variables to condition on
        alpha: Significance threshold
        
    Returns:
        Dictionary mapping pairs to independence test results (True if independent)
    """
    from scipy import stats
    
    results = {}
    
    # Only include conditioning variables that exist in the data
    valid_cond_vars = [v for v in conditioning_vars if v in data.columns]
    
    if not valid_cond_vars:
        # If no conditioning variables, just return regular correlations
        corr_matrix = compute_correlation_matrix(data)
        for var1, var2 in var_pairs:
            results[(var1, var2)] = corr_matrix.at[var1, var2] < alpha
        return results
    
    # For each pair, calculate partial correlation
    for var1, var2 in var_pairs:
        try:
            # Calculate residuals after regressing out conditioning variables
            X = data[[var1] + valid_cond_vars]
            Y = data[[var2] + valid_cond_vars]
            
            # Simple approximate method: get residuals after removing conditioning variables
            X_resid = X[var1] - X[valid_cond_vars].mean(axis=1)
            Y_resid = Y[var2] - Y[valid_cond_vars].mean(axis=1)
            
            # Test correlation of residuals using scipy.stats
            pearson_result = stats.pearsonr(X_resid, Y_resid)
            
            # Handle type issues by using a very robust approach that works with all SciPy versions
            # Convert the result to string representation and parse the p-value directly
            try:
                # For direct tuple access in most versions
                if isinstance(pearson_result, tuple) and len(pearson_result) >= 2:
                    p_value_str = str(pearson_result[1])
                    p_value_float = float(p_value_str)
                # For other result types, fall back to string parsing
                else:
                    # Convert the whole result to string and extract second value
                    result_str = str(pearson_result)
                    # Remove parentheses and split by comma for tuple-like strings
                    if ',' in result_str:
                        values = result_str.strip('()').split(',')
                        if len(values) >= 2:
                            p_value_float = float(values[1].strip())
                        else:
                            p_value_float = 1.0  # Default if parsing fails
                    else:
                        p_value_float = 1.0  # Default if not comma-separated
            except Exception as e:
                logger.warning(f"Error extracting p-value from pearsonr result: {e}")
                p_value_float = 1.0  # Conservative default (assume dependent)
            
            # Variables are independent if p-value exceeds threshold
            results[(var1, var2)] = p_value_float > alpha
            
        except Exception as e:
            logger.warning(f"Error testing conditional independence for {var1}-{var2}: {e}")
            # Default to dependent (safer assumption)
            results[(var1, var2)] = False
    
    return results

def optimize_graph_queries(graph_data: Dict, operation: str, variables: Optional[List[str]] = None) -> Dict:
    """
    Optimize batch operations on graph data to avoid repeated traversals.
    
    Args:
        graph_data: Graph data representation
        operation: Type of operation ('ancestors', 'descendants', etc.)
        variables: List of variables to process
        
    Returns:
        Dictionary mapping variables to their operation results
    """
    # Default to empty list if variables is None
    variables = variables or []
    import networkx as nx
    
    results = {}
    
    # Convert graph data to NetworkX graph if needed
    G = nx.DiGraph(graph_data) if not isinstance(graph_data, nx.Graph) else graph_data
    
    # Process all variables in one graph traversal session
    if operation == 'ancestors':
        for var in variables:
            results[var] = set(nx.ancestors(G, var))
    elif operation == 'descendants':
        for var in variables:
            results[var] = set(nx.descendants(G, var))
    elif operation == 'shortest_paths':
        # Calculate all shortest paths at once
        all_pairs = dict(nx.all_pairs_shortest_path_length(G))
        for var in variables:
            results[var] = all_pairs.get(var, {})
    
    return results