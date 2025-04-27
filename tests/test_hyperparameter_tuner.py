import unittest
from forecast_engine.hyperparameter_tuner import HyperparameterTuner

def dummy_objective(params):
    # Simple quadratic: minimum at x=2
    return (params["x"] - 2) ** 2

class TestHyperparameterTuner(unittest.TestCase):
    def test_optimize_and_best_params(self):
        param_space = {"x": {"type": "float", "low": 0, "high": 4}}
        tuner = HyperparameterTuner(dummy_objective, param_space)
        study = tuner.optimize(n_trials=10)
        best = tuner.best_params()
        self.assertIn("x", best)
        self.assertTrue(0 <= best["x"] <= 4)

if __name__ == "__main__":
    unittest.main()
