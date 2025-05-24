# === File: pulse/intelligence/function_router.py ===
"""
Pulse Function Router (patched)

Dynamically loads and routes function calls based on configured verbs.
Includes retry/back-off logic for module imports and centralizes logging.

- Adds PulseImportError with retry/back‑off logic
- Centralizes logging via `_log()`
- Keeps external interface unchanged
"""

from __future__ import annotations

import importlib
import inspect
import sys
import time
from types import ModuleType
from typing import Any, Dict, List, Optional, Tuple

from intelligence.intelligence_config import (
    FUNCTION_ROUTER_MAX_RETRIES,
    FUNCTION_ROUTER_RETRY_SLEEP,
)


class PulseImportError(ImportError):
    """Raised when a module cannot be imported after retries."""


class FunctionRouter:
    """
    Routes function calls based on configured verbs, handling module loading.
    """

    MAX_RETRIES: int = FUNCTION_ROUTER_MAX_RETRIES
    RETRY_SLEEP: float = FUNCTION_ROUTER_RETRY_SLEEP  # seconds

    # Mapping of CLI verbs to module paths and functions
    verbs: Dict[str, Tuple[str, str]] = {
        "forecast": ("intelligence.simulation_executor", "run_chunked_forecast"),
        "compress": ("forecast_output.forecast_compressor", "compress_forecasts"),
        "retrodict": ("intelligence.simulation_executor", "run_retrodiction_forecast"),
        "train-gpt": ("GPT.gpt_alignment_trainer", "run_alignment_cycle"),
        "status": ("intelligence.intelligence_core", "assemble_status_report"),
    }

    def __init__(self, additional_paths: Optional[List[str]] = None):
        """
        Initializes the FunctionRouter.

        Args:
            additional_paths: Optional list of paths to add to sys.path for module loading.
        """
        self.modules: Dict[str, ModuleType] = {}
        if additional_paths:
            for p in additional_paths:
                if p not in sys.path:
                    sys.path.append(p)

    # ---------------------------------------------------------------------
    # Public API
    # ---------------------------------------------------------------------
    def load_module(self, module_path: str, alias: Optional[str] = None) -> None:
        """
        Dynamically load a module with limited retries.

        Args:
            module_path: The dot-separated path to the module (e.g., "os.path").
            alias: An optional alias to use for the module in the internal modules dictionary.

        Raises:
            PulseImportError: If the module cannot be imported after the maximum number of retries.
        """
        attempts = 0
        while attempts < self.MAX_RETRIES:
            try:
                module = importlib.import_module(module_path)
                self.modules[alias or module_path] = module
                self._log("✅ Loaded module", module_path)
                return
            except Exception as exc:  # noqa: BLE001  # broad but logged
                attempts += 1
                self._log(
                    "⚠️  Import failed",
                    f"{module_path} (attempt {attempts}) → {type(exc).__name__}: {exc}",
                )
                time.sleep(self.RETRY_SLEEP)
        self._log(
            "❌ Failed to load module",
            f"{module_path} after {self.MAX_RETRIES} attempts",
        )
        raise PulseImportError(
            f"Failed to import {module_path} after {self.MAX_RETRIES} attempts"
        )

    def load_modules(self, modules: Dict[str, str]) -> None:
        """
        Load multiple modules.

        Args:
            modules: A dictionary mapping aliases to module paths.
        """
        for alias, path in modules.items():
            self.load_module(path, alias=alias)

    def unload_module(self, module_key: str) -> None:
        """
        Unload a previously loaded module.

        Args:
            module_key: The key (alias or path) of the module to unload.
        """
        if module_key in self.modules:
            del self.modules[module_key]
            self._log("✅ Unloaded module", module_key)
        else:
            self._log("❌ Module not loaded", module_key)

    def run_function(self, verb: str, **kwargs: Any) -> Any:
        """
        Run a function associated with a given verb.

        Args:
            verb: The verb string (e.g., "forecast").
            **kwargs: Keyword arguments to pass to the target function.

        Returns:
            The result of the target function.

        Raises:
            KeyError: If the verb is not recognized.
            AttributeError: If the associated function is not callable.
            Exception: Re-raises any exception raised by the target function.
        """
        # Route CLI verb to its configured module and function
        if verb not in self.verbs:
            raise KeyError(f"Unknown verb: {verb}")
        module_path, func_name = self.verbs[verb]
        # Load module under alias equal to verb
        self.load_module(module_path, alias=verb)
        module = self._get_module(verb)
        func = getattr(module, func_name, None)
        if not callable(func):
            raise AttributeError(f"{func_name} is not callable for verb {verb}")
        self._log("🔄 Running verb", f"{verb} -> {module_path}.{func_name}()")
        try:
            return func(**kwargs)
        except Exception as exc:
            self._log(
                "❌ Function execution failed",
                f"{module_path}.{func_name}() for verb '{verb}' → {type(exc).__name__}: {exc}",
            )
            raise  # Re-raise the original exception

    def available_functions(self, module_key: str) -> List[str]:
        """
        List public functions available in a loaded module.

        Args:
            module_key: The key (alias or path) of the loaded module.

        Returns:
            A list of public function names.

        Raises:
            KeyError: If the module is not loaded.
        """
        module = self._get_module(module_key)
        return [
            n
            for n, obj in inspect.getmembers(module)
            if inspect.isfunction(obj) and not n.startswith("_")
        ]

    def list_loaded_modules(self) -> List[str]:
        """
        List the keys of all currently loaded modules.

        Returns:
            A list of module keys (aliases or paths).
        """
        return list(self.modules.keys())

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def _get_module(self, key: str) -> ModuleType:
        """
        Retrieve a loaded module by its key.

        Args:
            key: The key (alias or path) of the module.

        Returns:
            The loaded module object.

        Raises:
            KeyError: If the module is not loaded.
        """
        if key not in self.modules:
            raise KeyError(f"Module '{key}' not loaded")
        return self.modules[key]

    @staticmethod
    def _log(prefix: str, msg: str) -> None:
        """
        Centralized logging for the FunctionRouter.

        Args:
            prefix: A prefix for the log message (e.g., "✅ Loaded module").
            msg: The main log message content.
        """
        print(f"[Router] {prefix}: {msg}", file=sys.stderr)
