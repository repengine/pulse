"""
gravity_fabric.py

Symbolic Gravity Fabric implementation for the Pulse system.

This module implements the core Symbolic Gravity Fabric that uses
symbolic pillars to support and adjust a residual gravity field
that corrects simulation outputs.

Author: Pulse v3.5
"""

import logging
import numpy as np
from typing import Dict, List, Optional, Tuple, Any
import time
from dataclasses import dataclass, field
from datetime import datetime

from engine.worldstate import WorldState
from symbolic_system.gravity.symbolic_pillars import (
    SymbolicPillar,
    SymbolicPillarSystem,
)
from symbolic_system.gravity.engines.residual_gravity_engine import (
    ResidualGravityEngine,
    GravityEngineConfig,
)
from symbolic_system.gravity.gravity_config import ResidualGravityConfig, DEFAULT_CONFIG

logger = logging.getLogger(__name__)


@dataclass
class ResidualPoint:
    """
    Record of a single residual point between prediction and reality.

    Attributes
    ----------
    timestamp : float
        Unix timestamp of the observation
    variable_name : str
        Name of the variable being predicted
    predicted : float
        Original predicted value
    actual : float
        Observed actual value
    corrected : Optional[float]
        Value after gravity correction
    residual : float
        Difference between actual and predicted
    correction : Optional[float]
        Amount of correction applied
    symbolic_state : Dict[str, float]
        Snapshot of symbolic pillar values at time of prediction
    """

    timestamp: float = field(default_factory=time.time)
    variable_name: str = ""
    predicted: float = 0.0
    actual: float = 0.0
    corrected: Optional[float] = None
    residual: float = 0.0
    correction: Optional[float] = None
    symbolic_state: Dict[str, float] = field(default_factory=dict)

    def __post_init__(self):
        """Calculate residual if not provided."""
        if self.residual == 0.0:
            self.residual = self.actual - self.predicted

        if self.corrected is not None and self.correction is None:
            self.correction = self.corrected - self.predicted

    @property
    def variable(self) -> str:
        """
        Alias for variable_name for backward compatibility.

        Returns
        -------
        str
            The variable name
        """
        return self.variable_name

    def improvement(self) -> Optional[float]:
        """
        Calculate improvement from correction.

        Returns
        -------
        Optional[float]
            Absolute improvement in error, or None if corrected not available
        """
        if self.corrected is None:
            return None

        original_error = abs(self.actual - self.predicted)
        corrected_error = abs(self.actual - self.corrected)
        return original_error - corrected_error

    def improvement_pct(self) -> Optional[float]:
        """
        Calculate improvement percentage.

        Returns
        -------
        Optional[float]
            Percentage improvement in error, or None if corrected not available
        """
        if self.corrected is None:
            return None

        original_error = abs(self.actual - self.predicted)
        if original_error < 1e-10:
            return 0.0

        corrected_error = abs(self.actual - self.corrected)
        return 100.0 * (original_error - corrected_error) / original_error

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert to dictionary.

        Returns
        -------
        Dict[str, Any]
            Dictionary representation of the point
        """
        return {
            "timestamp": self.timestamp,
            "datetime": datetime.fromtimestamp(self.timestamp).isoformat(),
            "variable_name": self.variable_name,
            "predicted": self.predicted,
            "actual": self.actual,
            "corrected": self.corrected,
            "residual": self.residual,
            "correction": self.correction,
            "improvement": self.improvement(),
            "improvement_pct": self.improvement_pct(),
            "symbolic_state": dict(self.symbolic_state),
        }


@dataclass
class GravityFabricMetrics:
    """
    Metrics tracking for the Symbolic Gravity Fabric.

    Attributes
    ----------
    total_corrections : int
        Number of corrections applied
    total_updates : int
        Number of weight updates performed
    correction_magnitudes : List[float]
        History of correction magnitudes
    residual_magnitudes : List[float]
        History of residual magnitudes
    pillars_dominant : Dict[str, int]
        Count of times each pillar was dominant
    max_history : int
        Maximum history length to maintain
    """

    total_corrections: int = 0
    total_updates: int = 0
    correction_magnitudes: List[float] = field(default_factory=list)
    residual_magnitudes: List[float] = field(default_factory=list)
    pillars_dominant: Dict[str, int] = field(default_factory=dict)
    max_history: int = 100

    def record_correction(self, magnitude: float) -> None:
        """Record a correction magnitude."""
        self.total_corrections += 1
        self.correction_magnitudes.append(magnitude)

        # Trim history if needed
        if len(self.correction_magnitudes) > self.max_history:
            self.correction_magnitudes = self.correction_magnitudes[-self.max_history :]

    def record_residual(self, magnitude: float) -> None:
        """Record a residual magnitude."""
        self.residual_magnitudes.append(magnitude)

        # Trim history if needed
        if len(self.residual_magnitudes) > self.max_history:
            self.residual_magnitudes = self.residual_magnitudes[-self.max_history :]

    def record_update(self) -> None:
        """Record a weight update."""
        self.total_updates += 1

    def record_dominant_pillars(self, pillars: List[str]) -> None:
        """Record dominant pillars."""
        for pillar in pillars:
            if pillar in self.pillars_dominant:
                self.pillars_dominant[pillar] += 1
            else:
                self.pillars_dominant[pillar] = 1

    def get_avg_correction(self) -> float:
        """Get average correction magnitude."""
        if not self.correction_magnitudes:
            return 0.0
        return float(np.mean(self.correction_magnitudes))

    def get_avg_residual(self) -> float:
        """Get average residual magnitude."""
        if not self.residual_magnitudes:
            return 0.0
        return float(np.mean(self.residual_magnitudes))

    def get_top_pillars(self, n: int = 3) -> List[Tuple[str, int]]:
        """Get top dominant pillars."""
        return sorted(self.pillars_dominant.items(), key=lambda x: x[1], reverse=True)[
            :n
        ]


class SymbolicGravityFabric:
    """
    Core implementation of the Symbolic Gravity Fabric.

    The gravity fabric uses symbolic pillars to support and adjust
    a residual gravity field that corrects simulation outputs towards
    observed reality.

    Attributes
    ----------
    pillar_system : SymbolicPillarSystem
        System that manages symbolic pillars
    gravity_engine : ResidualGravityEngine
        Engine that calculates gravity corrections
    config : ResidualGravityConfig
        Configuration for the fabric
    metrics : GravityFabricMetrics
        Metrics tracking for the fabric
    residual_history : Dict[str, List[ResidualPoint]]
        History of residuals for each variable
    last_apply_time : float
        Timestamp of last apply operation
    """

    def __init__(
        self,
        pillar_names: Optional[List[str]] = None,
        config: Optional[ResidualGravityConfig] = None,
        pillar_system: Optional[SymbolicPillarSystem] = None,
        gravity_engine: Optional[ResidualGravityEngine] = None,
    ):
        """
        Initialize the SymbolicGravityFabric.

        Parameters
        ----------
        pillar_names : List[str], optional
            Names of pillars to create. If None, uses defaults.
        config : ResidualGravityConfig, optional
            Configuration for the fabric. If None, uses defaults.
        pillar_system : SymbolicPillarSystem, optional
            Pre-configured pillar system. If provided, pillar_names is ignored.
        gravity_engine : ResidualGravityEngine, optional
            Pre-configured gravity engine. If provided, config is only used for
            fabric-specific settings.
        """
        self.config = config or DEFAULT_CONFIG

        # Initialize pillar system
        if pillar_system is not None:
            self.pillar_system = pillar_system
        else:
            self.pillar_system = SymbolicPillarSystem(
                pillar_names=pillar_names, config=self.config
            )

        # Initialize gravity engine
        if gravity_engine is not None:
            self.gravity_engine = gravity_engine
        else:
            self.gravity_engine = ResidualGravityEngine(
                config=GravityEngineConfig(
                    lambda_=self.config.lambda_,
                    regularization_strength=self.config.regularization,
                    learning_rate=self.config.learning_rate,
                    momentum_factor=self.config.momentum,
                    circuit_breaker_threshold=self.config.circuit_breaker_threshold,
                    max_correction=self.config.max_correction,
                    enable_adaptive_lambda=self.config.enable_adaptive_lambda,
                    enable_weight_pruning=self.config.enable_weight_pruning,
                    weight_pruning_threshold=self.config.weight_pruning_threshold,
                    fragility_threshold=self.config.fragility_threshold,
                ),
                dt=1.0,  # Default placeholder
                state_dimensionality=1,  # Default placeholder
            )

        # Initialize metrics
        self.metrics = GravityFabricMetrics(max_history=self.config.max_history)

        # Initialize residual history
        self.residual_history: Dict[str, List[ResidualPoint]] = {}

        # Performance tracking
        self.last_apply_time = 0.0

        if self.config.debug_logging:
            logger.debug(
                f"Initialized gravity fabric with {len(self.pillar_system.pillars)} pillars"
            )

    def apply_gravity(
        self, state: WorldState, predicted: float, truth: Optional[float] = None
    ) -> Tuple[float, Dict[str, Any]]:
        """
        Apply gravity correction to a predicted value.

        Parameters
        ----------
        state : WorldState
            Current world state with symbolic pillars
        predicted : float
            Predicted value from simulation
        truth : float, optional
            Observed ground truth. If provided, will update weights.

        Returns
        -------
        Tuple[float, Dict[str, Any]]
            Corrected value and information about the correction
        """
        # Track execution time
        start_time = time.time()

        # Load pillar values from state
        self.pillar_system.load_from_state(state)

        # Get pillar values as dict
        symbol_vec = self.pillar_system.as_dict()

        # Get dominant pillars for metrics
        dominant_pillars = self.pillar_system.get_dominant_pillars()
        if dominant_pillars:
            self.metrics.record_dominant_pillars(dominant_pillars)

        # Apply natural pillar interactions
        self.pillar_system.apply_interactions()

        # Apply gravity correction
        corrected = self.gravity_engine.apply_correction(predicted, symbol_vec)

        # Record correction magnitude
        correction = corrected - predicted
        self.metrics.record_correction(abs(correction))

        # Update weights if truth is provided
        if truth is not None:
            # Calculate residual
            residual = truth - predicted
            self.metrics.record_residual(abs(residual))

            # Update weights
            self.gravity_engine.update_weights(residual, symbol_vec)
            self.metrics.record_update()

        # Update state with new pillar values after interactions
        self.pillar_system.update_state_overlays(state)

        # Calculate execution time
        self.last_apply_time = time.time() - start_time

        # Return corrected value and info
        return corrected, {
            "original": predicted,
            "corrected": corrected,
            "correction": correction,
            "dominant_pillars": dominant_pillars,
            "elapsed_time": self.last_apply_time,
        }

    def apply_gravity_batch(
        self,
        state: WorldState,
        predicted_values: List[float],
        truth_values: Optional[List[float]] = None,
    ) -> Tuple[List[float], Dict[str, Any]]:
        """
        Apply gravity correction to a batch of predicted values.

        Parameters
        ----------
        state : WorldState
            Current world state with symbolic pillars
        predicted_values : List[float]
            Predicted values from simulation
        truth_values : List[float], optional
            Observed ground truths. If provided, will update weights.

        Returns
        -------
        Tuple[List[float], Dict[str, Any]]
            Corrected values and information about the corrections
        """
        # Track execution time
        start_time = time.time()

        # Load pillar values from state
        self.pillar_system.load_from_state(state)

        # Get pillar values as dict
        symbol_vec = self.pillar_system.as_dict()

        # Get dominant pillars for metrics
        dominant_pillars = self.pillar_system.get_dominant_pillars()
        if dominant_pillars:
            self.metrics.record_dominant_pillars(dominant_pillars)

        # Apply natural pillar interactions
        self.pillar_system.apply_interactions()

        # Apply gravity corrections
        corrected_values = []
        total_correction = 0.0

        for predicted in predicted_values:
            # Apply correction
            corrected = self.gravity_engine.apply_correction(predicted, symbol_vec)
            corrected_values.append(corrected)

            # Record correction magnitude
            correction = corrected - predicted
            total_correction += abs(correction)

        # Record average correction magnitude
        self.metrics.record_correction(total_correction / len(predicted_values))

        # Update weights if truths are provided
        if truth_values is not None and len(truth_values) == len(predicted_values):
            total_residual = 0.0

            for predicted, truth in zip(predicted_values, truth_values):
                # Calculate residual
                residual = truth - predicted
                total_residual += abs(residual)

                # Update weights
                self.gravity_engine.update_weights(residual, symbol_vec)
                self.metrics.record_update()

            # Record average residual magnitude
            self.metrics.record_residual(total_residual / len(predicted_values))

        # Update state with new pillar values after interactions
        self.pillar_system.update_state_overlays(state)

        # Calculate execution time
        elapsed_time = time.time() - start_time

        # Return corrected values and info
        return corrected_values, {
            "count": len(predicted_values),
            "avg_correction": total_correction / len(predicted_values),
            "dominant_pillars": dominant_pillars,
            "elapsed_time": elapsed_time,
        }

    def reset(self) -> None:
        """Reset the gravity fabric."""
        # Reset gravity engine
        self.gravity_engine.reset_weights()

        # Reset metrics
        self.metrics = GravityFabricMetrics(max_history=self.config.max_history)

        # Reset residual history
        self.residual_history.clear()

        if self.config.debug_logging:
            logger.debug("Reset gravity fabric")

    def get_top_contributors(self, n: int = 5) -> List[Tuple[str, float]]:
        """
        Get the symbols with strongest influence.

        Parameters
        ----------
        n : int, optional
            Number of symbols to return.

        Returns
        -------
        List[Tuple[str, float]]
            List of (symbol, weight) pairs, sorted by absolute weight.
        """
        return self.gravity_engine.get_top_contributors(n)

    def adjust_pillar(self, name: str, delta: float) -> None:
        """
        Adjust a pillar's intensity.

        Parameters
        ----------
        name : str
            Name of the pillar
        delta : float
            Amount to adjust by (positive or negative)
        """
        self.pillar_system.adjust_pillar(name, delta)

    def set_pillar_value(self, name: str, value: float) -> None:
        """
        Set a pillar's intensity directly.

        Parameters
        ----------
        name : str
            Name of the pillar
        value : float
            New intensity value (0-1)
        """
        pillar = self.pillar_system.get_pillar(name)
        if pillar:
            pillar.set_intensity(value)

    def get_pillar_value(self, name: str) -> float:
        """
        Get a pillar's intensity value.

        Parameters
        ----------
        name : str
            Name of the pillar

        Returns
        -------
        float
            Intensity value (0 if pillar not found)
        """
        return self.pillar_system.get_pillar_value(name)

    def get_pillar_values(self) -> Dict[str, float]:
        """
        Get all pillar intensity values.

        Returns
        -------
        Dict[str, float]
            Dictionary mapping pillar names to intensity values
        """
        return self.pillar_system.as_dict()

    def has_pillar(self, name: str) -> bool:
        """
        Check if a pillar exists.

        Parameters
        ----------
        name : str
            Name of the pillar

        Returns
        -------
        bool
            Whether the pillar exists
        """
        return name in self.pillar_system.pillars

    def add_pillar(self, name: str, initial_value: float = 0.5) -> SymbolicPillar:
        """
        Add a new pillar.

        Parameters
        ----------
        name : str
            Name of the pillar
        initial_value : float, optional
            Initial intensity value (0-1)

        Returns
        -------
        SymbolicPillar
            The created pillar
        """
        if name in self.pillar_system.pillars:
            pillar = self.pillar_system.pillars[name]
            pillar.set_intensity(initial_value)
            return pillar

        pillar = SymbolicPillar(
            name=name, intensity=initial_value, max_history=self.config.max_history
        )
        self.pillar_system.pillars[name] = pillar
        return pillar

    def get_metrics(self) -> Dict[str, Any]:
        """
        Get metrics about the gravity fabric.

        Returns
        -------
        Dict[str, Any]
            Dictionary of metrics
        """
        return {
            "corrections": {
                "total": self.metrics.total_corrections,
                "avg_magnitude": self.metrics.get_avg_correction(),
            },
            "residuals": {"avg_magnitude": self.metrics.get_avg_residual()},
            "updates": {"total": self.metrics.total_updates},
            "pillars": {
                "dominant": self.metrics.get_top_pillars(),
                "count": len(self.pillar_system.pillars),
            },
            "weights": {
                "rms": self.gravity_engine.rms_weight(),
                "top": self.gravity_engine.strongest_symbols(),
            },
            "health": {
                "fragility": self.gravity_engine.fragility_score(),
                "circuit_breaker": self.gravity_engine.is_circuit_breaker_triggered(),
            },
        }

    def get_diagnostic_info(self) -> Dict[str, Any]:
        """
        Get detailed diagnostic information about the fabric.

        Returns
        -------
        Dict[str, Any]
            Dictionary of diagnostic information
        """
        return {
            "metrics": self.get_metrics(),
            "config": {
                "lambda": self.config.lambda_,
                "learning_rate": self.config.learning_rate,
                "momentum": self.config.momentum,
                "regularization": self.config.regularization,
                "enable_momentum": self.config.enable_momentum,
                "circuit_breaker_threshold": self.config.circuit_breaker_threshold,
            },
            "pillar_system": {
                "pillars": list(self.pillar_system.pillars.keys()),
                "interactions": list(self.pillar_system.interaction_matrix.keys()),
            },
            "performance": {
                "last_apply_time": self.last_apply_time,
                "avg_corrections_per_second": self.metrics.total_corrections
                / max(1.0, self.last_apply_time),
            },
        }

    def suggest_fixes(self) -> List[str]:
        """
        Suggest fixes if system health is poor.

        Returns
        -------
        List[str]
            List of suggestions for improving system health
        """
        suggestions = []

        # Check if fragility is high
        metrics = self.get_metrics()
        if metrics["health"]["fragility"] > 0.7:
            suggestions.append(
                "High fragility detected. Consider reducing lambda or "
                "increasing regularization."
            )

        # Check if circuit breaker is triggered
        if metrics["health"]["circuit_breaker"]:
            suggestions.append(
                "Circuit breaker triggered. Large corrections being clamped. "
                "Consider improving causal model or increasing circuit "
                "breaker threshold."
            )

        # Check if average residual is large
        if metrics["residuals"]["avg_magnitude"] > 2.0:
            suggestions.append(
                "Large average residual detected. Causal model may be missing "
                "important factors."
            )

        # Check if a single pillar dominates
        top_pillars = self.metrics.get_top_pillars(1)
        if top_pillars and top_pillars[0][1] > self.metrics.total_corrections * 0.8:
            suggestions.append(
                f"Pillar '{top_pillars[0][0]}' dominates corrections ({top_pillars[0][1]} times). "
                "Consider improving causal model to handle this factor directly."
            )

        # Add general suggestion if things look good
        if not suggestions:
            suggestions.append("System health looks good. No specific fixes needed.")

        return suggestions

    def apply_to_world_state(self, state: WorldState) -> None:
        """
        Apply pillar interactions to a world state.

        Parameters
        ----------
        state : WorldState
            The state to update
        """
        # Load pillar values from state
        self.pillar_system.load_from_state(state)

        # Apply natural pillar interactions
        self.pillar_system.apply_interactions()

        # Update state with new pillar values
        self.pillar_system.update_state_overlays(state)

    def get_system_tension(self) -> float:
        """
        Calculate overall system tension based on opposing pillars.

        Returns
        -------
        float
            Tension score (0-1)
        """
        return self.pillar_system.symbolic_tension_score()

    # Additional methods needed for compatibility

    def apply_correction(self, variable_name: str, predicted_value: float) -> float:
        """
        Apply gravity correction to a predicted value for a specific variable.

        Parameters
        ----------
        variable_name : str
            Name of the variable being predicted
        predicted_value : float
            Predicted value from simulation

        Returns
        -------
        float
            Corrected value
        """
        # Get current pillar values
        symbol_vec = self.pillar_system.as_dict()

        # Apply correction
        corrected = self.gravity_engine.apply_correction(predicted_value, symbol_vec)

        # Record correction
        correction = corrected - predicted_value
        self.metrics.record_correction(abs(correction))

        return corrected

    def record_residual(
        self, variable_name: str, predicted_value: float, actual_value: float
    ) -> ResidualPoint:
        """
        Record a residual between prediction and actual value.

        Parameters
        ----------
        variable_name : str
            Name of the variable being predicted
        predicted_value : float
            Predicted value from simulation
        actual_value : float
            Observed actual value

        Returns
        -------
        ResidualPoint
            The recorded residual point
        """
        # Calculate residual
        residual = actual_value - predicted_value

        # Get current pillar values
        symbol_vec = self.pillar_system.as_dict()

        # Apply correction for diagnostic purposes
        corrected_value = self.gravity_engine.apply_correction(
            predicted_value, symbol_vec
        )

        # Update weights
        self.gravity_engine.update_weights(residual, symbol_vec)
        self.metrics.record_update()

        # Record residual magnitude
        self.metrics.record_residual(abs(residual))

        # Create residual point
        point = ResidualPoint(
            timestamp=time.time(),
            variable_name=variable_name,
            predicted=predicted_value,
            actual=actual_value,
            corrected=corrected_value,
            residual=residual,
            symbolic_state=dict(symbol_vec),
        )

        # Add to history
        if variable_name not in self.residual_history:
            self.residual_history[variable_name] = []

        self.residual_history[variable_name].append(point)

        # Trim history if needed
        if len(self.residual_history[variable_name]) > self.config.max_history:
            self.residual_history[variable_name] = self.residual_history[variable_name][
                -self.config.max_history :
            ]

        return point

    def get_recent_residuals(
        self, variable_name: str, n: int = 10
    ) -> List[ResidualPoint]:
        """
        Get recent residuals for a variable.

        Parameters
        ----------
        variable_name : str
            Name of the variable
        n : int, optional
            Number of recent residuals to return

        Returns
        -------
        List[ResidualPoint]
            List of recent residual points
        """
        if variable_name not in self.residual_history:
            return []

        return self.residual_history[variable_name][-n:]

    def get_mean_absolute_error(self, variable_name: str) -> Tuple[float, float]:
        """
        Calculate mean absolute error for a variable.

        Parameters
        ----------
        variable_name : str
            Name of the variable

        Returns
        -------
        Tuple[float, float]
            Tuple of (original MAE, corrected MAE)
        """
        if (
            variable_name not in self.residual_history
            or not self.residual_history[variable_name]
        ):
            return (0.0, 0.0)

        points = self.residual_history[variable_name]

        # Calculate original MAE
        original_errors = [abs(point.actual - point.predicted) for point in points]
        original_mae = float(np.mean(original_errors))

        # Calculate corrected MAE only for points with valid corrections
        points_with_correction = [
            point for point in points if point.corrected is not None
        ]
        if not points_with_correction:
            return (original_mae, original_mae)

        # Now we're sure all points have corrected values
        corrected_errors = [
            abs(point.actual - point.corrected)
            for point in points_with_correction
            if point.corrected is not None
        ]
        corrected_mae = float(np.mean(corrected_errors))

        return (original_mae, corrected_mae)

    def get_improvement_percentage(self, variable_name: str) -> float:
        """
        Calculate percentage improvement for a variable.

        Parameters
        ----------
        variable_name : str
            Name of the variable

        Returns
        -------
        float
            Percentage improvement (0-100)
        """
        original_mae, corrected_mae = self.get_mean_absolute_error(variable_name)

        if original_mae < 1e-10:
            return 0.0

        return 100.0 * (original_mae - corrected_mae) / original_mae

    def get_pillar_contributions(self) -> Dict[str, float]:
        """
        Calculate relative contribution of each pillar.

        Returns
        -------
        Dict[str, float]
            Dictionary mapping pillar names to relative contribution scores
        """
        # Get weights
        weights = self.gravity_engine.weight_snapshot()

        # Calculate sum of absolute weights
        total_weight = sum(abs(w) for w in weights.values())

        # If no significant weights, return empty dict
        if total_weight < 1e-10:
            return {}

        # Calculate relative contributions
        return {k: abs(w) / total_weight for k, w in weights.items()}

    def generate_diagnostic_report(self) -> Dict[str, Any]:
        """
        Generate a comprehensive diagnostic report.

        Returns
        -------
        Dict[str, Any]
            Dictionary with diagnostic information
        """
        # Get metrics and diagnostic info
        metrics = self.get_metrics()
        _diag_info = self.get_diagnostic_info()

        # Calculate variable-specific metrics
        variable_metrics = {}
        for var in self.residual_history:
            mae_orig, mae_corr = self.get_mean_absolute_error(var)
            improvement = self.get_improvement_percentage(var)

            variable_metrics[var] = {
                "mae_original": mae_orig,
                "mae_corrected": mae_corr,
                "improvement_pct": improvement,
                "residual_count": len(self.residual_history[var]),
            }

        # Generate report
        report = {
            "variables": variable_metrics,
            "pillars": {
                "count": len(self.pillar_system.pillars),
                "values": self.get_pillar_values(),
                "contributions": self.get_pillar_contributions(),
            },
            "metrics": metrics,
            "weights": {
                "top_contributors": self.get_top_contributors(),
                "rms_weight": self.gravity_engine.rms_weight(),
            },
            "health": {
                "fragility": self.gravity_engine.fragility_score(),
                "circuit_breaker": self.gravity_engine.is_circuit_breaker_triggered(),
                "tension_score": self.get_system_tension(),
            },
            "suggestions": self.suggest_fixes(),
        }

        return report

    def reset_weights(self) -> None:
        """Reset gravity engine weights (compatibility method)."""
        self.gravity_engine.reset_weights()
