"""
pulse_learning_log.py

Logs and persists all structural learning updates made by Pulse,
including variable trust changes, symbolic upgrades, revisions,
and overlay drift metrics.

Used for:
- Replay and diagnostics
- Meta-learning audit trails
- Visual summaries and evolution history

Author: Pulse v0.31

Security Note:
  Do not log sensitive or personally identifiable information. All log data should be safe for audit and review.
"""

import os
import json
import uuid
from typing import Any, Dict, Optional
from datetime import datetime, timezone
from contextlib import suppress
from engine.path_registry import PATHS

# Add import for Bayesian trust tracker
from analytics.bayesian_trust_tracker import bayesian_trust_tracker


def _get_log_path() -> str:
    """
    Returns the path to the learning log file, allowing override via environment variable.
    """
    return os.environ.get(
        "PULSE_LEARNING_LOG_PATH",
        str(PATHS.get("LEARNING_LOG", "logs/pulse_learning_log.jsonl")),
    )


LOG_PATH = _get_log_path()
os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)


def _set_file_permissions(path: str):
    """
    Restricts log file permissions to owner read/write only (where supported).
    """
    with suppress(Exception):
        os.chmod(path, 0o600)


class PulseLearningLogger:
    """
    Singleton logger for Pulse learning events.
    """

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(PulseLearningLogger, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        self.log_path = LOG_PATH
        # Set file permissions on creation
        if not os.path.exists(self.log_path):
            with open(self.log_path, "a", encoding="utf-8"):
                pass
            _set_file_permissions(self.log_path)

    def log_event(
        self,
        event_type: str,
        data: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Logs a meta-learning event with timestamp, event type, and unique event ID.

        Args:
            event_type (str): Type of the event.
            data (dict): Event-specific data.
            context (dict, optional): Additional context for the event.
        """
        entry = {
            "event_id": str(uuid.uuid4()),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "event_type": event_type,
            "data": data,
        }
        if context:
            entry["context"] = context
        try:
            with open(self.log_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(entry, ensure_ascii=False) + "\n")
                f.flush()
                os.fsync(f.fileno())
        except (OSError, IOError) as e:
            print(f"[LearningLog] File I/O error: {e}")
        except Exception as e:
            print(f"[LearningLog] Failed to log event: {e}")

    # --- Event-specific logging methods ---

    def log_variable_weight_change(
        self, var: str, old_weight: float, new_weight: float
    ):
        """
        Logs a variable weight update event.

        Args:
            var (str): Variable name.
            old_weight (float): Previous weight.
            new_weight (float): Updated weight.
        """
        if (
            not isinstance(var, str)
            or not isinstance(old_weight, (float, int))
            or not isinstance(new_weight, (float, int))
        ):
            raise ValueError("Invalid types for variable weight change log.")
        self.log_event(
            "variable_weight_update",
            {"variable": var, "from": float(old_weight), "to": float(new_weight)},
        )

    def log_symbolic_upgrade(self, plan: Dict[str, Any]):
        """
        Logs a symbolic upgrade event.

        Args:
            plan (dict): Upgrade plan details.
        """
        self.log_event("symbolic_upgrade_applied", {"changes": plan})

    def log_revision_trigger(self, reason: str):
        """
        Logs a symbolic revision trigger event.

        Args:
            reason (str): Reason for revision.
        """
        self.log_event("symbolic_revision_triggered", {"reason": reason})

    def log_arc_regret(self, scores: Dict[str, float]):
        """
        Logs symbolic arc regret scores.

        Args:
            scores (dict): Regret scores.
        """
        self.log_event("symbolic_arc_regret", {"regret_scores": scores})

    def log_learning_summary(self, summary: Dict[str, Any]):
        """
        Logs a meta-learning summary.

        Args:
            summary (dict): Summary data.
        """
        self.log_event("meta_learning_summary", summary)

    def log_rule_activation(
        self,
        rule_id: str,
        variable_id: str,
        outcome: str,
        forecast_id: Optional[str] = None,
        success: Optional[bool] = None,
    ):
        """
        Logs a rule/variable activation and outcome for Bayesian trust/confidence tracking.

        Args:
            rule_id (str): Rule identifier.
            variable_id (str): Variable identifier (if applicable).
            outcome (str): Outcome label (e.g., 'success', 'failure', 'error', etc.).
            forecast_id (str, optional): Associated forecast id.
            success (bool, optional): If provided, logs as a binary outcome for Bayesian update.
        """
        data = {
            "rule_id": rule_id,
            "variable_id": variable_id,
            "outcome": outcome,
            "forecast_id": forecast_id,
            "success": success,
        }
        self.log_event("rule_activation", data)

    def log_bayesian_trust_metrics(self, key: str, kind: str = "variable"):
        """
        Logs the current Bayesian trust/confidence and confidence interval for a variable or rule.
        Args:
            key (str): Variable or rule identifier.
            kind (str): 'variable' or 'rule'.
        """
        trust = bayesian_trust_tracker.get_trust(key)
        ci = bayesian_trust_tracker.get_confidence_interval(key)
        confidence = bayesian_trust_tracker.get_confidence_strength(key)
        sample_size = bayesian_trust_tracker.get_sample_size(key)

        # Both print to console and log to file
        print(
            f"[BayesianTrust] {kind}={key} trust={trust:.3f} CI={ci} confidence={confidence:.3f} samples={sample_size}"
        )

        # Log to file
        self.log_event(
            "bayesian_trust_metrics",
            {
                "key": key,
                "kind": kind,
                "trust": trust,
                "confidence_interval": ci,
                "confidence_strength": confidence,
                "sample_size": sample_size,
            },
        )

    def log_rule_effectiveness(
        self,
        rule_id: str,
        activation_count: int,
        success_rate: float,
        impact_score: float,
    ):
        """
        Logs the effectiveness of a rule based on activation count, success rate, and impact score.

        Args:
            rule_id (str): Identifier for the rule
            activation_count (int): How many times the rule was activated
            success_rate (float): Ratio of successful outcomes (0-1)
            impact_score (float): Measure of rule's impact (0-1)
        """
        self.log_event(
            "rule_effectiveness",
            {
                "rule_id": rule_id,
                "activation_count": activation_count,
                "success_rate": success_rate,
                "impact_score": impact_score,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
        )

    def generate_trust_report(self, min_samples: int = 5) -> Dict[str, Any]:
        """
        Generate a comprehensive trust metrics report.

        Args:
            min_samples (int): Minimum sample size to include in report

        Returns:
            Dict containing trust metrics report
        """
        report = bayesian_trust_tracker.generate_report(min_samples)
        self.log_event(
            "trust_report_generated",
            {
                "summary": report["summary"],
                "high_trust_count": len(report["high_trust"]),
                "low_trust_count": len(report["low_trust"]),
            },
        )
        return report

    def export_trust_data(self, filepath: str) -> bool:
        """
        Export trust metrics to a file for persistence.

        Args:
            filepath (str): Path to export file

        Returns:
            bool: Success status
        """
        try:
            bayesian_trust_tracker.export_to_file(filepath)
            self.log_event("trust_data_exported", {"filepath": filepath})
            return True
        except Exception as e:
            self.log_event("trust_data_export_failed", {"error": str(e)})
            return False

    def import_trust_data(self, filepath: str) -> bool:
        """
        Import trust metrics from a file.

        Args:
            filepath (str): Path to import file

        Returns:
            bool: Success status
        """
        success = bayesian_trust_tracker.import_from_file(filepath)
        if success:
            self.log_event("trust_data_imported", {"filepath": filepath})
        else:
            self.log_event("trust_data_import_failed", {"filepath": filepath})
        return success


# Singleton instance for module-level functions
_logger = PulseLearningLogger()


def log_learning_event(
    event_type: str, data: Dict[str, Any], context: Optional[Dict[str, Any]] = None
) -> None:
    """
    Module-level function to log a learning event.
    """
    _logger.log_event(event_type, data, context)


def log_variable_weight_change(var: str, old_weight: float, new_weight: float):
    """
    Module-level function to log a variable weight update.
    """
    _logger.log_variable_weight_change(var, old_weight, new_weight)


def log_symbolic_upgrade(plan: Dict[str, Any]):
    """
    Module-level function to log a symbolic upgrade.
    """
    _logger.log_symbolic_upgrade(plan)


def log_revision_trigger(reason: str):
    """
    Module-level function to log a symbolic revision trigger.
    """
    _logger.log_revision_trigger(reason)


def log_arc_regret(scores: Dict[str, float]):
    """
    Module-level function to log symbolic arc regret scores.
    """
    _logger.log_arc_regret(scores)


def log_learning_summary(summary: Dict[str, Any]):
    """
    Module-level function to log a meta-learning summary.
    """
    _logger.log_learning_summary(summary)


def log_bayesian_trust_metrics(key: str, kind: str = "variable"):
    """
    Module-level function to log Bayesian trust/confidence metrics.
    """
    _logger.log_bayesian_trust_metrics(key, kind)


def log_rule_effectiveness(
    rule_id: str, activation_count: int, success_rate: float, impact_score: float
):
    """
    Module-level function to log rule effectiveness.

    Args:
        rule_id (str): Identifier for the rule
        activation_count (int): How many times the rule was activated
        success_rate (float): Ratio of successful outcomes (0-1)
        impact_score (float): Measure of rule's impact (0-1)
    """
    _logger.log_rule_effectiveness(
        rule_id, activation_count, success_rate, impact_score
    )


def generate_trust_report(min_samples: int = 5) -> Dict[str, Any]:
    """
    Module-level function to generate a trust metrics report.

    Args:
        min_samples (int): Minimum sample size to include in report

    Returns:
        Dict containing trust metrics report
    """
    return _logger.generate_trust_report(min_samples)


def export_trust_data(filepath: str) -> bool:
    """
    Module-level function to export trust metrics to a file.

    Args:
        filepath (str): Path to export file

    Returns:
        bool: Success status
    """
    return _logger.export_trust_data(filepath)


def import_trust_data(filepath: str) -> bool:
    """
    Module-level function to import trust metrics from a file.

    Args:
        filepath (str): Path to import file

    Returns:
        bool: Success status
    """
    return _logger.import_trust_data(filepath)


def _test_logging():
    """
    Simple test to verify logging functionality.
    """
    print("Testing PulseLearningLogger...")
    try:
        log_variable_weight_change("hope", 1.0, 1.2)
        log_revision_trigger("fragmentation > threshold")
        log_symbolic_upgrade({"hope": "+0.1", "despair": "-0.2"})
        log_arc_regret({"arc_hope": 0.04, "arc_despair": 0.91})
        log_learning_summary({"summary": "test summary"})

        # Test trust metrics logging
        bayesian_trust_tracker.update("test_variable", True, 1.0)
        bayesian_trust_tracker.update("test_variable", False, 0.5)
        bayesian_trust_tracker.update("test_variable", True, 1.0)
        log_bayesian_trust_metrics("test_variable", "variable")

        # Test rule effectiveness logging
        log_rule_effectiveness("R001", 10, 0.8, 0.5)

        # Test trust report generation
        report = generate_trust_report()
        print(
            f"Trust report generated with {len(report['high_trust'])} high trust entities"
        )

        # Test trust data export/import
        export_trust_data("trust_data_test.json")
        import_trust_data("trust_data_test.json")

        print(f"Log entries written to {LOG_PATH}")
    except Exception as e:
        print(f"Test failed: {e}")


if __name__ == "__main__":
    _test_logging()
