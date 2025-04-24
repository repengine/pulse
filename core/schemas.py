"""
schemas.py

Pydantic models for Pulse forecast, log, and config validation.
"""
from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Any
from datetime import datetime

class ForecastRecord(BaseModel):
    forecast_id: str
    timestamp: str
    variables: Dict[str, Any]
    confidence: Optional[float]
    fragility: Optional[float]
    symbolic_overlay: Optional[str]
    trust_score: Optional[float]
    domain: Optional[str]
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
