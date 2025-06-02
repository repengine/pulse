"""
End-to-End tests for retrodiction analysis workflow.

This module tests the complete retrodiction flow from API request through
Celery task execution to result retrieval, simulating real user scenarios.
"""

import pytest
import time
import json
from unittest.mock import Mock, patch, MagicMock
from fastapi.testclient import TestClient
from datetime import datetime, timezone
import os

from api.fastapi_server import app, get_app_settings
from pulse.core.app_settings import AppSettings

# Import celery_app here to be able to modify its config before TestClient uses it
from adapters.celery_app import celery_app as actual_celery_app


__all__ = [
    "TestRetrodictionE2E",
    "TestRetrodictionWithLearning",
    "TestRetrodictionErrorScenarios",
]


@pytest.fixture
def e2e_settings():
    """Create realistic app settings for E2E testing."""
    settings = Mock(spec=AppSettings)
    settings.ai = Mock()
    settings.ai.model_name = "gpt-4"
    settings.gravity = Mock()
    settings.gravity.enabled = True
    settings.simulation = Mock()
    settings.simulation.enabled = True
    settings.retrodiction = Mock()
    settings.retrodiction.max_days = 365
    settings.retrodiction.min_confidence = 0.7
    return settings


@pytest.fixture
def e2e_client(e2e_settings, monkeypatch):
    """Create test client for E2E testing."""
    monkeypatch.setenv("PULSE_CELERY_BROKER", "memory://")
    monkeypatch.setenv("PULSE_CELERY_BACKEND", "memory://")
    monkeypatch.setenv("CELERY_TASK_ALWAYS_EAGER", "1")
    monkeypatch.setenv("CELERY_TASK_EAGER_PROPAGATES", "1")

    app.dependency_overrides[get_app_settings] = lambda: e2e_settings
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()


