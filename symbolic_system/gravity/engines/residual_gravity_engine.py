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
from collections import defaultdict, deque
import numpy as np
from typing import Dict, List, Optional, Tuple, Any, Union
from utils.log_utils import get_logger
import config.gravity_config as grav_cfg
from symbolic_system.gravity.symbolic_pillars import SymbolicPillarSystem


class GravityEngineConfig:
    """
    Configuration class for the ResidualGravityEngine.

    Holds all parameters that control the behavior of the gravity engine.
    """

    def __init__(
        self,
        lambda_: Optional[float] = None,
        regularization_strength: Optional[float] = None,
        learning_rate: Optional[float] = None,
        momentum_factor: Optional[float] = None,
        circuit_breaker_threshold: Optional[float] = None,
        max_correction: Optional[float] = None,
        enable_adaptive_lambda: Optional[bool] = None,
        enable_weight_pruning: Optional[bool] = None,
        weight_pruning_threshold: Optional[float] = None,
        fragility_threshold: Optional[float] = None,
        ewma_span: Optional[float] = None,
        adaptive_lambda_min: Optional[float] = None,
        adaptive_lambda_max: Optional[float] = None,
        adaptive_lambda_window_size: Optional[int] = None,
        adaptive_lambda_residual_threshold_high: Optional[float] = None,
        adaptive_lambda_residual_threshold_low: Optional[float] = None,
        adaptive_lambda_increase_factor: Optional[float] = None,
        adaptive_lambda_decrease_factor: Optional[float] = None,
        logging_level: Optional[int] = None,
    ):
        """
        Initialize the gravity engine configuration.

        Parameters
        ----------
        lambda_ : float, optional
            Global gravity strength (0 ≤ λ ≤ 1), by default None
        regularization_strength : float, optional
            L2 regularization coefficient to prevent weight blow-up, by default None
        learning_rate : float, optional
            Learning rate for SGD updates, by default None
        momentum_factor : float, optional
            Momentum term for smoother convergence, by default None
        circuit_breaker_threshold : float, optional
            Threshold for the circuit breaker, by default None
        max_correction : float, optional
            Maximum allowed correction, by default None
        enable_adaptive_lambda : bool, optional
            Whether to enable adaptive lambda, by default None
        enable_weight_pruning : bool, optional
            Whether to enable weight pruning, by default None
        weight_pruning_threshold : float, optional
            Threshold for weight pruning, by default None
        fragility_threshold : float, optional
            Threshold for fragility detection, by default None
        ewma_span : float, optional
            Span parameter for EWMA decay of impact matrix (alpha = 2/(span+1)), by default None
        adaptive_lambda_min : float, optional
            Minimum value for adaptive lambda, by default None
        adaptive_lambda_max : float, optional
            Maximum value for adaptive lambda, by default None
        adaptive_lambda_window_size : int, optional
            Window size for adaptive lambda adjustment, by default None
        adaptive_lambda_residual_threshold_high : float, optional
            Upper threshold for increasing lambda, by default None
        adaptive_lambda_residual_threshold_low : float, optional
            Lower threshold for decreasing lambda, by default None
        adaptive_lambda_increase_factor : float, optional
            Factor to increase lambda by when residuals are high, by default None
        adaptive_lambda_decrease_factor : float, optional
            Factor to decrease lambda by when residuals are low, by default None
        """
        # Use provided values or defaults from gravity_config
        self.lambda_ = lambda_ if lambda_ is not None else grav_cfg.DEFAULT_LAMBDA
        self.regularization_strength = (
            regularization_strength
            if regularization_strength is not None
            else grav_cfg.DEFAULT_REGULARIZATION
        )
        self.learning_rate = (
            learning_rate
            if learning_rate is not None
            else grav_cfg.DEFAULT_LEARNING_RATE
        )
        self.momentum_factor = (
            momentum_factor
            if momentum_factor is not None
            else grav_cfg.DEFAULT_MOMENTUM
        )
        self.circuit_breaker_threshold = (
            circuit_breaker_threshold
            if circuit_breaker_threshold is not None
            else grav_cfg.DEFAULT_CIRCUIT_BREAKER_THRESHOLD
        )
        self.max_correction = (
            max_correction
            if max_correction is not None
            else grav_cfg.DEFAULT_MAX_CORRECTION
        )
        self.enable_adaptive_lambda = (
            enable_adaptive_lambda
            if enable_adaptive_lambda is not None
            else grav_cfg.DEFAULT_ENABLE_ADAPTIVE_LAMBDA
        )
        self.enable_weight_pruning = (
            enable_weight_pruning
            if enable_weight_pruning is not None
            else grav_cfg.DEFAULT_ENABLE_WEIGHT_PRUNING
        )
        self.weight_pruning_threshold = (
            weight_pruning_threshold
            if weight_pruning_threshold is not None
            else grav_cfg.DEFAULT_WEIGHT_PRUNING_THRESHOLD
        )
        self.fragility_threshold = (
            fragility_threshold
            if fragility_threshold is not None
            else grav_cfg.DEFAULT_FRAGILITY_THRESHOLD
        )
        self.ewma_span = (
            ewma_span if ewma_span is not None else grav_cfg.DEFAULT_EWMA_SPAN
        )

        # Initialize adaptive lambda parameters
        self.adaptive_lambda_min = (
            adaptive_lambda_min
            if adaptive_lambda_min is not None
            else grav_cfg.DEFAULT_ADAPTIVE_LAMBDA_MIN
        )
        self.adaptive_lambda_max = (
            adaptive_lambda_max
            if adaptive_lambda_max is not None
            else grav_cfg.DEFAULT_ADAPTIVE_LAMBDA_MAX
        )
        self.adaptive_lambda_window_size = (
            adaptive_lambda_window_size
            if adaptive_lambda_window_size is not None
            else grav_cfg.DEFAULT_ADAPTIVE_LAMBDA_WINDOW_SIZE
        )
        self.adaptive_lambda_residual_threshold_high = (
            adaptive_lambda_residual_threshold_high
            if adaptive_lambda_residual_threshold_high is not None
            else grav_cfg.DEFAULT_ADAPTIVE_LAMBDA_RESIDUAL_THRESHOLD_HIGH
        )
        self.adaptive_lambda_residual_threshold_low = (
            adaptive_lambda_residual_threshold_low
            if adaptive_lambda_residual_threshold_low is not None
            else grav_cfg.DEFAULT_ADAPTIVE_LAMBDA_RESIDUAL_THRESHOLD_LOW
        )
        self.adaptive_lambda_increase_factor = (
            adaptive_lambda_increase_factor
            if adaptive_lambda_increase_factor is not None
            else grav_cfg.DEFAULT_ADAPTIVE_LAMBDA_INCREASE_FACTOR
        )
        self.adaptive_lambda_decrease_factor = (
            adaptive_lambda_decrease_factor
            if adaptive_lambda_decrease_factor is not None
            else grav_cfg.DEFAULT_ADAPTIVE_LAMBDA_DECREASE_FACTOR
        )

        # Logging level
        self.logging_level = (
            logging_level
            if logging_level is not None
            else grav_cfg.DEFAULT_LOGGING_LEVEL
        )

        # Shadow Model Trigger parameters
        self.enable_shadow_model_trigger = grav_cfg.DEFAULT_ENABLE_SHADOW_MODEL_TRIGGER
        self.shadow_model_variance_threshold = (
            grav_cfg.DEFAULT_SHADOW_MODEL_VARIANCE_THRESHOLD
        )
        self.shadow_model_window_size = grav_cfg.DEFAULT_SHADOW_MODEL_WINDOW_SIZE
        self.shadow_model_min_trigger_samples = (
            grav_cfg.DEFAULT_SHADOW_MODEL_MIN_TRIGGER_SAMPLES
        )
        self.shadow_model_min_causal_variance = (
            grav_cfg.DEFAULT_SHADOW_MODEL_MIN_CAUSAL_VARIANCE
        )


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
        config: GravityEngineConfig,
        dt: float,
        state_dimensionality: int,
        pillar_names: List[str],
        impact_matrix_B: Optional[np.ndarray] = None,
    ):
        """
        Initialize the residual gravity engine with the specified configuration.

        Parameters
        ----------
        config : GravityEngineConfig
            Configuration object containing gravity engine parameters
        dt : float
            Time step size for the simulation
        state_dimensionality : int
            Dimensionality of the state vector
        pillar_names : List[str]
            List of pillar names defining the canonical order of symbolic pillars
        impact_matrix_B : Optional[np.ndarray], optional
            Impact matrix B that maps symbolic forces to state corrections,
            by default None. If None, will be initialized with zeros.
            Shape should be (state_dimensionality, len(pillar_names))
        """
        # Store the configuration and parameters
        self.config = config

        # Initialize logger with specified logging level
        self.logger = get_logger(__name__, level=self.config.logging_level)
        self.dt = dt
        self.state_dimensionality = state_dimensionality
        self.pillar_names = pillar_names

        # Initialize gravity engine parameters from config
        self.lambda_ = config.lambda_  # Mutable copy of lambda
        self.reg = config.regularization_strength
        self.η = config.learning_rate
        self.β = config.momentum_factor
        self.circuit_breaker_threshold = config.circuit_breaker_threshold

        # Additional parameters from config
        self.max_correction = config.max_correction
        self.enable_adaptive_lambda = config.enable_adaptive_lambda
        self.enable_weight_pruning = config.enable_weight_pruning
        self.weight_pruning_threshold = config.weight_pruning_threshold
        self.fragility_threshold = config.fragility_threshold

        # Initialize adaptive lambda state
        if self.enable_adaptive_lambda:
            self.recent_residuals = deque(maxlen=config.adaptive_lambda_window_size)

        # Initialize shadow model state
        self.enable_shadow_model_trigger = config.enable_shadow_model_trigger
        if self.enable_shadow_model_trigger:
            self._recent_causal_residuals = deque(
                maxlen=config.shadow_model_window_size
            )
            self._recent_gravity_residuals = deque(
                maxlen=config.shadow_model_window_size
            )

        # Initialize EWMA parameters
        self.ewma_span = config.ewma_span
        # Calculate alpha value for EWMA and handle edge cases
        if self.ewma_span <= 0:
            # Disable EWMA if span is invalid
            self.ewma_alpha = 1.0
        else:
            # Formula: alpha = 2 / (span + 1)
            self.ewma_alpha = 2.0 / (self.ewma_span + 1.0)

        # Initialize impact matrix if provided, otherwise zero matrix
        if impact_matrix_B is not None:
            self.impact_matrix_B = impact_matrix_B
        else:
            # Initialize with zeros - will be learned through updates
            self.impact_matrix_B = np.zeros((state_dimensionality, len(pillar_names)))

        # Momentum buffer for impact matrix
        self._v_matrix = np.zeros_like(self.impact_matrix_B)

        # For backward compatibility - will be deprecated for state_dimensionality > 1
        # Dictionary view into impact_matrix_B[0,:] for single-dimensional state
        self.weights: Dict[str, float] = defaultdict(float)

        # Momentum buffer for SGD - legacy
        self._v: Dict[str, float] = defaultdict(float)

        # Statistics for monitoring
        self._stats = {
            "updates": 0,
            "total_residual": 0.0,
            "total_correction": 0.0,
            "max_weight": 0.0,
            "circuit_breaker_triggered": False,
            "fragility": 0.0,
        }

    # ---------- Public API ------------------------------------------------- #

    def _dict_to_ordered_array(self, symbol_vec: Dict[str, float]) -> np.ndarray:
        """
        Convert a symbol dictionary to an ordered column vector based on pillar_names.

        Parameters
        ----------
        symbol_vec : Dict[str, float]
            Mapping from symbol names to intensities

        Returns
        -------
        np.ndarray
            Ordered column vector of shape (len(self.pillar_names), 1)
        """
        # Create an array with values in the order of pillar_names
        # Set default value of 0.0 for any missing pillars
        symbol_array = np.array(
            [symbol_vec.get(name, 0.0) for name in self.pillar_names]
        )

        # Reshape to column vector (N, 1)
        return symbol_array.reshape(-1, 1)

    def _update_weights_dict_from_matrix(self) -> None:
        """
        Update self.weights dictionary from impact_matrix_B for single-dimensional state.
        This is used for backward compatibility.
        """
        if self.state_dimensionality == 1:
            for i, pillar_name in enumerate(self.pillar_names):
                self.weights[pillar_name] = float(self.impact_matrix_B[0, i])

    def compute_gravity(self, symbol_vec: Dict[str, float]) -> Union[float, np.ndarray]:
        """
        Compute g_t given current impact matrix and symbol intensities.

        This implements the equation: g_t+1 = B · s_t
        Where:
        - B is the impact matrix with shape (state_dimensionality, num_pillars)
        - s_t is the symbol vector with shape (num_pillars, 1)

        The gravity value represents the correction that will be applied to
        simulation outputs to pull them toward observed reality. Each symbolic
        pillar (like Hope, Despair, etc.) contributes to this correction based
        on its intensity and learned impact matrix weights.

        If symbolic system is disabled globally, returns 0.

        Parameters
        ----------
        symbol_vec : Dict[str, float]
            Mapping from symbol names to intensities (s_t(k) in the math)

        Returns
        -------
        Union[float, np.ndarray]
            The gravity correction value or vector depending on state_dimensionality
        """
        # Check if symbolic system is globally enabled
        from symbolic_system.context import is_symbolic_enabled

        if not is_symbolic_enabled():
            # Return 0 if symbolic system is disabled
            if self.state_dimensionality == 1:
                return 0.0
            else:
                return np.zeros((self.state_dimensionality, 1))

        # Convert symbol dictionary to ordered array
        symbol_array = self._dict_to_ordered_array(symbol_vec)

        # Calculate gravity using matrix multiplication: g = B · s
        gravity_vector = (
            self.impact_matrix_B @ symbol_array
        )  # Shape: (state_dimensionality, 1)

        # Update statistics for monitoring
        if self.state_dimensionality == 1:
            gravity_float = float(gravity_vector[0, 0])
            self._stats["last_gravity_value"] = gravity_float

            # For backward compatibility - track significant contributors
            self._update_weights_dict_from_matrix()
            self._stats["last_gravity_contributors"] = {
                k: self.weights[k] * symbol_vec.get(k, 0.0)
                for k in self.pillar_names
                if k in symbol_vec
                and abs(self.weights[k] * symbol_vec[k])
                > grav_cfg.SIGNIFICANT_CONTRIBUTOR_THRESHOLD
            }

            return gravity_float
        else:
            # For multidimensional state, return the full vector
            self._stats["last_gravity_value"] = float(np.mean(gravity_vector))
            return gravity_vector

    # Alias for backward compatibility
    gravity = compute_gravity

    def update_impact_matrix(
        self, residual: Union[float, np.ndarray], symbol_vec: Dict[str, float]
    ) -> None:
        """
        Update impact matrix using online SGD with momentum and apply EWMA decay.

        Implementation of the update rule:
        For each column j (pillar j) of impact_matrix_B:
        - If state_dimensionality == 1:
            - Similar to old update_weights but operates directly on impact_matrix_B[0, j]
        - If state_dimensionality > 1:
            - delta_B_column_j = learning_rate * s_j * residuals_vector

        After the SGD update, an EWMA decay is applied to the impact matrix:
        B_{ij}^{new_ewma} = α * B_{ij}^{post_sgd} + (1-α) * B_{ij}^{old_ewma}
        Where α is calculated as 2/(ewma_span+1).

        Parameters
        ----------
        residual : Union[float, np.ndarray]
            Prediction residual (y - ŷ)
        symbol_vec : Dict[str, float]
            Symbol intensities from pillar system
        """
        # Store a copy of the old impact matrix for EWMA if needed
        apply_ewma = self.ewma_alpha < 1.0
        impact_matrix_B_old_ewma = self.impact_matrix_B.copy() if apply_ewma else None

        # Convert symbols to ordered array
        _symbol_array = self._dict_to_ordered_array(symbol_vec)

        # Ensure residual is a numpy array
        if isinstance(residual, float):
            residual_array = np.array([residual]).reshape(-1, 1)
        else:
            # If already array, ensure correct shape (M, 1)
            # Need to handle ndarray properly to avoid type errors
            residual_array = np.asarray(residual)
            if residual_array.ndim == 0:  # scalar ndarray
                residual_array = residual_array.reshape(1, 1)
            elif residual_array.ndim == 1:  # vector
                residual_array = residual_array.reshape(-1, 1)

        # Update impact matrix based on state dimensionality
        if self.state_dimensionality == 1:
            # Single dimension update (similar to original algorithm)
            for i, pillar_name in enumerate(self.pillar_names):
                if pillar_name in symbol_vec:
                    s_k = symbol_vec[pillar_name]

                    # Calculate gradient with L2 regularization
                    grad = (
                        float(residual_array[0, 0]) * s_k
                        - self.reg * self.impact_matrix_B[0, i]
                    )

                    # Update momentum
                    self._v_matrix[0, i] = (
                        self.β * self._v_matrix[0, i] + (1 - self.β) * grad
                    )

                    # Update impact matrix element
                    self.impact_matrix_B[0, i] += self.η * self._v_matrix[0, i]

                    # Update legacy weights dict for backward compatibility
                    self.weights[pillar_name] = float(self.impact_matrix_B[0, i])
                    self._v[pillar_name] = float(self._v_matrix[0, i])
        else:
            # Multi-dimensional update
            # For each non-zero symbol in symbol_vec:
            for i, pillar_name in enumerate(self.pillar_names):
                if pillar_name in symbol_vec:
                    s_k = symbol_vec[pillar_name]

                    # Calculate gradient with L2 regularization for the entire column
                    # Shape of grad: (state_dimensionality, 1)
                    grad = (
                        s_k * residual_array
                        - self.reg * self.impact_matrix_B[:, i : i + 1]
                    )

                    # Update momentum for the entire column
                    self._v_matrix[:, i : i + 1] = (
                        self.β * self._v_matrix[:, i : i + 1] + (1 - self.β) * grad
                    )

                    # Update impact matrix column
                    self.impact_matrix_B[:, i : i + 1] += (
                        self.η * self._v_matrix[:, i : i + 1]
                    )

        # Update statistics
        self._stats["updates"] += 1
        self._stats["total_residual"] += float(np.mean(np.abs(residual_array)))
        self._stats["max_weight"] = float(np.max(np.abs(self.impact_matrix_B)))

        # Apply EWMA decay to impact matrix if enabled
        if apply_ewma and impact_matrix_B_old_ewma is not None:
            self.impact_matrix_B = (
                self.ewma_alpha * self.impact_matrix_B
                + (1 - self.ewma_alpha) * impact_matrix_B_old_ewma
            )

        # Calculate current residual magnitude for adaptive lambda update
        current_residual_magnitude = float(np.mean(np.abs(residual_array)))

        # Update adaptive lambda based on current residual
        self._update_adaptive_lambda(current_residual_magnitude)

    # Legacy alias that updates impact_matrix_B
    def update_weights(
        self, residual: Union[float, np.ndarray], symbol_vec: Dict[str, float]
    ) -> None:
        """
        Legacy method that updates the impact matrix.
        Calls update_impact_matrix internally.

        Parameters
        ----------
        residual : Union[float, np.ndarray]
            Prediction residual (y - ŷ)
        symbol_vec : Dict[str, float]
            Symbol intensities from pillar system
        """
        self.update_impact_matrix(residual, symbol_vec)

    # Alias for backward compatibility
    update = update_impact_matrix

    def apply_gravity_correction(
        self, sim_vec: Union[float, np.ndarray], symbol_vec: Dict[str, float]
    ) -> Tuple[Union[float, np.ndarray], Union[float, np.ndarray]]:
        """
        Apply the gravity correction to the simulation vector.

        Implementation of the corrected state equation:
        x*_t+1 = x^_t+1 + λ g_t+1

        Where:
        - x^_t+1 is the simulation vector (sim_vec)
        - g_t+1 is the gravity correction from impact_matrix_B and symbol_vec
        - λ is the global gravity strength parameter (lambda_)
        - x*_t+1 is the corrected vector

        If symbolic system is disabled globally, returns (0, sim_vec).

        Parameters
        ----------
        sim_vec : Union[float, np.ndarray]
            Simulation vector to correct (x^_t+1 in the math)
        symbol_vec : Dict[str, float]
            Symbol intensities from pillar system (s_t in the math)

        Returns
        -------
        Tuple[Union[float, np.ndarray], Union[float, np.ndarray]]
            Tuple of (correction_amount, corrected_vector)
        """
        # Check if symbolic system is globally enabled
        from symbolic_system.context import is_symbolic_enabled

        # Return original simulation vector without correction if symbolic system is disabled
        if not is_symbolic_enabled():
            # Return zero correction and original value
            if self.state_dimensionality == 1:
                return 0.0, sim_vec
            else:
                return np.zeros((self.state_dimensionality, 1)), sim_vec

        # Calculate gravity correction using impact_matrix_B and symbol_vec
        gravity_correction = self.compute_gravity(symbol_vec)

        # Apply adaptive lambda if enabled
        effective_lambda = self.lambda_
        if self.enable_adaptive_lambda:
            # Adjust lambda based on correction magnitude and fragility
            # _calculate_fragility now handles both float and ndarray internally
            fragility = self._calculate_fragility(gravity_correction)
            # Reduce lambda when fragility is high
            effective_lambda = self.lambda_ * max(
                grav_cfg.MIN_LAMBDA_SCALE_FACTOR, 1.0 - fragility
            )
            self._stats["fragility"] = fragility
            self._stats["effective_lambda"] = effective_lambda

        # Apply circuit breaker if needed
        if abs(gravity_correction) > self.circuit_breaker_threshold:
            self._stats["circuit_breaker_triggered"] = True
            self._stats["circuit_breaker_trips"] = (
                self._stats.get("circuit_breaker_trips", 0) + 1
            )
            # Limit correction to threshold
            gravity_correction = self.circuit_breaker_threshold * (
                1 if gravity_correction > 0 else -1
            )
            # When breaker trips, reduce lambda further
            effective_lambda *= grav_cfg.CIRCUIT_BREAKER_LAMBDA_REDUCTION

        # Apply the final correction (x*_t+1 = x^_t+1 + λ g_t+1)
        correction_amount = effective_lambda * gravity_correction

        # Limit correction to max_correction if set
        if hasattr(self, "max_correction") and self.max_correction > 0:
            if abs(correction_amount) > self.max_correction:
                correction_sign = 1 if correction_amount > 0 else -1
                correction_amount = self.max_correction * correction_sign

        # Apply the correction
        corrected = sim_vec + correction_amount

        # Update statistics
        if isinstance(correction_amount, np.ndarray):
            self._stats["total_correction"] += float(np.mean(np.abs(correction_amount)))
            self._stats["mean_abs_correction"] = float(
                np.mean(np.abs(correction_amount))
            )
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

        # Safely compute correction efficiency - handle both float and ndarray
        grav_mag = 1e-6  # Default small value to avoid division by zero
        if isinstance(gravity_correction, float):
            grav_mag = max(1e-6, abs(gravity_correction))
        elif isinstance(gravity_correction, np.ndarray):
            grav_mag = max(1e-6, float(np.mean(np.abs(gravity_correction))))

        self._stats["correction_efficiency"] = min(1.0, corr_mag / grav_mag)

        # If sim_vec is a float, convert to array for consistent handling
        if isinstance(sim_vec, float):
            sim_vec_array = np.array([sim_vec])
        else:
            sim_vec_array = sim_vec

        # Apply the correction
        if self.state_dimensionality == 1:
            # Handle single-dimensional case
            if isinstance(correction_amount, np.ndarray):
                correction_float = float(np.mean(correction_amount))
            else:
                correction_float = correction_amount

            if isinstance(sim_vec, float):
                corrected = sim_vec + correction_float
            else:
                corrected = sim_vec_array + correction_float

            return correction_float, corrected
        else:
            # Handle multi-dimensional case with appropriate broadcasting
            corrected = sim_vec_array + correction_amount
            return correction_amount, corrected

    def _update_adaptive_lambda(self, current_residual_magnitude: float) -> None:
        """
        Update the adaptive lambda parameter based on recent residual magnitudes.

        This method implements the adaptive lambda logic:
        1. Add current_residual_magnitude to recent_residuals deque
        2. If the deque is full (reached window_size):
           a. Calculate average recent residual
           b. If avg > high_threshold, increase lambda
           c. If avg < low_threshold, decrease lambda
           d. Clip lambda to [min, max] range

        Parameters
        ----------
        current_residual_magnitude : float
            The magnitude (absolute value) of the current residual
        """
        # Early return if adaptive lambda is not enabled
        if not self.config.enable_adaptive_lambda:
            return

        # Add current residual magnitude to the deque
        self.recent_residuals.append(current_residual_magnitude)

        # Check if we have enough residuals to adjust lambda
        if len(self.recent_residuals) == self.config.adaptive_lambda_window_size:
            # Calculate average recent residual
            avg_recent_residual = np.mean(list(self.recent_residuals))

            # Adjust lambda based on residual thresholds
            if (
                avg_recent_residual
                > self.config.adaptive_lambda_residual_threshold_high
            ):
                # Increase lambda when residuals are high
                new_lambda = self.lambda_ * self.config.adaptive_lambda_increase_factor
            elif (
                avg_recent_residual < self.config.adaptive_lambda_residual_threshold_low
            ):
                # Decrease lambda when residuals are low
                new_lambda = self.lambda_ * self.config.adaptive_lambda_decrease_factor
            else:
                # No change needed
                return

            # Clip lambda to configured min/max values
            self.lambda_ = np.clip(
                new_lambda,
                self.config.adaptive_lambda_min,
                self.config.adaptive_lambda_max,
            )

            # Log lambda update
            self.logger.info(f"Adaptive lambda updated to: {self.lambda_:.4f}")

            # Update stats for monitoring
            self._stats["adaptive_lambda_adjustment"] = (
                self._stats.get("adaptive_lambda_adjustment", 0) + 1
            )
            self._stats["current_lambda"] = float(self.lambda_)
            self._stats["avg_recent_residual"] = float(avg_recent_residual)

    def _calculate_fragility(
        self, gravity_correction: Union[float, np.ndarray]
    ) -> float:
        """
        Calculate the fragility score based on the current state.

        Fragility indicates how sensitive the system is to corrections.
        High fragility means corrections should be applied more cautiously.

        Parameters
        ----------
        gravity_correction : Union[float, np.ndarray]
            The current gravity correction value or vector

        Returns
        -------
        float
            Fragility score (0-1), where 1 is high fragility
        """
        # Convert ndarray to float if needed
        if isinstance(gravity_correction, np.ndarray):
            gravity_correction = float(np.mean(gravity_correction))
        # Factors that contribute to fragility:
        # 1. High RMS weight - indicates model is relying heavily on corrections
        rms_factor = min(1.0, self.rms_weight() / self.fragility_threshold)

        # 2. Correction volatility - rapid changes in correction
        prev_correction = self._stats.get("last_correction", 0.0)
        current_correction = gravity_correction
        volatility = abs(current_correction - prev_correction) / max(
            1e-6, abs(current_correction) + abs(prev_correction)
        )

        # 3. Circuit breaker history - frequency of past trips
        breaker_trips = self._stats.get("circuit_breaker_trips", 0)
        breaker_factor = min(1.0, breaker_trips / grav_cfg.MAX_CIRCUIT_BREAKER_TRIPS)

        # Combine factors (weighted average)
        fragility = (
            grav_cfg.FRAGILITY_RMS_WEIGHT * rms_factor
            + grav_cfg.FRAGILITY_VOLATILITY_WEIGHT * volatility
            + grav_cfg.FRAGILITY_BREAKER_WEIGHT * breaker_factor
        )

        return min(1.0, fragility)

    # Alias for backward compatibility
    def apply_correction(self, sim_vec, symbol_vec):
        return self.apply_gravity_correction(sim_vec, symbol_vec)[1]

    def process_and_correct(
        self,
        sim_vec: Union[float, np.ndarray],
        truth_vec: Union[float, np.ndarray],
        symbol_vec: Dict[str, float],
        update_weights: bool = True,
    ) -> Tuple[Union[float, np.ndarray], bool]:
        """
        Process the simulation and truth vectors, update weights, and apply correction.

        This is a convenience method that combines the following steps:
        1. Calculate residual
        2. Update weights (if update_weights is True)
        3. Apply correction
        4. Store residuals and perform shadow model check if enabled

        Parameters
        ----------
        sim_vec : Union[float, np.ndarray]
            Simulation vector (causal prediction)
        truth_vec : Union[float, np.ndarray]
            Observed truth vector
        symbol_vec : Dict[str, float]
            Symbol intensities from pillar system
        update_weights : bool, optional
            Whether to update weights, by default True

        Returns
        -------
        Tuple[Union[float, np.ndarray], bool]
            Tuple containing (corrected_prediction, review_needed_flag)
        """
        # Calculate residual (causal residual)
        causal_residual = truth_vec - sim_vec

        # Update weights if requested
        if update_weights:
            self.update(causal_residual, symbol_vec)

        # Apply correction to get corrected prediction
        correction, corrected_prediction = self.apply_gravity_correction(
            sim_vec, symbol_vec
        )

        # Calculate gravity residual
        gravity_residual = truth_vec - corrected_prediction

        # Set default review flag
        review_needed_flag = False

        # Shadow model check (if enabled)
        if self.enable_shadow_model_trigger:
            # Convert to float for simplified tracking if using multidimensional state
            if isinstance(causal_residual, np.ndarray):
                causal_residual_value = float(np.mean(causal_residual))
            else:
                causal_residual_value = float(causal_residual)

            if isinstance(gravity_residual, np.ndarray):
                gravity_residual_value = float(np.mean(gravity_residual))
            else:
                gravity_residual_value = float(gravity_residual)

            # Store residuals in the deques
            self._recent_causal_residuals.append(causal_residual_value)
            self._recent_gravity_residuals.append(gravity_residual_value)

            # Check if we have enough samples to perform the shadow model check
            if (
                len(self._recent_causal_residuals)
                >= self.config.shadow_model_min_trigger_samples
            ):
                # Calculate variance of the residuals
                var_causal_res = np.var(list(self._recent_causal_residuals))
                var_gravity_res = np.var(list(self._recent_gravity_residuals))

                # Calculate variance explained by gravity model
                if var_causal_res < self.config.shadow_model_min_causal_variance:
                    # Avoid division by near-zero causal variance
                    variance_explained = 0.0
                else:
                    # Calculate VE_gravity = 1 - (var_gravity_res / var_causal_res)
                    variance_explained = 1.0 - (var_gravity_res / var_causal_res)

                # Check if variance explained exceeds threshold
                if variance_explained > self.config.shadow_model_variance_threshold:
                    review_needed_flag = True
                    # Log critical message
                    self.logger.critical(
                        f"Shadow model trigger activated: Gravity model explaining {variance_explained:.2f} "
                        + f"of variance (threshold: {self.config.shadow_model_variance_threshold}). "
                        + f"Causal variance: {var_causal_res:.6f}, Gravity variance: {var_gravity_res:.6f}. "
                        + "Review recommended."
                    )

                    # Update stats
                    self._stats["shadow_model_trigger"] = {
                        "variance_explained": float(variance_explained),
                        "causal_variance": float(var_causal_res),
                        "gravity_variance": float(var_gravity_res),
                        "timestamp": np.datetime64("now"),
                    }

        return corrected_prediction, review_needed_flag

    # ---------- Interface with SymbolicPillarSystem ------------------------ #

    def process_with_pillar_system(
        self,
        sim_vec: Union[float, np.ndarray],
        truth_vec: Union[float, np.ndarray],
        pillar_system: SymbolicPillarSystem,
        update_weights: bool = True,
    ) -> Tuple[Union[float, np.ndarray], bool]:
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
        Tuple[Union[float, np.ndarray], bool]
            Tuple containing (corrected_prediction, review_needed_flag)
        """
        # Get symbol vector from pillar system
        symbol_vec = pillar_system.as_dict()

        # Process and correct
        return self.process_and_correct(sim_vec, truth_vec, symbol_vec, update_weights)

    # ---------- Diagnostics ------------------------------------------------ #

    def weight_snapshot(self) -> Dict[str, float]:
        """
        Get a snapshot of the current weights.

        For state_dimensionality > 1, this provides a flattened view of impact_matrix_B.

        Returns
        -------
        Dict[str, float]
            Mapping from pillar names to weights
        """
        if self.state_dimensionality == 1:
            # Use legacy weights dict for backward compatibility
            self._update_weights_dict_from_matrix()
            return dict(self.weights)
        else:
            # For multidimensional state, return the average impact across dimensions for each pillar
            return {
                pillar_name: float(np.mean(self.impact_matrix_B[:, i]))
                for i, pillar_name in enumerate(self.pillar_names)
            }

    def rms_weight(self) -> float:
        """
        Calculate the root mean square of the impact matrix.

        This metric indicates the overall magnitude of weights and is used
        to detect potential overfitting or instability in the correction model.
        High RMS weights suggest the model may be fitting to noise rather than
        systematic errors.

        Returns
        -------
        float
            RMS of impact matrix elements
        """
        # Use the impact matrix directly
        rms = float(np.sqrt(np.mean(self.impact_matrix_B**2)))

        # Track this in stats
        self._stats["rms_weight"] = rms

        # Check for weight pruning condition
        if self.enable_weight_pruning and rms > self.fragility_threshold:
            self._prune_weights()

        return rms

    def _prune_weights(self) -> None:
        """
        Prune small impact matrix elements to prevent overfitting.

        This sets elements with magnitudes below the pruning threshold to zero,
        preventing the accumulation of small, noisy weights that can lead
        to instability.
        """
        # Count elements below threshold
        below_threshold = np.abs(self.impact_matrix_B) < self.weight_pruning_threshold
        pruned_count = int(np.sum(below_threshold))

        # Set elements below threshold to zero
        if pruned_count > 0:
            self.impact_matrix_B[below_threshold] = 0.0

            # Update legacy weights for backward compatibility
            if self.state_dimensionality == 1:
                self._update_weights_dict_from_matrix()

            self._stats["pruned_weights"] = (
                self._stats.get("pruned_weights", 0) + pruned_count
            )

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
        if self.state_dimensionality == 1:
            # Update legacy weights dict for backward compatibility
            self._update_weights_dict_from_matrix()
            return {k: w for k, w in self.weights.items() if abs(w) >= threshold}
        else:
            # For multidimensional state, return average impact across dimensions for each pillar
            return {
                pillar_name: float(np.mean(self.impact_matrix_B[:, i]))
                for i, pillar_name in enumerate(self.pillar_names)
                if float(np.mean(np.abs(self.impact_matrix_B[:, i]))) >= threshold
            }

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
            return sorted(contributors.items(), key=lambda x: abs(x[1]), reverse=True)[
                :n
            ]

        # Fallback to weight magnitudes if no recent contribution data
        return sorted(self.weights.items(), key=lambda x: abs(x[1]), reverse=True)[:n]

    # Alias for backward compatibility
    top_weights = get_top_contributors

    def reset_weights(self) -> None:
        """Reset impact matrix and all weights to zero."""
        # Reset impact matrix
        self.impact_matrix_B.fill(0.0)
        self._v_matrix.fill(0.0)

        # Reset legacy weights for backward compatibility
        self.weights = defaultdict(float)
        self._v = defaultdict(float)

        # Reset statistics
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
            stats["mean_abs_residual"] = (
                stats.get("total_residual", 0.0) / stats["updates"]
            )
            stats["mean_abs_correction"] = (
                stats.get("total_correction", 0.0) / stats["updates"]
            )
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
            current_weights = {
                k: self.weights.get(k, 0.0)
                for k in set(prev_weights) | set(self.weights)
            }
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
        if health["max_weight"] > grav_cfg.CRITICAL_MAX_WEIGHT_THRESHOLD:
            health["status"] = "critical"
            health["warnings"].append("Maximum weight too high, possible divergence")

        # 2. Excessively large weights
        elif health["rms_weight"] > grav_cfg.UNHEALTHY_RMS_WEIGHT_THRESHOLD:
            health["status"] = "unhealthy"
            health["warnings"].append("RMS weights too high, possible overfitting")

        # 3. Frequent circuit breaker trips
        elif health["circuit_breaker_trips"] > grav_cfg.WARNING_CIRCUIT_BREAKER_TRIPS:
            health["status"] = "warning"
            health["warnings"].append(
                f"Circuit breaker triggered {health['circuit_breaker_trips']} times, corrections may be unstable"
            )

        # 4. High fragility
        elif health["fragility"] > grav_cfg.WARNING_FRAGILITY_THRESHOLD:
            health["status"] = "warning"
            health["warnings"].append(
                f"High fragility score ({health['fragility']:.2f}), corrections applied conservatively"
            )

        # 5. Stagnant weights (not learning)
        elif (
            self._stats.get("updates", 0) > grav_cfg.STAGNANT_WEIGHT_UPDATES
            and health["rms_weight"] < grav_cfg.STAGNANT_WEIGHT_RMS_THRESHOLD
        ):
            health["status"] = "caution"
            health["warnings"].append(
                "Weights remain very small after many updates, possibly not learning"
            )

        # 6. Low correction efficiency
        elif (
            health["correction_efficiency"]
            < grav_cfg.LOW_CORRECTION_EFFICIENCY_THRESHOLD
            and self._stats.get("updates", 0)
            > grav_cfg.MIN_UPDATES_FOR_EFFICIENCY_CHECK
        ):
            health["status"] = "caution"
            health["warnings"].append(
                f"Low correction efficiency ({health['correction_efficiency']:.2f}), corrections heavily limited"
            )

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
                recommendations.append(
                    "Consider pruning weights or reducing learning rate"
                )
            elif "divergence" in warning:
                recommendations.append(
                    "Reset weights and decrease learning rate significantly"
                )
                recommendations.append("Increase circuit breaker threshold temporarily")
            elif "circuit breaker" in warning:
                recommendations.append(
                    "Review which symbols have high weights and consider rule improvements"
                )
                recommendations.append(
                    "Increase regularization to prevent large corrections"
                )
            elif "fragility" in warning:
                recommendations.append(
                    "Monitor for over-reliance on symbolic corrections"
                )
                recommendations.append(
                    "Consider enhancing causal rules to reduce correction magnitude"
                )
            elif "not learning" in warning:
                recommendations.append(
                    "Increase learning rate or decrease regularization"
                )
                recommendations.append(
                    "Verify that meaningful residuals are being provided"
                )
            elif "correction efficiency" in warning:
                recommendations.append(
                    "Check if circuit breaker threshold is too restrictive"
                )
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
            "pillar_names": self.pillar_names,
            "state_dimensionality": self.state_dimensionality,
            "impact_matrix_B": self.impact_matrix_B.tolist(),
            "momentum_buffer_matrix": self._v_matrix.tolist(),
            "weights": dict(self.weights),  # For backward compatibility
            "momentum_buffer": dict(self._v),  # For backward compatibility
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
        # Create a configuration object with parameters from the data
        config = GravityEngineConfig(
            lambda_=data.get("lambda", grav_cfg.DEFAULT_LAMBDA),
            regularization_strength=data.get("reg", grav_cfg.DEFAULT_REGULARIZATION),
            learning_rate=data.get("lr", grav_cfg.DEFAULT_LEARNING_RATE),
            momentum_factor=data.get("momentum", grav_cfg.DEFAULT_MOMENTUM),
            circuit_breaker_threshold=data.get(
                "circuit_breaker_threshold", grav_cfg.DEFAULT_CIRCUIT_BREAKER_THRESHOLD
            ),
            # Use default values for additional parameters if not provided
            max_correction=data.get("max_correction", grav_cfg.DEFAULT_MAX_CORRECTION),
            enable_adaptive_lambda=data.get(
                "enable_adaptive_lambda", grav_cfg.DEFAULT_ENABLE_ADAPTIVE_LAMBDA
            ),
            enable_weight_pruning=data.get(
                "enable_weight_pruning", grav_cfg.DEFAULT_ENABLE_WEIGHT_PRUNING
            ),
            weight_pruning_threshold=data.get(
                "weight_pruning_threshold", grav_cfg.DEFAULT_WEIGHT_PRUNING_THRESHOLD
            ),
            fragility_threshold=data.get(
                "fragility_threshold", grav_cfg.DEFAULT_FRAGILITY_THRESHOLD
            ),
        )

        # Get state dimensionality and time step
        state_dim = data.get("state_dimensionality", 1)
        dt = data.get("dt", 1.0)

        # Get pillar names or extract from weights keys
        pillar_names = data.get("pillar_names", list(data.get("weights", {}).keys()))

        # Extract impact matrix if available, otherwise None
        impact_matrix = None
        if "impact_matrix_B" in data:
            impact_matrix = np.array(data["impact_matrix_B"])

        # Create the engine with the config
        engine = cls(
            config=config,
            dt=dt,
            state_dimensionality=state_dim,
            pillar_names=pillar_names,
            impact_matrix_B=impact_matrix,
        )

        # If impact matrix was not provided but weights were, convert weights to impact matrix
        if impact_matrix is None and "weights" in data:
            # For backward compatibility with old format
            if engine.state_dimensionality == 1:
                for i, pillar_name in enumerate(pillar_names):
                    if pillar_name in data["weights"]:
                        engine.impact_matrix_B[0, i] = data["weights"][pillar_name]

        # Load momentum matrix if available
        if "momentum_buffer_matrix" in data:
            engine._v_matrix = np.array(data["momentum_buffer_matrix"])
        elif "momentum_buffer" in data and engine.state_dimensionality == 1:
            # For backward compatibility - convert old momentum buffer to matrix
            for i, pillar_name in enumerate(pillar_names):
                if pillar_name in data["momentum_buffer"]:
                    engine._v_matrix[0, i] = data["momentum_buffer"][pillar_name]

        # Load legacy weights for backward compatibility
        if "weights" in data:
            for k, w in data["weights"].items():
                engine.weights[k] = w

        # Load legacy momentum buffer for backward compatibility
        if "momentum_buffer" in data:
            for k, v in data["momentum_buffer"].items():
                engine._v[k] = v

        # Load stats
        engine._stats = data.get("stats", engine._stats)

        return engine
