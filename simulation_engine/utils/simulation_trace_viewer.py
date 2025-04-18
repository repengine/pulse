import json
import sys
from collections import Counter

def load_trace(filepath):
    with open(filepath, 'r') as f:
        for line in f:
            yield json.loads(line)

def main():
    if len(sys.argv) < 2:
        print("Usage: python simulation_trace_viewer.py <trace.jsonl> [--summary]")
        return
    filepath = sys.argv[1]
    summary_mode = "--summary" in sys.argv
    events = list(load_trace(filepath))
    if summary_mode:
        print(f"Loaded {len(events)} events from {filepath}")
        if events:
            all_keys = Counter()
            for e in events:
                all_keys.update(e.keys())
            print("Top keys in events:", all_keys.most_common())
            print("First event sample:", events[0])
    else:
        for i, event in enumerate(events):
            print(f"Event {i}: {event}")

if __name__ == "__main__":
    main()
