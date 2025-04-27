import unittest
import pandas as pd
from causal_model.structural_causal_model import StructuralCausalModel
from causal_model.discovery import CausalDiscovery
from causal_model.counterfactual_engine import CounterfactualEngine

class TestStructuralCausalModel(unittest.TestCase):
    def test_add_and_remove_variable_and_edge(self):
        scm = StructuralCausalModel()
        scm.add_variable("A")
        scm.add_variable("B")
        scm.add_causal_edge("A", "B")
        self.assertIn(("A", "B"), scm.edges())
        scm.remove_causal_edge("A", "B")
        self.assertNotIn(("A", "B"), scm.edges())
        scm.remove_variable("A")
        self.assertNotIn("A", scm.variables())

class TestCausalDiscovery(unittest.TestCase):
    def test_run_pc_and_fci(self):
        df = pd.DataFrame({"X": [1, 2, 3], "Y": [1, 2, 3], "Z": [3, 2, 1]})
        cd = CausalDiscovery(df)
        scm_pc = cd.run_pc(alpha=0.1)
        scm_fci = cd.run_fci(alpha=0.1)
        self.assertTrue(len(scm_pc.edges()) > 0)
        self.assertTrue(len(scm_fci.edges()) > 0)

class TestCounterfactualEngine(unittest.TestCase):
    def test_predict_counterfactual(self):
        scm = StructuralCausalModel()
        scm.add_variable("X")
        scm.add_variable("Y")
        scm.add_causal_edge("X", "Y")
        engine = CounterfactualEngine(scm)
        evidence = {"X": 1, "Y": 2}
        interventions = {"X": 5}
        result = engine.predict_counterfactual(evidence, interventions)
        self.assertEqual(result["X"], 5)
        self.assertEqual(result["Y"], 2)

if __name__ == "__main__":
    unittest.main()
