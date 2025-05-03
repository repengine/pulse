"""
Configuration module for OpenAI API integration.
This module provides secure loading and management of OpenAI API credentials and settings.
"""
import os
import json  # Added for JSON serialization support
from typing import Optional, Dict, Any

# Import the centralized LLM configuration
from chatmode.config.llm_config import llm_config

class OpenAIConfig:
    """
    Configuration manager for OpenAI API settings.
    Handles API keys, model selection, and other configuration options.
    Uses the centralized LLM configuration for consistency.
    """
    def __init__(self, api_key: Optional[str] = None, model_name: str = "gpt-3.5-turbo"):
        """
        Initialize the OpenAI configuration with API key and default model.
        
        Args:
            api_key (str, optional): The OpenAI API key. If None, will try to load from env variable.
            model_name (str): The default model to use. Default is "gpt-3.5-turbo" for cost efficiency.
        """
        # Use API key from parameter, environment, or centralized config
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY")
        self.model_name = model_name
        
        # Load available models from the centralized configuration
        config = llm_config.model_types.get("openai", {})
        self.available_models = config.get("models", {})
    
    @property
    def has_api_key(self) -> bool:
        """Check if API key is configured."""
        return self.api_key is not None and len(self.api_key) > 0
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get information about the currently selected model."""
        # Get model info from available models, or fall back to default
        model_info = self.available_models.get(self.model_name, None)
        if model_info is None:
            # Fall back to default model from the centralized config
            model_info = self.available_models.get("gpt-3.5-turbo", {})
        return model_info
    
    def get_available_models(self) -> Dict[str, Dict[str, Any]]:
        """Get information about all available models."""
        return self.available_models
    
    def estimate_cost(self, input_tokens: int, output_tokens: int) -> float:
        """
        Estimate the cost for a given number of input and output tokens.
        
        Args:
            input_tokens (int): Number of input tokens
            output_tokens (int): Number of output tokens
            
        Returns:
            float: Estimated cost in USD
        """
        model_info = self.get_model_info()
        input_cost = (input_tokens / 1000) * model_info.get("input_cost_per_1k", 0)
        output_cost = (output_tokens / 1000) * model_info.get("output_cost_per_1k", 0)
        return input_cost + output_cost
        
    def save_model_selection(self, model_name: str) -> bool:
        """
        Save the current model selection to the centralized configuration.
        
        Args:
            model_name (str): The model name to save
            
        Returns:
            bool: True if successful, False otherwise
        """
        if model_name in self.available_models:
            # Update the current instance
            self.model_name = model_name
            # Save to the centralized configuration
            return llm_config.save_model_selection("openai", model_name)
        return False