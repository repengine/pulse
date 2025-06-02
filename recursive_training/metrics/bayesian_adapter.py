"""
BayesianAdapter

Adapter for integrating with Pulse's Bayesian trust system.
Provides bidirectional communication between the recursive training metrics
and Pulse's trust tracking mechanism.
"""

import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

# Import typing types including Any for handling potential unknown types
from typing import TypeVar, cast
from recursive_training.metrics.metrics_store import get_metrics_store

# Try to import Pulse's Bayesian trust tracker with graceful fallback
try:
    from analytics.bayesian_trust_tracker import bayesian_trust_tracker

    TRUST_TRACKER_AVAILABLE = True
except ImportError:
    TRUST_TRACKER_AVAILABLE = False
    # Define a placeholder for type checking
    bayesian_trust_tracker = None

# Define a generic trust tracker type for type hints
TrustTrackerType = TypeVar("TrustTrackerType")


class BayesianAdapter:
    """
    Adapter for Pulse's Bayesian trust system.

    Features:
    - Translate metrics to trust scores
    - Update Pulse's trust system based on performance metrics
    - Retrieve trust scores for specific rules or models
    - Track trust evolution over time
    - Handle trust-based decision making
    - Support hybrid rules evaluation
    """

    """
    Adapter for Pulse's Bayesian trust system.
    
    Features:
    - Translate metrics to trust scores
    - Update Pulse's trust system based on performance metrics
    - Retrieve trust scores for specific rules or models
    - Track trust evolution over time
    - Handle trust-based decision making
    - Support hybrid rules evaluation
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the BayesianAdapter.

        Args:
            config: Optional configuration dictionary
        """
        self.logger = logging.getLogger("BayesianAdapter")
        self.config = config or {}
        self.metrics_store = get_metrics_store(config)

        # Check if Pulse's trust tracker is available
        if not TRUST_TRACKER_AVAILABLE:
            self.logger.warning(
                "Pulse's Bayesian trust tracker not available, using fallback implementation"
            )
            self.trust_tracker: Any = FallbackTrustTracker()
        else:
            # Initialize with the imported trust tracker
            self.trust_tracker: Any = cast(Any, bayesian_trust_tracker)

        # Configure trust calculation settings
        self.error_weight = self.config.get("error_weight", 0.7)
        self.cost_weight = self.config.get("cost_weight", 0.3)
        self.min_confidence = self.config.get("min_confidence", 0.1)
        self.max_confidence = self.config.get("max_confidence", 0.9)
        self.trust_decay_rate = self.config.get("trust_decay_rate", 0.05)

        # Track historical trust scores
        self.trust_history = {}

    def get_trust_score(self, entity_id: str) -> float:
        """
        Get the current trust score for an entity.

        Args:
            entity_id: ID of the entity (rule, model, etc.)

        Returns:
            Trust score between 0.0 and 1.0
        """
        try:
            # Check if the method exists - use Any type to bypass type checking
            tracker = cast(Any, self.trust_tracker)
            if hasattr(tracker, "get_trust"):
                return tracker.get_trust(entity_id)
            else:
                self.logger.warning(
                    f"Trust tracker doesn't have get_trust method for {entity_id}"
                )
                return 0.5
        except Exception as e:
            self.logger.error(f"Error getting trust score for {entity_id}: {e}")
            # Return default neutral trust score on error
            return 0.5

    def update_trust_from_metrics(
        self,
        entity_id: str,
        metrics: Dict[str, float],
        weight: float = 1.0,
        tags: Optional[List[str]] = None,
    ) -> float:
        """
        Update trust score based on performance metrics.

        Args:
            entity_id: ID of the entity (rule, model, etc.)
            metrics: Dictionary of performance metrics
            weight: Weight of this update (0.0-1.0)
            tags: Optional tags for filtering

        Returns:
            Updated trust score
        """
        # Calculate normalized performance score from metrics
        performance_score = self._calculate_performance_score(metrics)

        # Update trust in Pulse's system
        try:
            prior_trust = self.get_trust_score(entity_id)

            # Use Any type to bypass type checking
            tracker = cast(Any, self.trust_tracker)

            # Update trust score in Pulse's trust system
            if hasattr(tracker, "update_trust"):
                # Call the method directly if it exists
                try:
                    updated_trust = tracker.update_trust(
                        entity_id, performance_score, weight
                    )
                except Exception as e:
                    self.logger.warning(
                        f"Error calling update_trust: {e}, using fallback"
                    )
                    updated_trust = self._fallback_update_trust(
                        entity_id, prior_trust, performance_score, weight
                    )
            else:
                # Fallback if specific update method isn't available
                updated_trust = self._fallback_update_trust(
                    entity_id, prior_trust, performance_score, weight
                )

            # Record the trust update
            self._record_trust_update(
                entity_id, prior_trust, updated_trust, performance_score, metrics, tags
            )

            return updated_trust

        except Exception as e:
            self.logger.error(f"Error updating trust for {entity_id}: {e}")
            return self.get_trust_score(entity_id)

    def _fallback_update_trust(
        self,
        entity_id: str,
        prior_trust: float,
        performance_score: float,
        weight: float,
    ) -> float:
        """
        Fallback trust update when Pulse's system isn't available.

        Args:
            entity_id: ID of the entity
            prior_trust: Previous trust score
            performance_score: New performance score
            weight: Weight of this update

        Returns:
            Updated trust score
        """
        # Simple weighted average as fallback
        updated_trust = (prior_trust * (1 - weight)) + (performance_score * weight)

        # Ensure trust is within valid range
        updated_trust = max(0.0, min(1.0, updated_trust))

        # Store in the tracker if possible
        tracker = cast(Any, self.trust_tracker)
        if hasattr(tracker, "set_trust"):
            try:
                tracker.set_trust(entity_id, updated_trust)
            except Exception as e:
                self.logger.warning(f"Error calling set_trust: {e}")

        return updated_trust

    def _calculate_performance_score(self, metrics: Dict[str, float]) -> float:
        """
        Calculate normalized performance score from metrics.

        Args:
            metrics: Dictionary of performance metrics

        Returns:
            Normalized performance score (0.0-1.0)
        """
        # Initialize components
        error_score = 0.5
        cost_score = 0.5

        # Calculate error-based score component
        if "mse" in metrics or "rmse" in metrics or "mae" in metrics:
            # Prioritize which error metric to use
            if "rmse" in metrics:
                error_value = metrics["rmse"]
            elif "mse" in metrics:
                error_value = metrics["mse"]
            else:
                error_value = metrics["mae"]

            # Simple inverse normalization for error (lower is better)
            max_error = self.config.get("max_error", 10.0)
            error_score = 1.0 - min(error_value / max_error, 1.0)

        # Calculate accuracy-based score component
        elif "accuracy" in metrics:
            # Accuracy is already normalized
            error_score = metrics["accuracy"]

        # Calculate cost-based score component
        if "cost" in metrics:
            # Simple inverse normalization for cost (lower is better)
            max_cost = self.config.get("max_cost", 1.0)
            cost_score = 1.0 - min(metrics["cost"] / max_cost, 1.0)

        # Combine components with weights
        performance_score = (error_score * self.error_weight) + (
            cost_score * self.cost_weight
        )

        # Ensure score is within valid range
        return max(0.0, min(1.0, performance_score))

    def _record_trust_update(
        self,
        entity_id: str,
        prior_trust: float,
        updated_trust: float,
        performance_score: float,
        metrics: Dict[str, float],
        tags: Optional[List[str]] = None,
    ) -> None:
        """
        Record a trust update for tracking and analysis.

        Args:
            entity_id: ID of the entity
            prior_trust: Previous trust score
            updated_trust: New trust score
            performance_score: Calculated performance score
            metrics: Original metrics dictionary
            tags: Optional tags for filtering
        """
        timestamp = datetime.now(timezone.utc).isoformat()

        # Add to local history
        if entity_id not in self.trust_history:
            self.trust_history[entity_id] = []

        self.trust_history[entity_id].append(
            {
                "timestamp": timestamp,
                "prior_trust": prior_trust,
                "updated_trust": updated_trust,
                "performance_score": performance_score,
                "metrics": metrics,
            }
        )

        # Trim history if too large
        max_history = self.config.get("max_history_per_entity", 100)
        if len(self.trust_history[entity_id]) > max_history:
            self.trust_history[entity_id] = self.trust_history[entity_id][-max_history:]

        # Store in metrics store
        trust_data = {
            "timestamp": timestamp,
            "metric_type": "trust_update",
            "entity_id": entity_id,
            "prior_trust": prior_trust,
            "updated_trust": updated_trust,
            "performance_score": performance_score,
            "metrics": metrics,
            "tags": tags or [],
        }

        self.metrics_store.store_metric(trust_data)

    def batch_update_trust(
        self, metrics_by_entity: Dict[str, Dict[str, float]], weight: float = 1.0
    ) -> Dict[str, float]:
        """
        Update trust scores for multiple entities in batch.

        Args:
            metrics_by_entity: Dictionary mapping entity IDs to their metrics
            weight: Weight of this update

        Returns:
            Dictionary of updated trust scores by entity ID
        """
        results = {}

        for entity_id, metrics in metrics_by_entity.items():
            updated_trust = self.update_trust_from_metrics(
                entity_id, metrics, weight, tags=["batch_update"]
            )
            results[entity_id] = updated_trust

        return results

    def get_trust_history(
        self, entity_id: str, limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Get trust history for an entity.

        Args:
            entity_id: ID of the entity
            limit: Maximum number of records to return

        Returns:
            List of historical trust records
        """
        if entity_id not in self.trust_history:
            return []

        history = sorted(
            self.trust_history[entity_id], key=lambda x: x["timestamp"], reverse=True
        )

        if limit is not None and limit > 0:
            history = history[:limit]

        return history

    def calculate_confidence(
        self, entity_id: str, default_confidence: float = 0.5
    ) -> float:
        """
        Calculate confidence in trust score based on history.

        Args:
            entity_id: ID of the entity
            default_confidence: Default confidence if history is insufficient

        Returns:
            Confidence score (0.0-1.0)
        """
        history = self.get_trust_history(entity_id)

        if not history:
            return default_confidence

        # More history gives higher confidence, up to a maximum
        history_confidence = min(len(history) / 10, 1.0)

        # Consistency in scores gives higher confidence
        if len(history) >= 3:
            trust_values = [record["updated_trust"] for record in history[:5]]
            variance = sum(
                (x - sum(trust_values) / len(trust_values)) ** 2 for x in trust_values
            ) / len(trust_values)
            consistency_confidence = 1.0 - min(
                variance * 4, 1.0
            )  # Scale variance impact
        else:
            consistency_confidence = 0.5

        # Combine factors
        confidence = (history_confidence * 0.6) + (consistency_confidence * 0.4)

        # Apply configured limits
        return max(self.min_confidence, min(self.max_confidence, confidence))

    def get_trusted_entities(
        self,
        threshold: float = 0.7,
        confidence_threshold: float = 0.5,
        tags: Optional[List[str]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Get entities that exceed a trust threshold.

        Args:
            threshold: Minimum trust score
            confidence_threshold: Minimum confidence score
            tags: Optional tags to filter by

        Returns:
            List of trusted entities with metadata
        """
        # Query metrics store for trust updates
        metrics = self.metrics_store.query_metrics(
            metric_types=["trust_update"], tags=tags
        )

        # Extract unique entity IDs
        entity_ids = set()
        for metric in metrics:
            entity_id = metric.get("entity_id")
            if entity_id:
                entity_ids.add(entity_id)

        # Check current trust for each entity
        trusted_entities = []
        for entity_id in entity_ids:
            trust_score = self.get_trust_score(entity_id)
            confidence = self.calculate_confidence(entity_id)

            if trust_score >= threshold and confidence >= confidence_threshold:
                trusted_entities.append(
                    {
                        "entity_id": entity_id,
                        "trust_score": trust_score,
                        "confidence": confidence,
                        "history": self.get_trust_history(entity_id, limit=5),
                    }
                )

        # Sort by trust score (highest first)
        trusted_entities.sort(key=lambda x: x["trust_score"], reverse=True)

        return trusted_entities

    def decay_trust_over_time(
        self, decay_factor: Optional[float] = None
    ) -> Dict[str, float]:
        """
        Apply time-based decay to trust scores that haven't been updated recently.

        Args:
            decay_factor: Optional override for decay rate

        Returns:
            Dictionary of updated trust scores
        """
        decay = decay_factor or self.trust_decay_rate
        results = {}
        now = datetime.now(timezone.utc)

        # Query metrics store for most recent trust updates
        metrics = self.metrics_store.query_metrics(metric_types=["trust_update"])

        # Group by entity and find most recent update
        latest_updates = {}
        for metric in metrics:
            entity_id = metric.get("entity_id")
            timestamp_str = metric.get("timestamp")

            if not entity_id or not timestamp_str:
                continue

            try:
                timestamp = datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
                if (
                    entity_id not in latest_updates
                    or timestamp > latest_updates[entity_id]["timestamp"]
                ):
                    latest_updates[entity_id] = {
                        "timestamp": timestamp,
                        "trust": metric.get("updated_trust", 0.5),
                    }
            except Exception as e:
                self.logger.error(f"Error parsing timestamp for {entity_id}: {e}")

        # Apply decay based on time since last update
        for entity_id, data in latest_updates.items():
            days_since_update = (now - data["timestamp"]).days
            current_trust = self.get_trust_score(entity_id)

            # Only decay if significant time has passed
            if days_since_update > 0:
                # Calculate decay (move toward neutral 0.5)
                if current_trust > 0.5:
                    new_trust = max(0.5, current_trust - (decay * days_since_update))
                else:
                    new_trust = min(0.5, current_trust + (decay * days_since_update))

                # Update trust score
                tracker = cast(Any, self.trust_tracker)
                if hasattr(tracker, "set_trust"):
                    try:
                        tracker.set_trust(entity_id, new_trust)
                        results[entity_id] = new_trust
                    except Exception as e:
                        self.logger.error(
                            f"Error updating decayed trust for {entity_id}: {e}"
                        )
                        results[entity_id] = current_trust
                else:
                    # Can't update without set_trust method
                    self.logger.warning(
                        f"Trust tracker doesn't have set_trust method for {entity_id}"
                    )
                    results[entity_id] = current_trust
            else:
                # No decay needed
                results[entity_id] = current_trust

        return results


class FallbackTrustTracker:
    """
    Fallback implementation when Pulse's trust tracker isn't available.
    """

    def __init__(self):
        """Initialize the fallback trust tracker."""
        self.trust_scores = {}
        self.logger = logging.getLogger("FallbackTrustTracker")

    def get_trust(self, entity_id: str) -> float:
        """
        Get trust score for an entity.

        Args:
            entity_id: ID of the entity

        Returns:
            Trust score (0.0-1.0)
        """
        return self.trust_scores.get(entity_id, 0.5)

    def set_trust(self, entity_id: str, trust_score: float) -> None:
        """
        Set trust score for an entity.

        Args:
            entity_id: ID of the entity
            trust_score: New trust score
        """
        self.trust_scores[entity_id] = max(0.0, min(1.0, trust_score))

    def update_trust(
        self, entity_id: str, evidence: float, weight: float = 1.0
    ) -> float:
        """
        Update trust based on new evidence.

        Args:
            entity_id: ID of the entity
            evidence: New evidence score (0.0-1.0)
            weight: Weight of the evidence

        Returns:
            Updated trust score
        """
        current_trust = self.get_trust(entity_id)
        updated_trust = (current_trust * (1 - weight)) + (evidence * weight)
        updated_trust = max(0.0, min(1.0, updated_trust))

        self.set_trust(entity_id, updated_trust)
        return updated_trust
