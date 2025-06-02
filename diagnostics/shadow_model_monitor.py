import logging
from collections import deque

logger = logging.getLogger(__name__)


class ShadowModelMonitor:
    """
    Monitors the influence of the gravity model on critical variables by tracking
    the proportion of variance it explains compared to the causal model.
    """

    def __init__(
        self, threshold: float, window_steps: int, critical_variables: list[str]
    ):
        """
        Initializes the ShadowModelMonitor.

        Args:
            threshold: The variance explained threshold (e.g., 0.35 for 35%).
                       If gravity explains more than this proportion of variance
                       for a critical variable, a trigger condition is met.
            window_steps: The number of simulation steps to consider in the rolling window.
            critical_variables: A list of variable names to monitor.
        """
        if not (0 < threshold < 1):
            raise ValueError("Threshold must be between 0 and 1 (exclusive).")
        if window_steps <= 0:
            raise ValueError("Window steps must be a positive integer.")
        if not critical_variables:
            logger.warning(
                "ShadowModelMonitor initialized with no critical variables to monitor."
            )

        self.threshold = threshold
        self.window_steps = window_steps
        self.critical_variables = critical_variables

        # Data storage for the rolling window
        # Each entry in the deque will be a tuple: (causal_deltas_step, gravity_deltas_step)
        # where each _deltas_step is a dict: {var_name: delta_value}
        self.delta_window: deque[tuple[dict[str, float], dict[str, float]]] = deque(
            maxlen=window_steps
        )
        # For internal tracking if needed, though `current_step` is passed in
        # `record_step`
        self.current_step_internal = 0

    def record_step(
        self,
        causal_deltas: dict[str, float],
        gravity_deltas: dict[str, float],
        current_step: int,
    ):
        """
        Records the deltas from the causal model and the gravity model for the current step.

        Args:
            causal_deltas: A dictionary mapping critical variable names to their deltas
                           predicted by the causal core (before gravity correction).
            gravity_deltas: A dictionary mapping critical variable names to the deltas
                            applied by the gravity correction.
            current_step: The current simulation step number.
        """
        # Filter deltas to only include critical variables to save space and processing
        causal_deltas_critical = {
            var: causal_deltas.get(var, 0.0)
            for var in self.critical_variables
            if var in causal_deltas
        }
        gravity_deltas_critical = {
            var: gravity_deltas.get(var, 0.0)
            for var in self.critical_variables
            if var in gravity_deltas
        }

        self.delta_window.append((causal_deltas_critical, gravity_deltas_critical))
        self.current_step_internal = current_step  # Keep track if needed

    def _sum_of_squares(self, values: list[float]) -> float:
        """Helper to calculate sum of squares."""
        return sum(v**2 for v in values)

    def calculate_variance_explained(self, variable: str) -> float:
        """
        Calculates the proportion of variance explained by gravity for a given variable
        over the current window.

        The proportion is calculated as:
        SumSq(GravityDeltas) / (SumSq(GravityDeltas) + SumSq(CausalDeltas))
        If the denominator is zero, returns 0.0.

        Args:
            variable: The name of the variable to calculate variance for.

        Returns:
            The proportion of variance explained by gravity (between 0.0 and 1.0).
            Returns -1.0 if the variable is not found or data is insufficient.
        """
        if variable not in self.critical_variables:
            logger.warning(
                f"Variable '{variable}' not in critical_variables list for ShadowModelMonitor.")
            return -1.0  # Or raise error

        if not self.delta_window:
            return 0.0  # No data yet

        causal_deltas_for_var_in_window = []
        gravity_deltas_for_var_in_window = []

        for causal_step_deltas, gravity_step_deltas in self.delta_window:
            causal_deltas_for_var_in_window.append(
                causal_step_deltas.get(variable, 0.0)
            )
            gravity_deltas_for_var_in_window.append(
                gravity_step_deltas.get(variable, 0.0)
            )

        sum_sq_gravity = self._sum_of_squares(gravity_deltas_for_var_in_window)
        sum_sq_causal = self._sum_of_squares(causal_deltas_for_var_in_window)

        denominator = sum_sq_gravity + sum_sq_causal

        if denominator == 0:
            return 0.0

        return sum_sq_gravity / denominator

    def check_trigger(self) -> tuple[bool, list[str]]:
        """
        Checks if the gravity term consistently explains more than X% of the variance
        for any critical variables over the defined window.

        Returns:
            A tuple: (trigger_met, list_of_problematic_variables)
            trigger_met (bool): True if the threshold was exceeded for any critical variable.
            list_of_problematic_variables (list[str]): Names of variables that exceeded the threshold.
        """
        if len(self.delta_window) < self.window_steps:
            # Not enough data yet to fill the window
            return False, []

        problematic_vars = []
        triggered = False

        for var in self.critical_variables:
            variance_explained_by_gravity = self.calculate_variance_explained(var)
            if variance_explained_by_gravity > self.threshold:
                problematic_vars.append(var)
                triggered = True
                logger.debug(
                    f"ShadowModelMonitor: Variable '{var}' exceeded threshold. " f"Gravity explained {
                        variance_explained_by_gravity *
                        100:.2f}% of variance " f"(Threshold: {
                        self.threshold *
                        100:.2f}%).")

        return triggered, problematic_vars


