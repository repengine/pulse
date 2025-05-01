"""
AI Forecaster Module

This module encapsulates an LSTM-based forecasting method.
"""

import logging
import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
from typing import List, Dict, Optional, Union, Any

logger = logging.getLogger(__name__)

class LSTMForecaster(nn.Module):
    def __init__(self, input_size: int, hidden_size: int = 64, num_layers: int = 2, output_size: int = 1):
        super(LSTMForecaster, self).__init__()
        self.lstm = nn.LSTM(input_size, hidden_size, num_layers, batch_first=True)
        self.fc = nn.Linear(hidden_size, output_size)

    def forward(self, x):
        try:
            out, _ = self.lstm(x)
            out = out[:, -1, :]
            out = self.fc(out)
            return out
        except Exception as e:
            logger.error(f"Forward pass error: {e}")
            # Return zero tensor with appropriate shape
            return torch.zeros(x.size(0), 1, device=x.device)

_model: Optional[LSTMForecaster] = None
_optimizer: Optional[optim.Optimizer] = None
_criterion: Optional[nn.Module] = None
_input_size: Optional[int] = None

def _initialize_model(input_size: int) -> bool:
    """
    Initialize the global model, optimizer, and criterion.
    
    Args:
        input_size: Number of input features
        
    Returns:
        bool: True if initialization succeeded, False otherwise
    """
    global _model, _optimizer, _criterion, _input_size
    
    try:
        if input_size <= 0:
            logger.error(f"Invalid input size: {input_size}. Must be positive.")
            return False
            
        _input_size = input_size
        _model = LSTMForecaster(input_size)
        _criterion = nn.MSELoss()
        _optimizer = optim.Adam(_model.parameters(), lr=1e-3)
        logger.info(f"Model initialized with input_size={input_size}")
        return True
    except Exception as e:
        logger.error(f"Model initialization failed: {e}")
        _model, _optimizer, _criterion = None, None, None
        return False

def _validate_features(features: List[float], expected_size: Optional[int] = None) -> bool:
    """
    Validate that features are valid numerical values.
    
    Args:
        features: List of feature values
        expected_size: Optional expected size of the feature list
        
    Returns:
        bool: True if features are valid, False otherwise
    """
    if not isinstance(features, list):
        logger.error(f"Features must be a list, got {type(features)}")
        return False
        
    if not features:
        logger.error("Features list is empty")
        return False
        
    if expected_size is not None and len(features) != expected_size:
        logger.error(f"Features length mismatch. Expected {expected_size}, got {len(features)}")
        return False
        
    for i, val in enumerate(features):
        try:
            float(val)  # Check if convertible to float
        except (ValueError, TypeError):
            logger.error(f"Invalid feature value at index {i}: {val}")
            return False
            
    return True

def train(data: List[Dict]) -> bool:
    """
    Train the AI model on historical forecast data.

    Args:
        data: A list of dictionaries containing 'features' (list of floats) and 'adjustment' (float).
        
    Returns:
        bool: True if training succeeded, False otherwise
    """
    try:
        logger.info(f"Training AI model with {len(data)} data points.")
        
        # Validate input data
        if not data:
            logger.warning("No training data provided.")
            return False
            
        # Validate and extract features and adjustments
        valid_data = []
        for i, item in enumerate(data):
            if not isinstance(item, dict):
                logger.warning(f"Item {i} is not a dictionary, skipping.")
                continue
                
            features = item.get("features", [])
            adjustment = item.get("adjustment")
            
            # Validate features and adjustment
            if not _validate_features(features):
                logger.warning(f"Invalid features in item {i}, skipping.")
                continue
                
            try:
                adjustment = float(adjustment)
            except (ValueError, TypeError):
                logger.warning(f"Invalid adjustment in item {i}: {adjustment}, skipping.")
                continue
                
            valid_data.append({"features": features, "adjustment": adjustment})
            
        if not valid_data:
            logger.warning("No valid training data after validation.")
            return False
            
        # Determine input size from the first item
        input_size = len(valid_data[0]["features"])
        
        # Initialize or validate model
        if _model is None:
            if not _initialize_model(input_size):
                return False
        elif _input_size != input_size:
            logger.warning(f"Input size mismatch. Model expects {_input_size}, got {input_size}. Reinitializing.")
            if not _initialize_model(input_size):
                return False
                
        # Prepare input and target tensors
        try:
            inputs = torch.tensor([d["features"] for d in valid_data], dtype=torch.float32).unsqueeze(1)  # shape (batch, seq=1, features)
            targets = torch.tensor([d["adjustment"] for d in valid_data], dtype=torch.float32).unsqueeze(1)  # shape (batch, 1)
        except Exception as e:
            logger.error(f"Error preparing input tensors: {e}")
            return False
            
        if _model is None or _optimizer is None or _criterion is None:
            logger.error("Model, optimizer, or criterion not initialized. Training aborted.")
            return False
            
        # Training loop
        _model.train()
        epochs = 10
        final_loss = None
        
        try:
            for epoch in range(epochs):
                _optimizer.zero_grad()
                outputs = _model(inputs)
                loss = _criterion(outputs, targets)
                loss.backward()
                _optimizer.step()
                
                final_loss = loss.item()
                if epoch % 2 == 0:
                    logger.debug(f"Epoch {epoch}/{epochs}: loss = {final_loss:.4f}")
                    
            logger.info(f"Training completed. Final loss: {final_loss:.4f}")
            return True
            
        except Exception as e:
            logger.error(f"Error during training: {e}")
            return False
            
    except Exception as e:
        logger.error(f"Unexpected error in train(): {e}")
        return False

