"""
rule_autoevolver.py

Meta-learning module for evaluating, mutating, and deprecating rules based on performance, drift, and coherence.

Responsibilities:
- Score and mutate rules based on forecast regret, drift, and trust
- Deprecate or promote rules as needed
- Use centralized rule registry, matching, and validation utilities

All rule access and validation should use shared utilities for consistency.
"""

import json
import logging
import os
from typing import Dict, List, Optional
from rules.rule_registry import RuleRegistry
from engine.rule_mutation_engine import propose_rule_mutations
from engine.simulation_drift_detector import run_simulation_drift_analysis

MUTATION_LOG_PATH = "logs/rule_mutation_log.jsonl"
TRUST_LOG_PATH = "logs/rule_trust_log.jsonl"

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("rule_autoevolver")

_registry = RuleRegistry()
_registry.load_all_rules()


def log_action(log_path: str, entry: dict):
    """Append an action to a log file."""
    try:
        os.makedirs(os.path.dirname(log_path), exist_ok=True)
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry) + "\n")
    except Exception as e:
        logger.error(f"Failed to log action: {e}")


def score_rule_from_forecast(rule_id: str, forecast: dict, outcome: dict) -> float:
    """
    Score rule trust based on forecast performance (stub: extend with PFPA, regret, etc).
    Returns a float trust score.
    """
    # Placeholder: use forecast['confidence'] or outcome delta
    score = forecast.get("confidence", 0.5)
    log_action(
        TRUST_LOG_PATH,
        {
            "rule_id": rule_id,
            "score": score,
            "forecast": forecast.get("trace_id"),
            "outcome": outcome,
        },
    )
    return score


def detect_drifted_rules(prev_trace: str, curr_trace: str) -> Dict:
    """
    Detect rules with drift/volatility between two traces.
    Returns a dict of drift metrics.
    """
    try:
        return run_simulation_drift_analysis(prev_trace, curr_trace)
    except Exception as e:
        logger.error(f"Drift detection failed: {e}")
        return {}


def propose_mutation(rule_id: str, dry_run: bool = False) -> Optional[Dict]:
    """
    Suggest mutation for a rule (threshold, effects, tags).
    If dry_run is True, do not apply mutation.
    Returns the mutation dict or None.
    """
    rules = {r.get("rule_id", r.get("id")): r for r in _registry.rules}
    if rule_id not in rules:
        logger.warning(f"Rule not found: {rule_id}")
        return None
    mutation = propose_rule_mutations({rule_id: rules[rule_id]}, top_n=1)
    if mutation:
        log_action(
            MUTATION_LOG_PATH,
            {"rule_id": rule_id, "mutation": mutation[0], "dry_run": dry_run},
        )
        if not dry_run:
            rules[rule_id].update(mutation[0])
        return mutation[0]
    return None


def deprecate(rule_id: str, dry_run: bool = False) -> bool:
    """
    Disable a rule (soft deprecation). Returns True if successful.
    If dry_run is True, do not apply.
    """
    for rule in _registry.rules:
        if rule.get("rule_id") == rule_id or rule.get("id") == rule_id:
            if not dry_run:
                rule["enabled"] = False
            log_action(
                MUTATION_LOG_PATH,
                {"rule_id": rule_id, "action": "deprecate", "dry_run": dry_run},
            )
            return True
    logger.warning(f"Rule not found for deprecation: {rule_id}")
    return False


def promote_from_candidate(verbose: bool = False) -> List[str]:
    """
    Promote all eligible candidate rules. Returns list of promoted rule_ids.
    """
    promoted = []
    for rule in list(_registry.candidate_rules):
        if rule.get("enabled", False):
            _registry.promote_candidate(rule.get("rule_id", rule.get("id")))
            promoted.append(rule.get("rule_id", rule.get("id")))
            log_action(
                MUTATION_LOG_PATH,
                {
                    "rule_id": rule.get("rule_id", rule.get("id")),
                    "action": "promote_candidate",
                },
            )
            if verbose:
                print(f"Promoted candidate: {rule.get('rule_id', rule.get('id'))}")
    return promoted


