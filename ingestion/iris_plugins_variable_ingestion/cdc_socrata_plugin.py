"""CDC Open Data � health plugin stub.

Set `enabled=True` when ready and fill in `fetch_signals`.
"""

from typing import List, Dict, Any
from ingestion.iris_plugins import IrisPluginManager


class CdcSocrataPlugin(IrisPluginManager):
    plugin_name = "cdc_socrata_plugin"
    enabled = False  # flip to True and provide API key to activate
    concurrency = 2

    def fetch_signals(self) -> List[Dict[str, Any]]:
        # TODO: implement real fetch + formatting
        return []

    def additional_method(self) -> None:
        pass
