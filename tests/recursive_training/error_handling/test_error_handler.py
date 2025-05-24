"""
Tests for RecursiveTrainingErrorHandler

Covers:
- Error classification and handling
- Alert triggering and thresholds
- Recovery attempts and error status
"""

import pytest
from unittest.mock import patch
from recursive_training.error_handling.error_handler import (
    RecursiveTrainingErrorHandler,
)


@pytest.fixture
def mock_config():
    return {"alert_threshold": 0.2, "recovery_enabled": True}


@pytest.fixture
def error_handler(mock_config):
    return RecursiveTrainingErrorHandler(mock_config)


def test_initialization(error_handler, mock_config):
    assert error_handler.config == mock_config


def test_handle_exception_triggers_alert(error_handler):
    exc = ValueError("Test error")
    with (
        patch.object(error_handler, "should_alert", return_value=True),
        patch.object(error_handler, "trigger_alert") as mock_alert,
    ):
        error_handler.handle_exception(exc)
        mock_alert.assert_called_once_with(exc, None)


def test_handle_exception_no_alert(error_handler):
    exc = RuntimeError("Non-alert error")
    with (
        patch.object(error_handler, "should_alert", return_value=False),
        patch.object(error_handler, "trigger_alert") as mock_alert,
    ):
        error_handler.handle_exception(exc)
        mock_alert.assert_not_called()


def test_should_alert(error_handler):
    exc = Exception("Critical error")
    # By default, should_alert may depend on error type or config
    result = error_handler.should_alert(exc)
    assert isinstance(result, bool)


def test_trigger_alert(error_handler):
    exc = Exception("Alert error")
    with patch.object(error_handler, "logger") as mock_logger:
        error_handler.trigger_alert(exc, context={"iteration": 1})
        assert mock_logger.warning.called or mock_logger.error.called


def test_attempt_recovery(error_handler):
    exc = Exception("Recoverable error")
    with patch.object(error_handler, "logger"):
        result = error_handler.attempt_recovery(exc)
        assert isinstance(result, bool)


def test_get_error_status(error_handler):
    status = error_handler.get_error_status()
    assert isinstance(status, dict)
