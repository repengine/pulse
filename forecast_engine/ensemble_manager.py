"""
Ensemble Manager for Pulse Forecast Engine.
Handles registration and combination of multiple forecasting models.
"""

import logging
from typing import Dict, List, Callable, Any
from core.pulse_config import ENSEMBLE_WEIGHTS

logger = logging.getLogger(__name__)


class EnsembleManager:
    """
    Manages a set of forecasting models and combines their outputs.
    """

    def __init__(self):
        self._models: Dict[str, Callable[..., Dict[str, Any]]] = {}
        self._weights: Dict[str, float] = {}
        # initialize ensemble weights from configuration
        self._weights |= ENSEMBLE_WEIGHTS

    def register_model(
        self, name: str, model_fn: Callable[..., Dict[str, Any]], weight: float = 1.0
    ):
        """
        Register a forecasting model function with a name and weight.
        """
        self._models[name] = model_fn
        self._weights[name] = weight
        logger.info("Registered ensemble model '%s' with weight %f", name, weight)

    def list_models(self) -> List[str]:
        """Return list of registered model names."""
        return list(self._models.keys())

    def set_weights(self, weights: Dict[str, float]):
        """
        Set ensemble weights for registered models.
        """
        for name, w in weights.items():
            if name in self._models:
                self._weights[name] = w
            else:
                logger.warning("Weight provided for unknown model '%s'", name)
        logger.info("Updated ensemble weights: %s", self._weights)

    def combine(self, **model_outputs: Dict[str, Any]) -> Dict[str, Any]:
        """
        Combine outputs from registered models according to weights.
        Each model output must be a dict with key 'value'.
        Returns a dict with combined 'ensemble_value'.
        """
        logger.info(
            "[Forecast Pipeline] Entering EnsembleManager.combine: model_outputs keys=%s, sample=%s",
            list(model_outputs.keys()),
            {k: model_outputs[k] for k in list(model_outputs.keys())[:3]},
        )
        total_weight = sum(self._weights.get(name, 0.0) for name in model_outputs)
        if total_weight <= 0:
            raise ValueError("Total ensemble weight must be positive")
        combined = 0.0
        for name, output in model_outputs.items():
            weight = self._weights.get(name, 0.0)
            try:
                val = float(output.get("value", 0.0))
            except (ValueError, TypeError):
                logger.warning(
                    f"Invalid value for model '{name}': {output.get('value')}. Using default 0.0"
                )
                val = 0.0
            combined += weight * val
        ensemble_value = combined / total_weight
        logger.info("Combined ensemble value: %f", ensemble_value)
        return {"ensemble_value": ensemble_value, "value": ensemble_value}

    def stack(
        self, meta_model: Callable[[List[float]], Any], model_outputs: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Perform stacking by passing model outputs to a meta-model to generate a combined forecast.
        """
        logger.info(
            "[Forecast Pipeline] Entering EnsembleManager.stack: model_outputs keys=%s, sample=%s",
            list(model_outputs.keys()),
            {k: model_outputs[k] for k in list(model_outputs.keys())[:3]},
        )
        values = []
        for name, output in model_outputs.items():
            try:
                val = float(output.get("value", 0.0))
                values.append(val)
            except (ValueError, TypeError):
                logger.warning(
                    f"Invalid value for model '{name}': {output.get('value')}. Using default 0.0"
                )
                values.append(0.0)

        stacked_value = meta_model(values)
        logger.info("Stacked ensemble value: %s", stacked_value)
        return {"stacked_value": stacked_value, "value": stacked_value}

    def boost(
        self,
        weak_learner: Callable[..., Dict[str, Any]],
        training_data: Any,
        n_rounds: int = 10,
        **kwargs,
    ) -> None:
        """
        Placeholder for boosting implementation using weak learners iteratively.
        """
        logger.info("Boosting with %d rounds", n_rounds)
        # TODO: implement boosting algorithm (e.g., AdaBoost or GradientBoosting)
