"""
Hyperparameter tuner for Pulse forecasting models using Optuna.
"""
import optuna
from typing import Dict, Any, Callable

class HyperparameterTuner:
    """
    Encapsulates hyperparameter optimization using Optuna.
    """

    def __init__(self, objective_fn: Callable[[Dict[str, Any]], float], param_space: Dict[str, Dict[str, Any]]):
        self.objective_fn = objective_fn
        self.param_space = param_space
        self.study = optuna.create_study(direction="minimize")

    def optimize(self, n_trials: int = 50) -> optuna.study.Study:
        """
        Run hyperparameter optimization.
        """
        def objective(trial):
            params = {}
            for name, spec in self.param_space.items():
                ptype = spec.get("type", "float")
                if ptype == "int":
                    params[name] = trial.suggest_int(name, spec["low"], spec["high"])
                elif ptype == "float":
                    params[name] = trial.suggest_float(name, spec["low"], spec["high"], log=spec.get("log", False))
                elif ptype == "categorical":
                    params[name] = trial.suggest_categorical(name, spec["choices"])
                else:
                    raise ValueError(f"Unsupported param type: {ptype}")
            return self.objective_fn(params)
        self.study.optimize(objective, n_trials=n_trials)
        return self.study

    def best_params(self) -> Dict[str, Any]:
        """
        Return the best found hyperparameters.
        """
        return self.study.best_params