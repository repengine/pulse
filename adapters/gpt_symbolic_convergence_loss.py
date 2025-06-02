"""
gpt_symbolic_convergence_loss.py

Computes symbolic divergence (loss) between Pulse and GPT outputs.
Supports hybrid learning and alignment by quantifying differences in symbolic tags, capital outcomes, rule traces, and trust deltas.

Core Functions:
- compute_symbolic_convergence_loss: Calculates the loss between Pulse and GPT outputs.
- decompose_loss_components: Breaks down the loss into interpretable components for diagnostics and curriculum learning.

Author: [Your Name]
Date: 2025-04-24
"""

from typing import Dict, Optional
from intelligence.forecast_schema import ForecastSchema
from pydantic import ValidationError


def compute_symbolic_convergence_loss(
    pulse_output: ForecastSchema,
    gpt_output: ForecastSchema,
    weights: Optional[Dict[str, float]] = None,
) -> float:
    """
    Computes the symbolic convergence loss between Pulse and GPT outputs.

    Args:
        pulse_output (Dict[str, Any]): Output from Pulse (symbolic tags, capital outcome, rule trace, trust).
        gpt_output (Dict[str, Any]): Output from GPT (same structure).
        weights (Dict[str, float], optional): Weights for each loss component.

    Returns:
        float: The total symbolic convergence loss.
    """
    if weights is None:
        weights = {
            "symbolic_tag": 1.0,
            "capital_outcome": 1.0,
            "rule_trace": 1.0,
            "trust_penalty": 1.0,
        }
    loss = 0.0
    loss += weights["symbolic_tag"] * delta(
        pulse_output.symbolic_tag, gpt_output.symbolic_tag
    )
    loss += weights["capital_outcome"] * delta(
        pulse_output.capital_outcome, gpt_output.capital_outcome
    )
    loss += weights["rule_trace"] * delta(
        pulse_output.rule_trace, gpt_output.rule_trace
    )
    loss += weights["trust_penalty"] * delta(pulse_output.trust, gpt_output.trust)
    return loss


def delta(a, b) -> float:
    """
    Computes a simple difference or distance between two values.
    Extend this function for more sophisticated comparison (e.g., edit distance, cosine similarity).

    Args:
        a: First value.
        b: Second value.

    Returns:
        float: Distance or difference.
    """
    if a is None or b is None:
        return 1.0  # Max penalty for missing data
    if isinstance(a, (int, float)) and isinstance(b, (int, float)):
        return abs(a - b)
    if isinstance(a, str) and isinstance(b, str):
        return 0.0 if a == b else 1.0
    if isinstance(a, list) and isinstance(b, list):
        # Jaccard distance for sets
        set_a, set_b = set(a), set(b)
        if not set_a and not set_b:
            return 0.0
        return 1.0 - len(set_a & set_b) / max(len(set_a | set_b), 1)
    if isinstance(a, dict) and isinstance(b, dict):
        # Compare keys and values
        keys = set(a.keys()) | set(b.keys())
        dist = 0.0
        for k in keys:
            dist += delta(a.get(k), b.get(k))
        return dist / max(len(keys), 1)
    return 1.0


def decompose_loss_components(
    pulse_output: ForecastSchema, gpt_output: ForecastSchema
) -> Dict[str, float]:
    """
    Decomposes the symbolic convergence loss into its components.

    Args:
        pulse_output (Dict[str, Any]): Output from Pulse.
        gpt_output (Dict[str, Any]): Output from GPT.

    Returns:
        Dict[str, float]: Loss for each component.
    """
    return {
        "symbolic_tag": delta(pulse_output.symbolic_tag, gpt_output.symbolic_tag),
        "capital_outcome": delta(
            pulse_output.capital_outcome, gpt_output.capital_outcome
        ),
        "rule_trace": delta(pulse_output.rule_trace, gpt_output.rule_trace),
        "trust_penalty": delta(pulse_output.trust, gpt_output.trust),
    }


# Example usage (for testing)
if __name__ == "__main__":
    # Example usage (for testing)
    # Create instances of ForecastSchema for testing
    pulse_data = {
        "pulse_output": "...",
        "gpt_struct": "...",
        "gpt_output": "...",
        "pulse_domains": [],
        "pulse_rules": [],
        "symbolic_tag": "hope",
        "capital_outcome": 100,
        "rule_trace": [],
        "trust": 0.8,
    }
    gpt_data = {
        "pulse_output": "...",
        "gpt_struct": "...",
        "gpt_output": "...",
        "pulse_domains": [],
        "pulse_rules": [],
        "symbolic_tag": "despair",
        "capital_outcome": 90,
        "rule_trace": [],
        "trust": 0.6,
    }

    try:
        pulse_forecast = ForecastSchema(**pulse_data)
        gpt_forecast = ForecastSchema(**gpt_data)

        print(
            "Total Loss:",
            compute_symbolic_convergence_loss(pulse_forecast, gpt_forecast),
        )
        print(
            "Loss Components:", decompose_loss_components(pulse_forecast, gpt_forecast)
        )

    except ValidationError as e:
        print(f"Example data validation failed: {e}")
