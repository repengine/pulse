"""
Integration tests for FastAPI + Celery workflow.

This module tests the complete integration between FastAPI endpoints and Celery
task processing, ensuring the full request-response cycle works correctly.
"""

import pytest
import time
from unittest.mock import Mock, patch, MagicMock
from fastapi.testclient import TestClient
from datetime import datetime, timezone

from api.fastapi_server import app, get_app_settings
from pulse.core.app_settings import AppSettings


__all__ = [
    "TestAPIToCeleryIntegration",
    "TestAutopilotWorkflow", 
    "TestRetrodictionWorkflow",
    "TestSignalIngestionWorkflow",
]


@pytest.fixture
def mock_settings():
    """Create mock app settings for integration testing."""
    settings = Mock(spec=AppSettings)
    settings.ai = Mock()
    settings.ai.model_name = "test-model"
    settings.gravity = Mock()
    settings.gravity.enabled = True
    settings.simulation = Mock()
    settings.simulation.enabled = True
    return settings


@pytest.fixture
def mock_celery_app():
    """Create mock Celery app for integration testing."""
    mock_app = Mock()
    mock_app.AsyncResult = Mock()
    return mock_app


@pytest.fixture
def integration_client(mock_settings, mock_celery_app):
    """Create test client for integration testing."""
    app.dependency_overrides[get_app_settings] = lambda: mock_settings
    
    # Configure mock celery_app.send_task to return proper task ID
    mock_result = Mock()
    mock_result.id = "integration-task-id"
    mock_celery_app.send_task.return_value = mock_result
    
    with patch('api.fastapi_server.celery_app', mock_celery_app):
        yield TestClient(app)
    
    app.dependency_overrides.clear()


