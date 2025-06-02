# simulation_engine/worldstate.py
"""
Defines the WorldState, the core data structure representing the state of a simulation.
Includes symbolic overlays, capital exposure, variables, turn count, simulation ID,
event log, metadata, and a timestamp.
"""

import copy
import json
import uuid
import logging
import time  # Added import
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple

logger = logging.getLogger(__name__)


@dataclass
class SymbolicOverlayMetadata:
    """Metadata for a symbolic overlay."""

    name: str
    category: str = "primary"  # e.g., primary, secondary, derived
    parent: Optional[str] = None  # For hierarchical overlays
    description: Optional[str] = None
    priority: int = 0  # For conflict resolution or ordering


@dataclass
class SymbolicOverlays:
    """
    Manages symbolic emotional/state overlays within the simulation.
    Core overlays (hope, despair, rage, fatigue, trust) are direct attributes.
    Dynamic overlays can be added and managed.
    Supports metadata and hierarchical relationships.
    """

    hope: float = 0.5
    despair: float = 0.5
    rage: float = 0.5
    fatigue: float = 0.5
    trust: float = 0.5

    # Internal storage for dynamic overlays and their metadata
    _dynamic_overlays: Dict[str, float] = field(default_factory=dict)
    _metadata: Dict[str, SymbolicOverlayMetadata] = field(default_factory=dict)
    _relationships: Dict[str, Dict[str, Any]] = field(
        default_factory=dict
    )  # e.g., {"overlay_name": {"influences": ["other_overlay"]}}

    def __post_init__(self) -> None:
        """Initialize metadata for core overlays."""
        core_overlays_meta = {
            "hope": SymbolicOverlayMetadata(
                name="hope", description="Positive outlook and expectation."
            ),
            "despair": SymbolicOverlayMetadata(
                name="despair", description="Absence of hope, negative outlook."
            ),
            "rage": SymbolicOverlayMetadata(
                name="rage", description="Intense anger or frustration."
            ),
            "fatigue": SymbolicOverlayMetadata(
                name="fatigue", description="Weariness, lack of energy."
            ),
            "trust": SymbolicOverlayMetadata(
                name="trust",
                description="Confidence in system or information integrity.",
            ),
        }
        for name, meta in core_overlays_meta.items():
            if name not in self._metadata:
                self._metadata[name] = meta
        self.validate()

    def __getattr__(self, name: str) -> float:
        # Prevent __getattr__ from handling internal attributes to avoid recursion
        # with deepcopy
        if name.startswith("_"):
            raise AttributeError(
                f"'{type(self).__name__}' object has no attribute '{name}' (internal attribute access)"
            )
        if name in self._dynamic_overlays:
            return self._dynamic_overlays[name]
        # This allows direct access to core overlays if they are not explicitly defined as fields
        # but it's better to have them as fields for type checking and clarity.
        # If this class were to be truly dynamic for core overlays too, this would
        # be more complex.
        raise AttributeError(
            f"'{type(self).__name__}' object has no attribute '{name}' and it's not a dynamic overlay"
        )

    def __setattr__(self, name: str, value: Any) -> None:
        if name in ["hope", "despair", "rage", "fatigue", "trust"]:
            super().__setattr__(name, float(value))
        elif name in ["_dynamic_overlays", "_metadata", "_relationships"]:
            super().__setattr__(name, value)
        else:
            # Assume it's a dynamic overlay if not a predefined field
            if not isinstance(value, (int, float)):
                raise ValueError(f"Overlay value for '{name}' must be numeric.")
            self._dynamic_overlays[name] = float(value)
            if name not in self._metadata:  # Add basic metadata if new
                self._metadata[name] = SymbolicOverlayMetadata(
                    name=name, category="dynamic"
                )
        if (
            "_dynamic_overlays" in self.__dict__
        ):  # Check if attr exists, bypassing __getattr__
            self.validate()

    def as_dict(self) -> Dict[str, float]:
        """Return all overlays (core and dynamic) as a dictionary."""
        data = {
            "hope": self.hope,
            "despair": self.despair,
            "rage": self.rage,
            "fatigue": self.fatigue,
            "trust": self.trust,
        }
        data.update(self._dynamic_overlays)
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SymbolicOverlays":
        """Create SymbolicOverlays from a dictionary."""
        instance = cls()
        dynamic_overlays_data = data.get("_dynamic_overlays", {})
        metadata_data = data.get("_metadata", {})

        # Set core overlays
        instance.hope = float(data.get("hope", 0.5))
        instance.despair = float(data.get("despair", 0.5))
        instance.rage = float(data.get("rage", 0.5))
        instance.fatigue = float(data.get("fatigue", 0.5))
        instance.trust = float(data.get("trust", 0.5))

        # Load dynamic overlays
        for name, value in dynamic_overlays_data.items():
            instance._dynamic_overlays[name] = float(value)

        # Load metadata
        for name, meta_dict in metadata_data.items():
            if isinstance(meta_dict, SymbolicOverlayMetadata):
                instance._metadata[name] = meta_dict
            elif isinstance(meta_dict, dict):
                instance._metadata[name] = SymbolicOverlayMetadata(**meta_dict)

        # Ensure metadata for core overlays if not present in data
        core_meta_names = ["hope", "despair", "rage", "fatigue", "trust"]
        default_meta = {
            "hope": SymbolicOverlayMetadata(
                name="hope", description="Positive outlook and expectation."
            ),
            "despair": SymbolicOverlayMetadata(
                name="despair", description="Absence of hope, negative outlook."
            ),
            "rage": SymbolicOverlayMetadata(
                name="rage", description="Intense anger or frustration."
            ),
            "fatigue": SymbolicOverlayMetadata(
                name="fatigue", description="Weariness, lack of energy."
            ),
            "trust": SymbolicOverlayMetadata(
                name="trust",
                description="Confidence in system or information integrity.",
            ),
        }
        for name in core_meta_names:
            if name not in instance._metadata:
                instance._metadata[name] = default_meta[name]

        # Load relationships if provided
        instance._relationships = data.get("_relationships", {})

        instance.validate()
        return instance

    def validate(self) -> None:
        """Validate overlay values (e.g., ensure they are within a 0-1 range if applicable)."""
        for name, value in self.as_dict().items():
            if not (0.0 <= value <= 1.0):
                # logger.warning(f"Overlay '{name}' value {value} is outside the typical 0-1 range.")
                # Clamping to range, or raise error, depends on desired behavior.
                # For now, let's clamp as per original analysis hints.
                clamped_value = max(0.0, min(1.0, value))
                if value != clamped_value:
                    logger.debug(
                        f"Clamping overlay '{name}' value from {value} to {clamped_value}.")
                    if hasattr(self, name) and name in [
                        "hope",
                        "despair",
                        "rage",
                        "fatigue",
                        "trust",
                    ]:
                        super().__setattr__(name, clamped_value)
                    elif name in self._dynamic_overlays:
                        self._dynamic_overlays[name] = clamped_value
        # Add more validation logic as needed (e.g., for relationships, metadata
        # consistency)

    def add_overlay(
        self,
        name: str,
        value: float,
        category: str = "dynamic",
        parent: Optional[str] = None,
        description: Optional[str] = None,
        priority: int = 0,
    ) -> None:
        """Add a new dynamic overlay or update an existing one."""
        if name in ["hope", "despair", "rage", "fatigue", "trust"]:
            raise ValueError(
                f"Cannot add core overlay '{name}' dynamically. Set it as an attribute."
            )
        self._dynamic_overlays[name] = float(value)
        self._metadata[name] = SymbolicOverlayMetadata(
            name=name,
            category=category,
            parent=parent,
            description=description,
            priority=priority,
        )
        if parent and parent not in self.as_dict() and parent not in self._metadata:
            logger.warning(f"Parent overlay '{parent}' for '{name}' does not exist.")
        self.validate()

    def get_overlay_value(self, name: str) -> Optional[float]:
        """Get the value of a specific overlay (core or dynamic)."""
        if hasattr(self, name) and name in [
            "hope",
            "despair",
            "rage",
            "fatigue",
            "trust",
        ]:
            return float(getattr(self, name))
        return self._dynamic_overlays.get(name)

    def get_metadata(self, overlay_name: str) -> Optional[SymbolicOverlayMetadata]:
        """Get metadata for a specific overlay."""
        return self._metadata.get(overlay_name)

    def has_overlay(self, name: str) -> bool:
        """Check if an overlay (core or dynamic) exists."""
        if name in ["hope", "despair", "rage", "fatigue", "trust"]:
            return True
        return name in self._dynamic_overlays

    def set_relationship(
        self,
        overlay_name: str,
        relationship_type: str,
        target_overlay: str,
        strength: float = 1.0,
    ) -> None:
        """Define a relationship between overlays."""
        if overlay_name not in self._relationships:
            self._relationships[overlay_name] = {}
        if relationship_type not in self._relationships[overlay_name]:
            self._relationships[overlay_name][relationship_type] = []
        self._relationships[overlay_name][relationship_type].append(
            {"target": target_overlay, "strength": strength}
        )

    def get_relationships(self, overlay_name: str) -> Optional[Dict[str, Any]]:
        """Get relationships for a specific overlay."""
        return self._relationships.get(overlay_name)

    def get_primary_overlays(self) -> Dict[str, float]:
        """Returns a dictionary of core (primary) overlays and their values."""
        return {
            "hope": self.hope,
            "despair": self.despair,
            "rage": self.rage,
            "fatigue": self.fatigue,
            "trust": self.trust,
        }

    def get_secondary_overlays(self) -> Dict[str, float]:
        """Returns a dictionary of dynamic (secondary) overlays and their values."""
        return self._dynamic_overlays

    def get_children(self, parent_name: str) -> Dict[str, float]:
        """Get all overlays that have the given overlay as a parent, with their values."""
        children = {}
        for name, meta in self._metadata.items():
            if meta.parent == parent_name:
                value = self.get_overlay_value(name)
                if value is not None:
                    children[name] = value
        return children

    def get_relationship(self, source_overlay: str, target_overlay: str) -> float:
        """Get the strength of a direct relationship between two overlays."""
        relationships = self._relationships.get(source_overlay)
        if relationships:
            for rel_type, targets in relationships.items():
                for target_info in targets:
                    if target_info["target"] == target_overlay:
                        return target_info["strength"]
        return 0.0  # Default to no relationship strength

    def get_dominant_overlays(self, threshold: float = 0.65) -> List[Tuple[str, float]]:
        """Get overlays whose values exceed a certain threshold."""
        dominant = []
        for name, value in self.as_dict().items():
            if value >= threshold:
                dominant.append((name, value))
        dominant.sort(
            key=lambda item: item[1], reverse=True
        )  # Sort by value descending
        return dominant


