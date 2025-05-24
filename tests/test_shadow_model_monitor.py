import pytest
import logging
from collections import deque  # Import deque for potential mocking or inspection

# Assuming the path is correct relative to the project root
from diagnostics.shadow_model_monitor import ShadowModelMonitor

# Configure logging for tests if needed
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Define a fixture for a basic monitor instance
@pytest.fixture
def basic_monitor():
    """Provides a basic ShadowModelMonitor instance for tests."""
    return ShadowModelMonitor(
        threshold=0.5, window_steps=3, critical_variables=["var1", "var2"]
    )


# Test initialization
def test_monitor_initialization_valid(basic_monitor):
    """Tests initialization with valid parameters."""
    assert basic_monitor.threshold == 0.5
    assert basic_monitor.window_steps == 3
    assert basic_monitor.critical_variables == ["var1", "var2"]
    assert isinstance(basic_monitor.delta_window, deque)
    assert basic_monitor.delta_window.maxlen == 3
    assert len(basic_monitor.delta_window) == 0


def test_monitor_initialization_invalid_threshold():
    """Tests initialization with invalid threshold."""
    with pytest.raises(ValueError, match="Threshold must be between 0 and 1"):
        ShadowModelMonitor(threshold=1.5, window_steps=10, critical_variables=["var1"])
    with pytest.raises(ValueError, match="Threshold must be between 0 and 1"):
        ShadowModelMonitor(threshold=0.0, window_steps=10, critical_variables=["var1"])


def test_monitor_initialization_invalid_window_steps():
    """Tests initialization with invalid window steps."""
    with pytest.raises(ValueError, match="Window steps must be a positive integer"):
        ShadowModelMonitor(threshold=0.5, window_steps=0, critical_variables=["var1"])
    with pytest.raises(ValueError, match="Window steps must be a positive integer"):
        ShadowModelMonitor(threshold=0.5, window_steps=-5, critical_variables=["var1"])


def test_monitor_initialization_no_critical_variables():
    """Tests initialization with an empty critical_variables list (should warn)."""
    # We can't easily assert on logging warnings directly with default pytest,
    # but we can check the instance is created.
    monitor = ShadowModelMonitor(threshold=0.5, window_steps=10, critical_variables=[])
    assert monitor.critical_variables == []
    # A more advanced test would capture logging output to confirm the warning.


# Test record_step
def test_record_step_adds_to_window(basic_monitor):
    """Tests that record_step adds data to the rolling window."""
    causal_deltas = {"var1": 0.1, "var2": 0.2, "var3": 0.3}
    gravity_deltas = {"var1": 0.05, "var2": 0.1, "var3": 0.03}
    basic_monitor.record_step(causal_deltas, gravity_deltas, 1)
    assert len(basic_monitor.delta_window) == 1
    # Check that only critical variables are stored
    assert basic_monitor.delta_window[0][0] == {"var1": 0.1, "var2": 0.2}
    assert basic_monitor.delta_window[0][1] == {"var1": 0.05, "var2": 0.1}


def test_record_step_rolling_window(basic_monitor):
    """Tests that the rolling window correctly discards old data."""
    # Window size is 3
    for i in range(5):
        causal_deltas = {"var1": i * 0.1, "var2": i * 0.2}
        gravity_deltas = {"var1": i * 0.05, "var2": i * 0.1}
        basic_monitor.record_step(causal_deltas, gravity_deltas, i)

    assert len(basic_monitor.delta_window) == 3
    # Check the data in the window corresponds to the last 3 steps (steps 2, 3, 4)
    assert basic_monitor.delta_window[0][0] == {"var1": 2 * 0.1, "var2": 2 * 0.2}
    assert basic_monitor.delta_window[2][0] == {"var1": 4 * 0.1, "var2": 4 * 0.2}


# Test calculate_variance_explained
def test_calculate_variance_explained_no_data(basic_monitor):
    """Tests variance calculation with no data in the window."""
    assert basic_monitor.calculate_variance_explained("var1") == 0.0


def test_calculate_variance_explained_zero_deltas(basic_monitor):
    """Tests variance calculation when all deltas are zero."""
    basic_monitor.record_step({"var1": 0.0}, {"var1": 0.0}, 1)
    basic_monitor.record_step({"var1": 0.0}, {"var1": 0.0}, 2)
    basic_monitor.record_step({"var1": 0.0}, {"var1": 0.0}, 3)  # Window full
    assert basic_monitor.calculate_variance_explained("var1") == 0.0


def test_calculate_variance_explained_causal_only(basic_monitor):
    """Tests variance calculation with only causal deltas."""
    basic_monitor.record_step({"var1": 1.0}, {"var1": 0.0}, 1)
    basic_monitor.record_step({"var1": 1.0}, {"var1": 0.0}, 2)
    basic_monitor.record_step({"var1": 1.0}, {"var1": 0.0}, 3)  # Window full
    # SumSq(Gravity) = 0, SumSq(Causal) = 1*3 = 3.0. 0 / (0 + 3) = 0.0
    assert basic_monitor.calculate_variance_explained("var1") == 0.0


