"""
capital_layer_cli.py

CLI tool for running shortview forecasts and portfolio alignment summary.

Usage:
    python -m capital_engine.capital_layer_cli
"""

from capital_engine.capital_layer import run_shortview_forecast, summarize_exposure, portfolio_alignment_tags
from simulation_engine.worldstate import WorldState

# Dummy worldstate values for testing
mock_vars = {
    "hope": 0.6,
    "despair": 0.2,
    "fatigue": 0.3,
    "trust": 0.7,
    "rage": 0.1,
    "inflation_index": 0.03,
    "market_volatility_index": 0.4
}

if __name__ == "__main__":
    print("🧠 Running Capital Shortview CLI...")
    ws = WorldState(**mock_vars)
    forecast = run_shortview_forecast(ws)
    print("---- Shortview Forecast ----")
    for k, v in forecast.items():
        print(f"{k}: {v}")
    print("\n---- Exposure Summary ----")
    print(summarize_exposure(ws))
    print("\n---- Alignment Tags ----")
    print(portfolio_alignment_tags(ws))