@dataclass
class CapitalExposure:
    """Manages capital exposure across different assets and cash."""

    # Common assets - can be extended or made dynamic
    nvda: float = 0.0
    msft: float = 0.0
    ibit: float = 0.0  # Example Bitcoin ETF
    spy: float = 0.0  # Example S&P 500 ETF
    cash: float = 100000.0
    _dynamic_assets: Dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.validate()

    def __getattr__(self, name: str) -> float:
        # Prevent __getattr__ from handling internal attributes to avoid recursion
        # with deepcopy
        if name.startswith("_"):
            raise AttributeError(
                f"'{type(self).__name__}' object has no attribute '{name}' (internal attribute access)"
            )
        if name in self._dynamic_assets:
            return self._dynamic_assets[name]
        raise AttributeError(
            f"'{type(self).__name__}' object has no attribute '{name}' and it's not a dynamic asset"
        )

    def __setattr__(self, name: str, value: Any) -> None:
        if name in ["nvda", "msft", "ibit", "spy", "cash", "_dynamic_assets"]:
            super().__setattr__(
                name, float(value) if name != "_dynamic_assets" else value
            )
        else:
            if not isinstance(value, (int, float)):
                raise ValueError(f"Asset value for '{name}' must be numeric.")
            self._dynamic_assets[name] = float(value)
        # Avoid calling validate during initial field setting by __init__ if it
        # causes issues
        if (
            "_dynamic_assets" in self.__dict__
        ):  # Check if attr exists, bypassing __getattr__
            self.validate()

    def as_dict(self) -> Dict[str, float]:
        """Return all capital exposures as a dictionary."""
        data = {
            "nvda": self.nvda,
            "msft": self.msft,
            "ibit": self.ibit,
            "spy": self.spy,
            "cash": self.cash,
        }
        data.update(self._dynamic_assets)
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CapitalExposure":
        """Create CapitalExposure from a dictionary."""
        instance = cls()  # Initializes with defaults
        dynamic_assets_data = data.get("_dynamic_assets", {})

        # Set core assets
        instance.nvda = float(data.get("nvda", 0.0))
        instance.msft = float(data.get("msft", 0.0))
        instance.ibit = float(data.get("ibit", 0.0))
        instance.spy = float(data.get("spy", 0.0))
        instance.cash = float(data.get("cash", 100000.0))

        # Load dynamic assets
        for name, value in dynamic_assets_data.items():
            instance._dynamic_assets[name] = float(value)

        instance.validate()
        return instance

    def validate(self) -> None:
        """Validate capital values (e.g., ensure they are non-negative)."""
        for name, value in self.as_dict().items():
            if value < 0:
                logger.warning(
                    f"Capital exposure for '{name}' is negative: {value}. Setting to 0."
                )
                if hasattr(self, name) and name in [
                    "nvda",
                    "msft",
                    "ibit",
                    "spy",
                    "cash",
                ]:
                    super().__setattr__(name, 0.0)
                elif name in self._dynamic_assets:
                    self._dynamic_assets[name] = 0.0

    def total_exposure(self, exclude_cash: bool = True) -> float:
        """Calculate total capital exposure, optionally excluding cash."""
        total = 0.0
        for name, value in self.as_dict().items():
            if exclude_cash and name == "cash":
                continue
            total += value
        return total

    def get_exposure(self, asset_name: str) -> Optional[float]:
        """Get exposure for a specific asset."""
        if hasattr(self, asset_name) and asset_name in [
            "nvda",
            "msft",
            "ibit",
            "spy",
            "cash",
        ]:
            return float(getattr(self, asset_name))
        return self._dynamic_assets.get(asset_name)