def test_calculate_variance_explained_gravity_only(basic_monitor):
    """Tests variance calculation with only gravity deltas."""
    basic_monitor.record_step({"var1": 0.0}, {"var1": 1.0}, 1)
    basic_monitor.record_step({"var1": 0.0}, {"var1": 1.0}, 2)
    basic_monitor.record_step({"var1": 0.0}, {"var1": 1.0}, 3)  # Window full
    # SumSq(Gravity) = 1*3 = 3.0, SumSq(Causal) = 0. 3 / (3 + 0) = 1.0
    assert basic_monitor.calculate_variance_explained("var1") == 1.0


def test_calculate_variance_explained_mixed_deltas(basic_monitor):
    """Tests variance calculation with mixed causal and gravity deltas."""
    # Window size 3
    # Step 0: Causal=1, Gravity=0.5 -> SumSq(C)=1, SumSq(G)=0.25
    # Step 1: Causal=0.5, Gravity=1 -> SumSq(C)=0.25, SumSq(G)=1
    # Step 2: Causal=1, Gravity=1 -> SumSq(C)=1, SumSq(G)=1
    basic_monitor.record_step({"var1": 1.0}, {"var1": 0.5}, 0)
    basic_monitor.record_step({"var1": 0.5}, {"var1": 1.0}, 1)
    basic_monitor.record_step({"var1": 1.0}, {"var1": 1.0}, 2)  # Window full

    # Total SumSq(Causal) = 1.0**2 + 0.5**2 + 1.0**2 = 1.0 + 0.25 + 1.0 = 2.25
    # Total SumSq(Gravity) = 0.5**2 + 1.0**2 + 1.0**2 = 0.25 + 1.0 + 1.0 = 2.25
    # Variance Explained = 2.25 / (2.25 + 2.25) = 2.25 / 4.5 = 0.5
    assert basic_monitor.calculate_variance_explained("var1") == pytest.approx(0.5)


def test_calculate_variance_explained_variable_not_critical(basic_monitor):
    """Tests variance calculation for a variable not in critical_variables."""
    # Should return -1.0 and potentially log a warning (not asserting log here)
    assert basic_monitor.calculate_variance_explained("var_not_critical") == -1.0


# Test check_trigger
def test_check_trigger_window_not_full(basic_monitor):
    """Tests trigger check when the window is not yet full."""
    basic_monitor.record_step(
        {"var1": 1.0}, {"var1": 1.0}, 1
    )  # Window size 3, only 1 step recorded
    triggered, problematic_vars = basic_monitor.check_trigger()
    assert not triggered
    assert problematic_vars == []


def test_check_trigger_below_threshold(basic_monitor):
    """Tests trigger check when variance explained is below the threshold."""
    # Threshold = 0.5, Window = 3
    # Step 0: C=1, G=0.1 -> VE = 0.1^2 / (1^2 + 0.1^2) = 0.01 / 1.01 approx 0.01
    # Step 1: C=1, G=0.2 -> VE = 0.2^2 / (1^2 + 0.2^2) = 0.04 / 1.04 approx 0.038
    # Step 2: C=1, G=0.3 -> VE = 0.3^2 / (1^2 + 0.3^2) = 0.09 / 1.09 approx 0.082
    # Total SumSq(C) = 1+1+1 = 3, Total SumSq(G) = 0.01+0.04+0.09 = 0.14
    # Overall VE = 0.14 / (3 + 0.14) approx 0.044 < 0.5
    basic_monitor.record_step({"var1": 1.0}, {"var1": 0.1}, 0)
    basic_monitor.record_step({"var1": 1.0}, {"var1": 0.2}, 1)
    basic_monitor.record_step({"var1": 1.0}, {"var1": 0.3}, 2)  # Window full

    triggered, problematic_vars = basic_monitor.check_trigger()
    assert not triggered
    assert problematic_vars == []


