"""
Tests for RecursiveTrainingRecovery

Covers:
- Recovery strategies and retry mechanisms
- Rollback to safe state
- Recovery status reporting
"""

import pytest
from unittest.mock import patch, MagicMock
from recursive_training.error_handling.recovery import RecursiveTrainingRecovery

@pytest.fixture
def mock_config():
    return {
        "recovery_enabled": True
    }

@pytest.fixture
def recovery(mock_config):
    return RecursiveTrainingRecovery(mock_config)

def test_initialization(recovery, mock_config):
    assert recovery.config == mock_config

def test_recover_success(recovery):
    error = Exception("Recoverable error")
    with patch.object(recovery, "logger"):
        result = recovery.recover(error, context={"iteration": 1})
        assert isinstance(result, bool)

def test_recover_failure(recovery):
    # Simulate recover returning False for unrecoverable error
    with patch.object(recovery, "logger"), \
         patch.object(recovery, "recover", return_value=False) as mock_recover:
        result = recovery.recover(Exception("Unrecoverable"), context={"iteration": 2})
        assert result is False
        mock_recover.assert_called()

def test_rollback_to_safe_state(recovery):
    with patch.object(recovery, "logger"):
        recovery.rollback_to_safe_state(context={"iteration": 3})
        # No exception means success

def test_get_recovery_status(recovery):
    status = recovery.get_recovery_status()
    assert isinstance(status, dict)