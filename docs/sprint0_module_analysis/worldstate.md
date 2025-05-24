# WorldState Module

## Overview

The `worldstate.py` module provides the core state representation for the Pulse simulation system. It contains the fundamental data structures that represent the simulation state, including symbolic overlays, capital exposure, variables, and event logs.

## Key Components

### WorldState

The central class that encapsulates the entire simulation state. It includes:

- Turn counter
- Simulation ID
- Symbolic overlays (emotional state)
- Capital exposure across assets
- Variables dictionary
- Event log
- Metadata

### SymbolicOverlays

Represents the emotional state of the simulation with both core and dynamic overlays:

- Core overlays: hope, despair, rage, fatigue, trust
- Dynamic overlay support with metadata
- Hierarchical structure (primary/secondary)
- Relationship tracking between overlays

### CapitalExposure

Tracks capital allocation across different assets:

- NVDA, MSFT, IBIT, SPY
- Cash reserves

### Variables

A flexible dictionary-like structure for simulation variables with dot notation access.

## Recent Changes

- Added `from_dict` static method to `WorldState` class to complement the existing `from_json` method
- Fixed type hints and validation in various components
- Enhanced serialization and deserialization capabilities

## Usage Examples

```python
# Create a new world state
state = WorldState()

# Access and modify overlays
state.overlays.hope = 0.7
state.overlays.add_overlay("confidence", 0.8, category="secondary")

# Set variables
state.variables.gdp_growth = 2.5
state.variables.inflation = 3.1

# Log events
state.log_event("Economic policy change detected")

# Advance simulation
state.advance_turn()

# Create a snapshot
snapshot = state.snapshot()

# Serialize to JSON
json_data = state.to_json()

# Deserialize from JSON
new_state = WorldState.from_json(json_data)

# Deserialize from dictionary
dict_state = WorldState.from_dict(snapshot)
```

## Integration Points

- Used by `simulation_replayer.py` for audit, diagnostics, and retrodiction
- Core component in `turn_engine.py` for simulation progression
- Utilized by various symbolic system components for state analysis