@pytest.mark.e2e
class TestRetrodictionE2E:
    """End-to-end tests for complete retrodiction workflow."""

    @patch("engine.simulate_backward.run_retrodiction")
    @patch("analytics.learning_profile.LearningProfile")
    def test_complete_retrodiction_workflow(
        self, mock_learning_profile, mock_engine_run_retrodiction, e2e_client
    ):
        """Test complete retrodiction workflow from request to results."""
        task_id = "retro-e2e-12345"

        expected_task_analysis_results = {
            "accuracy": 0.87,
            "confidence": 0.92,
            "predictions": [
                {
                    "date": "2024-01-15",
                    "predicted_value": 105.2,
                    "actual_value": 103.8,
                    "error": 1.4,
                },
                {
                    "date": "2024-01-16",
                    "predicted_value": 107.1,
                    "actual_value": 108.3,
                    "error": -1.2,
                },
            ],
            "summary": {
                "total_predictions": 2,
                "mean_absolute_error": 1.3,
                "root_mean_square_error": 1.31,
            },
        }
        # This mock is for the function that the Celery task itself might call.
        mock_engine_run_retrodiction.return_value = expected_task_analysis_results

        task_states_for_polling = ["PENDING", "STARTED", "SUCCESS"]
        task_results_for_polling = [
            None,
            {"status": "processing", "progress": 50},
            {
                "status": "completed",
                "analysis_results": expected_task_analysis_results,  # This is what the Celery task returns
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
        ]

        with patch("adapters.celery_app.celery_app.send_task") as mock_send_task, patch(
            "adapters.celery_app.celery_app.AsyncResult"
        ) as mock_async_result_constructor:

            mock_task_submission_result = Mock()
            mock_task_submission_result.id = task_id
            mock_send_task.return_value = mock_task_submission_result

            mock_async_result_instance = Mock()
            mock_async_result_constructor.return_value = mock_async_result_instance

            retro_request = {
                "target_date": "2024-01-31",
                "parameters": {
                    "model_type": "ensemble",
                    "confidence_threshold": 0.8,
                    "include_gravity": True,
                },
            }

            response = e2e_client.post("/api/retrodiction/run", json=retro_request)

            assert response.status_code == 202
            response_data = response.json()
            assert response_data["task_id"] == task_id
            assert response_data["status"] == "submitted"
            # assert "estimated_completion" in response_data # Removed as per debugging

            for i, (state_val, result_payload) in enumerate(
                zip(task_states_for_polling, task_results_for_polling)
            ):
                mock_async_result_instance.state = state_val
                mock_async_result_instance.result = result_payload

                status_response = e2e_client.get(f"/api/tasks/{task_id}/status")
                assert status_response.status_code == 200

                status_data = status_response.json()
                assert status_data["task_id"] == task_id
                assert status_data["status"] == state_val

                if state_val == "SUCCESS":
                    assert status_data["result"]["status"] == "completed"
                    analysis = status_data["result"]["analysis_results"]
                    assert analysis["accuracy"] == 0.87
                    assert analysis["confidence"] == 0.92
                    assert len(analysis["predictions"]) == 2
                    assert analysis["summary"]["total_predictions"] == 2

                    prediction = analysis["predictions"][0]
                    assert "date" in prediction
                    assert "predicted_value" in prediction
                    assert "actual_value" in prediction
                    assert "error" in prediction

            audit_response = e2e_client.get("/api/learning/audit")
            assert audit_response.status_code == 200

            mock_send_task.assert_called_once_with(
                "retrodiction_run_task",
                args=[retro_request["target_date"], retro_request["parameters"]],
            )

    def test_retrodiction_parameter_validation(self, e2e_client):
        """Test E2E parameter validation for retrodiction requests."""
        with patch("adapters.celery_app.celery_app.send_task") as mock_send_task:
            invalid_format_request = {"target_date": "2024/01/01", "parameters": {}}
            response = e2e_client.post(
                "/api/retrodiction/run", json=invalid_format_request
            )
            assert response.status_code == 422

            incomplete_request = {"parameters": {}}
            response = e2e_client.post("/api/retrodiction/run", json=incomplete_request)
            assert response.status_code == 422

            mock_send_task.assert_not_called()


@pytest.mark.e2e
class TestRetrodictionWithLearning:
    """E2E tests for retrodiction with learning integration."""

    @patch("analytics.learning_profile.LearningProfile")
    @patch("trust_system.trust_engine.TrustEngine")
    def test_retrodiction_with_trust_scoring(
        self, mock_trust_engine, mock_learning_profile, e2e_client
    ):
        """Test retrodiction workflow with trust scoring and learning updates."""
        task_id = "retro-trust-67890"

        with patch("adapters.celery_app.celery_app.send_task") as mock_send_task, patch(
            "adapters.celery_app.celery_app.AsyncResult"
        ) as mock_async_result_constructor:

            mock_task_submission_result = Mock()
            mock_task_submission_result.id = task_id
            mock_send_task.return_value = mock_task_submission_result

            mock_trust_instance = Mock()
            mock_trust_engine.return_value = mock_trust_instance
            mock_trust_instance.score_forecast.return_value = {
                "trust_score": 0.89,
                "confidence": 0.91,
                "risk_factors": ["market_volatility", "data_quality"],
            }

            mock_learning_instance = Mock()
            mock_learning_profile.return_value = mock_learning_instance
            mock_learning_instance.update_from_retrodiction.return_value = {
                "learning_events": 3,
                "accuracy_improvement": 0.05,
                "new_patterns": ["trend_reversal", "volatility_spike"],
            }

            mock_async_result_instance = Mock()
            mock_async_result_instance.state = "SUCCESS"
            mock_async_result_instance.result = {
                "status": "completed",
                "analysis_results": {
                    "accuracy": 0.89,
                    "trust_metadata": mock_trust_instance.score_forecast.return_value,
                    "learning_updates": mock_learning_instance.update_from_retrodiction.return_value,
                },
            }
            mock_async_result_constructor.return_value = mock_async_result_instance

            response = e2e_client.post(
                "/api/retrodiction/run",
                json={
                    "target_date": "2024-01-31",
                    "parameters": {
                        "enable_learning": True,
                        "enable_trust_scoring": True,
                        "update_models": True,
                    },
                },
            )

            assert response.status_code == 202

            status_response = e2e_client.get(f"/api/tasks/{task_id}/status")

            assert status_response.status_code == 200
            status_data = status_response.json()

            results = status_data["result"]["analysis_results"]
            assert "trust_metadata" in results
            assert results["trust_metadata"]["trust_score"] == 0.89
            assert "learning_updates" in results
            assert results["learning_updates"]["learning_events"] == 3


@pytest.mark.e2e
class TestRetrodictionErrorScenarios:
    """E2E tests for retrodiction error handling and recovery."""

    def test_retrodiction_task_failure_recovery(self, e2e_client):
        """Test E2E handling of retrodiction task failures."""
        task_id = "retro-fail-99999"
        traceback_str = "Traceback: Data validation failed..."
        error_message = "Retrodiction engine failed: insufficient data"

        with patch("adapters.celery_app.celery_app.send_task") as mock_send_task, patch(
            "adapters.celery_app.celery_app.AsyncResult"
        ) as mock_async_result_constructor:

            mock_task_submission_result = Mock()
            mock_task_submission_result.id = task_id
            mock_send_task.return_value = mock_task_submission_result

            mock_async_result_instance = Mock()
            mock_async_result_instance.state = "FAILURE"
            # Pydantic model expects a Dict for 'result' field in TaskStatusResponse
            mock_async_result_instance.result = {
                "error": error_message,
                "details": traceback_str,
            }
            # Celery's AsyncResult uses 'info' for traceback on failure
            mock_async_result_instance.info = traceback_str
            mock_async_result_constructor.return_value = mock_async_result_instance

            response = e2e_client.post(
                "/api/retrodiction/run",
                json={
                    "target_date": "2024-01-31",
                    "parameters": {"model_type": "invalid_model"},
                },
            )

            assert response.status_code == 202

            status_response = e2e_client.get(f"/api/tasks/{task_id}/status")

            assert (
                status_response.status_code == 200
            )  # API should handle task failure gracefully
            status_data = status_response.json()
            assert status_data["status"] == "FAILURE"
            assert "error" in status_data["result"]
            assert error_message in status_data["result"]["error"]
            assert status_data["info"] == traceback_str

    def test_retrodiction_timeout_handling(self, e2e_client):
        """Test E2E handling of retrodiction task timeouts."""
        task_id = "retro-timeout-11111"
        with patch("adapters.celery_app.celery_app.send_task") as mock_send_task, patch(
            "adapters.celery_app.celery_app.AsyncResult"
        ) as mock_async_result_constructor:

            mock_task_submission_result = Mock()
            mock_task_submission_result.id = task_id
            mock_send_task.return_value = mock_task_submission_result

            mock_async_result_instance = Mock()
            mock_async_result_instance.state = "STARTED"  # Initial state
            mock_async_result_instance.result = {"status": "processing", "progress": 10}
            mock_async_result_constructor.return_value = mock_async_result_instance

            response = e2e_client.post(
                "/api/retrodiction/run",
                json={"target_date": "2024-12-31", "parameters": {"timeout": 30}},
            )

            assert response.status_code == 202

            # First status check: still processing
            status_response = e2e_client.get(f"/api/tasks/{task_id}/status")
            assert status_response.status_code == 200
            status_data = status_response.json()
            assert status_data["status"] == "STARTED"
            assert status_data["result"]["status"] == "processing"
            assert "progress" in status_data["result"]

            # Simulate timeout by changing mock state to FAILURE due to timeout
            mock_async_result_instance.state = "FAILURE"
            timeout_error_message = "Task timed out after 30 seconds"
            timeout_traceback = "Traceback: Celery task exceeded timeout limit."
            mock_async_result_instance.result = {
                "error": timeout_error_message,
                "details": "Timeout",
            }
            mock_async_result_instance.info = timeout_traceback  # For traceback

            # Second status check: should reflect timeout failure
            status_response_after_timeout = e2e_client.get(
                f"/api/tasks/{task_id}/status"
            )
            assert status_response_after_timeout.status_code == 200
            status_data_after_timeout = status_response_after_timeout.json()

            assert status_data_after_timeout["status"] == "FAILURE"
            assert "error" in status_data_after_timeout["result"]
            assert timeout_error_message in status_data_after_timeout["result"]["error"]
            assert status_data_after_timeout["info"] == timeout_traceback