def batch_score_rules(forecast_file: str) -> Dict[str, float]:
    """
    Batch score all rules against a forecast file.
    Returns a dict of rule_id to score.
    """
    try:
        with open(forecast_file, "r") as f:
            forecasts = json.load(f)
        results = {}
        for fc in forecasts:
            for rule in _registry.rules:
                rid = rule.get("rule_id", rule.get("id"))
                results[rid] = score_rule_from_forecast(rid, fc, fc.get("outcome", {}))
        return results
    except Exception as e:
        logger.error(f"Batch scoring failed: {e}")
        return {}


def audit_summary() -> None:
    """
    Print a summary of recent mutations and trust changes for operator review.
    """
    print("\n=== Rule Mutation Log ===")
    if os.path.exists(MUTATION_LOG_PATH):
        with open(MUTATION_LOG_PATH, "r") as f:
            for line in f.readlines()[-10:]:
                print(line.strip())
    print("\n=== Rule Trust Log ===")
    if os.path.exists(TRUST_LOG_PATH):
        with open(TRUST_LOG_PATH, "r") as f:
            for line in f.readlines()[-10:]:
                print(line.strip())


# --- CLI ---
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Pulse Rule Autoevolver CLI\n\n"
        "--mutate rule_id [--dry-run]         Propose mutation for rule_id\n"
        "--score rule_id forecast.json        Score rule_id against forecast.json\n"
        "--run-drift-checks prev curr        Run drift checks between two traces\n"
        "--promote-candidates                Promote all eligible candidate rules\n"
        "--deprecate rule_id [--dry-run]      Deprecate (disable) a rule\n"
        "--batch-score forecast.json          Batch score all rules\n"
        "--audit-summary                      Print recent mutation/trust log entries\n"
        "--verbose                            Verbose output\n"
    )
    parser.add_argument("--mutate", type=str, help="Propose mutation for rule_id")
    parser.add_argument("--score", nargs=2, help="Score rule_id against forecast.json")
    parser.add_argument(
        "--run-drift-checks",
        nargs=2,
        metavar=("prev", "curr"),
        help="Run drift checks between two traces",
    )
    parser.add_argument(
        "--promote-candidates",
        action="store_true",
        help="Promote all eligible candidate rules",
    )
    parser.add_argument("--deprecate", type=str, help="Deprecate (disable) a rule")
    parser.add_argument(
        "--dry-run", action="store_true", help="Dry run (no changes applied)"
    )
    parser.add_argument(
        "--batch-score", type=str, help="Batch score all rules against forecast file"
    )
    parser.add_argument(
        "--audit-summary",
        action="store_true",
        help="Print recent mutation/trust log entries",
    )
    parser.add_argument("--verbose", action="store_true", help="Verbose output")
    args = parser.parse_args()

    if args.mutate:
        result = propose_mutation(args.mutate, dry_run=args.dry_run)
        print(
            json.dumps(result, indent=2)
            if result
            else f"No mutation proposed for {args.mutate}"
        )
    if args.score:
        rule_id, forecast_file = args.score
        try:
            with open(forecast_file, "r") as f:
                forecast = json.load(f)
            score = score_rule_from_forecast(
                rule_id, forecast, forecast.get("outcome", {})
            )
            print(f"Rule {rule_id} score: {score}")
        except Exception as e:
            logger.error(f"Score failed: {e}")
    if args.run_drift_checks:
        prev, curr = args.run_drift_checks
        drift = detect_drifted_rules(prev, curr)
        print(json.dumps(drift, indent=2))
    if args.promote_candidates:
        promoted = promote_from_candidate(verbose=args.verbose)
        print(f"Promoted candidates: {promoted}")
    if args.deprecate:
        ok = deprecate(args.deprecate, dry_run=args.dry_run)
        print(f"Rule {args.deprecate} deprecated: {ok}")
    if args.batch_score:
        results = batch_score_rules(args.batch_score)
        print(json.dumps(results, indent=2))
    if args.audit_summary:
        audit_summary()
