"""
AI Forecaster Module

This module encapsulates an LSTM-based forecasting method.
"""

import logging
import torch
import torch.nn as nn
import torch.optim as optim
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)

class LSTMForecaster(nn.Module):
    def __init__(self, input_size: int, hidden_size: int = 64, num_layers: int = 2, output_size: int = 1):
        super(LSTMForecaster, self).__init__()
        self.lstm = nn.LSTM(input_size, hidden_size, num_layers, batch_first=True)
        self.fc = nn.Linear(hidden_size, output_size)

    def forward(self, x):
        out, _ = self.lstm(x)
        out = out[:, -1, :]
        out = self.fc(out)
        return out

_model: Optional[LSTMForecaster] = None
_optimizer: Optional[optim.Optimizer] = None
_criterion: Optional[nn.Module] = None

def _initialize_model(input_size: int):
    global _model, _optimizer, _criterion
    _model = LSTMForecaster(input_size)
    _criterion = nn.MSELoss()
    _optimizer = optim.Adam(_model.parameters(), lr=1e-3)

def train(data: List[Dict]) -> None:
    """
    Train the AI model on historical forecast data.

    Args:
        data: A list of dictionaries containing 'features' (list of floats) and 'adjustment' (float).
    """
    logger.info("Training AI model with %d data points.", len(data))
    if not data:
        return
    # Prepare input and target tensors
    inputs = torch.tensor([d["features"] for d in data], dtype=torch.float32).unsqueeze(1)  # shape (batch, seq=1, features)
    targets = torch.tensor([d["adjustment"] for d in data], dtype=torch.float32).unsqueeze(1)  # shape (batch, 1)
    if _model is None:
        input_size = inputs.shape[-1]
        _initialize_model(input_size)
    if _model is None or _optimizer is None or _criterion is None:
        logger.error("Model, optimizer, or criterion not initialized. Training aborted.")
        return
    _model.train()
    epochs = 10
    loss = None
    for _ in range(epochs):
        _optimizer.zero_grad()
        loss = _criterion(_model(inputs), targets)
        loss.backward()
        _optimizer.step()
    if loss is not None:
        logger.info("Training completed. Final loss: %.4f", loss.item())

def predict(input_features: Dict) -> Dict:
    """
    Predict forecast adjustments based on input features.

    Args:
        input_features: A dictionary of feature name to value.

    Returns:
        A dictionary with key 'adjustment' and predicted float value.
    """
    logger.info("Predicting forecast adjustments with features: %s", input_features)
    features = list(input_features.values())
    if _model is None:
        input_size = len(features)
        _initialize_model(input_size)
        logger.warning("Model was not initialized before prediction. Initialized with input size %d, but model is untrained. Prediction may be unreliable.", input_size)
    tensor = torch.tensor(features, dtype=torch.float32).unsqueeze(0).unsqueeze(1)  # shape (1,1,features)
    if _model is None:
        logger.error("Model initialization failed. Returning default adjustment.")
        return {"adjustment": 0.0}
    _model.eval()
    with torch.no_grad():
        return {"adjustment": float(_model(tensor).item())}

def update(new_data: List[Dict]) -> None:
    """
    Update the AI model with new data for continuous learning.

    Args:
        new_data: A list of dictionaries containing 'features' and 'adjustment'.
    """
    logger.info("Updating AI model with %d new data points.", len(new_data))
    if not new_data:
        return
    train(new_data)