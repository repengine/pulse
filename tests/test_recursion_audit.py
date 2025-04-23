# tests/test_recursion_audit.py

import unittest
from learning.recursion_audit import generate_recursion_report

class TestRecursionAudit(unittest.TestCase):
    def setUp(self):
        self.prev_batch = [
            {"trace_id": "a1", "confidence": 0.5, "retrodiction_error": 0.6, "trust_label": "🟡 Unstable", "arc_label": "Hope Surge"},
            {"trace_id": "a2", "confidence": 0.4, "retrodiction_error": 0.7, "trust_label": "🔴 Rejected", "arc_label": "Fatigue Loop"}
        ]
        self.curr_batch = [
            {"trace_id": "a1", "confidence": 0.6, "retrodiction_error": 0.5, "trust_label": "🟢 Trusted", "arc_label": "Hope Surge"},
            {"trace_id": "a2", "confidence": 0.7, "retrodiction_error": 0.4, "trust_label": "🟢 Trusted", "arc_label": "Hope Surge"}
        ]

    def test_generate_recursion_report(self):
        report = generate_recursion_report(self.prev_batch, self.curr_batch)
        self.assertIn("confidence_delta", report)
        self.assertIn("retrodiction_error_delta", report)
        self.assertIn("trust_distribution_current", report)
        self.assertIn("arc_shift_summary", report)
        self.assertEqual(report["arc_shift_summary"]["changed"], 1)
        self.assertEqual(report["arc_shift_summary"]["same"], 1)

if __name__ == "__main__":
    unittest.main(verbosity=2)
