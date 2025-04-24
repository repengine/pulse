"""
learning_log_viewer.py

Displays and summarizes the Pulse learning log.
Useful for operator review, audits, and UI rendering of meta-evolution events.

Author: Pulse v0.31
"""

import json
import os
import sys
from typing import List, Dict, Optional, Any
from collections import defaultdict
from datetime import datetime
from core.path_registry import PATHS
from core.bayesian_trust_tracker import bayesian_trust_tracker

LOG_PATH = PATHS.get("LEARNING_LOG", "logs/pulse_learning_log.jsonl")


def load_learning_events(limit: Optional[int] = None) -> List[Dict[str, Any]]:
    """
    Loads learning events from the log file.

    Args:
        limit: Optional maximum number of events to return (most recent).

    Returns:
        List of event dictionaries.
    """
    if not os.path.exists(LOG_PATH):
        print("[LearningLog] No log found.")
        return []

    events = []
    try:
        with open(LOG_PATH, "r", encoding="utf-8") as f:
            for idx, line in enumerate(f):
                try:
                    event = json.loads(line)
                    # Validate event structure
                    if isinstance(event, dict) and "event_type" in event and "timestamp" in event:
                        events.append(event)
                    else:
                        print(f"[LearningLogViewer] Skipping malformed event at line {idx+1}")
                except json.JSONDecodeError as jde:
                    print(f"[LearningLogViewer] JSON decode error at line {idx+1}: {jde}")
        if limit:
            return events[-limit:]
        return events
    except Exception as e:
        print(f"[LearningLogViewer] Load error: {e}")
        return []


def summarize_learning_events(events: List[Dict[str, Any]]) -> Dict[str, int]:
    """
    Summarizes the count of each event type.

    Args:
        events: List of event dictionaries.

    Returns:
        Dictionary mapping event_type to count.
    """
    summary = defaultdict(int)
    for ev in events:
        summary[ev.get("event_type", "unknown")] += 1
    return dict(summary)


def filter_events(events: List[Dict[str, Any]], event_type: str) -> List[Dict[str, Any]]:
    """
    Filters events by event_type.

    Args:
        events: List of event dictionaries.
        event_type: The event type to filter by.

    Returns:
        Filtered list of events.
    """
    return [e for e in events if e.get("event_type") == event_type]


def render_event_digest(events: List[Dict[str, Any]]) -> None:
    """
    Prints a digest of events to the console.

    Args:
        events: List of event dictionaries.
    """
    print("\n🧠 Pulse Learning Log Digest (latest events)")
    print("-" * 60)
    for e in events:
        t = e.get("timestamp", "?")
        typ = e.get("event_type", "?")
        dat = e.get("data", {})
        print(f"[{t}] {typ}")
        if isinstance(dat, dict):
            for k, v in dat.items():
                print(f"   - {k}: {v}")
        elif dat:
            print(f"   - data: {dat}")
        print("-" * 60)


def display_variable_trust(variable_id):
    trust = bayesian_trust_tracker.get_trust(variable_id)
    conf_int = bayesian_trust_tracker.get_confidence_interval(variable_id)
    print(f"Variable {variable_id}: Trust={trust:.3f}, 95% CI=({conf_int[0]:.3f}, {conf_int[1]:.3f})")

def display_rule_trust(rule_id):
    trust = bayesian_trust_tracker.get_trust(rule_id)
    conf_int = bayesian_trust_tracker.get_confidence_interval(rule_id)
    print(f"Rule {rule_id}: Trust={trust:.3f}, 95% CI=({conf_int[0]:.3f}, {conf_int[1]:.3f})")

# Example usage in your dashboard rendering logic:
# for var_id in variable_ids:
#     display_variable_trust(var_id)
# for rule_id in rule_ids:
#     display_rule_trust(rule_id)


def main():
    """
    Main entry point for CLI usage.
    Supports optional filtering by event type and limiting number of events.
    """
    import argparse
    parser = argparse.ArgumentParser(description="Pulse Learning Log Viewer")
    parser.add_argument("--limit", type=int, default=20, help="Number of recent events to show")
    parser.add_argument("--filter", type=str, default=None, help="Filter by event_type")
    parser.add_argument("--test", action="store_true", help="Run a simple self-test")
    args = parser.parse_args()

    if args.test:
        # Simple test: create a fake event and print summary
        test_events = [
            {"timestamp": "2024-06-01T12:00:00Z", "event_type": "test_event", "data": {"foo": "bar"}},
            {"timestamp": "2024-06-01T12:01:00Z", "event_type": "test_event", "data": {"baz": 42}},
            {"timestamp": "2024-06-01T12:02:00Z", "event_type": "other_event", "data": {}}
        ]
        print("Running self-test...")
        summary = summarize_learning_events(test_events)
        print("Summary:", summary)
        render_event_digest(test_events)
        return

    evts = load_learning_events(limit=args.limit)
    if args.filter:
        evts = filter_events(evts, args.filter)
    if evts:
        summary = summarize_learning_events(evts)
        print("\n🧾 Learning Summary:")
        for k, v in summary.items():
            print(f" - {k}: {v} events")
        render_event_digest(evts)
    else:
        print("No learning events logged yet.")


if __name__ == "__main__":
    main()