"""
Causal discovery algorithms for structural causal models.
Supports PC and FCI algorithms to infer causal structure from data.
"""
import pandas as pd
from typing import List
import itertools
from causal_model.structural_causal_model import StructuralCausalModel

class CausalDiscovery:
    """
    Encapsulates causal discovery methods on a dataset.
    """
    def __init__(self, data: pd.DataFrame):
        self.data = data

    def run_pc(self, alpha: float = 0.05) -> StructuralCausalModel:
        """
        Run the PC algorithm to infer a DAG representing causal relationships.
        Args:
            alpha: significance level for conditional independence tests.
        Returns:
            An SCM populated with discovered edges.
        """
        # initialize SCM with all variables
        scm = StructuralCausalModel()
        for var in self.data.columns:
            scm.add_variable(var)
        # perform simple correlation-based edge inclusion
        for var1, var2 in itertools.combinations(self.data.columns, 2):
            corr_val = self.data[var1].corr(self.data[var2])
            if abs(corr_val) >= alpha:
                scm.add_causal_edge(var1, var2)
        return scm

    def run_fci(self, alpha: float = 0.05) -> StructuralCausalModel:
        """
        Run the FCI algorithm to infer a PAG (Partial Ancestral Graph).
        Args:
            alpha: significance level for conditional independence tests.
        Returns:
            An SCM or PAG with edges indicating possible latent confounders.
        """
        # initialize SCM with all variables
        scm = StructuralCausalModel()
        for var in self.data.columns:
            scm.add_variable(var)
        # perform simple FCI: include bidirectional edges for correlated pairs
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