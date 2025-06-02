"""
Configuration module for LLM models in the conversational interface.
This module defines the available models, their configurations, and parameters.
"""

import os
from typing import Dict, Any, Optional


class LLMConfig:
    """Configuration manager for LLM settings in Pulse."""

    def __init__(self):
        """Initialize the LLM configuration with defaults."""
        # Default model settings
        self.default_model_type = "openai"
        self.default_model_name = "gpt-3.5-turbo"

        # Available model types and their configurations
        self.model_types = {
            "openai": {
                "description": "OpenAI API models (requires API key)",
                "models": {
                    "gpt-4-turbo": {
                        "description": "Most powerful model, best for complex tasks",
                        "max_tokens": 128000,
                        "input_cost_per_1k": 0.01,
                        "output_cost_per_1k": 0.03,
                    },
                    "gpt-4o": {
                        "description": (
                            "Latest optimized GPT-4 model with multimodal capabilities"
                        ),
                        "max_tokens": 128000,
                        "input_cost_per_1k": 0.01,
                        "output_cost_per_1k": 0.03,
                    },
                    "gpt-3.5-turbo": {
                        "description": "Fast and cost-effective model for most tasks",
                        "max_tokens": 16385,
                        "input_cost_per_1k": 0.0005,
                        "output_cost_per_1k": 0.0015,
                    },
                },
            },
            "mock": {
                "description": "Mock models for testing (no API required)",
                "models": {
                    "mock-model": {
                        "description": (
                            "Simple mock model that returns placeholder responses"
                        ),
                        "max_tokens": 1000,
                        "input_cost_per_1k": 0,
                        "output_cost_per_1k": 0,
                    }
                },
            },
        }

        # Load model selection from environment variable if available
        self._load_from_env()

    def _load_from_env(self):
        """Load configuration from environment variables."""
        env_model_type = os.environ.get("PULSE_LLM_MODEL_TYPE")
        env_model_name = os.environ.get("PULSE_LLM_MODEL_NAME")

        if env_model_type and env_model_type in self.model_types:
            self.default_model_type = env_model_type

        if env_model_name:
            # Check if the model name exists in the selected model type
            model_type_config = self.model_types.get(self.default_model_type, {})
            models = model_type_config.get("models", {})

            if env_model_name in models:
                self.default_model_name = env_model_name

    def get_model_config(
        self, model_type: Optional[str] = None, model_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get configuration for a specific model.

        Args:
            model_type: The type of model (e.g., "openai", "mock")
            model_name: The name of the model

        Returns:
            Dict containing the model configuration
        """
        # Use defaults if not specified
        model_type = model_type or self.default_model_type
        model_name = model_name or self.default_model_name

        # Get model type configuration
        model_type_config = self.model_types.get(model_type, {})
        models = model_type_config.get("models", {})

        # Get specific model configuration
        model_config = models.get(model_name, {})

        return {
            "model_type": model_type,
            "model_name": model_name,
            "model_config": model_config,
            "api_key": os.environ.get(f"{model_type.upper()}_API_KEY", ""),
        }

    def save_model_selection(self, model_type: str, model_name: str) -> bool:
        """
        Save model selection to environment variables.

        Args:
            model_type: The type of model to use
            model_name: The name of the model to use

        Returns:
            bool: True if successful, False otherwise
        """
        # Validate model type and name
        if model_type not in self.model_types:
            return False

        model_type_config = self.model_types.get(model_type, {})
        models = model_type_config.get("models", {})

        if model_name not in models:
            return False

        # Set environment variables
        os.environ["PULSE_LLM_MODEL_TYPE"] = model_type
        os.environ["PULSE_LLM_MODEL_NAME"] = model_name

        # Update defaults
        self.default_model_type = model_type
        self.default_model_name = model_name

        return True


# Global instance for easy access
llm_config = LLMConfig()
