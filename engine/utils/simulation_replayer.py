# simulation_engine/utils/simulation_replayer.py
"""
Replays previously saved WorldState snapshots for audit, diagnostics, or retrodiction.
Includes drift detection, symbolic diffs, and optional rerunning of logic.

Modes:
- audit: Load + inspect variable state at each turn
- diagnostic: Show diffs in variables + overlays
- retrodiction: Re-run logic on historical state and compare changes

Author: Pulse AI (Architect Mode)
Plan: docs/planning/worldstate_replayer_timestamp_fix_plan_v1.md
"""

import os
import json
import copy
import time  # Added import
from typing import (
    List,
    Optional,
    Dict,
    Any,
    Tuple,
    TYPE_CHECKING,
)  # Added TYPE_CHECKING
from dataclasses import dataclass, field
from datetime import datetime
import logging

# Assuming WorldState is in the parent directory as per typical project structure
# Adjust import if WorldState is located elsewhere relative to this file.

if TYPE_CHECKING:
    from engine.worldstate import WorldState, SymbolicOverlays, Variables
    from engine.turn_engine import run_turn  # If used for retrodiction
else:
    try:
        from engine.worldstate import WorldState, SymbolicOverlays, Variables
        from engine.turn_engine import run_turn
    except ImportError as e:
        logger_fallback = logging.getLogger(__name__)
        logger_fallback.error(
            f"Runtime: Failed to import WorldState or run_turn. Actual error: {e}. Using dummy classes."
        )

        # Re-raise the error to make it visible during testing if imports are truly broken
        # raise # Commented out for now to allow script to complete with dummies if needed for other parts
        # Define Dummies only if import fails
        class DummyVariables:
            def __init__(self, data=None):
                self.data = data if data is not None else {}

            def as_dict(self):
                return self.data

            def get(self, key, default=None):
                return self.data.get(key, default)

        class DummySymbolicOverlays:
            def __init__(self, data=None):
                self.data = data if data is not None else {}

            def as_dict(self):
                return self.data

        class DummyWorldState:
            def __init__(
                self,
                turn=0,
                timestamp=0.0,
                variables=None,
                overlays=None,
                sim_id="dummy_sim",
            ):
                self.turn = turn
                self.timestamp = timestamp
                self.variables = (
                    variables if variables is not None else DummyVariables()
                )
                self.overlays = (
                    overlays if overlays is not None else DummySymbolicOverlays()
                )
                self.sim_id = sim_id
                self.event_log: List[str] = []
                self.metadata: Dict[str, Any] = {}

            @classmethod
            def from_dict(cls, data: Dict[str, Any]) -> "DummyWorldState":
                return cls(
                    turn=data.get("turn", 0),
                    timestamp=float(data.get("timestamp", time.time())),
                    variables=DummyVariables(data.get("variables", {}).get("data", {})),
                    overlays=DummySymbolicOverlays(data.get("overlays", {})),
                    sim_id=data.get("sim_id", "dummy_from_dict"),
                )

            def clone(self) -> "DummyWorldState":
                return DummyWorldState.from_dict(self.snapshot())  # type: ignore

            def snapshot(self) -> Dict[str, Any]:
                return {
                    "turn": self.turn,
                    "timestamp": self.timestamp,
                    "variables": self.variables.as_dict(),
                    "overlays": self.overlays.as_dict(),
                    "sim_id": self.sim_id,
                    "event_log": self.event_log,
                    "metadata": self.metadata,
                }

        WorldState = DummyWorldState  # type: ignore
        SymbolicOverlays = DummySymbolicOverlays  # type: ignore
        Variables = DummyVariables  # type: ignore

        def run_turn(x, **kwargs) -> None:
            pass  # Dummy

    # Original dummy class definitions are now inside the except block
    class DummyVariables:
        def __init__(self, data=None):
            self.data = data if data is not None else {}

        def as_dict(self):
            return self.data

        def get(self, key, default=None):
            return self.data.get(key, default)

    class DummySymbolicOverlays:
        def __init__(self, data=None):
            self.data = data if data is not None else {}

        def as_dict(self):
            return self.data

    class DummyWorldState:
        def __init__(
            self,
            turn=0,
            timestamp=0.0,
            variables=None,
            overlays=None,
            sim_id="dummy_sim",
        ):
            self.turn = turn
            self.timestamp = timestamp
            self.variables = variables if variables is not None else DummyVariables()
            self.overlays = (
                overlays if overlays is not None else DummySymbolicOverlays()
            )
            self.sim_id = sim_id
            self.event_log: List[str] = []
            self.metadata: Dict[str, Any] = {}

        @classmethod
        def from_dict(cls, data: Dict[str, Any]) -> "DummyWorldState":
            return cls(
                turn=data.get("turn", 0),
                timestamp=float(data.get("timestamp", time.time())),
                variables=DummyVariables(
                    data.get("variables", {}).get("data", {})
                ),  # Handle nested 'data' for Variables
                overlays=DummySymbolicOverlays(data.get("overlays", {})),
                sim_id=data.get("sim_id", "dummy_from_dict"),
            )

        def clone(self) -> "DummyWorldState":
            return DummyWorldState.from_dict(self.snapshot())  # type: ignore

        def snapshot(self) -> Dict[str, Any]:
            return {
                "turn": self.turn,
                "timestamp": self.timestamp,
                "variables": self.variables.as_dict(),
                "overlays": self.overlays.as_dict(),
                "sim_id": self.sim_id,
                "event_log": self.event_log,
                "metadata": self.metadata,
            }

    WorldState = DummyWorldState  # type: ignore
    SymbolicOverlays = DummySymbolicOverlays  # type: ignore
    Variables = DummyVariables  # type: ignore

    def run_turn(x, **kwargs) -> None:  # Dummy
        pass


