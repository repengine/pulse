"""
worldstate.py

Defines the WorldState class and supporting structures to represent the evolving
simulation state of Pulse. This includes core variables, symbolic overlays,
capital exposures, turn control, and event logging.

Supports serialization, cloning, and controlled mutation of the simulation state.

Author: Pulse v0.4
"""

from simulation_engine.variables.worldstate_variables import WorldstateVariables
from typing import Dict, Any, List
from dataclasses import dataclass, field
import copy
import json
from core.path_registry import PATHS
from core.variable_registry import get_default_variable_state

WORLDSTATE_LOG_PATH = PATHS.get("WORLDSTATE_LOG_PATH", PATHS["WORLDSTATE_LOG_DIR"])
# ...use WORLDSTATE_LOG_PATH for worldstate logs...

SCHEMA_VERSION = "1.0.0"  # Used to validate replay compatibility


@dataclass
class SymbolicOverlay:
    hope: float = 0.5
    despair: float = 0.5
    rage: float = 0.5
    fatigue: float = 0.5
    trust: float = 0.5

    def as_dict(self) -> Dict[str, float]:
        return {
            "hope": self.hope,
            "despair": self.despair,
            "rage": self.rage,
            "fatigue": self.fatigue,
            "trust": self.trust,
        }

    @staticmethod
    def from_dict(data: Dict[str, float]) -> 'SymbolicOverlay':
        return SymbolicOverlay(**data)


@dataclass
class CapitalExposure:
    nvda: float = 0.0
    msft: float = 0.0
    ibit: float = 0.0
    spy: float = 0.0
    cash: float = 100000.0  # Default initial liquidity

    def as_dict(self) -> Dict[str, float]:
        return {
            "nvda": self.nvda,
            "msft": self.msft,
            "ibit": self.ibit,
            "spy": self.spy,
            "cash": self.cash,
        }

    @staticmethod
    def from_dict(data: Dict[str, float]) -> 'CapitalExposure':
        return CapitalExposure(**data)


@dataclass
class WorldState:
    turn: int = 0
    variables: WorldstateVariables = field(default_factory=WorldstateVariables)
    overlays: SymbolicOverlay = field(default_factory=SymbolicOverlay)
    capital: CapitalExposure = field(default_factory=CapitalExposure)
    log: List[str] = field(default_factory=list)
    schema_version: str = SCHEMA_VERSION
    timestamp: str = "init"  # Could be datetime or stringified run ID

    # ------------------ Core Methods ------------------

    def clone(self) -> 'WorldState':
        """Return a deep copy of the worldstate."""
        return copy.deepcopy(self)

    def increment_turn(self) -> None:
        self.turn += 1
        self.log_event(f"Turn advanced to {self.turn}")

    def update_variable(self, name: str, value: Any) -> None:
        self.variables[name] = value
        self.log_event(f"Variable '{name}' updated to {value}")

    def get_variable(self, name: str, default: Any = None) -> Any:
        return self.variables.get(name, default)

    def log_event(self, msg: str) -> None:
        self.log.append(msg)

    def get_log(self, last_n: int = 10) -> List[str]:
        return self.log[-last_n:]

    # ------------------ Serialization ------------------

    def to_dict(self) -> Dict[str, Any]:
        """Serialize the full state to dictionary format."""
        return {
            "turn": self.turn,
            "variables": dict(self.variables),
            "overlays": self.overlays.as_dict(),
            "capital": self.capital.as_dict(),
            "log": self.log,
            "schema_version": self.schema_version,
            "timestamp": self.timestamp
        }

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> 'WorldState':
        """Reconstruct WorldState from dictionary."""
        state = WorldState(
            turn=data.get("turn", 0),
            variables=WorldstateVariables(**data.get("variables", {})),
            overlays=SymbolicOverlay.from_dict(data.get("overlays", {})),
            capital=CapitalExposure.from_dict(data.get("capital", {})),
            log=data.get("log", []),
            schema_version=data.get("schema_version", SCHEMA_VERSION),
            timestamp=data.get("timestamp", "replayed")
        )
        return state

    def snapshot(self) -> Dict[str, Any]:
        """Return a lightweight snapshot of key elements (omit logs)."""
        return {
            "turn": self.turn,
            "variables": dict(self.variables),
            "overlays": self.overlays.as_dict(),
            "capital": self.capital.as_dict(),
            "timestamp": self.timestamp
        }
