# tests/test_history_tracker.py

import unittest
import os
import json
from diagnostics.history_tracker import track_variable_history

class TestHistoryTracker(unittest.TestCase):
    def setUp(self):
        self.mock_states = [
            {"variables": {"hope": 0.6, "fatigue": 0.2}},
            {"variables": {"hope": 0.58, "fatigue": 0.3}},
            {"variables": {"hope": 0.63, "fatigue": 0.4}}
        ]
        self.output_dir = "test_logs"
        self.run_id = "test001"

    def test_basic_write_and_structure(self):
        track_variable_history(self.run_id, self.mock_states, output_dir=self.output_dir)
        path = os.path.join(self.output_dir, f"vars_{self.run_id}.jsonl")
        self.assertTrue(os.path.exists(path))

        with open(path, "r") as f:
            lines = f.readlines()
            self.assertEqual(len(lines), len(self.mock_states))
            for i, line in enumerate(lines):
                record = json.loads(line.strip())
                self.assertIn("step", record)
                self.assertIn("variables", record)
                self.assertEqual(record["step"], i)
                self.assertTrue(isinstance(record["variables"], dict))

    def tearDown(self):
        # Clean up
        try:
            os.remove(os.path.join(self.output_dir, f"vars_{self.run_id}.jsonl"))
            os.rmdir(self.output_dir)
        except Exception:
            pass

if __name__ == '__main__':
    unittest.main(verbosity=2)
