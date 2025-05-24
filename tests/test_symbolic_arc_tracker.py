# tests/test_symbolic_arc_tracker.py

import unittest
from symbolic_system.pulse_symbolic_arc_tracker import (
    track_symbolic_arcs,
    compare_arc_drift,
    compute_arc_stability,
)


class TestSymbolicArcTracker(unittest.TestCase):
    def setUp(self):
        self.prev = [
            {"arc_label": "Hope Surge"},
            {"arc_label": "Hope Surge"},
            {"arc_label": "Fatigue Plateau"},
        ]
        self.curr = [
            {"arc_label": "Hope Surge"},
            {"arc_label": "Collapse Risk"},
            {"arc_label": "Hope Surge"},
            {"arc_label": "Collapse Risk"},
        ]

    def test_arc_tracking(self):
        result = track_symbolic_arcs(self.prev)
        self.assertEqual(result["Hope Surge"], 2)
        self.assertEqual(result["Fatigue Plateau"], 1)

    def test_drift_calc(self):
        drift = compare_arc_drift(self.prev, self.curr)
        self.assertIn("Hope Surge", drift)
        self.assertIn("Collapse Risk", drift)
        self.assertTrue(isinstance(drift["Hope Surge"], float))

    def test_stability_score(self):
        drift = compare_arc_drift(self.prev, self.curr)
        score = compute_arc_stability(drift)
        self.assertTrue(0.0 <= score <= 200.0)  # possible drift range


if __name__ == "__main__":
    unittest.main()