@dataclass
class Variables:
    """A flexible container for arbitrary key-value simulation variables."""

    data: Dict[str, Any] = field(default_factory=dict)

    def __getattr__(self, name: str) -> Any:
        # Prevent __getattr__ from handling internal attributes to avoid recursion
        # with deepcopy
        if name.startswith("_"):
            raise AttributeError(
                f"'{type(self).__name__}' object has no attribute '{name}' (internal attribute access)"
            )
        if name in self.data:
            return self.data[name]
        # Fallback for direct attribute access if needed, though 'data' is the primary store
        # raise AttributeError(f"'Variables' object has no attribute '{name}' and it's not in 'data'")
        return None  # Or raise error, depending on strictness

    def __setattr__(self, name: str, value: Any) -> None:
        if name == "data":
            super().__setattr__(name, value)
        else:
            self.data[name] = value

    def get(self, name: str, default: Optional[Any] = None) -> Any:
        """Get a variable's value, with an optional default."""
        return self.data.get(name, default)

    def as_dict(self) -> Dict[str, Any]:
        """Return the variables as a dictionary."""
        return copy.deepcopy(self.data)  # Return a copy

    @classmethod
    def from_dict(cls, data_dict: Dict[str, Any]) -> "Variables":
        """Create Variables from a dictionary."""
        # The 'data' key in the input dict should contain the actual variables dict
        if "data" in data_dict and isinstance(data_dict["data"], dict):
            return cls(data=copy.deepcopy(data_dict["data"]))
        # If the input dict is the variables dict itself
        return cls(data=copy.deepcopy(data_dict))


