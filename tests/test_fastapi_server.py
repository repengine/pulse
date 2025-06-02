"""
Tests for FastAPI server endpoints and integration.

This module tests the FastAPI server implementation including all endpoints,
Pydantic models, error handling, and Celery task integration.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from fastapi.testclient import TestClient
from datetime import datetime, timezone

from api.fastapi_server import app, get_app_settings
from pulse.core.app_settings import AppSettings


@pytest.fixture
def mock_settings():
    """Create mock app settings for testing."""
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
    """Create mock Celery app for testing."""
    mock_app = Mock()
    mock_app.AsyncResult = Mock()
    return mock_app


@pytest.fixture
def client(mock_settings, mock_celery_app):
    """Create test client with dependency overrides and Celery mocking."""
    app.dependency_overrides[get_app_settings] = lambda: mock_settings
    
    # Configure mock celery_app.send_task to return proper task ID
    mock_result = Mock()
    mock_result.id = "test-task-id"
    mock_celery_app.send_task.return_value = mock_result
    
    # Mock all Celery imports and tasks
    with patch('api.fastapi_server.celery_app', mock_celery_app), \
         patch('api.fastapi_server.autopilot_engage_task') as mock_engage, \
         patch('api.fastapi_server.autopilot_disengage_task') as mock_disengage, \
         patch('api.fastapi_server.retrodiction_run_task') as mock_retro:
        
        # Configure mock tasks with proper return values (for direct calls)
        mock_engage.delay.return_value = mock_result
        mock_disengage.delay.return_value = mock_result
        mock_retro.delay.return_value = mock_result
        
        with TestClient(app) as test_client:
            yield test_client
    
    app.dependency_overrides.clear()


class TestStatusEndpoint:
    """Test cases for the /api/status endpoint."""

    def test_status_success(self, client):
        """Test successful status endpoint response."""
        response = client.get("/api/status")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "operational"
        assert data["service"] == "pulse-api"
        assert "timestamp" in data
        assert "version" in data
        assert data["components"]["database"] == "connected"
        assert data["components"]["celery"] == "connected"
        assert data["components"]["redis"] == "connected"

    def test_status_response_structure(self, client):
        """Test that status response has correct structure."""
        response = client.get("/api/status")
        data = response.json()
        
        required_fields = ["status", "service", "timestamp", "version", "components"]
        for field in required_fields:
            assert field in data
        
        required_components = ["database", "celery", "redis"]
        for component in required_components:
            assert component in data["components"]


class TestForecastsEndpoint:
    """Test cases for the /api/forecasts/latest/all endpoint."""

    def test_forecasts_success(self, client):
        """Test successful forecasts endpoint response."""
        response = client.get("/api/forecasts/latest/all")
        
        assert response.status_code == 200
        data = response.json()
        assert "forecasts" in data
        assert "metadata" in data
        assert len(data["forecasts"]) > 0

    def test_forecasts_structure(self, client):
        """Test that forecast response has correct structure."""
        response = client.get("/api/forecasts/latest/all")
        data = response.json()

        # Check first forecast structure
        forecast = data["forecasts"][0]
        required_fields = ["id", "symbol", "prediction", "confidence", "timestamp", "horizon"]
        for field in required_fields:
            assert field in forecast

        # Check metadata structure
        metadata = data["metadata"]
        assert "total_forecasts" in metadata
        assert "data_freshness" in metadata
        assert "model_version" in metadata

    def test_forecasts_data_types(self, client):
        """Test that forecast data has correct types."""
        response = client.get("/api/forecasts/latest/all")
        data = response.json()
        
        forecast = data["forecasts"][0]
        assert isinstance(forecast["confidence"], (int, float))
        assert isinstance(forecast["prediction"], (int, float))
        assert isinstance(forecast["symbol"], str)


class TestAutopilotEndpoints:
    """Test cases for autopilot endpoints."""

    def test_autopilot_engage_success(self, client):
        """Test successful autopilot engagement."""
        payload = {
            "action": "start_trading",
            "parameters": {"risk_level": "medium", "max_position": 1000}
        }

        response = client.post("/api/autopilot/engage", json=payload)

        assert response.status_code == 202
        data = response.json()
        assert data["task_id"] == "test-task-id"
        assert data["status"] == "submitted"
        assert "result" in data
        assert "message" in data["result"]

    def test_autopilot_engage_validation_error(self, client):
        """Test autopilot engagement with invalid payload."""
        payload = {
            "action": "",  # Invalid empty action
            "parameters": {}
        }

        response = client.post("/api/autopilot/engage", json=payload)
        assert response.status_code == 422

    def test_autopilot_disengage_success(self, client):
        """Test successful autopilot disengagement."""
        response = client.post("/api/autopilot/disengage")

        assert response.status_code == 202
        data = response.json()
        assert data["task_id"] == "test-task-id"
        assert data["status"] == "submitted"


class TestRetrodictionEndpoints:
    """Test cases for retrodiction endpoints."""

    def test_retrodiction_run_success(self, client):
        """Test successful retrodiction run."""
        payload = {
            "target_date": "2024-01-15",
            "parameters": {"lookback_days": 30, "confidence_threshold": 0.8}
        }

        response = client.post("/api/retrodiction/run", json=payload)

        assert response.status_code == 202
        data = response.json()
        assert data["task_id"] == "test-task-id"
        assert data["status"] == "submitted"

    def test_retrodiction_run_validation_error(self, client):
        """Test retrodiction run with invalid date format."""
        payload = {
            "target_date": "invalid-date",
            "parameters": {}
        }

        response = client.post("/api/retrodiction/run", json=payload)
        assert response.status_code == 422


class TestLearningAuditEndpoint:
    """Test cases for the /api/learning/audit endpoint."""

    def test_learning_audit_success(self, client):
        """Test successful learning audit endpoint response."""
        response = client.get("/api/learning/audit")
        
        assert response.status_code == 200
        data = response.json()
        assert "audit_results" in data
        assert "summary" in data

    def test_learning_audit_structure(self, client):
        """Test that learning audit response has correct structure."""
        response = client.get("/api/learning/audit")
        data = response.json()

        # Check audit results structure
        if data["audit_results"]:
            audit_item = data["audit_results"][0]
            required_fields = ["component", "status", "last_updated", "metrics"]
            for field in required_fields:
                assert field in audit_item

        # Check summary structure
        summary = data["summary"]
        assert "total_events" in summary
        assert "last_update" in summary
        assert "status" in summary


class TestTaskMonitoring:
    """Test cases for task monitoring endpoints."""

    def test_task_status_success(self, client, mock_celery_app):
        """Test successful task status retrieval."""
        mock_result = Mock()
        mock_result.state = "SUCCESS"
        mock_result.result = {"status": "completed", "data": "test"}
        mock_result.info = None
        mock_celery_app.AsyncResult.return_value = mock_result

        response = client.get("/api/tasks/test-task-id/status")

        assert response.status_code == 200
        data = response.json()
        assert data["task_id"] == "test-task-id"
        assert data["status"] == "SUCCESS"
        assert data["result"] == {"status": "completed", "data": "test"}

    def test_task_status_pending(self, client, mock_celery_app):
        """Test task status for pending task."""
        mock_result = Mock()
        mock_result.state = "PENDING"
        mock_result.result = None
        mock_result.info = None
        mock_celery_app.AsyncResult.return_value = mock_result

        response = client.get("/api/tasks/test-task-id/status")

        assert response.status_code == 200
        data = response.json()
        assert data["task_id"] == "test-task-id"
        assert data["status"] == "PENDING"

    def test_task_status_failure(self, client, mock_celery_app):
        """Test task status for failed task."""
        mock_result = Mock()
        mock_result.state = "FAILURE"
        mock_result.result = None
        mock_result.info = "Task failed with error"
        mock_celery_app.AsyncResult.return_value = mock_result

        response = client.get("/api/tasks/test-task-id/status")

        assert response.status_code == 200
        data = response.json()
        assert data["task_id"] == "test-task-id"
        assert data["status"] == "FAILURE"
        assert data["info"] == "Task failed with error"


class TestPydanticModels:
    """Test cases for Pydantic model validation."""

    def test_autopilot_engage_request_valid(self):
        """Test valid AutopilotEngageRequest model."""
        from api.fastapi_server import AutopilotEngageRequest
        
        request = AutopilotEngageRequest(
            action="start_trading",
            parameters={"risk_level": "medium"}
        )
        assert request.action == "start_trading"
        assert request.parameters is not None
        assert request.parameters["risk_level"] == "medium"

    def test_autopilot_engage_request_invalid(self):
        """Test invalid AutopilotEngageRequest model."""
        from api.fastapi_server import AutopilotEngageRequest
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            AutopilotEngageRequest(
                action="",  # Empty action should fail validation
                parameters={}
            )

    def test_retrodiction_run_request_valid(self):
        """Test valid RetrodictionRunRequest model."""
        from api.fastapi_server import RetrodictionRunRequest
        
        request = RetrodictionRunRequest(
            target_date="2024-01-15",
            parameters={"lookback_days": 30}
        )
        assert request.target_date == "2024-01-15"
        assert request.parameters is not None
        assert request.parameters["lookback_days"] == 30


class TestErrorHandling:
    """Test cases for error handling."""

    def test_404_not_found(self, client):
        """Test 404 error for non-existent endpoint."""
        response = client.get("/api/nonexistent")
        assert response.status_code == 404

    def test_method_not_allowed(self, client):
        """Test 405 error for wrong HTTP method."""
        response = client.put("/api/status")
        assert response.status_code == 405

    def test_celery_task_error_handling(self, client):
        """Test error handling when Celery task fails to start."""
        # This test needs to override the mock behavior set in the client fixture
        # We'll patch the celery_app.send_task method to raise an exception
        with patch('api.fastapi_server.celery_app') as mock_celery:
            mock_celery.send_task.side_effect = Exception("Celery connection error")

            payload = {
                "action": "start_trading",
                "parameters": {"risk_level": "medium"}
            }

            response = client.post("/api/autopilot/engage", json=payload)
            assert response.status_code == 500
            data = response.json()
            assert "Failed to engage autopilot" in data["detail"]


class TestIntegration:
    """Integration test cases."""

    def test_app_startup(self, client):
        """Test that the app starts up correctly."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"

    def test_openapi_docs(self, client):
        """Test that OpenAPI docs are accessible."""
        response = client.get("/docs")
        assert response.status_code == 200

    def test_openapi_json(self, client):
        """Test that OpenAPI JSON schema is accessible."""
        response = client.get("/openapi.json")
        assert response.status_code == 200
        data = response.json()
        assert "openapi" in data
        assert "info" in data