# tests/test_pulse_ui_plot.py

import unittest
import os
import json
from dev_tools.pulse_ui_plot import load_variable_trace

class TestPulseUIPlot(unittest.TestCase):
    def setUp(self):
        self.temp_file = "temp_var_trace.jsonl"
        mock_data = [
            {"step": 0, "variables": {"hope": 0.6}},
            {"step": 1, "variables": {"hope": 0.61}},
            {"step": 2, "variables": {"hope": 0.58}}
        ]
        with open(self.temp_file, "w") as f:
            for entry in mock_data:
                f.write(json.dumps(entry) + "\n")

    def test_variable_trace_load(self):
        steps, values = load_variable_trace(self.temp_file, "hope")
        self.assertEqual(steps, [0, 1, 2])
        self.assertEqual(values, [0.6, 0.61, 0.58])

    def test_missing_variable(self):
        steps, values = load_variable_trace(self.temp_file, "rage")
        self.assertEqual(steps, [])
        self.assertEqual(values, [])

    def tearDown(self):
        try:
            os.remove(self.temp_file)
        except Exception:
            pass

if __name__ == '__main__':
    unittest.main(verbosity=2)
