"""
EnhancedRetrodictionCurriculum

Implements an enhanced retrodiction curriculum based on uncertainty and
training performance.
"""

import logging
from typing import Any, Dict, List, Optional
import statistics
import numpy as np
from recursive_training.integration.cost_controller import get_cost_controller
from recursive_training.advanced_metrics.enhanced_metrics import (
    EnhancedRecursiveTrainingMetrics,
)

NUMPY_AVAILABLE = True


def get_data_store():
    """Get a data store instance for retrodiction curriculum.

    Returns:
        DummyDataStore: A dummy data store implementation for testing.

    Example:
        Basic usage:
        >>> store = get_data_store()
        >>> data = store.get_all_data()
        >>> len(data)
        0
        >>> isinstance(data, list)
        True

        Verify store type:
        >>> store.__class__.__name__
        'DummyDataStore'
    """
    class DummyDataStore:
        """Dummy data store implementation for testing purposes."""

        def get_all_data(self):
            """Get all available data.

            Returns:
                List[Any]: Empty list for dummy implementation.
            """
            return []

    return DummyDataStore()


class EnhancedRetrodictionCurriculum:
    """
    An enhanced retrodiction curriculum that dynamically selects training data
    based on model uncertainty and performance metrics.

    This curriculum implementation uses uncertainty-driven data selection to improve
    training efficiency by focusing on data points where the model exhibits high
    uncertainty or where recent performance metrics indicate degradation.

    Attributes:
        logger: Logger instance for curriculum operations.
        metrics_tracker: Enhanced metrics tracker for performance monitoring.
        data_store: Data store instance for accessing training data.
        cost_controller: Cost controller for tracking operation costs.
        uncertainty_threshold_multiplier: Multiplier for uncertainty threshold.
        performance_degradation_threshold: Threshold for performance degradation.
        uncertainty_sampling_ratio: Ratio of uncertain data to sample.

    Example:
        Basic initialization:
        >>> curriculum = EnhancedRetrodictionCurriculum()
        >>> curriculum.uncertainty_threshold_multiplier
        1.5
        >>> curriculum.uncertainty_sampling_ratio
        0.3

        Custom configuration:
        >>> config = {
        ...     "uncertainty_threshold_multiplier": 2.0,
        ...     "performance_degradation_threshold": 0.15,
        ...     "uncertainty_sampling_ratio": 0.4
        ... }
        >>> custom_curriculum = EnhancedRetrodictionCurriculum(config)
        >>> custom_curriculum.uncertainty_threshold_multiplier
        2.0
        >>> custom_curriculum.uncertainty_sampling_ratio
        0.4

        Complete workflow:
        >>> curriculum = EnhancedRetrodictionCurriculum()
        >>> selected_data = curriculum.select_data_for_training(current_iteration=1)
        >>> isinstance(selected_data, list)
        True
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None) -> None:
        """
        Initialize the EnhancedRetrodictionCurriculum.

        Args:
            config: Optional configuration dictionary containing:
                - uncertainty_threshold_multiplier (float): Multiplier for
                  uncertainty
                  threshold calculation. Defaults to 1.5.
                - performance_degradation_threshold (float): Threshold for detecting
                  performance degradation. Defaults to 0.1 (10%).
                - uncertainty_sampling_ratio (float): Percentage of data to sample
                  based on uncertainty. Defaults to 0.3 (30%).
                - cost_control (Dict[str, Any]): Cost control configuration.

        Example:
            Default initialization:
            >>> curriculum = EnhancedRetrodictionCurriculum()
            >>> curriculum.uncertainty_threshold_multiplier
            1.5
            >>> curriculum.performance_degradation_threshold
            0.1

            Custom configuration:
            >>> config = {"uncertainty_threshold_multiplier": 2.0}
            >>> curriculum = EnhancedRetrodictionCurriculum(config)
            >>> curriculum.uncertainty_threshold_multiplier
            2.0

            Full configuration:
            >>> full_config = {
            ...     "uncertainty_threshold_multiplier": 1.8,
            ...     "performance_degradation_threshold": 0.12,
            ...     "uncertainty_sampling_ratio": 0.35
            ... }
            >>> full_curriculum = EnhancedRetrodictionCurriculum(full_config)
            >>> full_curriculum.uncertainty_sampling_ratio
            0.35
        """
        self.logger = logging.getLogger("EnhancedRetrodictionCurriculum")
        self.metrics_tracker = EnhancedRecursiveTrainingMetrics(config)
        self.data_store = get_data_store()
        self.cost_controller = get_cost_controller()

        # Configuration for uncertainty-driven curriculum
        self.config = config or {}  # Store config as an instance attribute
        self.uncertainty_threshold_multiplier = self.config.get(
            "uncertainty_threshold_multiplier", 1.5
        )
        self.performance_degradation_threshold = self.config.get(
            "performance_degradation_threshold", 0.1
        )  # 10% degradation
        self.uncertainty_sampling_ratio = self.config.get(
            "uncertainty_sampling_ratio", 0.3
        )  # Percentage of data to sample based on uncertainty

        self.logger.info("EnhancedRetrodictionCurriculum initialized")

    def select_data_for_training(
        self,
        current_iteration: int,
        recent_metrics: Optional[Dict[str, Any]] = None,
        model: Optional[Any] = None,
    ) -> List[Dict[str, Any]]:
        """
        Selects data points for the next training iteration based on enhanced criteria.

        This implementation prioritizes data points where the model exhibits high
        uncertainty or where recent performance metrics indicate degradation. The
        selection process uses uncertainty scoring and adaptive sampling ratios.

        Args:
            current_iteration: The current training iteration number (0-based).
            recent_metrics: Optional dictionary of recent performance metrics
                containing keys like 'mse', 'rule_type', etc.
            model: Optional current model being trained. Must have 'predict' and
                'predict_proba' methods for uncertainty calculation.

        Returns:
            List of data point dictionaries selected for training. Returns empty
            list if no data is available in the data store.

        Raises:
            Exception: Re-raises any exceptions from model prediction with context.

        Example:
            Basic data selection without model:
            >>> curriculum = EnhancedRetrodictionCurriculum()
            >>> selected = curriculum.select_data_for_training(current_iteration=0)
            >>> isinstance(selected, list)
            True

            Data selection with metrics:
            >>> metrics = {"mse": 0.1, "rule_type": "hybrid"}
            >>> selected = curriculum.select_data_for_training(
            ...     current_iteration=1,
            ...     recent_metrics=metrics
            ... )
            >>> isinstance(selected, list)
            True

            Data selection with mock model:
            >>> class MockModel:
            ...     def predict(self, data): return [0.5] * len(data)
            ...     def predict_proba(self, data): return [[0.3, 0.7]] * len(data)
            >>> model = MockModel()
            >>> selected = curriculum.select_data_for_training(
            ...     current_iteration=1,
            ...     recent_metrics={"mse": 0.1},
            ...     model=model
            ... )
            >>> isinstance(selected, list)
            True
        """
        self.logger.info(
            f"Selecting data for iteration {current_iteration} using enhanced curriculum.")  # noqa: E501
        self.cost_controller.track_operation(
            operation_type="curriculum_data_selection", cost=0.01
        )  # Track cost

        all_data = self.data_store.get_all_data()
        if not all_data:
            self.logger.warning("No data available in the data store.")
            return []

        # 1. Assess overall training performance and uncertainty
        performance_summary = self.metrics_tracker.get_advanced_performance_summary()
        overall_uncertainty = performance_summary.get("uncertainty", {}).get(
            "mean", 0.0
        )
        is_degrading = performance_summary.get("drift", {}).get("detected", False)

        # Determine the uncertainty threshold for sampling
        uncertainty_threshold = (
            overall_uncertainty * self.uncertainty_threshold_multiplier
        )

        # 2. Score data points based on uncertainty (requires model predictions)
        uncertainty_scores = []
        if model and hasattr(model, "predict") and hasattr(model, "predict_proba"):
            try:
                # Predict and get uncertainty for each data point
                # This is a simplified example; a real implementation might use
                # more sophisticated uncertainty estimation per data point.
                model.predict(all_data)  # Get predictions for uncertainty calc
                predicted_probs = model.predict_proba(all_data)

                for i, data_point in enumerate(all_data):
                    # Example: Use the variance of predicted probabilities as
                    # uncertainty score
                    if (
                        NUMPY_AVAILABLE
                        and np is not None
                        and hasattr(np, "ndarray")
                        and isinstance(predicted_probs, np.ndarray)
                        and hasattr(predicted_probs, "ndim")
                        and predicted_probs.ndim > 1
                    ):
                        score = (
                            np.var(predicted_probs[i]) if hasattr(np, "var") else 0.0
                        )
                    elif (
                        isinstance(predicted_probs, list)
                        and predicted_probs
                        and isinstance(predicted_probs[i], (list, tuple))
                    ):
                        # Fallback for list of probabilities
                        score = (
                            statistics.variance(predicted_probs[i])
                            if len(predicted_probs[i]) > 1
                            else 0.0
                        )
                    else:
                        score = 0.0  # Cannot calculate uncertainty

                    uncertainty_scores.append((data_point, score))

            except Exception as e:
                self.logger.warning(
                    f"Could not calculate uncertainty scores for data points: {e}"
                )
                uncertainty_scores = [
                    (dp, 0.0) for dp in all_data
                ]  # Default to zero scores
        else:
            self.logger.warning(
                "Model or prediction methods not available for uncertainty scoring."
            )
            uncertainty_scores = [
                (dp, 0.0) for dp in all_data
            ]  # Default to zero scores

        # 3. Prioritize data based on uncertainty and performance degradation
        prioritized_data = []
        uncertain_data = [
            dp for dp, score in uncertainty_scores if score > uncertainty_threshold
        ]
        other_data = [
            dp for dp, score in uncertainty_scores if score <= uncertainty_threshold
        ]

        # If performance is degrading, prioritize uncertain data
        if is_degrading:
            self.logger.info(
                f"Performance degrading. Prioritizing {
                    len(uncertain_data)} uncertain data points.")
            prioritized_data.extend(uncertain_data)
            # Add remaining data randomly
            import random

            random.shuffle(other_data)
            prioritized_data.extend(other_data)
        else:
            # Otherwise, sample a portion of uncertain data and the rest from other data
            import random

            num_uncertain_samples = int(
                len(uncertain_data) * self.uncertainty_sampling_ratio
            )
            random.shuffle(uncertain_data)
            prioritized_data.extend(uncertain_data[:num_uncertain_samples])

            num_other_samples = len(all_data) - num_uncertain_samples
            random.shuffle(other_data)
            prioritized_data.extend(other_data[:num_other_samples])

        # Ensure we don't exceed the total number of data points
        selected_data = prioritized_data[: len(all_data)]

        self.logger.info(f"Selected {len(selected_data)} data points for training.")
        return selected_data

    def update_curriculum(
        self, current_iteration: int, recent_metrics: Dict[str, Any], model: Any
    ) -> None:
        """
        Updates the curriculum strategy based on recent training performance.

        This method adjusts curriculum parameters dynamically based on performance
        degradation detection. When degradation is detected, it increases focus on
        uncertain data points. When performance is stable, it gradually reduces
        the uncertainty focus.

        Args:
            current_iteration: The current training iteration number (0-based).
            recent_metrics: Dictionary of recent performance metrics containing
                keys like 'mse', 'rule_type', 'drift', etc.
            model: The current model being trained (used for future extensions).

        Example:
            Basic curriculum update:
            >>> curriculum = EnhancedRetrodictionCurriculum()
            >>> initial_ratio = curriculum.uncertainty_sampling_ratio
            >>> metrics = {"mse": 0.15, "rule_type": "hybrid"}
            >>> curriculum.update_curriculum(
            ...     current_iteration=5,
            ...     recent_metrics=metrics,
            ...     model=None
            ... )
            >>> curriculum.uncertainty_sampling_ratio >= 0.1
            True

            Multiple updates simulation:
            >>> curriculum = EnhancedRetrodictionCurriculum()
            >>> for i in range(3):
            ...     metrics = {"mse": 0.1 + i * 0.05, "rule_type": "hybrid"}
            ...     curriculum.update_curriculum(i, metrics, None)
            >>> curriculum.uncertainty_sampling_ratio >= 0.1
            True
        """
        self.logger.info(
            f"Updating enhanced curriculum for iteration {current_iteration}."
        )
        self.cost_controller.track_operation(
            operation_type="curriculum_update", cost=0.005
        )  # Track cost

        # Assess performance degradation
        performance_summary = self.metrics_tracker.get_advanced_performance_summary()
        is_degrading = performance_summary.get("drift", {}).get("detected", False)

        # Adjust curriculum parameters based on degradation
        if is_degrading:
            self.logger.warning(
                "Performance degradation detected. Adjusting curriculum to focus more on uncertain data."  # noqa: E501
            )
            # Increase the ratio of uncertain data sampled
            self.uncertainty_sampling_ratio = min(
                self.uncertainty_sampling_ratio + 0.1, 1.0
            )
            # Potentially adjust the uncertainty threshold multiplier
            self.uncertainty_threshold_multiplier = max(
                self.uncertainty_threshold_multiplier * 0.9, 1.0
            )
        else:
            # If performance is stable or improving, gradually reduce focus on
            # uncertain data
            self.uncertainty_sampling_ratio = max(
                self.uncertainty_sampling_ratio - 0.05, 0.1
            )
            self.uncertainty_threshold_multiplier = min(
                self.uncertainty_threshold_multiplier * 1.1, 2.0
            )

        self.logger.info(
            f"Curriculum updated: uncertainty_sampling_ratio={
                self.uncertainty_sampling_ratio:.2f}, " f"uncertainty_threshold_multiplier={  # noqa: E501
                self.uncertainty_threshold_multiplier:.2f}")  # noqa: E501

    def get_curriculum_state(self) -> Dict[str, Any]:
        """
        Gets the current state of the enhanced curriculum.

        This method returns a snapshot of all curriculum parameters that can be
        used for monitoring, debugging, or state persistence.

        Returns:
            Dict[str, Any]: Dictionary containing current curriculum state with keys:
                - uncertainty_threshold_multiplier (float): Current uncertainty
                  threshold multiplier
                - performance_degradation_threshold (float): Performance
                  degradation threshold
                - uncertainty_sampling_ratio (float): Current uncertainty
                  sampling ratio
                - base_curriculum_state (Dict): Reserved for base curriculum state (empty)  # noqa: E501

        Example:
            Get default state:
            >>> curriculum = EnhancedRetrodictionCurriculum()
            >>> state = curriculum.get_curriculum_state()
            >>> state["uncertainty_threshold_multiplier"]
            1.5
            >>> state["uncertainty_sampling_ratio"]
            0.3
            >>> "performance_degradation_threshold" in state
            True

            State after configuration:
            >>> config = {"uncertainty_threshold_multiplier": 2.5}
            >>> curriculum = EnhancedRetrodictionCurriculum(config)
            >>> state = curriculum.get_curriculum_state()
            >>> state["uncertainty_threshold_multiplier"]
            2.5

            Verify all expected keys:
            >>> expected_keys = {
            ...     "uncertainty_threshold_multiplier",
            ...     "performance_degradation_threshold",
            ...     "uncertainty_sampling_ratio",
            ...     "base_curriculum_state"
            ... }
            >>> set(state.keys()) == expected_keys
            True
        """
        return {
            "uncertainty_threshold_multiplier": self.uncertainty_threshold_multiplier,
            "performance_degradation_threshold": self.performance_degradation_threshold,
            "uncertainty_sampling_ratio": self.uncertainty_sampling_ratio,
            "base_curriculum_state": {},
        }
