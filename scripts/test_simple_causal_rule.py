# scripts/test_simple_causal_rule.py
from engine.variable_accessor import get_variable, set_variable
from engine.pulse_config import CONFIDENCE_THRESHOLD
from rules.static_rules import build_static_rules
from engine.rule_engine import run_rules
from engine.worldstate import WorldState, Variables
import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def main():
    print("--- Testing Simple Causal Rule Application ---")

    # 1. Initialize WorldState
    ws = WorldState()
    ws.variables = Variables(data={})  # Ensure variables.data is initialized

    # 2. Set initial variables for R001_EnergySpike
    initial_energy_price = CONFIDENCE_THRESHOLD + 0.1  # Ensure condition is met
    initial_inflation_index = 0.05
    rule_effect_size = 0.01  # Default effect_size for R001

    set_variable(ws, "energy_price_index", initial_energy_price)
    set_variable(ws, "inflation_index", initial_inflation_index)

    print(f"Initial energy_price_index: {get_variable(ws, 'energy_price_index')}")
    print(f"Initial inflation_index: {get_variable(ws, 'inflation_index')}")
    print(f"Rule CONFIDENCE_THRESHOLD: {CONFIDENCE_THRESHOLD}")

    # 3. Load static rules (which includes R001_EnergySpike)
    # The run_rules function internally gets rules from the registry,
    # which should load them. We don't need to manually pick one here,
    # but ensure the conditions for R001 are met.

    # 4. Apply rules
    print("Running rules...")
    run_rules(ws)  # run_rules will use the RuleRegistry which loads static_rules

    # 5. Verify output
    final_inflation_index = get_variable(ws, "inflation_index")
    expected_inflation_index = initial_inflation_index + rule_effect_size

    print(f"Final inflation_index: {final_inflation_index}")
    print(f"Expected inflation_index: {expected_inflation_index}")

    if abs(final_inflation_index - expected_inflation_index) < 1e-5:
        print("SUCCESS: R001_EnergySpike rule applied correctly.")
        # Update assessment document - Causal Rules: Largely Operational (Simple
        # Case Passed)
    else:
        print("FAILURE: R001_EnergySpike rule did NOT apply as expected.")
        print(
            f"  Delta: {
                final_inflation_index -
                initial_inflation_index}, Expected Delta: {rule_effect_size}")


if __name__ == "__main__":
    main()