@pytest.mark.integration
class TestAPIToCeleryIntegration:
    """Test complete API to Celery integration workflows."""
    
    def test_autopilot_engage_to_task_completion(self, integration_client, mock_celery_app):
        """Test complete autopilot engagement workflow from API to task completion."""
        # Arrange
        task_id = "autopilot-engage-123"
        mock_result = Mock()
        mock_result.id = task_id
        mock_result.state = "SUCCESS"
        mock_result.result = {
            "status": "engaged",
            "action": "start_trading",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "parameters": {"risk_level": "medium"}
        }
        
        mock_celery_app.send_task.return_value = mock_result
        mock_celery_app.AsyncResult.return_value = mock_result
        
        # Act - Submit autopilot engagement
        response = integration_client.post(
            "/autopilot/engage",
            json={
                "action": "start_trading",
                "parameters": {"risk_level": "medium"}
            }
        )
        
        # Assert - Task submitted successfully
        assert response.status_code == 202
        response_data = response.json()
        assert response_data["task_id"] == task_id
        assert response_data["status"] == "submitted"
        
        # Act - Check task status
        status_response = integration_client.get(f"/tasks/{task_id}/status")
        
        # Assert - Task completed successfully
        assert status_response.status_code == 200
        status_data = status_response.json()
        assert status_data["task_id"] == task_id
        assert status_data["state"] == "SUCCESS"
        assert status_data["result"]["status"] == "engaged"
        
        # Verify Celery task was called correctly
        mock_celery_app.send_task.assert_called_once_with(
            "autopilot_engage_task",
            args=["start_trading", {"risk_level": "medium"}]
        )
    
    def test_retrodiction_run_to_completion(self, integration_client, mock_celery_app):
        """Test complete retrodiction workflow from API to task completion."""
        # Arrange
        task_id = "retrodiction-run-456"
        mock_result = Mock()
        mock_result.id = task_id
        mock_result.state = "SUCCESS"
        mock_result.result = {
            "status": "completed",
            "analysis_results": {
                "accuracy": 0.85,
                "confidence": 0.92,
                "predictions": ["forecast_1", "forecast_2"]
            },
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        mock_celery_app.send_task.return_value = mock_result
        mock_celery_app.AsyncResult.return_value = mock_result
        
        # Act - Submit retrodiction run
        response = integration_client.post(
            "/retrodiction/run",
            json={
                "start_date": "2024-01-01",
                "end_date": "2024-01-31",
                "parameters": {"model_type": "ensemble"}
            }
        )
        
        # Assert - Task submitted successfully
        assert response.status_code == 202
        response_data = response.json()
        assert response_data["task_id"] == task_id
        
        # Act - Check task status
        status_response = integration_client.get(f"/tasks/{task_id}/status")
        
        # Assert - Task completed successfully
        assert status_response.status_code == 200
        status_data = status_response.json()
        assert status_data["result"]["analysis_results"]["accuracy"] == 0.85
        
        # Verify Celery task was called correctly
        mock_celery_app.send_task.assert_called_once_with(
            "retrodiction_run_task",
            args=[{
                "start_date": "2024-01-01",
                "end_date": "2024-01-31",
                "parameters": {"model_type": "ensemble"}
            }]
        )
    
    def test_task_failure_handling(self, integration_client, mock_celery_app):
        """Test handling of failed Celery tasks."""
        # Arrange
        task_id = "failed-task-789"
        mock_result = Mock()
        mock_result.id = task_id
        mock_result.state = "FAILURE"
        mock_result.result = Exception("Task processing failed")
        mock_result.traceback = "Traceback: Task failed due to..."
        
        mock_celery_app.send_task.return_value = mock_result
        mock_celery_app.AsyncResult.return_value = mock_result
        
        # Act - Submit task
        response = integration_client.post(
            "/autopilot/engage",
            json={"action": "start_trading", "parameters": {}}
        )
        
        # Assert - Task submitted
        assert response.status_code == 202
        
        # Act - Check failed task status
        status_response = integration_client.get(f"/tasks/{task_id}/status")
        
        # Assert - Failure handled correctly
        assert status_response.status_code == 200
        status_data = status_response.json()
        assert status_data["state"] == "FAILURE"
        assert "error" in status_data
        assert status_data["traceback"] is not None


@pytest.mark.integration
class TestAutopilotWorkflow:
    """Test complete autopilot engagement/disengagement workflows."""
    
    def test_autopilot_engage_disengage_cycle(self, integration_client, mock_celery_app):
        """Test complete autopilot engage-disengage cycle."""
        # Setup mock results for both operations
        engage_result = Mock()
        engage_result.id = "engage-task-123"
        engage_result.state = "SUCCESS"
        engage_result.result = {"status": "engaged", "action": "start_trading"}
        
        disengage_result = Mock()
        disengage_result.id = "disengage-task-456"
        disengage_result.state = "SUCCESS"
        disengage_result.result = {"status": "disengaged"}
        
        mock_celery_app.send_task.side_effect = [engage_result, disengage_result]
        mock_celery_app.AsyncResult.side_effect = [engage_result, disengage_result]
        
        # Act - Engage autopilot
        engage_response = integration_client.post(
            "/autopilot/engage",
            json={"action": "start_trading", "parameters": {"risk_level": "low"}}
        )
        
        # Assert - Engagement successful
        assert engage_response.status_code == 202
        engage_data = engage_response.json()
        assert engage_data["task_id"] == "engage-task-123"
        
        # Act - Disengage autopilot
        disengage_response = integration_client.post("/autopilot/disengage")
        
        # Assert - Disengagement successful
        assert disengage_response.status_code == 202
        disengage_data = disengage_response.json()
        assert disengage_data["task_id"] == "disengage-task-456"
        
        # Verify both tasks were called
        assert mock_celery_app.send_task.call_count == 2


@pytest.mark.integration
class TestRetrodictionWorkflow:
    """Test complete retrodiction analysis workflows."""
    
    def test_retrodiction_with_learning_audit(self, integration_client, mock_celery_app):
        """Test retrodiction run followed by learning audit."""
        # Arrange
        retro_result = Mock()
        retro_result.id = "retro-task-789"
        retro_result.state = "SUCCESS"
        retro_result.result = {
            "analysis_results": {"accuracy": 0.88},
            "learning_insights": ["insight_1", "insight_2"]
        }
        
        mock_celery_app.send_task.return_value = retro_result
        mock_celery_app.AsyncResult.return_value = retro_result
        
        # Act - Run retrodiction
        retro_response = integration_client.post(
            "/retrodiction/run",
            json={
                "start_date": "2024-01-01",
                "end_date": "2024-01-31",
                "parameters": {"include_learning": True}
            }
        )
        
        # Assert - Retrodiction submitted
        assert retro_response.status_code == 202
        
        # Act - Get learning audit (should include retrodiction insights)
        audit_response = integration_client.get("/learning/audit")
        
        # Assert - Learning audit includes retrodiction data
        assert audit_response.status_code == 200
        audit_data = audit_response.json()
        assert "retrodiction_insights" in audit_data
        assert audit_data["total_learning_events"] > 0


@pytest.mark.integration
class TestSignalIngestionWorkflow:
    """Test signal ingestion and processing workflows."""
    
    @patch('adapters.celery_app.scraper')
    def test_signal_ingestion_to_forecast_generation(self, mock_scraper, integration_client):
        """Test signal ingestion leading to forecast generation."""
        # Arrange
        mock_scraper.ingest_signal.return_value = {
            "name": "test_signal",
            "value": 100.0,
            "source": "integration_test",
            "forecast": {"prediction": 105.0, "confidence": 0.85}
        }
        
        # Act - Check forecasts endpoint (should trigger signal processing)
        response = integration_client.get("/forecasts")
        
        # Assert - Forecasts generated successfully
        assert response.status_code == 200
        forecast_data = response.json()
        assert "forecasts" in forecast_data
        assert len(forecast_data["forecasts"]) > 0
        
        # Verify forecast structure
        forecast = forecast_data["forecasts"][0]
        assert "prediction" in forecast
        assert "confidence" in forecast
        assert "timestamp" in forecast