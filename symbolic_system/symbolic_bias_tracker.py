"""
symbolic_bias_tracker.py

Tracks frequency of symbolic tags over time for bias analysis.
Provides CSV export and optional visualization.

Usage:
    tracker = SymbolicBiasTracker()
    tracker.record("Hope Rising")
    tracker.export_csv()
    tracker.plot_frequencies()
"""

import json
from collections import Counter
from typing import Dict
from core.path_registry import PATHS

assert isinstance(PATHS, dict), f"PATHS is not a dict, got {type(PATHS)}"

BIAS_LOG_PATH = PATHS.get("SYMBOLIC_BIAS_LOG", "logs/symbolic_bias_log.jsonl")


class SymbolicBiasTracker:
    def __init__(self):
        self.counter = Counter()
        self.history = []

    def record(self, tag: str):
        self.counter[tag] += 1
        self.history.append(tag)
        try:
            with open(BIAS_LOG_PATH, "a") as f:
                f.write(json.dumps({"tag": tag}) + "\n")
        except Exception as e:
            print(f"[BiasTracker] Log error: {e}")

    def get_frequencies(self) -> Dict[str, int]:
        return dict(self.counter)

    def export_csv(self, csv_path="symbolic_bias.csv"):
        import csv

        with open(csv_path, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["tag", "count"])
            for tag, count in self.counter.items():
                writer.writerow([tag, count])

    def plot_frequencies(self):
        try:
            import matplotlib.pyplot as plt

            tags, counts = zip(*self.counter.items())
            plt.bar(tags, counts)
            plt.title("Symbolic Tag Frequencies")
            plt.xlabel("Tag")
            plt.ylabel("Count")
            plt.xticks(rotation=45)
            plt.tight_layout()
            plt.show()
        except ImportError:
            print("matplotlib not installed. Skipping plot.")
        except Exception as e:
            print(f"[BiasTracker] Plot error: {e}")
