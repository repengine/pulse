"""
simulation_replayer.py

Replays previously saved WorldState snapshots for audit, diagnostics, or retrodiction.
Includes drift detection, symbolic diffs, and optional rerunning of logic.

Modes:
- audit: Load + inspect variable state at each turn
- diagnostic: Show diffs in variables + overlays
- retrodiction: Re-run logic on historical state and compare changes

Author: Pulse v0.4
"""

import os
import json
import copy
from typing import List, Optional
from dataclasses import dataclass
from datetime import datetime
from simulation_engine.worldstate import WorldState
from simulation_engine.turn_engine import run_turn
from utils.log_utils import get_logger

logger = get_logger(__name__)


@dataclass
class ReplayerConfig:
    mode: str = "audit"  # 'audit', 'diagnostic', 'retrodiction'
    step_limit: Optional[int] = None
    log_to_file: bool = False
    log_path: str = "replay_logs"
    verbose: bool = True
    show_symbolic: bool = True
    decay_rate: float = 0.01  # For retrodiction reruns


class SimulationReplayer:
    def __init__(self, log_dir: str, config: ReplayerConfig):
        self.log_dir = log_dir
        self.config = config
        os.makedirs(config.log_path, exist_ok=True)
        self.replay_log = []

    def load_state(self, path: str) -> WorldState:
        with open(path, 'r') as f:
            data = json.load(f)
        return WorldState.from_dict(data)

    def replay(self):
        files = sorted(f for f in os.listdir(self.log_dir) if f.endswith(".json"))
        if self.config.step_limit:
            files = files[:self.config.step_limit]

        prev_state = None
        for idx, file in enumerate(files):
            full_path = os.path.join(self.log_dir, file)
            state = self.load_state(full_path)

            output = {"turn": idx + 1, "file": file, "timestamp": state.timestamp}

            if self.config.verbose:
                logger.info(f"\n--- Turn {idx + 1}: {file} ---")

            if self.config.mode == "diagnostic" and prev_state:
                var_diff, overlay_diff = self._diff_states(prev_state, state)
                output["var_diff"] = var_diff
                output["overlay_diff"] = overlay_diff
                if self.config.verbose:
                    self._print_diffs(var_diff, overlay_diff)

            elif self.config.mode == "retrodiction":
                copy_state = copy.deepcopy(state)
                run_turn(copy_state, decay_rate=self.config.decay_rate)

            elif self.config.mode == "audit":
                output["vars"] = list(state.variables.keys())[:5]
                if self.config.verbose:
                    print(f"State Keys: {output['vars']}")

            self.replay_log.append(output)
            prev_state = state

        if self.config.log_to_file:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            log_file = os.path.join(self.config.log_path, f"replay_log_{timestamp}.json")
            with open(log_file, 'w') as f:
                json.dump(self.replay_log, f, indent=2)
            if self.config.verbose:
                logger.info(f"\nReplay log written to {log_file}")

    def _diff_states(self, old: WorldState, new: WorldState):
        var_changes = {}
        overlay_changes = {}
        for k in new.variables:
            if k in old.variables and old.variables[k] != new.variables[k]:
                var_changes[k] = {"old": old.variables[k], "new": new.variables[k]}
        if self.config.show_symbolic:
            for k in new.overlay:
                if k in old.overlay and old.overlay[k] != new.overlay[k]:
                    overlay_changes[k] = {"old": old.overlay[k], "new": new.overlay[k]}
        return var_changes, overlay_changes

    def _print_diffs(self, var_diff, overlay_diff):
        logger.info(f"Variable diffs: {var_diff}")
        logger.info(f"Overlay diffs: {overlay_diff}")
