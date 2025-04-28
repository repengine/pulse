# === File: pulse/intelligence/function_router.py ===
"""
Pulse Function Router (patched)

- Adds PulseImportError with retry/back‑off logic
- Centralizes logging via `_log()`
- Keeps external interface unchanged
"""
from __future__ import annotations

import importlib
import inspect
import os
import sys
import time
from types import ModuleType
from typing import Any, Dict, List, Optional


class PulseImportError(ImportError):
    """Raised when a module cannot be imported after retries."""


class FunctionRouter:
    MAX_RETRIES = 3
    RETRY_SLEEP = 1.5  # seconds

    def __init__(self, additional_paths: Optional[List[str]] = None):
        self.modules: Dict[str, ModuleType] = {}
        if additional_paths:
            for p in additional_paths:
                if p not in sys.path:
                    sys.path.append(p)

    # ---------------------------------------------------------------------
    # Public API
    # ---------------------------------------------------------------------
    def load_module(self, module_path: str, alias: Optional[str] = None) -> None:
        """Dynamically load a module with limited retries."""
        attempts = 0
        while attempts < self.MAX_RETRIES:
            try:
                module = importlib.import_module(module_path)
                self.modules[alias or module_path] = module
                self._log("✅ Loaded module", module_path)
                return
            except Exception as exc:  # noqa: BLE001  # broad but logged
                attempts += 1
                self._log("⚠️  Import failed", f"{module_path} (attempt {attempts}) → {exc}")
                time.sleep(self.RETRY_SLEEP)
        raise PulseImportError(f"Failed to import {module_path} after {self.MAX_RETRIES} attempts")

    def load_modules(self, modules: Dict[str, str]) -> None:
        for alias, path in modules.items():
            self.load_module(path, alias=alias)

    def unload_module(self, module_key: str) -> None:
        if module_key in self.modules:
            del self.modules[module_key]
            self._log("✅ Unloaded module", module_key)
        else:
            self._log("❌ Module not loaded", module_key)

    def run_function(self, module_key: str, function_name: str, *args, **kwargs) -> Any:  # noqa: ANN401
        module = self._get_module(module_key)
        func = getattr(module, function_name, None)
        if not callable(func):
            raise AttributeError(f"{function_name} is not callable in {module_key}")
        self._log("🔄 Running", f"{module_key}.{function_name}()")
        return func(*args, **kwargs)

    def available_functions(self, module_key: str) -> List[str]:
        module = self._get_module(module_key)
        return [
            n for n, obj in inspect.getmembers(module) if inspect.isfunction(obj) and not n.startswith("_")
        ]

    def list_loaded_modules(self) -> List[str]:
        return list(self.modules.keys())

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def _get_module(self, key: str) -> ModuleType:
        if key not in self.modules:
            raise KeyError(f"Module '{key}' not loaded")
        return self.modules[key]

    @staticmethod
    def _log(prefix: str, msg: str) -> None:
        print(f"[Router] {prefix}: {msg}")

