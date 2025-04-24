"""
causal_inference.py

CausalInferenceEngine: Discovers and validates causal relationships using DoWhy (if available) or standard statistical methods. Generates human-readable explanations for rule changes, logs all discoveries, and provides a CLI entry point.
"""

import pandas as pd
from core.pulse_learning_log import log_learning_event
from datetime import datetime

try:
    import dowhy
    from dowhy import CausalModel
    DOWHY_AVAILABLE = True
except ImportError:
    DOWHY_AVAILABLE = False

class CausalInferenceEngine:
    def __init__(self):
        pass

    def discover_causal_relationships(self, data, treatment, outcome):
        df = pd.DataFrame(data)
        if DOWHY_AVAILABLE:
            model = CausalModel(
                data=df,
                treatment=treatment,
                outcome=outcome,
                common_causes=[col for col in df.columns if col not in [treatment, outcome]]
            )
            identified_estimand = model.identify_effect()
            estimate = model.estimate_effect(identified_estimand, method_name="backdoor.linear_regression")
            explanation = model.refute_estimate(identified_estimand, estimate, method_name="placebo_treatment_refuter")
            log_learning_event("causal_inference_discovery", {
                "treatment": treatment,
                "outcome": outcome,
                "estimate": str(estimate.value),
                "refutation": str(explanation),
                "timestamp": datetime.utcnow().isoformat()
            })
            return estimate.value, explanation
        else:
            # Fallback: use correlation
            corr = df[treatment].corr(df[outcome])
            log_learning_event("causal_inference_discovery", {
                "treatment": treatment,
                "outcome": outcome,
                "correlation": corr,
                "timestamp": datetime.utcnow().isoformat()
            })
            return corr, None

    def explain_rule_change(self, rule_id, cause, effect, estimate):
        explanation = f"Rule {rule_id} was changed because {cause} has a causal effect on {effect} (estimate: {estimate})."
        log_learning_event("causal_inference_explanation", {
            "rule_id": rule_id,
            "cause": cause,
            "effect": effect,
            "estimate": estimate,
            "explanation": explanation,
            "timestamp": datetime.utcnow().isoformat()
        })
        return explanation

if __name__ == "__main__":
    import argparse
    import numpy as np
    parser = argparse.ArgumentParser(description="Causal Inference CLI")
    parser.add_argument("--discover", nargs=2, metavar=("treatment", "outcome"), help="Discover causal relationship between treatment and outcome on random data")
    parser.add_argument("--explain", nargs=3, metavar=("rule_id", "cause", "effect"), help="Explain a rule change causally")
    args = parser.parse_args()
    engine = CausalInferenceEngine()
    # Dummy data for demonstration
    data = pd.DataFrame({
        "A": np.random.rand(100),
        "B": np.random.rand(100),
        "C": np.random.rand(100)
    })
    if args.discover:
        treatment, outcome = args.discover
        estimate, explanation = engine.discover_causal_relationships(data, treatment, outcome)
        print(f"Causal estimate: {estimate}\nExplanation: {explanation}")
    if args.explain:
        rule_id, cause, effect = args.explain
        explanation = engine.explain_rule_change(rule_id, cause, effect, estimate="0.42")
        print("Explanation:", explanation)
