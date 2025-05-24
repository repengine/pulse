"""AI Configuration using centralized Config loader."""

from pulse.config.loader import Config

OPENAI_API_KEY: str = Config.get("ai.openai_api_key")
DEFAULT_OPENAI_MODEL: str = Config.get("ai.default_model_name")