@dataclass
class WorldState:
    """
    Central data structure representing the complete state of the simulation at a given turn.
    """

    turn: int = 0
    sim_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: float = field(default_factory=time.time)  # NEW: Timestamp of the state
    overlays: SymbolicOverlays = field(default_factory=SymbolicOverlays)
    capital: CapitalExposure = field(default_factory=CapitalExposure)
    variables: Variables = field(default_factory=Variables)
    event_log: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Post-initialization validation."""
        if self.timestamp is None:  # Should be handled by default_factory
            self.timestamp = time.time()
        self.validate()

    def log_event(
        self,
        event_description: str,
        event_type: str = "generic",
        data: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Log an event that occurred in this turn."""
        timestamp_str = datetime.now().isoformat()
        log_entry = (
            f"[{timestamp_str}][Turn {self.turn}][{event_type}] {event_description}"
        )
        if data:
            log_entry += f" | Data: {json.dumps(data)}"
        self.event_log.append(log_entry)
        logger.debug(f"Event logged for sim {self.sim_id}: {event_description}")

    def advance_turn(self) -> None:
        """Advance the simulation to the next turn."""
        self.turn += 1
        # self.timestamp = time.time() # Optionally update timestamp on turn advance
        logger.debug(f"Sim {self.sim_id} advanced to turn {self.turn}")

    def snapshot(self) -> Dict[str, Any]:
        """
        Create a dictionary snapshot of the current world state.
        This is the primary method for serializing the WorldState to a dictionary.
        """
        data = {
            "sim_id": self.sim_id,
            "turn": self.turn,
            "timestamp": self.timestamp,  # MODIFIED: Include WorldState's timestamp
            "overlays": self.overlays.as_dict(),
            "capital": self.capital.as_dict(),
            "variables": self.variables.as_dict(),
            "event_log": list(self.event_log),  # Ensure it's a list copy
            "metadata": copy.deepcopy(self.metadata),
            # "snapshot_time": datetime.now().isoformat() # This can be kept if a separate snapshot creation time is needed
        }
        return data

    def to_dict(self) -> Dict[str, Any]:
        """Alias for snapshot() for consistency if preferred."""
        return self.snapshot()

    def clone(self) -> "WorldState":
        """Create a deep copy of the current world state."""
        # Using snapshot and from_dict ensures consistent (de)serialization logic
        # and handles deepcopying of mutable fields correctly.
        current_snapshot = self.snapshot()
        return WorldState.from_dict(current_snapshot)

    def validate(self) -> None:
        """Validate the overall world state."""
        if not isinstance(self.turn, int) or self.turn < 0:
            raise ValueError("Turn must be a non-negative integer.")
        if not isinstance(self.sim_id, str) or not self.sim_id:
            raise ValueError("sim_id must be a non-empty string.")
        if not isinstance(self.timestamp, float):
            raise ValueError("timestamp must be a float.")
        # Delegate validation to sub-components
        self.overlays.validate()
        self.capital.validate()
        # Variables.validate() could be added if needed
        logger.debug(f"WorldState for sim {self.sim_id} validated at turn {self.turn}.")

    def to_json(self, indent: Optional[int] = 4) -> str:
        """Serialize the world state to a JSON string."""
        return json.dumps(self.snapshot(), indent=indent)

    @classmethod
    def from_json(cls, json_string: str) -> "WorldState":
        """Deserialize a world state from a JSON string."""
        data = json.loads(json_string)
        return cls.from_dict(data)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "WorldState":
        """Create a WorldState object from a dictionary representation."""
        # Ensure sub-components are also created from their dict representations
        # The analysis doc for worldstate.py (line 127) implies these from_dict
        # methods exist.

        # Handle potential missing timestamp in older data
        timestamp_val = data.get("timestamp", time.time())

        return cls(
            turn=data.get("turn", 0),
            sim_id=data.get("sim_id", str(uuid.uuid4())),
            timestamp=float(timestamp_val),  # MODIFIED: Deserialize timestamp
            overlays=SymbolicOverlays.from_dict(data.get("overlays", {})),
            capital=CapitalExposure.from_dict(data.get("capital", {})),
            variables=Variables.from_dict(data.get("variables", {})),
            event_log=data.get("event_log", []),
            metadata=data.get("metadata", {}),
        )


