"""
residual_gravity_engine.py

Implementation of the Residual Gravity Engine for the Symbolic Gravity System.

This module provides the implementation of the ResidualGravityEngine, which
learns a low-rank residual correction g_t = B s_t that nudges simulation
outputs toward observed reality using online ridge-regression with momentum.

Mathematical Model:
- Residual: r_t+1 = y_t+1 - x^_t+1 (observation - simulation)
- Gravity: g_t+1 = ∑_k w_k s_t(k) (weighted sum of symbol intensities)
- Corrected State: x*_t+1 = x^_t+1 + λ g_t+1 (simulation + gravity correction)

Author: Pulse v3.5
"""

from __future__ import annotations
from collections import defaultdict
import numpy as np
import logging
from typing import Dict, List, Optional, Tuple, Any, Union, Set

from symbolic_system.gravity.symbolic_pillars import SymbolicPillarSystem

logger = logging.getLogger(__name__)


class ResidualGravityEngine:
    """
    Learns a low-rank residual correction g_t = B s_t that nudges simulation
    outputs toward observed reality using online ridge-regression with momentum.
    
    Attributes
    ----------
    lambda_ : float
        Global gravity strength (0 ≤ λ ≤ 1)
    reg : float
        L2 regularization coefficient to prevent weight blow-up
    η : float
        Learning rate for SGD updates
    β : float
        Momentum term for smoother convergence
    weights : Dict[str, float]
        Mapping from pillar name to weight
    _v : Dict[str, float]
        Momentum buffer for each weight
    """
    
    def __init__(
        self,
        config = None
    ):
        """
        Initialize the residual gravity engine.
        
        Parameters
        ----------
        config : ResidualGravityConfig, optional
            Configuration for the gravity engine, by default None
        """
        if config is not None:
            self.lambda_ = config.lambda_
            self.reg = config.regularization
            self.η = config.learning_rate
            self.β = config.momentum if config.enable_momentum else 0.0
            self.circuit_breaker_threshold = config.circuit_breaker_threshold
            
            # Additional parameters from config
            self.max_correction = config.max_correction
            self.enable_adaptive_lambda = config.enable_adaptive_lambda
            self.enable_weight_pruning = config.enable_weight_pruning
            self.weight_pruning_threshold = config.weight_pruning_threshold
            self.fragility_threshold = config.fragility_threshold
        else:
            # Default values if no config provided
            self.lambda_ = 0.25
            self.reg = 1e-3
            self.η = 1e-2
            self.β = 0.9
            self.circuit_breaker_threshold = 5.0
            
            # Default values for additional parameters
            self.max_correction = 0.5
            self.enable_adaptive_lambda = True
            self.enable_weight_pruning = True
            self.weight_pruning_threshold = 1e-4
            self.fragility_threshold = 3.0
        
        # Pillar weights (w_k in the math notation)
        self.weights: Dict[str, float] = defaultdict(float)
        
        # Momentum buffer for SGD
        self._v: Dict[str, float] = defaultdict(float)
        
        # Statistics for monitoring
        self._stats = {
            "updates": 0,
            "total_residual": 0.0,
            "total_correction": 0.0,
            "max_weight": 0.0,
            "circuit_breaker_triggered": False,
            "fragility": 0.0
        }
    
    # ---------- Public API ------------------------------------------------- #
    
    def compute_gravity(self, symbol_vec: Dict[str, float]) -> float:
        """
        Compute g_t given current weights and symbol intensities.
        
        This implements the equation: g_t+1 = ∑_k w_k s_t(k)
        
        The gravity value represents the correction that will be applied to
        simulation outputs to pull them toward observed reality. Each symbolic
        pillar (like Hope, Despair, etc.) contributes to this correction based
        on its intensity and learned weight.
        
        Parameters
        ----------
        symbol_vec : Dict[str, float]
            Mapping from symbol names to intensities (s_t(k) in the math)
            
        Returns
        -------
        float
            The gravity correction value
        """
        # Calculate weighted sum of symbol intensities
        gravity = sum(self.weights[k] * v for k, v in symbol_vec.items())
        
        # Update statistics for monitoring
        self._stats["last_gravity_value"] = gravity
        self._stats["last_gravity_contributors"] = {
            k: self.weights[k] * v
            for k, v in symbol_vec.items()
            if abs(self.weights[k] * v) > 0.001  # Only track significant contributors
        }
        
        return gravity
    
    # Alias for backward compatibility
    gravity = compute_gravity
    
    def update_weights(self, residual: Union[float, np.ndarray], symbol_vec: Dict[str, float]) -> None:
        """
        Update weights using online SGD with momentum.
        
        Implementation of the update rule:
        w_k ← w_k + β·v_k + η·(residual·s_k − reg·w_k)
        
        Parameters
        ----------
        residual : Union[float, np.ndarray]
            Prediction residual (y - ŷ)
        symbol_vec : Dict[str, float]
            Symbol intensities from pillar system
        """
        # Convert numpy arrays to float if needed
        if isinstance(residual, np.ndarray):
            residual = float(residual)
            
        for k, s_k in symbol_vec.items():
            # Calculate gradient with L2 regularization
            grad = residual * s_k - self.reg * self.weights[k]
            
            # Update momentum
            self._v[k] = self.β * self._v[k] + (1 - self.β) * grad
            
            # Update weight
            self.weights[k] += self.η * self._v[k]
        
        # Update statistics
        self._stats["updates"] += 1
        self._stats["total_residual"] += abs(residual)
        self._stats["max_weight"] = max(self._stats["max_weight"], max(abs(w) for w in self.weights.values()) if self.weights else 0)
    
    # Alias for backward compatibility
    update = update_weights
    
    def apply_gravity_correction(self,
                         sim_vec: Union[float, np.ndarray],
                         symbol_vec: Dict[str, float]
                        ) -> Tuple[float, Union[float, np.ndarray]]:
        """
        Apply the gravity correction to the simulation vector.
        
        Implementation of the corrected state equation:
        x*_t+1 = x^_t+1 + λ g_t+1
        
        Where:
        - x^_t+1 is the simulation vector (sim_vec)
        - g_t+1 is the gravity correction (weighted sum of symbolic pillars)
        - λ is the global gravity strength parameter (lambda_)
        - x*_t+1 is the corrected vector
        
        Parameters
        ----------
        sim_vec : Union[float, np.ndarray]
            Simulation vector to correct (x^_t+1 in the math)
        symbol_vec : Dict[str, float]
            Symbol intensities from pillar system (s_t in the math)
            
        Returns
        -------
        Tuple[float, Union[float, np.ndarray]]
            Tuple of (correction_amount, corrected_vector)
        """
        # Calculate gravity correction (g_t+1 = ∑_k w_k s_t(k))
        gravity_correction = self.compute_gravity(symbol_vec)
        
        # Apply adaptive lambda if enabled
        effective_lambda = self.lambda_
        if self.enable_adaptive_lambda:
            # Adjust lambda based on correction magnitude and fragility
            fragility = self._calculate_fragility(gravity_correction)
            # Reduce lambda when fragility is high
            effective_lambda = self.lambda_ * max(0.1, 1.0 - fragility)
            self._stats["fragility"] = fragility
            self._stats["effective_lambda"] = effective_lambda
        
        # Apply circuit breaker if needed
        if abs(gravity_correction) > self.circuit_breaker_threshold:
            self._stats["circuit_breaker_triggered"] = True
            self._stats["circuit_breaker_trips"] = self._stats.get("circuit_breaker_trips", 0) + 1
            # Limit correction to threshold
            gravity_correction = self.circuit_breaker_threshold * (1 if gravity_correction > 0 else -1)
            # When breaker trips, reduce lambda further
            effective_lambda *= 0.5
        
        # Apply the final correction (x*_t+1 = x^_t+1 + λ g_t+1)
        correction_amount = effective_lambda * gravity_correction
        
        # Limit correction to max_correction if set
        if hasattr(self, 'max_correction') and self.max_correction > 0:
            if abs(correction_amount) > self.max_correction:
                correction_sign = 1 if correction_amount > 0 else -1
                correction_amount = self.max_correction * correction_sign
        
        # Apply the correction
        corrected = sim_vec + correction_amount
        
        # Update statistics
        if isinstance(correction_amount, np.ndarray):
            self._stats["total_correction"] += float(np.mean(np.abs(correction_amount)))
            self._stats["mean_abs_correction"] = float(np.mean(np.abs(correction_amount)))
        else:
            self._stats["total_correction"] += abs(correction_amount)
            self._stats["mean_abs_correction"] = abs(correction_amount)
        
        self._stats["last_correction"] = correction_amount
        self._stats["last_gravity_value"] = gravity_correction
        # Handle correction efficiency calculation, ensuring proper scalar handling
        if isinstance(correction_amount, np.ndarray):
            corr_mag = float(np.mean(np.abs(correction_amount)))
        else:
            corr_mag = abs(correction_amount)
            
        self._stats["correction_efficiency"] = min(1.0, corr_mag / max(1e-6, abs(gravity_correction)))
        
        # Ensure return types match the annotation
        if isinstance(correction_amount, np.ndarray):
            correction_amount = float(np.mean(correction_amount))
            
        return correction_amount, corrected
        
    def _calculate_fragility(self, gravity_correction: float) -> float:
        """
        Calculate the fragility score based on the current state.
        
        Fragility indicates how sensitive the system is to corrections.
        High fragility means corrections should be applied more cautiously.
        
        Parameters
        ----------
        gravity_correction : float
            The current gravity correction value
            
        Returns
        -------
        float
            Fragility score (0-1), where 1 is high fragility
        """
        # Factors that contribute to fragility:
        # 1. High RMS weight - indicates model is relying heavily on corrections
        rms_factor = min(1.0, self.rms_weight() / self.fragility_threshold)
        
        # 2. Correction volatility - rapid changes in correction
        prev_correction = self._stats.get("last_correction", 0.0)
        current_correction = gravity_correction
        volatility = abs(current_correction - prev_correction) / max(1e-6, abs(current_correction) + abs(prev_correction))
        
        # 3. Circuit breaker history - frequency of past trips
        breaker_trips = self._stats.get("circuit_breaker_trips", 0)
        breaker_factor = min(1.0, breaker_trips / 10)  # Max out at 10 trips
        
        # Combine factors (weighted average)
        fragility = 0.5 * rms_factor + 0.3 * volatility + 0.2 * breaker_factor
        
        return min(1.0, fragility)
    
    # Alias for backward compatibility
    apply_correction = lambda self, sim_vec, symbol_vec: self.apply_gravity_correction(sim_vec, symbol_vec)[1]
    
    def process_and_correct(self, 
                           sim_vec: Union[float, np.ndarray],
                           truth_vec: Union[float, np.ndarray],
                           symbol_vec: Dict[str, float],
                           update_weights: bool = True
                          ) -> Union[float, np.ndarray]:
        """
        Process the simulation and truth vectors, update weights, and apply correction.
        
        This is a convenience method that combines the following steps:
        1. Calculate residual
        2. Update weights (if update_weights is True)
        3. Apply correction
        
        Parameters
        ----------
        sim_vec : Union[float, np.ndarray]
            Simulation vector
        truth_vec : Union[float, np.ndarray]
            Observed truth vector
        symbol_vec : Dict[str, float]
            Symbol intensities from pillar system
        update_weights : bool, optional
            Whether to update weights, by default True
            
        Returns
        -------
        Union[float, np.ndarray]
            Corrected simulation vector
        """
        # Calculate residual
        residual = truth_vec - sim_vec
        
        # Update weights if requested
        if update_weights:
            self.update(residual, symbol_vec)
        
        # Apply correction and return
        return self.apply_correction(sim_vec, symbol_vec)
    
    # ---------- Interface with SymbolicPillarSystem ------------------------ #
    
    def process_with_pillar_system(self, 
                                  sim_vec: Union[float, np.ndarray],
                                  truth_vec: Union[float, np.ndarray],
                                  pillar_system: SymbolicPillarSystem,
                                  update_weights: bool = True
                                 ) -> Union[float, np.ndarray]:
        """
        Process and correct using a pillar system directly.
        
        This is a convenience method that gets the symbol vector from the
        pillar system and then calls process_and_correct.
        
        Parameters
        ----------
        sim_vec : Union[float, np.ndarray]
            Simulation vector
        truth_vec : Union[float, np.ndarray]
            Observed truth vector
        pillar_system : SymbolicPillarSystem
            Symbolic pillar system
        update_weights : bool, optional
            Whether to update weights, by default True
            
        Returns
        -------
        Union[float, np.ndarray]
            Corrected simulation vector
        """
        # Get symbol vector from pillar system
        symbol_vec = pillar_system.as_dict()
        
        # Process and correct
        return self.process_and_correct(sim_vec, truth_vec, symbol_vec, update_weights)
    
    # ---------- Diagnostics ------------------------------------------------ #
    
    def weight_snapshot(self) -> Dict[str, float]:
        """
        Get a snapshot of the current weights.
        
        Returns
        -------
        Dict[str, float]
            Mapping from pillar names to weights
        """
        return dict(self.weights)
    
    def rms_weight(self) -> float:
        """
        Calculate the root mean square of the weights.
        
        This metric indicates the overall magnitude of weights and is used
        to detect potential overfitting or instability in the correction model.
        High RMS weights suggest the model may be fitting to noise rather than
        systematic errors.
        
        Returns
        -------
        float
            RMS of weights
        """
        if not self.weights:
            return 0.0
        
        w = np.array(list(self.weights.values()))
        rms = float(np.sqrt(np.mean(w ** 2)))
        
        # Track this in stats
        self._stats["rms_weight"] = rms
        
        # Check for weight pruning condition
        if self.enable_weight_pruning and rms > self.fragility_threshold:
            self._prune_weights()
            
        return rms
        
    def _prune_weights(self) -> None:
        """
        Prune small weights to prevent overfitting.
        
        This removes weights with magnitudes below the pruning threshold,
        preventing the accumulation of small, noisy weights that can lead
        to instability.
        """
        pruned_count = 0
        for k in list(self.weights.keys()):
            if abs(self.weights[k]) < self.weight_pruning_threshold:
                del self.weights[k]
                pruned_count += 1
                
        if pruned_count > 0:
            self._stats["pruned_weights"] = self._stats.get("pruned_weights", 0) + pruned_count
    
    def significant_weights(self, threshold: float = 0.1) -> Dict[str, float]:
        """
        Get weights above a significance threshold.
        
        Parameters
        ----------
        threshold : float, optional
            Significance threshold, by default 0.1
            
        Returns
        -------
        Dict[str, float]
            Mapping from pillar names to significant weights
        """
        return {k: w for k, w in self.weights.items() if abs(w) >= threshold}
    
    # Alias for backward compatibility
    strongest_symbols = significant_weights
        
    def get_top_contributors(self, n: int = 5) -> List[Tuple[str, float]]:
        """
        Get the top N contributors to gravity by influence magnitude.
        
        This identifies which symbolic pillars have the most significant impact
        on the gravity correction, considering both their weight and typical
        intensity values.
        
        Parameters
        ----------
        n : int, optional
            Number of top contributors to return, by default 5
            
        Returns
        -------
        List[Tuple[str, float]]
            List of (pillar_name, weight) pairs, sorted by impact magnitude
        """
        # Use last gravity contributors if available
        if "last_gravity_contributors" in self._stats:
            contributors = self._stats["last_gravity_contributors"]
            return sorted(
                contributors.items(),
                key=lambda x: abs(x[1]),
                reverse=True
            )[:n]
        
        # Fallback to weight magnitudes if no recent contribution data
        return sorted(
            self.weights.items(),
            key=lambda x: abs(x[1]),
            reverse=True
        )[:n]
    
    # Alias for backward compatibility
    top_weights = get_top_contributors
    
    def reset_weights(self) -> None:
        """Reset all weights to zero."""
        self.weights = defaultdict(float)
        self._v = defaultdict(float)
        self._stats["circuit_breaker_triggered"] = False
        self._stats["fragility"] = 0.0
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get comprehensive engine statistics.
        
        Returns a detailed dictionary of performance metrics, current state,
        and health indicators for monitoring and diagnostics.
        
        Returns
        -------
        Dict[str, Any]
            Statistics dictionary
        """
        stats = dict(self._stats)
        
        # Add derived statistics
        if stats.get("updates", 0) > 0:
            stats["mean_abs_residual"] = stats.get("total_residual", 0.0) / stats["updates"]
            stats["mean_abs_correction"] = stats.get("total_correction", 0.0) / stats["updates"]
        else:
            stats["mean_abs_residual"] = 0.0
            stats["mean_abs_correction"] = 0.0
        
        # Calculate RMS weight
        stats["rms_weight"] = self.rms_weight()
        
        # Count active weights
        stats["active_weights"] = len(self.significant_weights())
        
        # Correction efficiency (how much of potential correction is applied)
        stats["correction_efficiency"] = stats.get("correction_efficiency", 0.0)
        
        # Health metrics
        health = self.check_health()
        stats["health_status"] = health["status"]
        stats["health_warnings"] = health["warnings"]
        
        # Get current top contributors
        top = self.get_top_contributors(5)
        stats["top_contributors"] = dict(top)
        
        # Calculate volatility - how much weights are changing
        if "prev_weights" in self._stats:
            prev_weights = self._stats["prev_weights"]
            current_weights = {k: self.weights.get(k, 0.0) for k in set(prev_weights) | set(self.weights)}
            prev_vals = {k: prev_weights.get(k, 0.0) for k in current_weights}
            
            # Calculate average change
            diffs = [abs(current_weights[k] - prev_vals[k]) for k in current_weights]
            if diffs:
                stats["weight_volatility"] = sum(diffs) / len(diffs)
            else:
                stats["weight_volatility"] = 0.0
        
        # Store current weights for next volatility calculation
        self._stats["prev_weights"] = dict(self.weights)
        
        return stats
    
    def check_health(self) -> Dict[str, Any]:
        """
        Check the health of the gravity engine.
        
        Performs comprehensive diagnostics to detect potential issues like
        overfitting, instability, or ineffective learning. Returns a detailed
        health assessment with warnings and metrics.
        
        Returns
        -------
        Dict[str, Any]
            Health check results with status, warnings, and metrics
        """
        health = {
            "status": "healthy",
            "warnings": [],
            "rms_weight": self.rms_weight(),
            "max_weight": self._stats.get("max_weight", 0.0),
            "circuit_breaker_trips": self._stats.get("circuit_breaker_trips", 0),
            "correction_efficiency": self._stats.get("correction_efficiency", 0.0),
            "fragility": self._stats.get("fragility", 0.0),
        }
        
        # Check for potential issues in order of severity
        
        # 1. Exploding weights (most severe)
        if health["max_weight"] > 100.0:
            health["status"] = "critical"
            health["warnings"].append("Maximum weight too high, possible divergence")
        
        # 2. Excessively large weights
        elif health["rms_weight"] > 10.0:
            health["status"] = "unhealthy"
            health["warnings"].append("RMS weights too high, possible overfitting")
        
        # 3. Frequent circuit breaker trips
        elif health["circuit_breaker_trips"] > 5:
            health["status"] = "warning"
            health["warnings"].append(f"Circuit breaker triggered {health['circuit_breaker_trips']} times, corrections may be unstable")
        
        # 4. High fragility
        elif health["fragility"] > 0.8:
            health["status"] = "warning"
            health["warnings"].append(f"High fragility score ({health['fragility']:.2f}), corrections applied conservatively")
        
        # 5. Stagnant weights (not learning)
        elif self._stats.get("updates", 0) > 100 and health["rms_weight"] < 0.01:
            health["status"] = "caution"
            health["warnings"].append("Weights remain very small after many updates, possibly not learning")
        
        # 6. Low correction efficiency
        elif health["correction_efficiency"] < 0.3 and self._stats.get("updates", 0) > 20:
            health["status"] = "caution"
            health["warnings"].append(f"Low correction efficiency ({health['correction_efficiency']:.2f}), corrections heavily limited")
        
        # Add recommendations based on health status
        if health["status"] != "healthy":
            health["recommendations"] = self._get_health_recommendations(health)
            
        return health
        
    def _get_health_recommendations(self, health: Dict[str, Any]) -> List[str]:
        """Generate recommendations based on health status."""
        recommendations = []
        
        # Add specific recommendations based on warnings
        for warning in health["warnings"]:
            if "overfitting" in warning:
                recommendations.append("Increase regularization parameter")
                recommendations.append("Consider pruning weights or reducing learning rate")
            elif "divergence" in warning:
                recommendations.append("Reset weights and decrease learning rate significantly")
                recommendations.append("Increase circuit breaker threshold temporarily")
            elif "circuit breaker" in warning:
                recommendations.append("Review which symbols have high weights and consider rule improvements")
                recommendations.append("Increase regularization to prevent large corrections")
            elif "fragility" in warning:
                recommendations.append("Monitor for over-reliance on symbolic corrections")
                recommendations.append("Consider enhancing causal rules to reduce correction magnitude")
            elif "not learning" in warning:
                recommendations.append("Increase learning rate or decrease regularization")
                recommendations.append("Verify that meaningful residuals are being provided")
            elif "correction efficiency" in warning:
                recommendations.append("Check if circuit breaker threshold is too restrictive")
                recommendations.append("Consider raising max_correction parameter")
                
        # Remove duplicates while preserving order
        seen = set()
        unique_recommendations = []
        for rec in recommendations:
            if rec not in seen:
                seen.add(rec)
                unique_recommendations.append(rec)
                
        return unique_recommendations
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert engine to dictionary for serialization.
        
        Returns
        -------
        Dict[str, Any]
            Dictionary representation of engine
        """
        return {
            "lambda": self.lambda_,
            "reg": self.reg,
            "lr": self.η,
            "momentum": self.β,
            "circuit_breaker_threshold": self.circuit_breaker_threshold,
            "weights": dict(self.weights),
            "momentum_buffer": dict(self._v),
            "stats": self._stats,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ResidualGravityEngine":
        """
        Create engine from dictionary.
        
        Parameters
        ----------
        data : Dict[str, Any]
            Dictionary representation of engine
            
        Returns
        -------
        ResidualGravityEngine
            Engine instance
        """
        engine = cls()
        
        # Load parameters
        engine.lambda_ = data.get("lambda", 0.25)
        engine.reg = data.get("reg", 1e-3)
        engine.η = data.get("lr", 1e-2)
        engine.β = data.get("momentum", 0.9)
        engine.circuit_breaker_threshold = data.get("circuit_breaker_threshold", 5.0)
        
        # Load weights
        for k, w in data.get("weights", {}).items():
            engine.weights[k] = w
        
        # Load momentum buffer
        for k, v in data.get("momentum_buffer", {}).items():
            engine._v[k] = v
        
        # Load stats
        engine._stats = data.get("stats", engine._stats)
        
        return engine