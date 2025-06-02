"""
Iris Plugin Manager

Manages dynamic ingestion plugins for ingestion.
Plugins must return List[Dict] formatted signals.

Author: Pulse Development Team
Date: 2025-04-27
"""

import logging
from typing import Callable, List, Dict
import os
import importlib
import inspect

logger = logging.getLogger(__name__)


class IrisPluginManager:
    def __init__(self):
        """
        Initialize the Iris Plugin Manager.
        """
        self.plugins: List[Callable[[], List[Dict]]] = []

    def register_plugin(self, plugin_fn: Callable[[], List[Dict]]) -> None:
        """
        Register a new ingestion plugin.

        Args:
            plugin_fn (Callable): A function that returns a list of signal dictionaries.
        """
        self.plugins.append(plugin_fn)
        logger.info("[IrisPluginManager] Plugin registered: %s", plugin_fn.__name__)

    def run_plugins(self) -> List[Dict]:
        """
        Execute all registered plugins and collect signals.

        Returns:
            List[Dict]: Aggregated signals from all plugins.
        """
        aggregated_signals = []
        for plugin in self.plugins:
            try:
                signals = plugin()
                if signals:
                    aggregated_signals.extend(signals)
            except Exception as e:
                logger.error(
                    "[IrisPluginManager] Plugin %s failed: %s", plugin.__name__, e
                )
        return aggregated_signals

    def list_plugins(self) -> List[str]:
        """
        List names of currently registered plugins.

        Returns:
            List[str]: Plugin function names.
        """
        return [plugin.__name__ for plugin in self.plugins]

    def autoload(self) -> None:
        """
        Auto-register default ingestion plugins:
          - finance_plugins
          - vi_plugin
          - any enabled IrisIngestionPlugin subclasses under iris_plugins_variable_ingestion package
        """
        # finance + core variable ingestion
        from .iris_plugins_finance import finance_plugins
        from .iris_plugins_variable_ingestion import vi_plugin

        self.register_plugin(finance_plugins)
        self.register_plugin(vi_plugin)
        # register every _plugin function and every enabled IrisIngestionPlugin in the variable_ingestion folder

        var_dir = os.path.join(
            os.path.dirname(__file__), "iris_plugins_variable_ingestion"
        )
        for fname in os.listdir(var_dir):
            if not fname.endswith(".py") or fname.startswith("_"):
                continue
            mod_name = fname[:-3]
            mod = importlib.import_module(
                f"{__package__}.iris_plugins_variable_ingestion.{mod_name}"
            )
            # register any free functions ending in '_plugin'
            for attr in dir(mod):
                obj = getattr(mod, attr)
                if callable(obj) and attr.endswith("_plugin"):
                    self.register_plugin(obj)
            # register any enabled IrisIngestionPlugin subclasses
            for cls in vars(mod).values():
                if (
                    inspect.isclass(cls)
                    and issubclass(cls, IrisPluginManager)
                    and cls is not IrisPluginManager
                ):
                    inst = cls()
                    if getattr(inst, "enabled", False):
                        self.register_plugin(inst.fetch_signals)
        logger.info(
            "[IrisPluginManager] Autoloaded finance, vi_plugin, and any enabled variable stubs"
        )
