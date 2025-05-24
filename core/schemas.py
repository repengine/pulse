"""
schemas.py

Pydantic models for Pulse forecast, log, and config validation.
"""

from pydantic import BaseModel
from typing import Dict, Optional, Any


class ForecastRecord(BaseModel):
    forecast_id: str
    timestamp: Optional[str] = None
    variables: Optional[Dict[str, Any]] = None
    confidence: Optional[float] = None
    fragility: Optional[float] = None
    symbolic_overlay: Optional[str] = None
    trust_score: Optional[float] = None
    domain: Optional[str] = None
    # Add more fields as needed


class OverlayLog(BaseModel):
    overlay: str
    old_value: float
    new_value: float
    timestamp: str


class TrustScoreLog(BaseModel):
    scenario_id: str
    trust_score: float
    timestamp: str


class CapitalOutcome(BaseModel):
    scenario_id: str
    capital: float
    timestamp: str


class DigestTag(BaseModel):
    scenario_id: str
    tag: str
    timestamp: str


# Add more schemas as needed for other logs/configs
