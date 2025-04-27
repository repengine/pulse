import unittest
from forecast_engine.ensemble_manager import EnsembleManager

def dummy_model_a(**kwargs):
    return {"value": 10.0}
def dummy_model_b(**kwargs):
    return {"value": 20.0}
def meta_model(values):
    return sum(values) / len(values)

class TestEnsembleManager(unittest.TestCase):
    def setUp(self):
        self.manager = EnsembleManager()
        self.manager.register_model("a", dummy_model_a, weight=0.6)
        self.manager.register_model("b", dummy_model_b, weight=0.4)

    def test_list_models(self):
        self.assertIn("a", self.manager.list_models())
        self.assertIn("b", self.manager.list_models())

    def test_combine(self):
        outputs = {"a": dummy_model_a(), "b": dummy_model_b()}
        result = self.manager.combine(**outputs)
        expected = (0.6 * 10.0 + 0.4 * 20.0) / (0.6 + 0.4)
        self.assertAlmostEqual(result["ensemble_value"], expected)

    def test_stack(self):
        outputs = {"a": dummy_model_a(), "b": dummy_model_b()}
        result = self.manager.stack(meta_model, outputs)
        self.assertAlmostEqual(result["stacked_value"], 15.0)

if __name__ == "__main__":
    unittest.main()
