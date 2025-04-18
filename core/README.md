# Pulse Core Utilities

This folder contains Pulse's centralized configuration, registry, and utility access modules. These modules are designed to eliminate hardcoded logic and enable modular, scalable, and testable development across the entire Pulse system.

---

## 📦 Modules Overview

### `pulse_config.py`
Central simulation constants and runtime toggles.

- `DEFAULT_DECAY_RATE`: Default decay rate for symbolic overlays
- `MAX_SIMULATION_FORKS`: Controls fork depth for forecasts
- `CONFIDENCE_THRESHOLD`: Minimum score for trustable outputs
- `MODULES_ENABLED`: Global boolean flags to enable/disable key systems

---

### `path_registry.py`
Handles all file path management.

- Dynamically builds file paths for worldstate I/O, logs, etc.
- Keeps relative paths portable across dev environments

---

### `module_registry.py`
Defines versioning and enablement for every module in the Pulse stack.

```python
MODULE_REGISTRY = {
  "turn_engine": {"version": "v0.000", "enabled": True},
  "decay_overlay": {"version": "v0.002", "enabled": True},
  ...
}
