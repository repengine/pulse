"""
module_registry.py

Tracks module states, versions, and toggle control for execution.

Each entry in MODULE_REGISTRY should have:
    - version (str): Module version string
    - enabled (bool): Whether the module is active

Provides helper functions for querying and updating module states.
Now uses a class-based registry for type safety and validation.
"""
from typing import Dict, Any, Optional

class ModuleInfo:
    """
    Represents a module's registry entry.
    """
    def __init__(self, version: str, enabled: bool):
        self.version = version
        self.enabled = enabled

    def as_dict(self) -> Dict[str, Any]:
        return {"version": self.version, "enabled": self.enabled}

    @staticmethod
    def validate(entry: Dict[str, Any]) -> bool:
        return (
            isinstance(entry, dict)
            and isinstance(entry.get("version"), str)
            and isinstance(entry.get("enabled"), bool)
        )

class ModuleRegistry:
    """
    Class-based registry for Pulse modules.
    Provides validation, enable/disable, and version access.
    """
    def __init__(self):
        self._registry: Dict[str, ModuleInfo] = {
            "turn_engine": ModuleInfo("v0.000", True),
            "worldstate": ModuleInfo("v0.001", True),
            "decay_overlay": ModuleInfo("v0.002", True),
            "simulation_replayer": ModuleInfo("v0.003", False),
            "forecast_tracker": ModuleInfo("v0.005", True),
            "symbolic_memory": ModuleInfo("v0.020", True),
            "trust_engine": ModuleInfo("v0.030", False),
            # Add new modules here as needed for gating
        }

    def is_enabled(self, module_name: str) -> bool:
        return self._registry.get(module_name, ModuleInfo("", False)).enabled

    def set_enabled(self, module_name: str, enabled: bool) -> None:
        if module_name in self._registry:
            self._registry[module_name].enabled = enabled

    def get_version(self, module_name: str) -> str:
        return self._registry.get(module_name, ModuleInfo("", False)).version

    def validate_registry(self) -> bool:
        """Validate that all entries follow the expected schema."""
        return all(ModuleInfo.validate(m.as_dict()) for m in self._registry.values())

    def enable_module(self, module_name: str) -> None:
        self.set_enabled(module_name, True)

    def disable_module(self, module_name: str) -> None:
        self.set_enabled(module_name, False)

    def as_dict(self) -> Dict[str, Dict[str, Any]]:
        return {k: v.as_dict() for k, v in self._registry.items()}

# Instantiate a global registry for use throughout the codebase
MODULE_REGISTRY = ModuleRegistry()

# Backward compatibility: helper functions

def is_module_enabled(module_name: str) -> bool:
    return MODULE_REGISTRY.is_enabled(module_name)

def set_module_enabled(module_name: str, enabled: bool) -> None:
    MODULE_REGISTRY.set_enabled(module_name, enabled)

def get_module_version(module_name: str) -> str:
    return MODULE_REGISTRY.get_version(module_name)
