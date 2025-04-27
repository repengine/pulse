"""
pulsegrow.py

PulseGrow — Variable Evolution Engine

This module introduces new candidate variables into Pulse simulations, evaluates their performance over time, and selectively promotes them to core memory if they enhance forecast clarity, symbolic richness, or capital foresight.

Key Features:
- Candidate variable registration
- Performance scoring via PFPA and SUS deltas
- Symbolic correlation testing
- Promotion gating with audit trace
- Soft memory retention for unpromoted variables
- Registry integration with variable_registry.py

Author: Pulse v0.304
"""

import logging
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

class PulseGrow:
    def __init__(self):
        self.candidates: Dict[str, Dict] = {}
        self.promoted: List[str] = []
        self.rejected: List[str] = []

    def register_variable(self, name: str, meta: Optional[Dict] = None, metadata: Optional[Dict] = None, **kwargs):
        """Register a new variable for evaluation. Accepts both 'meta' and 'metadata' for compatibility."""
        # Prefer 'meta' if provided, else 'metadata'
        meta = meta or metadata or {}
        if name in self.candidates:
            logger.warning("[PulseGrow] Variable %s already registered.", name)
            return
        self.candidates[name] = {
            "name": name,
            "metadata": meta,
            "scores": [],
            "symbolic_links": [],
            "attempts": 0
        }
        logger.info("[PulseGrow] Registered candidate variable: %s", name)

    def score_variable(self, name: str, score: float, symbolic_link: Optional[str] = None):
        """Log a new score for a variable. Optionally track symbolic linkage."""
        if name not in self.candidates:
            logger.warning("[PulseGrow] Attempted to score unknown variable: %s", name)
            return
        self.candidates[name]["scores"].append(score)
        self.candidates[name]["attempts"] += 1
        if symbolic_link:
            self.candidates[name]["symbolic_links"].append(symbolic_link)

    def evaluate_and_promote(self, threshold: float = 0.7, min_attempts: int = 3):
        """Evaluate all candidates for promotion to core variables"""
        for name, data in self.candidates.items():
            if data["attempts"] < min_attempts:
                continue
            avg_score = sum(data["scores"]) / max(len(data["scores"]), 1)
            if avg_score >= threshold:
                self.promoted.append(name)
                logger.info("[PulseGrow] Promoted variable: %s with score %.2f", name, avg_score)
            else:
                self.rejected.append(name)
                logger.info("[PulseGrow] Rejected variable: %s with score %.2f", name, avg_score)

    def promote_to_registry(self):
        """Promote all eligible variables into the canonical registry."""
        try:
            from core.variable_registry import VariableRegistry
            vr = VariableRegistry()
            for name in self.promoted:
                if vr.get(name) is None:
                    vr.register_variable(name, {
                        "type": "experimental",
                        "description": "Auto-promoted from PulseGrow",
                        "default": 0.0,
                        "range": [0.0, 1.0]
                    })
                    logger.info("[PulseGrow] Promoted %s to VARIABLE_REGISTRY", name)
        except Exception as e:
            logger.error("[PulseGrow] Registry promotion failed: %s", e)

    def export_audit(self) -> Dict[str, List[str]]:
        """Export the final promotion results"""
        return {
            "promoted": self.promoted,
            "rejected": self.rejected,
            "candidates": list(self.candidates.keys())
        }

    def auto_tick(self):
        """Evaluate and promote variables on periodic simulation ticks"""
        self.evaluate_and_promote()
        self.promote_to_registry()

    def score_from_forecast(self, variable: str, confidence: float, fragility: float):
        """Score a variable using forecast confidence and fragility."""
        score = confidence * (1 - fragility)
        self.score_variable(variable, score)

    def link_symbolic_events(self, var: str, symbolic_event: str):
        """Score variable for symbolic linkage to high-signal events."""
        self.score_variable(var, 0.8, symbolic_link=symbolic_event)

    def log_failed_candidate(self, name: str, reason: str = ""):
        """Log a failed candidate variable for later review (PulseMemory stub)."""
        # This would append to a persistent memory or file in a real implementation
        logger.info(f"[PulseGrow] Logging failed candidate: {name} | Reason: {reason}")
        # Example: PulseMemory.add_failed_candidate(name, reason)

    def track_anomaly(self, name: str, sti: Optional[float] = None, volatility: Optional[float] = None):
        """Flag variable as anomaly-prone based on STI/volatility."""
        if name in self.candidates:
            self.candidates[name]["anomaly_flag"] = True
            self.candidates[name]["sti"] = sti
            self.candidates[name]["volatility"] = volatility
            logger.info(f"[PulseGrow] Anomaly tracked for {name}: STI={sti}, Volatility={volatility}")

    def score_from_scraper(self, name: str, sti: float, volatility: float, sti_threshold: float = 0.7, vol_threshold: float = 0.5):
        """Score variable based on STI/volatility from scraper logic."""
        score = 0.0
        if sti > sti_threshold:
            score += 0.5
        if volatility > vol_threshold:
            score += 0.5
        self.score_variable(name, score)
        if score == 0.0:
            self.log_failed_candidate(name, reason="Low STI/volatility")
        if sti > sti_threshold or volatility > vol_threshold:
            self.track_anomaly(name, sti, volatility)

    def memory_feedback_loop(self, cycles: int = 5):
        """Feedback loop: soft-retire/archive variables not promoted after X cycles."""
        # This would be called periodically (e.g., at end of simulation batch)
        for name, data in self.candidates.items():
            if name in self.promoted:
                continue
            if data.get("attempts", 0) >= cycles:
                data["status"] = "soft_retired"
                logger.info(f"[PulseGrow] Soft-retired variable: {name}")
                # Archive as 'variable fossil' (stub)
                # PulseMemory.archive_variable_fossil(name, data)
                # Optionally reconsider under different symbolic regime (stub)
                # self.reconsider_variable(name, regime="alternate")

class PulseGrowAuditRunner:
    """Scaffold for reviewing PulseGrow candidates and thresholds."""
    def __init__(self, pulsegrow: PulseGrow):
        self.pulsegrow = pulsegrow

    def review_candidates(self):
        """Prints a summary of candidate variables and their scores."""
        for name, data in self.pulsegrow.candidates.items():
            avg_score = sum(data["scores"]) / max(len(data["scores"]), 1)
            print(f"Candidate: {name} | Attempts: {data['attempts']} | Avg Score: {avg_score:.2f} | Symbolic Links: {len(data['symbolic_links'])}")

    def review_thresholds(self, threshold: float = 0.7, min_attempts: int = 3):
        """Show which candidates would be promoted/rejected under given thresholds."""
        for name, data in self.pulsegrow.candidates.items():
            if data["attempts"] < min_attempts:
                status = "pending"
            else:
                avg_score = sum(data["scores"]) / max(len(data["scores"]), 1)
                status = "promote" if avg_score >= threshold else "reject"
            print(f"{name}: {status}")