def predict(input_features: Dict) -> Dict:
    """
    Predict forecast adjustments based on input features.

    Args:
        input_features: A dictionary of feature name to value.

    Returns:
        A dictionary with key 'adjustment' and predicted float value.
    """
    try:
        logger.info(f"Predicting forecast adjustments with {len(input_features)} features.")
        
        # Validate input features
        if not isinstance(input_features, dict):
            logger.error(f"Input features must be a dictionary, got {type(input_features)}")
            return {"adjustment": 0.0, "error": "Invalid input type"}
            
        if not input_features:
            logger.warning("Empty input features dictionary.")
            return {"adjustment": 0.0, "error": "No features provided"}
            
        # Extract and validate feature values
        features = []
        try:
            for key, value in input_features.items():
                try:
                    features.append(float(value))
                except (ValueError, TypeError):
                    logger.warning(f"Skipping non-numeric feature '{key}': {value}")
        except Exception as e:
            logger.error(f"Error extracting feature values: {e}")
            return {"adjustment": 0.0, "error": f"Feature extraction error: {str(e)}"}
            
        if not features:
            logger.warning("No valid numeric features found.")
            return {"adjustment": 0.0, "error": "No valid numeric features"}
            
        # Initialize model if needed
        input_size = len(features)
        if _model is None:
            logger.warning(f"Model not initialized. Initializing with input_size={input_size} (untrained).")
            if not _initialize_model(input_size):
                return {"adjustment": 0.0, "error": "Model initialization failed"}
        elif _input_size != input_size:
            logger.warning(f"Input size mismatch. Model expects {_input_size}, got {input_size}. Using default value.")
            return {"adjustment": 0.0, "error": "Input size mismatch"}
            
        # Prepare input tensor
        try:
            tensor = torch.tensor(features, dtype=torch.float32).unsqueeze(0).unsqueeze(1)  # shape (1,1,features)
        except Exception as e:
            logger.error(f"Error creating input tensor: {e}")
            return {"adjustment": 0.0, "error": f"Tensor creation error: {str(e)}"}
            
        # Make prediction
        _model.eval()
        with torch.no_grad():
            try:
                output = _model(tensor)
                adjustment = float(output.item())
                # Clip to reasonable range to prevent extreme values
                adjustment = max(min(adjustment, 10.0), -10.0)
                logger.info(f"Prediction successful: adjustment={adjustment:.4f}")
                return {"adjustment": adjustment, "confidence": 0.8}  # Add confidence score
            except Exception as e:
                logger.error(f"Error during prediction: {e}")
                return {"adjustment": 0.0, "error": f"Prediction error: {str(e)}"}
                
    except Exception as e:
        logger.error(f"Unexpected error in predict(): {e}")
        return {"adjustment": 0.0, "error": f"Unexpected error: {str(e)}"}

def update(new_data: List[Dict]) -> bool:
    """
    Update the AI model with new data for continuous learning.

    Args:
        new_data: A list of dictionaries containing 'features' and 'adjustment'.
        
    Returns:
        bool: True if update succeeded, False otherwise
    """
    try:
        logger.info(f"Updating AI model with {len(new_data)} new data points.")
        
        if not new_data:
            logger.warning("No update data provided.")
            return False
            
        return train(new_data)
        
    except Exception as e:
        logger.error(f"Unexpected error in update(): {e}")
        return False

def get_model_status() -> Dict[str, Any]:
    """
    Get the current status of the AI model.
    
    Returns:
        Dict: Status information about the model
    """
    return {
        "initialized": _model is not None,
        "input_size": _input_size,
        "type": "LSTM" if _model else None,
        "trainable_parameters": sum(p.numel() for p in _model.parameters() if p.requires_grad) if _model else 0
    }