# Assuming PATHS is centrally managed, e.g., in a core.config or core.path_registry
# For robustness, provide a default if PATHS isn't available.
try:
    from engine.path_registry import PATHS
    from analytics.pulse_learning_log import log_learning_event  # If used
except ImportError:
    logger = logging.getLogger(__name__)
    logger.warning(
        "core.path_registry.PATHS or core.pulse_learning_log not found. Using default paths/stubs."
    )
    PATHS = {"REPLAY_LOG_PATH": "replay_logs"}  # Default

    def log_learning_event(*args, **kwargs) -> None:  # Dummy
        pass


logger = logging.getLogger(__name__)


@dataclass
class ReplayerConfig:
    """Configuration for the SimulationReplayer."""

    mode: str = "audit"  # 'audit', 'diagnostic', 'retrodiction'
    step_limit: Optional[int] = None
    log_to_file: bool = False
    log_path: str = field(
        default_factory=lambda: str(PATHS.get("REPLAY_LOG_PATH", "replay_logs/"))
    )  # Cast to str
    verbose: bool = True
    show_symbolic: bool = True  # For diagnostic mode: show overlay diffs
    # decay_rate: float = 0.01 # Example: For retrodiction reruns, if turn_engine uses it

    def __post_init__(self):
        if not os.path.exists(self.log_path):
            try:
                os.makedirs(self.log_path, exist_ok=True)
            except OSError as e:
                logger.error(f"Failed to create log directory {self.log_path}: {e}")
                # Potentially fall back to a local directory or raise error
                self.log_path = "./replay_logs/"
                os.makedirs(self.log_path, exist_ok=True)


