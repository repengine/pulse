"""
Counterfactual engine for structural causal models.
Supports optimized counterfactual inference with caching and batch processing.
"""
import os
import logging
import time
import hashlib
import json
from typing import Dict, Any, List, Tuple, Optional, Set, Callable
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor, as_completed
import numpy as np

from causal_model.structural_causal_model import StructuralCausalModel

logger = logging.getLogger(__name__)

class CounterfactualEngine:
    """
    Performs counterfactual inference using do-calculus on an SCM.
    Features optimized computation with caching and parallelization.
    """

    def __init__(self, scm: StructuralCausalModel, max_cache_size: int = 1000, max_workers: Optional[int] = None):
        """
        Initialize with a structural causal model.
        
        Args:
            scm: The structural causal model to use for inference
            max_cache_size: Maximum number of results to cache
            max_workers: Maximum number of parallel workers for batch operations (default: CPU count - 1)
        """
        self.scm = scm
        self.max_workers = max_workers or max(1, (os.cpu_count() or 4) - 1)
        
        # Set up caching
        self._cache = {}
        self._cache_hits = 0
        self._cache_misses = 0
        self._max_cache_size = max_cache_size
        
        # Precompute a topological ordering of variables for efficient inference
        self._ordered_variables = self._compute_variable_ordering()
        
        logger.info(f"CounterfactualEngine initialized with {self.max_workers} workers and cache size {max_cache_size}")

    def _compute_variable_ordering(self) -> List[str]:
        """
        Compute an ordering of the variables for efficient inference.
        
        Returns:
            List of variable names in a logical order for inference
        """
        # For now, just return all variables
        # In a more sophisticated implementation, we would compute a topological sort
        return list(self.scm.variables())
    
    def _compute_cache_key(self, evidence: Dict[str, Any], interventions: Dict[str, Any]) -> str:
        """
        Compute a cache key for a counterfactual query.
        
        Args:
            evidence: Observed variable values
            interventions: Variables to intervene on with assigned values
            
        Returns:
            A string hash key
        """
        # Combine evidence and interventions into a sorted JSON string for consistent hashing
        key_dict = {
            "evidence": dict(sorted(evidence.items())),
            "interventions": dict(sorted(interventions.items()))
        }
        key_str = json.dumps(key_dict, sort_keys=True)
        return hashlib.md5(key_str.encode()).hexdigest()
    
    def predict_counterfactual(self,
                              evidence: Dict[str, Any],
                              interventions: Dict[str, Any]) -> Dict[str, Any]:
        """
        Given observed evidence and do-interventions, compute counterfactual outcomes.
        Uses caching for improved performance.

        Args:
            evidence: Observed variable values (e.g., {'X': 1, 'Y': 0}).
            interventions: Variables to intervene on with assigned values (do-operations).
            
        Returns:
            Counterfactual predictions as a dict of variable values.
        """
        # Check cache first
        cache_key = self._compute_cache_key(evidence, interventions)
        if cache_key in self._cache:
            self._cache_hits += 1
            return self._cache[cache_key].copy()
        
        self._cache_misses += 1
        
        # Perform counterfactual inference
        start_time = time.time()
        
        # Implementation of proper counterfactual inference would involve:
        # 1. Abduction: Update the exogenous variables to be consistent with evidence
        # 2. Action: Modify the model by removing incoming edges to intervention variables
        # 3. Prediction: Compute the values of all variables in the modified model
        
        # For now, we have a simple placeholder implementation
        cf_results = evidence.copy()
        cf_results.update(interventions)
        
        # We'll iterate through variables in our computed order to simulate proper inference
        for var in self._ordered_variables:
            # Skip intervention variables (their values are fixed)
            if var in interventions:
                continue
                
            # In a real implementation, we would apply the structural equations for each variable
            # For now, just keep the values from evidence or placeholder values
            if var not in cf_results:
                # This is a placeholder - in a real implementation we would compute
                # the value based on the SCM's structural equations
                cf_results[var] = 0.5
        
        # Store in cache if not full
        if len(self._cache) < self._max_cache_size:
            self._cache[cache_key] = cf_results.copy()
        else:
            # In a more sophisticated implementation, we would use an LRU cache
            # For now, just log that the cache is full
            logger.debug("Counterfactual cache is full, not storing result")
        
        inference_time = time.time() - start_time
        logger.debug(f"Counterfactual inference completed in {inference_time:.4f}s")
        
        return cf_results

    def predict_counterfactuals_batch(self,
                                    queries: List[Tuple[Dict[str, Any], Dict[str, Any]]]) -> List[Dict[str, Any]]:
        """
        Process multiple counterfactual queries in parallel for improved performance.
        
        Args:
            queries: List of (evidence, interventions) tuples
            
        Returns:
            List of counterfactual prediction results
        """
        if not queries:
            return []
            
        # If only one query, just use the regular method
        if len(queries) == 1:
            evidence, interventions = queries[0]
            return [self.predict_counterfactual(evidence, interventions)]
            
        # Check cache first to avoid unnecessary parallel processing
        results = []
        uncached_indices = []
        uncached_queries = []
        
        # Process cached queries first
        for i, (evidence, interventions) in enumerate(queries):
            cache_key = self._compute_cache_key(evidence, interventions)
            if cache_key in self._cache:
                self._cache_hits += 1
                results.append(self._cache[cache_key].copy())
            else:
                self._cache_misses += 1
                # Use None as a placeholder for uncached results
                results.append(None)
                uncached_indices.append(i)
                uncached_queries.append((evidence, interventions))
        
        # If all queries were cached, return results
        if not uncached_queries:
            return results
            
        # Process uncached queries in parallel
        start_time = time.time()
        logger.info(f"Processing {len(uncached_queries)} uncached counterfactual queries in parallel")
        
        # Use ThreadPoolExecutor for parallelization (ProcessPoolExecutor is harder to use with shared objects)
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Submit all uncached queries
            futures = []
            for evidence, interventions in uncached_queries:
                futures.append(
                    executor.submit(
                        self._process_counterfactual_query,
                        evidence,
                        interventions
                    )
                )
            
            # Process results as they complete
            for i, future in enumerate(as_completed(futures)):
                try:
                    cf_result = future.result()
                    # Update results list with the computed result
                    results[uncached_indices[i]] = cf_result
                except Exception as e:
                    logger.error(f"Error in parallel counterfactual computation: {e}")
                    # Set a default error result
                    results[uncached_indices[i]] = {"error": str(e)}
        
        parallel_time = time.time() - start_time
        logger.info(f"Batch counterfactual processing completed in {parallel_time:.4f}s")
        
        return results
    
    def _process_counterfactual_query(self, evidence: Dict[str, Any], interventions: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a single counterfactual query, for use in parallel execution.
        
        Args:
            evidence: Observed variable values
            interventions: Variables to intervene on with assigned values
            
        Returns:
            Counterfactual prediction result
        """
        # Compute the counterfactual
        result = self.predict_counterfactual(evidence, interventions)
        return result
    
    def clear_cache(self):
        """Clear the counterfactual cache."""
        cache_size = len(self._cache)
        self._cache = {}
        logger.info(f"Cleared counterfactual cache ({cache_size} entries)")
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get statistics about the cache usage."""
        total_queries = self._cache_hits + self._cache_misses
        hit_ratio = self._cache_hits / total_queries if total_queries > 0 else 0
        
        return {
            "cache_size": len(self._cache),
            "max_cache_size": self._max_cache_size,
            "cache_hits": self._cache_hits,
            "cache_misses": self._cache_misses,
            "hit_ratio": hit_ratio
        }