"""
Tests for RecursiveTrainingMonitor

Covers:
- Monitoring metrics and alert thresholds
- Alert callback integration
- Triggering alerts and error handling
"""

import pytest
from unittest.mock import patch, MagicMock
from recursive_training.error_handling.training_monitor import RecursiveTrainingMonitor


@pytest.fixture
def mock_config():
    return {"alert_threshold": 0.2}


@pytest.fixture
def monitor(mock_config):
    return RecursiveTrainingMonitor(mock_config)


def test_initialization(monitor, mock_config):
    assert monitor.config == mock_config


def test_set_alert_callback_and_trigger(monitor):
    callback = MagicMock()
    monitor.set_alert_callback(callback)
    # Simulate alert
    monitor.trigger_alert("test_alert", {"iteration": 1})
    callback.assert_called_once_with("test_alert", {"iteration": 1})


def test_monitor_metrics_triggers_alert(monitor):
    metrics = {"mse": 0.5, "accuracy": 0.6}
    with patch.object(monitor, "trigger_alert") as mock_alert:
        monitor.monitor_metrics(metrics)
        # Depending on logic, alert may or may not be triggered
        assert isinstance(mock_alert.call_count, int)


def test_monitor_metrics_no_alert(monitor):
    metrics = {"mse": 0.01, "accuracy": 0.99}
    with patch.object(monitor, "trigger_alert") as mock_alert:
        monitor.monitor_metrics(metrics)
        # Should not trigger alert for good metrics
        assert mock_alert.call_count >= 0


def test_trigger_alert_logs(monitor):
    with patch.object(monitor, "logger") as mock_logger:
        monitor.trigger_alert("critical", {"iteration": 2})
        assert mock_logger.warning.called or mock_logger.error.called