class SimulationReplayer:
    """
    Handles loading and replaying simulation snapshots.
    """

    def __init__(
        self, snapshot_directory: str, config: Optional[ReplayerConfig] = None
    ):
        """
        Initialize the replayer.

        Args:
            snapshot_directory: Directory containing WorldState JSON snapshots.
            config: ReplayerConfig object. If None, a default config is used.
        """
        self.snapshot_directory = snapshot_directory
        self.config = config if config else ReplayerConfig()
        self.replay_log_entries: List[Dict[str, Any]] = []

        if not os.path.isdir(self.snapshot_directory):
            logger.error(f"Snapshot directory not found: {self.snapshot_directory}")
            raise FileNotFoundError(
                f"Snapshot directory not found: {self.snapshot_directory}"
            )

    def _load_snapshot(
        self, file_path: str
    ) -> Optional["WorldState"]:  # Changed to string literal
        """Loads a single WorldState snapshot from a JSON file."""
        try:
            with open(file_path, "r") as f:
                data = json.load(f)
            return WorldState.from_dict(data)
        except FileNotFoundError:
            logger.error(f"Snapshot file not found: {file_path}")
        except json.JSONDecodeError:
            logger.error(f"Error decoding JSON from snapshot: {file_path}")
        except Exception as e:
            logger.error(f"Unexpected error loading snapshot {file_path}: {e}")
        return None

    def _diff_states(
        self, old_state: "WorldState", new_state: "WorldState"
    ) -> Tuple[Dict[str, Any], Dict[str, Any]]:  # Changed to string literal
        """Compares two WorldState objects and returns differences in variables and overlays."""
        variable_diffs = {}
        overlay_diffs = {}

        # Corrected: Access variables via state.variables.data (or state.variables.as_dict())
        old_vars = old_state.variables.as_dict() if old_state.variables else {}
        new_vars = new_state.variables.as_dict() if new_state.variables else {}

        all_var_keys = set(old_vars.keys()) | set(new_vars.keys())
        for key in all_var_keys:
            old_val = old_vars.get(key)
            new_val = new_vars.get(key)
            if old_val != new_val:
                variable_diffs[key] = {"old": old_val, "new": new_val}

        if self.config.show_symbolic:
            # Corrected: Access overlays via state.overlays.as_dict()
            old_overlays_dict = (
                old_state.overlays.as_dict() if old_state.overlays else {}
            )
            new_overlays_dict = (
                new_state.overlays.as_dict() if new_state.overlays else {}
            )

            all_overlay_keys = set(old_overlays_dict.keys()) | set(
                new_overlays_dict.keys()
            )
            for key in all_overlay_keys:
                old_val = old_overlays_dict.get(key)
                new_val = new_overlays_dict.get(key)
                if old_val != new_val:
                    overlay_diffs[key] = {"old": old_val, "new": new_val}

        return variable_diffs, overlay_diffs

    def _print_diffs(self, variable_diffs: Dict, overlay_diffs: Dict):
        """Prints formatted differences."""
        if variable_diffs:
            logger.info("Variable Differences:")
            for key, changes in variable_diffs.items():
                logger.info(f"  {key}: {changes['old']} -> {changes['new']}")
        if overlay_diffs and self.config.show_symbolic:
            logger.info("Overlay Differences:")
            for key, changes in overlay_diffs.items():
                logger.info(f"  {key}: {changes['old']} -> {changes['new']}")
        if not variable_diffs and (not overlay_diffs or not self.config.show_symbolic):
            logger.info(
                "No significant differences detected or displayed based on config."
            )

    def replay_simulation(self, replay_session_id: Optional[str] = None):
        """
        Replays the simulation from snapshots in the log_dir.
        """
        snapshot_files = sorted(
            [
                f
                for f in os.listdir(self.snapshot_directory)
                if f.endswith(".json") and f.startswith("worldstate_snapshot_turn_")
            ]
        )

        if not snapshot_files:
            logger.warning(f"No snapshot files found in {self.snapshot_directory}")
            return

        if self.config.step_limit is not None:
            snapshot_files = snapshot_files[: self.config.step_limit]

        previous_state: Optional["WorldState"] = None  # Changed to string literal

        for turn_index, filename in enumerate(snapshot_files):
            full_path = os.path.join(self.snapshot_directory, filename)
            current_state = self._load_snapshot(full_path)

            if not current_state:
                logger.warning(
                    f"Skipping turn {turn_index} due to load error for file {filename}"
                )
                continue

            log_entry: Dict[str, Any] = {
                "turn": current_state.turn,  # Use turn from WorldState
                "snapshot_file": filename,
                "timestamp": current_state.timestamp,  # Timestamp from WorldState
            }

            if self.config.verbose:
                logger.info(
                    f"\n--- Turn {current_state.turn} (File: {filename}, Timestamp: {datetime.fromtimestamp(current_state.timestamp).isoformat() if current_state.timestamp else 'N/A'}) ---"
                )

            if self.config.mode == "audit":
                # Display basic info or selected variables
                log_entry["variables_sample"] = (
                    dict(list(current_state.variables.as_dict().items())[:5])
                    if current_state.variables
                    else {}
                )
                log_entry["overlays_sample"] = (
                    dict(list(current_state.overlays.as_dict().items())[:3])
                    if current_state.overlays
                    else {}
                )
                if self.config.verbose:
                    logger.info(f"  Variables Sample: {log_entry['variables_sample']}")
                    logger.info(f"  Overlays Sample: {log_entry['overlays_sample']}")

            elif self.config.mode == "diagnostic" and previous_state:
                variable_diffs, overlay_diffs = self._diff_states(
                    previous_state, current_state
                )
                log_entry["variable_diffs"] = variable_diffs
                log_entry["overlay_diffs"] = overlay_diffs
                if self.config.verbose:
                    self._print_diffs(variable_diffs, overlay_diffs)

            elif self.config.mode == "retrodiction" and previous_state:
                # Example: Re-run logic. This part is highly dependent on `run_turn`'s signature
                # and what a "retrodiction" entails for your specific simulation.
                # state_for_rerun = previous_state.clone() # Use a clone of the *previous* state to predict the current
                # # Apply any necessary inputs or conditions for the rerun if they are not in WorldState
                # # For example: run_turn(state_for_rerun, inputs_for_this_turn)
                # predicted_next_state = run_turn(state_for_rerun) # Assuming run_turn modifies state_for_rerun

                # # Now compare `predicted_next_state` (which is `state_for_rerun` after modification) with `current_state`
                # variable_diffs, overlay_diffs = self._diff_states(predicted_next_state, current_state)
                # log_entry["retrodiction_variable_diffs"] = variable_diffs
                # log_entry["retrodiction_overlay_diffs"] = overlay_diffs
                # if self.config.verbose:
                #     logger.info("Retrodiction Diffs (Predicted vs Actual for current turn):")
                #     self._print_diffs(variable_diffs, overlay_diffs)
                logger.info(
                    "Retrodiction mode is a placeholder. Implement re-running logic and comparison."
                )

            self.replay_log_entries.append(log_entry)
            previous_state = current_state

        if self.config.log_to_file:
            self._save_replay_log(replay_session_id)

        if replay_session_id:
            log_learning_event(
                "simulation_replay_session_completed",
                {
                    "replay_session_id": replay_session_id,
                    "snapshot_directory": self.snapshot_directory,
                    "mode": self.config.mode,
                    "turns_replayed": len(self.replay_log_entries),
                    "completion_timestamp": datetime.utcnow().isoformat(),
                },
            )

        logger.info(
            f"Replay completed. {len(self.replay_log_entries)} turns processed."
        )

    def _save_replay_log(self, replay_session_id: Optional[str] = None):
        """Saves the collected replay log to a file."""
        if not self.replay_log_entries:
            logger.info("No replay log entries to save.")
            return

        timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
        session_suffix = f"_{replay_session_id}" if replay_session_id else ""
        log_filename = (
            f"replay_log_{self.config.mode}{session_suffix}_{timestamp_str}.json"
        )
        full_log_path = os.path.join(self.config.log_path, log_filename)

        try:
            with open(full_log_path, "w") as f:
                json.dump(self.replay_log_entries, f, indent=2)
            if self.config.verbose:
                logger.info(f"Replay log saved to: {full_log_path}")
        except IOError as e:
            logger.error(f"Failed to save replay log to {full_log_path}: {e}")


