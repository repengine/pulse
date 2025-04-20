"""
Module: pulse_regret_chain.py
Pulse Version: v0.100.4
Location: pulse/trust/

Purpose:
Tracks a sequence of regret events — forecast errors, missed scenarios, symbolic contradictions — and stores them as a learning chain.

Features:
- Log regret events (forecast_id, arc_label, rule_id, reason, etc.)
- Get full regret chain (JSONL-based)
- Print summary of causes and repeat errors
- CLI interface for adding, viewing, and marking reviewed regrets

Author: Pulse AI Engine
"""

import json
import os
from typing import List, Dict

REGRET_LOG = "data/regret_chain.jsonl"

def ensure_log_path(path=REGRET_LOG):
    os.makedirs(os.path.dirname(path), exist_ok=True)

def log_regret_event(trace_id: str, reason: str, arc_label: str = None, rule_id: str = None,
                     timestamp: str = None, feedback: str = "", review_status: str = "Unreviewed") -> Dict:
    """
    Append a regret event to the regret chain log.
    """
    ensure_log_path()
    event = {
        "trace_id": trace_id,
        "reason": reason,
        "arc_label": arc_label,
        "rule_id": rule_id,
        "timestamp": timestamp,
        "feedback": feedback,
        "review_status": review_status
    }
    with open(REGRET_LOG, "a") as f:
        f.write(json.dumps(event) + "\n")
    return event

def get_regret_chain() -> List[Dict]:
    """
    Load all regret events from disk.
    """
    ensure_log_path()
    regrets = []
    if os.path.exists(REGRET_LOG):
        with open(REGRET_LOG, "r") as f:
            for line in f:
                try:
                    regrets.append(json.loads(line.strip()))
                except:
                    continue
    return regrets

def print_regret_summary(regrets: List[Dict]):
    """
    Summarize regret causes and patterns.
    """
    print(f"📉 Regret Chain: {len(regrets)} total regrets")
    arc_count = {}
    rule_count = {}
    for r in regrets:
        arc = r.get("arc_label", "Unknown")
        rule = r.get("rule_id", "N/A")
        arc_count[arc] = arc_count.get(arc, 0) + 1
        rule_count[rule] = rule_count.get(rule, 0) + 1
    print("🔁 Top Symbolic Arcs:")
    for k, v in sorted(arc_count.items(), key=lambda x: -x[1]):
        print(f"  {k}: {v}")
    print("🔍 Top Rule Triggers:")
    for k, v in sorted(rule_count.items(), key=lambda x: -x[1]):
        print(f"  {k}: {v}")

def mark_regret_reviewed(trace_id: str, status: str = "Operator-Reviewed"):
    """
    Update a regret entry to mark it as reviewed.
    """
    regrets = get_regret_chain()
    updated = False
    with open(REGRET_LOG, "w") as f:
        for r in regrets:
            if r.get("trace_id") == trace_id:
                r["review_status"] = status
                updated = True
            f.write(json.dumps(r) + "\n")
    return updated

# CLI entry
if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Pulse Regret Chain CLI")
    parser.add_argument("--add", nargs=2, metavar=("trace_id", "reason"), help="Add a new regret")
    parser.add_argument("--arc", help="Arc label for new regret")
    parser.add_argument("--rule", help="Rule ID for new regret")
    parser.add_argument("--timestamp", help="Timestamp for new regret")
    parser.add_argument("--feedback", help="Operator notes")
    parser.add_argument("--summary", action="store_true", help="Print regret summary")
    parser.add_argument("--review", metavar="trace_id", help="Mark a regret as reviewed")

    args = parser.parse_args()
    if args.add:
        trace_id, reason = args.add
        event = log_regret_event(trace_id, reason, arc_label=args.arc, rule_id=args.rule,
                                 timestamp=args.timestamp, feedback=args.feedback)
        print("Logged regret:", event)
    elif args.review:
        updated = mark_regret_reviewed(args.review)
        print("Review status updated." if updated else "Trace ID not found.")
    elif args.summary:
        regrets = get_regret_chain()
        print_regret_summary(regrets)
    else:
        regrets = get_regret_chain()
        for r in regrets:
            print(json.dumps(r, indent=2))
