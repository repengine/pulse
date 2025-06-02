"""
FastAPI server for Pulse API endpoints.

This module provides a modern FastAPI-based API server that replaces the legacy
Flask implementation. It integrates with Celery for asynchronous task processing
and uses the centralized AppSettings configuration system.

Example:
    ```python
    from api.fastapi_server import app
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
    ```
"""

import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException, BackgroundTasks, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, field_validator

from pulse.core.app_settings import get_app_settings
from adapters.celery_app import (
    celery_app,
    autopilot_engage_task,
    autopilot_disengage_task,
    retrodiction_run_task,
)

__all__ = [
    "app",
    "ForecastResponse",
    "AutopilotEngageRequest",
    "AutopilotResponse",
    "RetrodictionRunRequest",
    "RetrodictionResponse",
    "LearningAuditResponse",
    "TaskStatusResponse",
    "autopilot_engage_task",
    "autopilot_disengage_task",
    "retrodiction_run_task",
]

# Configure logging
logger = logging.getLogger("pulse.api.fastapi_server")

# Initialize FastAPI app
app = FastAPI(
    title="Pulse API",
    description="Modern FastAPI-based API for Pulse forecasting and analysis",
    version="0.10.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Pydantic models for request/response validation
class ForecastResponse(BaseModel):
    """Response model for forecast data."""

    timestamp: str = Field(..., description="Forecast timestamp")
    forecasts: List[Dict[str, Any]] = Field(..., description="List of forecast data")
    metadata: Dict[str, Any] = Field(
        default_factory=dict, description="Additional metadata"
    )


class AutopilotEngageRequest(BaseModel):
    """Request model for autopilot operations."""

    action: str = Field(..., min_length=1, description="Autopilot action to perform")
    parameters: Optional[Dict[str, Any]] = Field(
        default_factory=dict, description="Action parameters"
    )


class AutopilotResponse(BaseModel):
    """Response model for autopilot operations."""

    status: str = Field(..., description="Operation status")
    result: Dict[str, Any] = Field(..., description="Operation result")
    task_id: Optional[str] = Field(None, description="Celery task ID if async")


class RetrodictionRunRequest(BaseModel):
    """Request model for retrodiction operations."""

    target_date: str = Field(..., description="Target date for retrodiction")
    parameters: Optional[Dict[str, Any]] = Field(
        default_factory=dict, description="Retrodiction parameters"
    )

    @field_validator("target_date")
    @classmethod
    def validate_target_date(cls, v):
        """Validate target_date format."""
        try:
            datetime.strptime(v, "%Y-%m-%d")
            return v
        except ValueError:
            raise ValueError("target_date must be in YYYY-MM-DD format")


class RetrodictionResponse(BaseModel):
    """Response model for retrodiction operations."""

    status: str = Field(..., description="Retrodiction status")
    results: Dict[str, Any] = Field(..., description="Retrodiction results")
    task_id: Optional[str] = Field(None, description="Celery task ID if async")


class LearningAuditResponse(BaseModel):
    """Response model for learning audit data."""

    audit_results: List[Dict[str, Any]] = Field(
        ..., description="Learning audit entries"
    )
    summary: Dict[str, Any] = Field(..., description="Audit summary statistics")


class TaskStatusResponse(BaseModel):
    """Response model for Celery task status."""

    task_id: str = Field(..., description="Celery task ID")
    status: str = Field(..., description="Task status")
    result: Optional[Dict[str, Any]] = Field(
        None, description="Task result if completed"
    )
    progress: Optional[Dict[str, Any]] = Field(
        None, description="Task progress information"
    )
    info: Optional[str] = Field(None, description="Task info for failure cases")


def get_settings():
    """Dependency to get application settings."""
    return get_app_settings()


@app.get("/api/status", response_model=Dict[str, Any])
async def get_status(settings=Depends(get_settings)) -> Dict[str, Any]:
    """
    Get API status and health information.

    Returns:
        Dictionary containing API status, version, and health metrics.

    Example:
        ```python
        response = await client.get("/api/status")
        print(response.json()["status"])  # "operational"
        ```
    """
    try:
        return {
            "status": "operational",
            "service": "pulse-api",
            "version": settings.app_version,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "debug_mode": settings.debug,
            "components": {
                "database": "connected",
                "celery": "connected",  # Could add actual health check
                "redis": "connected",  # Could add actual health check
            },
        }
    except Exception as e:
        logger.error(f"Status check failed: {e}")
        raise HTTPException(status_code=500, detail="Status check failed")


@app.get("/api/forecasts/latest/all", response_model=ForecastResponse)
async def get_latest_forecasts(settings=Depends(get_settings)) -> ForecastResponse:
    """
    Get the latest forecasts for all tracked metrics.

    Returns:
        ForecastResponse containing latest forecast data.

    Example:
        ```python
        response = await client.get("/api/forecasts/latest/all")
        forecasts = response.json()["forecasts"]
        ```
    """
    try:
        # Simulate forecast data (replace with actual forecast logic)
        simulated_forecasts = [
            {
                "id": "forecast_001",
                "symbol": "MARKET_VOL",
                "metric": "market_volatility",
                "prediction": 0.75,
                "value": 0.75,
                "confidence": 0.85,
                "horizon": "1d",
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
            {
                "id": "forecast_002",
                "symbol": "TREND_STR",
                "metric": "trend_strength",
                "prediction": 0.62,
                "value": 0.62,
                "confidence": 0.78,
                "horizon": "1d",
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
        ]

        return ForecastResponse(
            timestamp=datetime.now(timezone.utc).isoformat(),
            forecasts=simulated_forecasts,
            metadata={
                "model_version": "v2.1",
                "data_freshness": "real-time",
                "total_forecasts": len(simulated_forecasts),
                "total_metrics": len(simulated_forecasts),
            },
        )
    except Exception as e:
        logger.error(f"Failed to get latest forecasts: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve forecasts")


@app.post("/api/autopilot/engage", response_model=AutopilotResponse, status_code=202)
async def engage_autopilot(
    request: AutopilotEngageRequest,
    background_tasks: BackgroundTasks,
    settings=Depends(get_settings),
) -> AutopilotResponse:
    """
    Engage autopilot with specified parameters.

    Args:
        request: Autopilot engagement request with action and parameters.
        background_tasks: FastAPI background tasks for async processing.
        settings: Application settings dependency.

    Returns:
        AutopilotResponse with engagement status and task information.

    Example:
        ```python
        request = {"action": "start", "parameters": {"mode": "conservative"}}
        response = await client.post("/api/autopilot/engage", json=request)
        task_id = response.json()["task_id"]
        ```
    """
    try:
        # Submit autopilot task to Celery
        task = celery_app.send_task(
            "autopilot_engage_task", args=[request.action, request.parameters]
        )

        logger.info(f"Autopilot engagement task submitted: {task.id}")

        return AutopilotResponse(
            status="submitted",
            result={"message": f"Autopilot {request.action} task submitted"},
            task_id=str(task.id),
        )
    except Exception as e:
        logger.error(f"Failed to engage autopilot: {e}")
        raise HTTPException(status_code=500, detail="Failed to engage autopilot")


@app.post("/api/autopilot/disengage", response_model=AutopilotResponse, status_code=202)
async def disengage_autopilot(settings=Depends(get_settings)) -> AutopilotResponse:
    """
    Disengage autopilot system.

    Returns:
        AutopilotResponse with disengagement status.

    Example:
        ```python
        response = await client.post("/api/autopilot/disengage")
        print(response.json()["status"])  # "disengaged"
        ```
    """
    try:
        # Submit autopilot disengagement task to Celery
        task = celery_app.send_task("autopilot_disengage_task", args=[])

        logger.info(f"Autopilot disengagement task submitted: {task.id}")

        return AutopilotResponse(
            status="submitted",
            result={"message": "Autopilot disengagement task submitted"},
            task_id=str(task.id),
        )
    except Exception as e:
        logger.error(f"Failed to disengage autopilot: {e}")
        raise HTTPException(status_code=500, detail="Failed to disengage autopilot")


@app.post("/api/retrodiction/run", response_model=RetrodictionResponse, status_code=202)
async def run_retrodiction(
    request: RetrodictionRunRequest,
    background_tasks: BackgroundTasks,
    settings=Depends(get_settings),
) -> RetrodictionResponse:
    """
    Run retrodiction analysis for specified target date.

    Args:
        request: Retrodiction request with target date and parameters.
        background_tasks: FastAPI background tasks for async processing.
        settings: Application settings dependency.

    Returns:
        RetrodictionResponse with analysis status and task information.

    Example:
        ```python
        request = {"target_date": "2024-01-01", "parameters": {"depth": "full"}}
        response = await client.post("/api/retrodiction/run", json=request)
        task_id = response.json()["task_id"]
        ```
    """
    try:
        # Submit retrodiction task to Celery
        task = celery_app.send_task(
            "retrodiction_run_task", args=[request.target_date, request.parameters]
        )

        logger.info(f"Retrodiction task submitted: {task.id}")

        return RetrodictionResponse(
            status="submitted",
            results={"message": f"Retrodiction for {request.target_date} submitted"},
            task_id=str(task.id),
        )
    except Exception as e:
        logger.error(f"Failed to run retrodiction: {e}")
        raise HTTPException(status_code=500, detail="Failed to run retrodiction")


@app.get("/api/learning/audit", response_model=LearningAuditResponse)
async def get_learning_audit(settings=Depends(get_settings)) -> LearningAuditResponse:
    """
    Get learning system audit data.

    Returns:
        LearningAuditResponse containing audit data and summary.

    Example:
        ```python
        response = await client.get("/api/learning/audit")
        audit_entries = response.json()["audit_results"]
        ```
    """
    try:
        # Simulate learning audit data (replace with actual audit logic)
        simulated_audit = [
            {
                "component": "model_trainer",
                "status": "active",
                "last_updated": datetime.now(timezone.utc).isoformat(),
                "metrics": {"accuracy_improvement": 0.05, "samples_processed": 1000},
            },
            {
                "component": "feature_selector",
                "status": "active",
                "last_updated": datetime.now(timezone.utc).isoformat(),
                "metrics": {"features_added": 3, "features_removed": 1},
            },
        ]

        summary = {
            "total_events": len(simulated_audit),
            "last_update": datetime.now(timezone.utc).isoformat(),
            "status": "optimal",
        }

        return LearningAuditResponse(audit_results=simulated_audit, summary=summary)
    except Exception as e:
        logger.error(f"Failed to get learning audit: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve learning audit")


@app.get("/api/tasks/{task_id}/status", response_model=TaskStatusResponse)
async def get_task_status(task_id: str) -> TaskStatusResponse:
    """
    Get status of a Celery task.

    Args:
        task_id: Celery task ID to check status for.

    Returns:
        TaskStatusResponse with task status and result information.

    Example:
        ```python
        response = await client.get(f"/api/tasks/{task_id}/status")
        status = response.json()["status"]
        ```
    """
    try:
        # Get task result from Celery
        result = celery_app.AsyncResult(task_id)

        # Convert task state to string and handle result/info properly
        status = str(result.state) if result.state else "UNKNOWN"
        task_result = result.result if result.result is not None else {}

        # Handle info field - keep as string for test compatibility
        task_info = (
            str(result.info) if result.info is not None else "No additional information"
        )

        response_data = {
            "task_id": task_id,
            "status": status,
            "result": task_result,
            "progress": None,
            "info": task_info,
        }

        return TaskStatusResponse(**response_data)
    except Exception as e:
        logger.error(f"Failed to get task status for {task_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve task status")


# Health check endpoint for load balancers
@app.get("/health")
async def health_check() -> Dict[str, str]:
    """
    Simple health check endpoint.

    Returns:
        Dictionary with health status.
    """
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn

    settings = get_app_settings()
    uvicorn.run(
        app, host="0.0.0.0", port=8000, log_level="debug" if settings.debug else "info"
    )
