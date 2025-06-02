"""AI Configuration using centralized Config loader."""

from pulse.config.loader import Config

# Create a config instance for backward compatibility
_config = Config()

OPENAI_API_KEY: str = _config.get("ai.openai_api_key")
DEFAULT_OPENAI_MODEL: str = _config.get("ai.default_model_name")
