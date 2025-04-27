"""
Iris Plugin Manager

Manages dynamic ingestion plugins for Iris.
Plugins must return List[Dict] formatted signals.

Author: Pulse Development Team
Date: 2025-04-27
"""

import logging
from typing import Callable, List, Dict

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
                logger.error("[IrisPluginManager] Plugin %s failed: %s", plugin.__name__, e)
        return aggregated_signals

    def list_plugins(self) -> List[str]:
        """
        List names of currently registered plugins.

        Returns:
            List[str]: Plugin function names.
        """
        return [plugin.__name__ for plugin in self.plugins]