if __name__ == "__main__":
    # Example Usage
    ws = WorldState(turn=1, sim_id="test_sim_001")
    ws.overlays.hope = 0.8
    ws.overlays.add_overlay("anticipation", 0.7, category="secondary", parent="hope")
    ws.capital.nvda = 15000.0
    ws.variables.data["market_sentiment_index"] = 0.75  # Direct dict access
    ws.variables.inflation_rate = 0.025  # Dynamic attribute access

    ws.log_event("Initial conditions set.", event_type="setup")
    print(f"Initial WorldState (Turn {ws.turn}, Timestamp {ws.timestamp}):")
    print(ws.to_json(indent=2))

    ws.advance_turn()
    ws.overlays.trust = 0.65
    ws.log_event("Market rally observed.", event_type="market_event")

    snapshot_data = ws.snapshot()
    print(f"\nSnapshot at Turn {ws.turn} (Timestamp {ws.timestamp}):")
    print(json.dumps(snapshot_data, indent=2))

    # Test cloning
    cloned_ws = ws.clone()
    cloned_ws.advance_turn()
    cloned_ws.log_event("Cloned state diverged.")
    print(f"\nOriginal WS turn: {ws.turn}, Cloned WS turn: {cloned_ws.turn}")
    assert ws.turn != cloned_ws.turn
    assert (
        ws.timestamp == cloned_ws.timestamp
    )  # Timestamp is part of the state, so it's copied
    # Test that the cloned overlays are independent
    cloned_ws.overlays.hope = 0.1
    assert (
        ws.overlays.hope != cloned_ws.overlays.hope
    ), "Overlays in cloned state should be independent"

    # Test from_dict with partial data
    partial_data = {
        "sim_id": "partial_sim_test",
        "turn": 5,
        # timestamp will be auto-generated
        # overlays, capital, variables will use defaults
    }
    ws_from_partial = WorldState.from_dict(partial_data)
    print(
        f"\nWorldState from partial data (Turn {
            ws_from_partial.turn}, SimID {
            ws_from_partial.sim_id}):")
    print(ws_from_partial.to_json(indent=2))
    assert ws_from_partial.turn == 5
    assert ws_from_partial.sim_id == "partial_sim_test"
    assert ws_from_partial.overlays.hope == 0.5  # Default value
    assert ws_from_partial.capital.cash == 100000.0  # Default value

    # Test timestamp deserialization
    specific_timestamp = time.time() - 3600  # An hour ago
    data_with_timestamp = {
        "sim_id": "ts_test",
        "turn": 1,
        "timestamp": specific_timestamp,
    }
    ws_with_ts = WorldState.from_dict(data_with_timestamp)
    print(
        f"\nWorldState with specific timestamp: {
            ws_with_ts.timestamp} (should be approx {specific_timestamp})")
    assert (
        abs(ws_with_ts.timestamp - specific_timestamp) < 0.001
    )  # Check float equality with tolerance

    logger.info("WorldState example usage completed successfully.")
