"""
Module: pulse_rule_explainer.py
Pulse Version: v0.100.8
Location: simulation_engine/rules/

Purpose:
Explains which rule fingerprints contributed to a forecast.
Detects matched triggers, aligned effects, and symbolic alignment.

Features:
- Match forecast triggers and outcomes to rule fingerprints
- Return best rule matches with confidence scores
- CLI and JSONL batch support

Author: Pulse AI Engine
"""

import json
from typing import Dict, List, Tuple

def load_rule_fingerprints(path="data/rule_fingerprints.json") -> Dict:
    with open(path, "r") as f:
        return json.load(f)

def match_forecast_to_rules(forecast: Dict, rules: Dict) -> List[Dict]:
    """
    Score all rules against a single forecast.
    Returns ranked list of rule matches.
    """
    trigger = forecast.get("trigger", forecast.get("alignment", {}))
    outcome = forecast.get("forecast", {}).get("symbolic_change", {})
    score_list = []

    for rule_id, rule in rules.items():
        r_trig = rule.get("trigger", {})
        r_eff = rule.get("effect", {})
        match_count = 0
        total = 0

        for k, v in r_trig.items():
            if k in trigger:
                total += 1
                if str(trigger[k]) == str(v):
                    match_count += 1

        for k, v in r_eff.items():
            if k in outcome:
                total += 1
                if str(outcome[k]).startswith(str(v)[0]):
                    match_count += 1

        if total > 0:
            confidence = round(match_count / total, 3)
            score_list.append({
                "rule_id": rule_id,
                "trigger_matches": match_count,
                "total_fields": total,
                "confidence": confidence,
                "description": rule.get("description", "")
            })

    return sorted(score_list, key=lambda x: -x["confidence"])

def explain_forecast(forecast: Dict, rules: Dict) -> Dict:
    """
    Returns top 3 rules with explanation scores.
    """
    top_rules = match_forecast_to_rules(forecast, rules)[:3]
    return {
        "trace_id": forecast.get("trace_id"),
        "symbolic_tag": forecast.get("symbolic_tag"),
        "top_rules": top_rules
    }

def explain_forecast_batch(forecasts: List[Dict], rule_file="data/rule_fingerprints.json") -> List[Dict]:
    rules = load_rule_fingerprints(rule_file)
    return [explain_forecast(f, rules) for f in forecasts]

# CLI
if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Pulse Rule Explainer CLI")
    parser.add_argument("--file", required=True, help="Forecast batch (.jsonl)")
    args = parser.parse_args()

    forecasts = []
    with open(args.file, "r") as f:
        for line in f:
            try:
                forecasts.append(json.loads(line.strip()))
            except:
                continue

    explanations = explain_forecast_batch(forecasts)
    print(json.dumps(explanations, indent=2))