#!/usr/bin/env python
"""
Generate empty plugin stubs so devs can fill them incrementally.
Run once; idempotent (won't overwrite changed files).
"""

import textwrap
import pathlib
import json
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]  # …\pulse
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


STUBS = json.loads(r"""
[
  ["gdelt_plugin",         "GDELT v2 REST",            "geopolitics"],
  ["acled_plugin",         "ACLED API",                "geopolitics"],
  ["world_bank_plugin",    "World Bank OData",         "geopolitics"],
  ["cia_factbook_plugin",  "CIA Factbook JSON",        "geopolitics"],

  ["reddit_plugin",        "Reddit API",               "sentiment"],
  ["newsapi_plugin",       "NewsAPI",                  "sentiment"],
  ["google_trends_plugin", "Google Trends (PyTrends)", "sentiment"],
  ["twitter_plugin",       "X API (v2)",               "sentiment"],

  ["noaa_cdo_plugin",      "NOAA CDO",                 "climate"],
  ["open_meteo_plugin",    "Open-Meteo",               "climate"],
  ["nasa_power_plugin",    "NASA POWER",               "climate"],
  ["openaq_plugin",        "OpenAQ",                   "climate"],

  ["github_plugin",        "GitHub REST",              "technology"],
  ["hackernews_plugin",    "Hacker News Firebase",     "technology"],
  ["stackexchange_plugin", "Stack Exchange API",       "technology"],
  ["patentsview_plugin",   "USPTO PatentsView",        "technology"],

  ["who_gho_plugin",       "WHO GHO OData",            "health"],
  ["cdc_socrata_plugin",   "CDC Open Data",            "health"],
  ["openfda_plugin",       "openFDA",                  "health"],
  ["healthmap_plugin",     "HealthMap RSS",            "health"],

  ["mediastack_plugin",    "Mediastack News",          "general"],
  ["wikidata_plugin",      "Wikidata SPARQL",          "general"],
  ["data_portal_plugin",   "Data.gov / EU Open Data",  "general"],
  ["wolfram_plugin",       "Wolfram Alpha API",        "general"]
]
""")

BASE_DIR = pathlib.Path("iris_plugins_variable_ingestion")
BASE_DIR.mkdir(exist_ok=True, parents=True)

TEMPLATE = textwrap.dedent("""\
    \"\"\"{desc} — {domain} plugin stub.

    Set `enabled=True` when ready and fill in `fetch_signals`.
    \"\"\"
    from typing import List, Dict, Any
    from ingestion.iris_plugins import IrisScraper

    class {cls}(IrisScraper):
        plugin_name = "{name}"
        enabled = False     # flip to True and provide API key to activate
        concurrency = 2

        def fetch_signals(self) -> List[Dict[str, Any]]:
            # TODO: implement real fetch + formatting
            return []

        def additional_method(self) -> None:

            pass
""")

for stub, desc, domain in STUBS:
    path = BASE_DIR / f"{stub}.py"
    if path.exists():
        print("skip", path)
        continue
    code = TEMPLATE.format(
        desc=desc,
        domain=domain,
        cls="".join(part.title() for part in stub.split("_")),
        name=stub,
    )
    path.write_text(code)
    print("created", path)
