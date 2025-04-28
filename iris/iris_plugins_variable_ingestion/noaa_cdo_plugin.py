"""NOAA CDO � climate plugin stub.

Set `enabled=True` when ready and fill in `fetch_signals`.
"""
from typing import List, Dict, Any
from iris.iris_plugins import IrisPluginManager

class NoaaCdoPlugin(IrisPluginManager):
    plugin_name = "noaa_cdo_plugin"
    enabled = False     # flip to True and provide API key to activate
    concurrency = 2

    def fetch_signals(self) -> List[Dict[str, Any]]:
        # TODO: implement real fetch + formatting
        return []

    def additional_method(self) -> None:

        pass