# Example Usage (Illustrative)
if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
    )

    # Create dummy snapshot files for testing
    dummy_snapshot_dir = "temp_snapshots_for_replay_test"
    os.makedirs(dummy_snapshot_dir, exist_ok=True)

    base_state_data = {
        "sim_id": "test_sim_replay",
        "turn": 0,
        "timestamp": time.time(),
        "overlays": {
            "hope": 0.5,
            "trust": 0.5,
            "_dynamic_overlays": {},
            "_metadata": {},
        },
        "capital": {"cash": 100000, "_dynamic_assets": {}},
        "variables": {
            "var1": 10,
            "var2": "initial",
            "data": {"var1": 10, "var2": "initial"},
        },  # Ensure 'data' for Variables.from_dict
        "event_log": [],
        "metadata": {},
    }

    for i in range(3):
        state_data = copy.deepcopy(base_state_data)
        state_data["turn"] = i
        state_data["timestamp"] = time.time() + i
        state_data["variables"]["data"]["var1"] = 10 + i
        state_data["overlays"]["hope"] = 0.5 + (i * 0.1)
        # Ensure snapshot filenames match expected pattern if `replay_simulation` relies on it
        # e.g., "worldstate_snapshot_turn_0_ts_....json"
        ts_for_file = datetime.fromtimestamp(state_data["timestamp"]).strftime(
            "%Y%m%d%H%M%S%f"
        )
        snapshot_filename = f"worldstate_snapshot_turn_{i}_ts_{ts_for_file}.json"

        with open(os.path.join(dummy_snapshot_dir, snapshot_filename), "w") as f:
            json.dump(state_data, f, indent=2)

    # Test Audit Mode
    logger.info("\n--- TESTING AUDIT MODE ---")
    audit_config = ReplayerConfig(mode="audit", verbose=True, log_to_file=True)
    auditor = SimulationReplayer(
        snapshot_directory=dummy_snapshot_dir, config=audit_config
    )
    auditor.replay_simulation(replay_session_id="audit_test_001")

    # Test Diagnostic Mode
    logger.info("\n--- TESTING DIAGNOSTIC MODE ---")
    diagnostic_config = ReplayerConfig(
        mode="diagnostic", verbose=True, show_symbolic=True, log_to_file=True
    )
    diagnoser = SimulationReplayer(
        snapshot_directory=dummy_snapshot_dir, config=diagnostic_config
    )
    diagnoser.replay_simulation(replay_session_id="diag_test_001")

    # Test Retrodiction Mode (Placeholder)
    # logger.info("\n--- TESTING RETRODICTION MODE (Placeholder) ---")
    # retro_config = ReplayerConfig(mode="retrodiction", verbose=True, log_to_file=True)
    # retro_player = SimulationReplayer(snapshot_directory=dummy_snapshot_dir, config=retro_config)
    # retro_player.replay_simulation(replay_session_id="retro_test_001")

    logger.info(
        f"\nReplay logs should be in: {audit_config.log_path} (and similar for diagnostic)"
    )

    # Clean up dummy files (optional)
    # import shutil
    # shutil.rmtree(dummy_snapshot_dir)
    # # shutil.rmtree(audit_config.log_path) # Careful if other logs are there
    logger.info("Example usage finished. Check console output and log files.")
