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
from datetime import datetime
from core.path_registry import PATHS

def _get_log_path() -> str:
    """
    Returns the path to the learning log file, allowing override via environment variable.
    """
    return os.environ.get("PULSE_LEARNING_LOG_PATH", PATHS.get("LEARNING_LOG", "logs/pulse_learning_log.jsonl"))

LOG_PATH = _get_log_path()
os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)

def _set_file_permissions(path: str):
    """
    Restricts log file permissions to owner read/write only (where supported).
    """
    try:
        os.chmod(path, 0o600)
    except Exception:
        pass  # Not all OSes support chmod or may not be needed

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

    def log_event(self, event_type: str, data: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> None:
        """
        Logs a meta-learning event with timestamp, event type, and unique event ID.

        Args:
            event_type (str): Type of the event.
            data (dict): Event-specific data.
            context (dict, optional): Additional context for the event.
        """
        entry = {
            "event_id": str(uuid.uuid4()),
            "timestamp": datetime.utcnow().isoformat(),
            "event_type": event_type,
            "data": data
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

    def log_variable_weight_change(self, var: str, old_weight: float, new_weight: float):
        """
        Logs a variable weight update event.

        Args:
            var (str): Variable name.
            old_weight (float): Previous weight.
            new_weight (float): Updated weight.
        """
        if not isinstance(var, str) or not isinstance(old_weight, (float, int)) or not isinstance(new_weight, (float, int)):
            raise ValueError("Invalid types for variable weight change log.")
        self.log_event("variable_weight_update", {
            "variable": var,
            "from": float(old_weight),
            "to": float(new_weight)
        })

    def log_symbolic_upgrade(self, plan: Dict[str, Any]):
        """
        Logs a symbolic upgrade event.

        Args:
            plan (dict): Upgrade plan details.
        """
        self.log_event("symbolic_upgrade_applied", {
            "changes": plan
        })

    def log_revision_trigger(self, reason: str):
        """
        Logs a symbolic revision trigger event.

        Args:
            reason (str): Reason for revision.
        """
        self.log_event("symbolic_revision_triggered", {
            "reason": reason
        })

    def log_arc_regret(self, scores: Dict[str, float]):
        """
        Logs symbolic arc regret scores.

        Args:
            scores (dict): Regret scores.
        """
        self.log_event("symbolic_arc_regret", {
            "regret_scores": scores
        })

    def log_learning_summary(self, summary: Dict[str, Any]):
        """
        Logs a meta-learning summary.

        Args:
            summary (dict): Summary data.
        """
        self.log_event("meta_learning_summary", summary)

# Singleton instance for module-level functions
_logger = PulseLearningLogger()

def log_learning_event(event_type: str, data: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> None:
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
        print(f"Log entries written to {LOG_PATH}")
    except Exception as e:
        print(f"Test failed: {e}")

if __name__ == "__main__":
    _test_logging()