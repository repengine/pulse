# Retrodiction & Reverse Rule Engine

## Overview

The Pulse project supports **retrodiction**—the process of inferring plausible prior states and causal chains from observed state deltas—via a modular **Reverse Rule Engine**. This system enables backward simulation, causal analysis, and integration with Trust and Symbolic systems.

---

## Core Concepts

- **Retrodiction**: Backward inference of prior world states and causal rules from observed changes in overlays/variables.
- **Reverse Rule Engine**: Matches observed deltas to rule fingerprints, reconstructs possible causal chains, and integrates with trust and symbolic scoring.

---

## Architecture & Integration

### Main Components

- `simulation_engine/rules/reverse_rule_engine.py`: Core logic for tracing causal rule chains from deltas.
- `simulation_engine/simulator_core.py`: Integration point; calls `reverse_rule_engine` during backward simulation.
- **Trust System**: Used to score the plausibility of inferred rule chains.
- **Symbolic System**: Used to extract and score symbolic tags associated with inferred rules.

### Key Interface

```python
def reverse_rule_engine(state: WorldState, overlays: Dict[str, float], variables: Dict[str, float], step: int = 1) -> dict:
    """
    Args:
        state: The current WorldState (not mutated)
        overlays: The overlays at this step (dict)
        variables: The variables at this step (dict)
        step: The backward step index (1 = most recent prior)
    Returns:
        Dict with:
            - rule_chains: List of possible rule chains (list of rule_id lists)
            - symbolic_tags: List of symbolic tags associated with matched rules
            - trust_scores: List of trust/confidence scores for each chain
            - symbolic_confidence: List of symbolic confidence scores for each chain
            - suggestions: Any suggested new rules if no match found
    """
```

---

## How It Works

1. **Delta Calculation**: The engine receives overlays/variables and computes the delta to be explained.
2. **Rule Fingerprinting**: Uses fingerprints to match deltas to possible causal rules (supports fuzzy and trust-weighted matching).
3. **Causal Chain Tracing**: Recursively traces possible multi-step rule chains that could explain the observed delta.
4. **Symbolic & Trust Integration**:
    - Extracts symbolic tags from matched rules and computes symbolic confidence.
    - Uses the TrustEngine to score the plausibility of each inferred chain.
5. **Suggestions**: If no match is found, suggests new rule fingerprints for future learning.

---

## Integration Guidelines

- **Simulation Engine**: Use `reverse_rule_engine` in backward simulation or analysis workflows.
- **Trust System**: Trust scores are computed for each inferred chain; can be used for filtering or ranking.
- **Symbolic System**: Symbolic tags and confidence scores are provided for downstream symbolic analysis.
- **Extensibility**: The engine is modular—new rule types, fingerprinting strategies, or integration hooks can be added as needed.

---

## Example Usage

```python
from simulation_engine.simulator_core import reverse_rule_engine
state = ...  # WorldState instance
overlays = {"hope": 0.5, "despair": -0.1}
variables = {"energy_cost": 1.0}
result = reverse_rule_engine(state, overlays, variables, step=1)
print(result["rule_chains"])  # Possible causal rule chains
print(result["symbolic_tags"])  # Symbolic tags for each chain
print(result["trust_scores"])  # Trust/confidence scores
print(result["suggestions"])   # Suggestions for new rules if no match
```

---

## Testing

- Comprehensive unit and integration tests are provided in `tests/test_simulator_core.py` and related files.
- Tests cover:
    - Rule chain inference
    - Symbolic and trust integration
    - Edge cases and suggestions

---

## Extension Notes

- To add new rule types or fingerprints, update the rule registry and fingerprinting logic.
- To extend symbolic or trust integration, implement additional hooks in the respective interfaces.

---

## References

- See also: `simulation_engine/rules/rule_matching_utils.py`, `interfaces/symbolic_interface.py`, `interfaces/trust_interface.py`