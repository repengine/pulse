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

from api.fastapi_server import app, get_app_settings
from pulse.core.app_settings import AppSettings


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
def e2e_client(e2e_settings):
    """Create test client for E2E testing."""
    app.dependency_overrides[get_app_settings] = lambda: e2e_settings
    yield TestClient(app)
    app.dependency_overrides.clear()


@pytest.mark.e2e
class TestRetrodictionE2E:
    """End-to-end tests for complete retrodiction workflow."""
    
    @patch('adapters.celery_app.celery_app')
    @patch('engine.historical_retrodiction_runner.HistoricalRetrodictionRunner')
    @patch('analytics.learning.LearningProfile')
    def test_complete_retrodiction_workflow(
        self, 
        mock_learning, 
        mock_retro_runner, 
        mock_celery, 
        e2e_client
    ):
        """Test complete retrodiction workflow from request to results."""
        # Arrange - Setup realistic mock responses
        task_id = "retro-e2e-12345"
        
        # Mock Celery task submission
        mock_task_result = Mock()
        mock_task_result.id = task_id
        mock_celery.send_task.return_value = mock_task_result
        
        # Mock retrodiction runner results
        mock_runner_instance = Mock()
        mock_retro_runner.return_value = mock_runner_instance
        mock_runner_instance.run_retrodiction.return_value = {
            "accuracy": 0.87,
            "confidence": 0.92,
            "predictions": [
                {
                    "date": "2024-01-15",
                    "predicted_value": 105.2,
                    "actual_value": 103.8,
                    "error": 1.4
                },
                {
                    "date": "2024-01-16", 
                    "predicted_value": 107.1,
                    "actual_value": 108.3,
                    "error": -1.2
                }
            ],
            "summary": {
                "total_predictions": 2,
                "mean_absolute_error": 1.3,
                "root_mean_square_error": 1.31
            }
        }
        
        # Mock task status progression
        task_states = ["PENDING", "STARTED", "SUCCESS"]
        task_results = [
            None,
            {"status": "processing", "progress": 50},
            {
                "status": "completed",
                "analysis_results": mock_runner_instance.run_retrodiction.return_value,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        ]
        
        mock_async_result = Mock()
        mock_celery.AsyncResult.return_value = mock_async_result
        
        # Step 1: Submit retrodiction request
        retro_request = {
            "start_date": "2024-01-01",
            "end_date": "2024-01-31", 
            "parameters": {
                "model_type": "ensemble",
                "confidence_threshold": 0.8,
                "include_gravity": True
            }
        }
        
        response = e2e_client.post("/retrodiction/run", json=retro_request)
        
        # Assert - Request accepted
        assert response.status_code == 202
        response_data = response.json()
        assert response_data["task_id"] == task_id
        assert response_data["status"] == "submitted"
        assert "estimated_completion" in response_data
        
        # Step 2: Poll task status (simulate real user behavior)
        for i, (state, result) in enumerate(zip(task_states, task_results)):
            mock_async_result.state = state
            mock_async_result.result = result
            
            status_response = e2e_client.get(f"/tasks/{task_id}/status")
            assert status_response.status_code == 200
            
            status_data = status_response.json()
            assert status_data["task_id"] == task_id
            assert status_data["state"] == state
            
            if state == "SUCCESS":
                # Step 3: Verify final results
                assert status_data["result"]["status"] == "completed"
                analysis = status_data["result"]["analysis_results"]
                assert analysis["accuracy"] == 0.87
                assert analysis["confidence"] == 0.92
                assert len(analysis["predictions"]) == 2
                assert analysis["summary"]["total_predictions"] == 2
                
                # Verify prediction structure
                prediction = analysis["predictions"][0]
                assert "date" in prediction
                assert "predicted_value" in prediction
                assert "actual_value" in prediction
                assert "error" in prediction
        
        # Step 4: Verify learning audit includes retrodiction data
        audit_response = e2e_client.get("/learning/audit")
        assert audit_response.status_code == 200
        audit_data = audit_response.json()
        assert "retrodiction_insights" in audit_data
        
        # Verify Celery task was called with correct parameters
        mock_celery.send_task.assert_called_once_with(
            "retrodiction_run_task",
            args=[retro_request]
        )
    
    @patch('adapters.celery_app.celery_app')
    def test_retrodiction_parameter_validation(self, mock_celery, e2e_client):
        """Test E2E parameter validation for retrodiction requests."""
        # Test invalid date range
        invalid_request = {
            "start_date": "2024-01-31",  # Start after end
            "end_date": "2024-01-01",
            "parameters": {}
        }
        
        response = e2e_client.post("/retrodiction/run", json=invalid_request)
        assert response.status_code == 422  # Validation error
        
        # Test missing required fields
        incomplete_request = {
            "start_date": "2024-01-01"
            # Missing end_date
        }
        
        response = e2e_client.post("/retrodiction/run", json=incomplete_request)
        assert response.status_code == 422
        
        # Verify no Celery tasks were submitted for invalid requests
        mock_celery.send_task.assert_not_called()


@pytest.mark.e2e
class TestRetrodictionWithLearning:
    """E2E tests for retrodiction with learning integration."""
    
    @patch('adapters.celery_app.celery_app')
    @patch('analytics.learning.LearningProfile')
    @patch('trust_system.trust_engine.TrustEngine')
    def test_retrodiction_with_trust_scoring(
        self, 
        mock_trust_engine, 
        mock_learning, 
        mock_celery, 
        e2e_client
    ):
        """Test retrodiction workflow with trust scoring and learning updates."""
        # Arrange
        task_id = "retro-trust-67890"
        
        mock_task_result = Mock()
        mock_task_result.id = task_id
        mock_celery.send_task.return_value = mock_task_result
        
        # Mock trust engine scoring
        mock_trust_instance = Mock()
        mock_trust_engine.return_value = mock_trust_instance
        mock_trust_instance.score_forecast.return_value = {
            "trust_score": 0.89,
            "confidence": 0.91,
            "risk_factors": ["market_volatility", "data_quality"]
        }
        
        # Mock learning profile updates
        mock_learning_instance = Mock()
        mock_learning.return_value = mock_learning_instance
        mock_learning_instance.update_from_retrodiction.return_value = {
            "learning_events": 3,
            "accuracy_improvement": 0.05,
            "new_patterns": ["trend_reversal", "volatility_spike"]
        }
        
        # Mock successful task completion
        mock_async_result = Mock()
        mock_async_result.state = "SUCCESS"
        mock_async_result.result = {
            "status": "completed",
            "analysis_results": {
                "accuracy": 0.89,
                "trust_metadata": mock_trust_instance.score_forecast.return_value,
                "learning_updates": mock_learning_instance.update_from_retrodiction.return_value
            }
        }
        mock_celery.AsyncResult.return_value = mock_async_result
        
        # Act - Submit retrodiction with learning enabled
        response = e2e_client.post(
            "/retrodiction/run",
            json={
                "start_date": "2024-01-01",
                "end_date": "2024-01-31",
                "parameters": {
                    "enable_learning": True,
                    "enable_trust_scoring": True,
                    "update_models": True
                }
            }
        )
        
        # Assert - Request accepted
        assert response.status_code == 202
        
        # Act - Check final results
        status_response = e2e_client.get(f"/tasks/{task_id}/status")
        
        # Assert - Trust and learning data included
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
    
    @patch('adapters.celery_app.celery_app')
    def test_retrodiction_task_failure_recovery(self, mock_celery, e2e_client):
        """Test E2E handling of retrodiction task failures."""
        # Arrange
        task_id = "retro-fail-99999"
        
        mock_task_result = Mock()
        mock_task_result.id = task_id
        mock_celery.send_task.return_value = mock_task_result
        
        # Mock task failure
        mock_async_result = Mock()
        mock_async_result.state = "FAILURE"
        mock_async_result.result = Exception("Retrodiction engine failed: insufficient data")
        mock_async_result.traceback = "Traceback: Data validation failed..."
        mock_celery.AsyncResult.return_value = mock_async_result
        
        # Act - Submit retrodiction request
        response = e2e_client.post(
            "/retrodiction/run",
            json={
                "start_date": "2024-01-01",
                "end_date": "2024-01-31",
                "parameters": {"model_type": "invalid_model"}
            }
        )
        
        # Assert - Request accepted initially
        assert response.status_code == 202
        
        # Act - Check failed task status
        status_response = e2e_client.get(f"/tasks/{task_id}/status")
        
        # Assert - Failure handled gracefully
        assert status_response.status_code == 200
        status_data = status_response.json()
        assert status_data["state"] == "FAILURE"
        assert "error" in status_data
        assert "insufficient data" in str(status_data["error"])
        assert status_data["traceback"] is not None
    
    @patch('adapters.celery_app.celery_app')
    def test_retrodiction_timeout_handling(self, mock_celery, e2e_client):
        """Test E2E handling of retrodiction task timeouts."""
        # Arrange
        task_id = "retro-timeout-11111"
        
        mock_task_result = Mock()
        mock_task_result.id = task_id
        mock_celery.send_task.return_value = mock_task_result
        
        # Mock task timeout (long running task)
        mock_async_result = Mock()
        mock_async_result.state = "STARTED"
        mock_async_result.result = {"status": "processing", "progress": 10}
        mock_celery.AsyncResult.return_value = mock_async_result
        
        # Act - Submit retrodiction request
        response = e2e_client.post(
            "/retrodiction/run",
            json={
                "start_date": "2023-01-01",  # Large date range
                "end_date": "2024-12-31",
                "parameters": {"timeout": 30}  # Short timeout
            }
        )
        
        # Assert - Request accepted
        assert response.status_code == 202
        
        # Act - Check task status (still running)
        status_response = e2e_client.get(f"/tasks/{task_id}/status")
        
        # Assert - Task still processing
        assert status_response.status_code == 200
        status_data = status_response.json()
        assert status_data["state"] == "STARTED"
        assert status_data["result"]["status"] == "processing"
        assert "progress" in status_data["result"]