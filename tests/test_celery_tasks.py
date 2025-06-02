"""
Tests for Celery tasks in the adapters module.

This module tests the Celery task implementations including autopilot,
retrodiction, and signal processing tasks.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import time
from celery.exceptions import Retry

from adapters.celery_app import (
    celery_app,
    autopilot_engage_task,
    autopilot_disengage_task,
    retrodiction_run_task,
    ingest_and_score_signal,
    health_check
)


@pytest.fixture
def mock_celery_task():
    """Create a mock Celery task for testing."""
    task = Mock()
    task.retry = Mock(side_effect=Retry("Test retry"))
    return task


class TestAutopilotEngageTask:
    """Test cases for autopilot_engage_task."""

    def test_autopilot_engage_success(self):
        """Test successful autopilot engagement."""
        action = "start_trading"
        parameters = {"risk_level": "medium", "max_position": 1000}
        
        with patch('time.sleep') as mock_sleep:
            result = autopilot_engage_task(action, parameters)
        
        assert result["action"] == action
        assert result["parameters"] == parameters
        assert result["status"] == "engaged"
        assert "timestamp" in result
        assert "message" in result
        assert "Autopilot start_trading completed successfully" in result["message"]
        mock_sleep.assert_called_once_with(2)

    def test_autopilot_engage_with_different_action(self):
        """Test autopilot engagement with different action."""
        action = "stop_trading"
        parameters = {"immediate": True}
        
        with patch('time.sleep'):
            result = autopilot_engage_task(action, parameters)
        
        assert result["action"] == action
        assert result["parameters"] == parameters
        assert result["status"] == "engaged"

    @patch('adapters.celery_app.logging.getLogger')
    def test_autopilot_engage_exception_handling(self, mock_logger):
        """Test autopilot engagement exception handling."""
        mock_task = Mock()
        mock_task.retry = Mock(side_effect=Retry("Test retry"))
        
        with patch('time.sleep', side_effect=Exception("Test error")):
            with pytest.raises(Retry):
                autopilot_engage_task.apply(
                    args=["start_trading", {}],
                    task=mock_task
                )
        
        mock_task.retry.assert_called_once()

    def test_autopilot_engage_empty_parameters(self):
        """Test autopilot engagement with empty parameters."""
        action = "start_trading"
        parameters = {}
        
        with patch('time.sleep'):
            result = autopilot_engage_task(action, parameters)
        
        assert result["action"] == action
        assert result["parameters"] == {}
        assert result["status"] == "engaged"

    def test_autopilot_engage_complex_parameters(self):
        """Test autopilot engagement with complex parameters."""
        action = "configure_strategy"
        parameters = {
            "strategy": "momentum",
            "settings": {
                "lookback_period": 20,
                "threshold": 0.05,
                "risk_management": {
                    "stop_loss": 0.02,
                    "take_profit": 0.06
                }
            }
        }
        
        with patch('time.sleep'):
            result = autopilot_engage_task(action, parameters)
        
        assert result["action"] == action
        assert result["parameters"] == parameters
        assert result["status"] == "engaged"


class TestAutopilotDisengageTask:
    """Test cases for autopilot_disengage_task."""

    def test_autopilot_disengage_success(self):
        """Test successful autopilot disengagement."""
        with patch('time.sleep') as mock_sleep:
            result = autopilot_disengage_task()
        
        assert result["status"] == "disengaged"
        assert "timestamp" in result
        assert "message" in result
        assert "Autopilot disengaged successfully" in result["message"]
        mock_sleep.assert_called_once_with(1)

    @patch('adapters.celery_app.logging.getLogger')
    def test_autopilot_disengage_exception_handling(self, mock_logger):
        """Test autopilot disengagement exception handling."""
        mock_task = Mock()
        mock_task.retry = Mock(side_effect=Retry("Test retry"))
        
        with patch('time.sleep', side_effect=Exception("Test error")):
            with pytest.raises(Retry):
                autopilot_disengage_task.apply(task=mock_task)
        
        mock_task.retry.assert_called_once()

    def test_autopilot_disengage_timestamp_format(self):
        """Test that disengagement timestamp is valid."""
        with patch('time.sleep'):
            result = autopilot_disengage_task()
        
        timestamp = result["timestamp"]
        assert isinstance(timestamp, float)
        assert timestamp > 0


class TestRetrodictionRunTask:
    """Test cases for retrodiction_run_task."""

    def test_retrodiction_run_success(self):
        """Test successful retrodiction run."""
        target_date = "2024-01-15"
        parameters = {"lookback_days": 30, "confidence_threshold": 0.8}
        
        with patch('time.sleep') as mock_sleep:
            result = retrodiction_run_task(target_date, parameters)
        
        assert result["target_date"] == target_date
        assert result["parameters"] == parameters
        assert result["status"] == "completed"
        assert "timestamp" in result
        assert "analysis_results" in result
        assert "message" in result
        
        # Check analysis results structure
        analysis = result["analysis_results"]
        assert "accuracy" in analysis
        assert "confidence" in analysis
        assert "key_factors" in analysis
        assert "recommendations" in analysis
        
        mock_sleep.assert_called_once_with(5)

    def test_retrodiction_run_analysis_results(self):
        """Test retrodiction analysis results structure and values."""
        target_date = "2024-02-01"
        parameters = {"lookback_days": 60}
        
        with patch('time.sleep'):
            result = retrodiction_run_task(target_date, parameters)
        
        analysis = result["analysis_results"]
        assert isinstance(analysis["accuracy"], float)
        assert isinstance(analysis["confidence"], float)
        assert isinstance(analysis["key_factors"], list)
        assert isinstance(analysis["recommendations"], list)
        assert 0 <= analysis["accuracy"] <= 1
        assert 0 <= analysis["confidence"] <= 1

    @patch('adapters.celery_app.logging.getLogger')
    def test_retrodiction_run_exception_handling(self, mock_logger):
        """Test retrodiction run exception handling."""
        mock_task = Mock()
        mock_task.retry = Mock(side_effect=Retry("Test retry"))
        
        with patch('time.sleep', side_effect=Exception("Test error")):
            with pytest.raises(Retry):
                retrodiction_run_task.apply(
                    args=["2024-01-15", {}],
                    task=mock_task
                )
        
        mock_task.retry.assert_called_once()

    def test_retrodiction_run_empty_parameters(self):
        """Test retrodiction run with empty parameters."""
        target_date = "2024-01-15"
        parameters = {}
        
        with patch('time.sleep'):
            result = retrodiction_run_task(target_date, parameters)
        
        assert result["target_date"] == target_date
        assert result["parameters"] == {}
        assert result["status"] == "completed"

    def test_retrodiction_run_message_content(self):
        """Test retrodiction run message content."""
        target_date = "2024-03-01"
        parameters = {"test": "value"}
        
        with patch('time.sleep'):
            result = retrodiction_run_task(target_date, parameters)
        
        expected_message = f"Retrodiction analysis for {target_date} completed"
        assert result["message"] == expected_message


class TestIngestAndScoreSignal:
    """Test cases for ingest_and_score_signal task."""

    @patch('adapters.celery_app.scraper')
    @patch('adapters.celery_app.signal_ingest_counter')
    def test_ingest_and_score_signal_success(self, mock_counter, mock_scraper):
        """Test successful signal ingestion and scoring."""
        # Setup mock scraper
        mock_result = {
            "name": "test_signal",
            "value": 100.0,
            "source": "test",
            "timestamp": time.time()
        }
        mock_scraper.ingest_signal.return_value = mock_result
        
        # Setup mock counter
        mock_counter.labels.return_value.inc = Mock()
        
        signal_data = {
            "name": "test_signal",
            "value": 100.0,
            "source": "test"
        }
        
        result = ingest_and_score_signal(signal_data)
        
        assert result == mock_result
        mock_scraper.ingest_signal.assert_called_once_with(
            name="test_signal",
            value=100.0,
            source="test",
            timestamp=None
        )
        mock_counter.labels.assert_called_once_with(source="test")

    @patch('adapters.celery_app.scraper')
    def test_ingest_and_score_signal_with_forecast(self, mock_scraper):
        """Test signal ingestion with forecast enrichment."""
        mock_result = {
            "name": "test_signal",
            "value": 100.0,
            "source": "test",
            "forecast": {"prediction": 105.0}
        }
        mock_scraper.ingest_signal.return_value = mock_result
        
        with patch('trust_system.trust_engine.enrich_trust_metadata') as mock_enrich:
            mock_enrich.return_value = {
                "confidence": 0.85,
                "alignment_score": 0.92
            }
            
            signal_data = {"name": "test_signal", "value": 100.0}
            result = ingest_and_score_signal(signal_data)
            
            assert result["trust_score"] == 0.85
            assert result["alignment_score"] == 0.92
            mock_enrich.assert_called_once_with(mock_result)

    @patch('adapters.celery_app.scraper')
    def test_ingest_and_score_signal_none_result(self, mock_scraper):
        """Test signal ingestion when scraper returns None."""
        mock_scraper.ingest_signal.return_value = None
        
        signal_data = {"name": "test_signal", "value": 100.0}
        result = ingest_and_score_signal(signal_data)
        
        assert result is None

    @patch('adapters.celery_app.scraper')
    @patch('adapters.celery_app.logging.getLogger')
    def test_ingest_and_score_signal_exception_handling(self, mock_logger, mock_scraper):
        """Test signal ingestion exception handling."""
        mock_scraper.ingest_signal.side_effect = Exception("Test error")
        mock_task = Mock()
        mock_task.retry = Mock(side_effect=Retry("Test retry"))
        
        signal_data = {"name": "test_signal", "value": 100.0}
        
        with pytest.raises(Retry):
            ingest_and_score_signal.apply(
                args=[signal_data],
                task=mock_task
            )
        
        mock_task.retry.assert_called_once()

    @patch('adapters.celery_app.scraper')
    def test_ingest_and_score_signal_without_forecast(self, mock_scraper):
        """Test signal ingestion without forecast data."""
        mock_result = {
            "name": "test_signal",
            "value": 100.0,
            "source": "test"
        }
        mock_scraper.ingest_signal.return_value = mock_result
        
        signal_data = {"name": "test_signal", "value": 100.0}
        result = ingest_and_score_signal(signal_data)
        
        assert result["trust_score"] == 0.0
        assert result["alignment_score"] == 0.0


class TestHealthCheck:
    """Test cases for health_check task."""

    def test_health_check_success(self):
        """Test successful health check."""
        result = health_check()
        
        assert result == {"status": "ok"}

    def test_health_check_return_type(self):
        """Test health check return type."""
        result = health_check()
        
        assert isinstance(result, dict)
        assert "status" in result


class TestCeleryAppConfiguration:
    """Test cases for Celery app configuration."""

    def test_celery_app_exists(self):
        """Test that Celery app is properly configured."""
        assert celery_app is not None
        assert celery_app.main == "pulse"

    def test_celery_app_config(self):
        """Test Celery app configuration settings."""
        config = celery_app.conf
        
        assert config.task_track_started is True
        assert config.task_serializer == "json"
        assert config.result_serializer == "json"
        assert "json" in config.accept_content

    def test_celery_broker_backend_urls(self):
        """Test that broker and backend URLs are configured."""
        # These should be set from environment variables or defaults
        assert celery_app.broker_url is not None
        assert celery_app.backend is not None


class TestTaskRegistration:
    """Test cases for task registration."""

    def test_autopilot_engage_task_registered(self):
        """Test that autopilot_engage_task is registered."""
        assert "autopilot_engage_task" in celery_app.tasks

    def test_autopilot_disengage_task_registered(self):
        """Test that autopilot_disengage_task is registered."""
        assert "autopilot_disengage_task" in celery_app.tasks

    def test_retrodiction_run_task_registered(self):
        """Test that retrodiction_run_task is registered."""
        assert "retrodiction_run_task" in celery_app.tasks

    def test_ingest_and_score_signal_registered(self):
        """Test that ingest_and_score_signal is registered."""
        assert "ingest_and_score_signal" in celery_app.tasks

    def test_health_check_registered(self):
        """Test that health_check is registered."""
        assert "health_check" in celery_app.tasks


class TestTaskRetryBehavior:
    """Test cases for task retry behavior."""

    def test_autopilot_engage_retry_parameters(self):
        """Test autopilot engage task retry parameters."""
        task = celery_app.tasks["autopilot_engage_task"]
        
        # Test that the task is configured with bind=True for retry functionality
        assert task.bind is True

    def test_autopilot_disengage_retry_parameters(self):
        """Test autopilot disengage task retry parameters."""
        task = celery_app.tasks["autopilot_disengage_task"]
        
        assert task.bind is True

    def test_retrodiction_run_retry_parameters(self):
        """Test retrodiction run task retry parameters."""
        task = celery_app.tasks["retrodiction_run_task"]
        
        assert task.bind is True

    def test_ingest_and_score_signal_retry_parameters(self):
        """Test ingest and score signal task retry parameters."""
        task = celery_app.tasks["ingest_and_score_signal"]
        
        assert task.bind is True


class TestTaskIntegration:
    """Integration test cases for tasks."""

    @patch('time.sleep')
    def test_multiple_task_execution(self, mock_sleep):
        """Test executing multiple tasks in sequence."""
        # Test autopilot engage
        engage_result = autopilot_engage_task("start_trading", {"risk": "low"})
        assert engage_result["status"] == "engaged"
        
        # Test retrodiction
        retro_result = retrodiction_run_task("2024-01-15", {"days": 30})
        assert retro_result["status"] == "completed"
        
        # Test autopilot disengage
        disengage_result = autopilot_disengage_task()
        assert disengage_result["status"] == "disengaged"
        
        # Verify sleep was called for each task
        assert mock_sleep.call_count == 3

    def test_task_result_consistency(self):
        """Test that task results have consistent structure."""
        with patch('time.sleep'):
            # All tasks should return dictionaries with status
            engage_result = autopilot_engage_task("test", {})
            disengage_result = autopilot_disengage_task()
            retro_result = retrodiction_run_task("2024-01-15", {})
            
            for result in [engage_result, disengage_result, retro_result]:
                assert isinstance(result, dict)
                assert "status" in result
                assert "timestamp" in result
                assert "message" in result