if __name__ == "__main__":
    # Basic test and usage example
    logging.basicConfig(level=logging.DEBUG)

    monitor_config_example = {
        "threshold_variance_explained": 0.35,
        "window_steps": 3,  # Small window for testing
        "critical_variables": ["var1", "var2", "var3"],
    }

    monitor = ShadowModelMonitor(
        threshold=monitor_config_example["threshold_variance_explained"],
        window_steps=monitor_config_example["window_steps"],
        critical_variables=monitor_config_example["critical_variables"],
    )

    # Simulate some steps
    steps_data = [
        # Step 0
        (
            {
                "var1": 1.0,
                "var2": 2.0,
                "var3": 0.5,
                "var4_ignored": 10.0,
            },  # Causal deltas
            {"var1": 0.1, "var2": 0.3, "var3": 0.05, "var4_ignored": 1.0},
        ),  # Gravity deltas
        # Step 1
        (
            {"var1": 1.2, "var2": 2.1, "var3": 0.6},
            {"var1": 0.8, "var2": 0.5, "var3": 0.1},
        ),  # var1 gravity is higher
        # Step 2 - Window is now full
        (
            {"var1": 0.9, "var2": 1.9, "var3": 0.4},
            {"var1": 0.7, "var2": 1.5, "var3": 0.05},
        ),  # var2 gravity is higher
        # Step 3 - Window rolls
        (
            {"var1": 1.1, "var2": 0.5, "var3": 0.5},
            {"var1": 0.1, "var2": 1.8, "var3": 0.1},
        ),  # var2 gravity remains high
    ]

    for i, (cd, gd) in enumerate(steps_data):
        monitor.record_step(causal_deltas=cd, gravity_deltas=gd, current_step=i)
        logger.info(f"--- Step {i} ---")
        if len(monitor.delta_window) >= monitor.window_steps:
            for var_to_check in monitor.critical_variables:
                ve = monitor.calculate_variance_explained(var_to_check)
                logger.info(
                    f"Variance explained by gravity for '{var_to_check}': {
                        ve * 100:.2f}%")

            triggered, problematic_vars = monitor.check_trigger()
            if triggered:
                logger.warning(
                    f"TRIGGERED at step {i}! Problematic variables: {problematic_vars}"
                )
            else:
                logger.info(f"No trigger at step {i}.")
        else:
            logger.info(
                f"Window not full yet ({len(monitor.delta_window)}/{monitor.window_steps} steps)."
            )

    # Test edge cases
    logger.info("\n--- Testing Edge Cases ---")
    monitor_edge = ShadowModelMonitor(0.5, 2, ["v_zero"])
    monitor_edge.record_step({"v_zero": 0.0}, {"v_zero": 0.0}, 0)
    monitor_edge.record_step({"v_zero": 0.0}, {"v_zero": 0.0}, 1)
    ve_zero = monitor_edge.calculate_variance_explained("v_zero")
    logger.info(
        f"Variance explained for v_zero (all zeros): {ve_zero}"
    )  # Should be 0.0
    triggered_zero, _ = monitor_edge.check_trigger()
    logger.info(
        f"Triggered for v_zero (all zeros): {triggered_zero}"
    )  # Should be False

    monitor_edge.record_step({"v_zero": 1.0}, {"v_zero": 0.0}, 2)  # Causal only
    monitor_edge.record_step({"v_zero": 1.0}, {"v_zero": 0.0}, 3)
    ve_causal_only = monitor_edge.calculate_variance_explained("v_zero")
    logger.info(
        f"Variance explained for v_zero (causal only): {ve_causal_only}"
    )  # Should be 0.0
    triggered_causal_only, _ = monitor_edge.check_trigger()
    logger.info(
        f"Triggered for v_zero (causal only): {triggered_causal_only}"
    )  # Should be False

    monitor_edge.record_step({"v_zero": 0.0}, {"v_zero": 1.0}, 4)  # Gravity only
    monitor_edge.record_step({"v_zero": 0.0}, {"v_zero": 1.0}, 5)
    ve_gravity_only = monitor_edge.calculate_variance_explained("v_zero")
    logger.info(
        f"Variance explained for v_zero (gravity only): {ve_gravity_only}"
    )  # Should be 1.0
    triggered_gravity_only, _ = monitor_edge.check_trigger()  # Threshold is 0.5
    logger.info(
        f"Triggered for v_zero (gravity only): {triggered_gravity_only}"
    )  # Should be True