def test_check_trigger_above_threshold_single_variable(basic_monitor):
    """Tests trigger check when variance explained is above threshold for one variable."""
    # Threshold = 0.5, Window = 3
    # Step 0: var1 C=1, G=1 -> VE = 0.5
    # Step 1: var1 C=0.5, G=1 -> VE = 1^2 / (0.5^2 + 1^2) = 1 / 1.25 = 0.8
    # Step 2: var1 C=1, G=1 -> VE = 0.5
    # Total SumSq(C) = 1^2 + 0.5^2 + 1^2 = 2.25
    # Total SumSq(G) = 1^2 + 1^2 + 1^2 = 3.0
    # Overall VE for var1 = 3.0 / (2.25 + 3.0) = 3.0 / 5.25 approx 0.57 > 0.5
    basic_monitor.record_step({"var1": 1.0, "var2": 1.0}, {"var1": 1.0, "var2": 0.1}, 0)
    basic_monitor.record_step({"var1": 0.5, "var2": 1.0}, {"var1": 1.0, "var2": 0.1}, 1)
    basic_monitor.record_step(
        {"var1": 1.0, "var2": 1.0}, {"var1": 1.0, "var2": 0.1}, 2
    )  # Window full

    triggered, problematic_vars = basic_monitor.check_trigger()
    assert triggered
    # Order might not be guaranteed, check for presence
    assert "var1" in problematic_vars
    assert len(problematic_vars) == 1  # Only var1 should be problematic


def test_check_trigger_above_threshold_multiple_variables():
    """Tests trigger check when variance explained is above threshold for multiple variables."""
    # Use a new monitor with different critical variables and threshold
    monitor = ShadowModelMonitor(
        threshold=0.6,
        window_steps=2,  # Smaller window
        critical_variables=["vA", "vB", "vC"],
    )
    # Window size 2, Threshold 0.6
    # Step 0: vA C=1, G=2; vB C=2, G=1; vC C=1, G=1
    # Step 1: vA C=1, G=2; vB C=2, G=1; vC C=1, G=3
    monitor.record_step({"vA": 1, "vB": 2, "vC": 1}, {"vA": 2, "vB": 1, "vC": 1}, 0)
    monitor.record_step(
        {"vA": 1, "vB": 2, "vC": 1}, {"vA": 2, "vB": 1, "vC": 3}, 1
    )  # Window full

    # vA: SumSq(C)=1^2+1^2=2, SumSq(G)=2^2+2^2=8. VE = 8/(2+8) = 0.8 > 0.6 (Trigger)
    # vB: SumSq(C)=2^2+2^2=8, SumSq(G)=1^2+1^2=2. VE = 2/(8+2) = 0.2 < 0.6 (No trigger)
    # vC: SumSq(C)=1^2+1^2=2, SumSq(G)=1^2+3^2=10. VE = 10/(2+10) = 10/12 approx 0.83 > 0.6 (Trigger)

    triggered, problematic_vars = monitor.check_trigger()
    assert triggered
    # Order might not be guaranteed, check for presence
    assert "vA" in problematic_vars
    assert "vC" in problematic_vars
    assert "vB" not in problematic_vars
    assert len(problematic_vars) == 2


def test_check_trigger_rolling_window_effect():
    """Tests that the rolling window affects the trigger check."""
    # Threshold = 0.5, Window = 2
    monitor = ShadowModelMonitor(
        threshold=0.5, window_steps=2, critical_variables=["var1"]
    )

    # Step 0: C=1, G=1 -> VE = 0.5
    monitor.record_step({"var1": 1.0}, {"var1": 1.0}, 0)
    triggered, _ = monitor.check_trigger()
    assert not triggered  # Window not full

    # Step 1: C=1, G=1 -> VE = 0.5. Window is now full (steps 0, 1). Total C SumSq=2, G SumSq=2. VE = 2/(2+2) = 0.5.
    monitor.record_step({"var1": 1.0}, {"var1": 1.0}, 1)
    triggered, _ = monitor.check_trigger()
    assert not triggered  # VE is exactly 0.5, not > 0.5

    # Step 2: C=0.1, G=1 -> VE = 1^2 / (0.1^2 + 1^2) = 1 / 1.01 approx 0.99. Window is now (steps 1, 2).
    # Step 1: C=1, G=1
    # Step 2: C=0.1, G=1
    # Total C SumSq = 1^2 + 0.1^2 = 1 + 0.01 = 1.01
    # Total G SumSq = 1^2 + 1^2 = 2
    # Overall VE = 2 / (1.01 + 2) = 2 / 3.01 approx 0.66 > 0.5 (Trigger)
    monitor.record_step({"var1": 0.1}, {"var1": 1.0}, 2)
    triggered, problematic_vars = monitor.check_trigger()
    assert triggered
    assert problematic_vars == ["var1"]

    # Step 3: C=1, G=0.1 -> VE approx 0.01. Window is now (steps 2, 3).
    # Step 2: C=0.1, G=1
    # Step 3: C=1, G=0.1
    # Total C SumSq = 0.1^2 + 1^2 = 0.01 + 1 = 1.01
    # Total G SumSq = 1^2 + 0.1^2 = 1 + 0.01 = 1.01
    # Overall VE = 1.01 / (1.01 + 1.01) = 0.5.
    monitor.record_step({"var1": 1.0}, {"var1": 0.1}, 3)
    triggered, _ = monitor.check_trigger()
    assert not triggered  # VE is 0.5, not > 0.5
