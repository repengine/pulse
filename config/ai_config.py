import os

# Configuration for AI services

# OpenAI API Key
# Loads from environment variable OPENAI_API_KEY if not set here
OPENAI_API_KEY: str = os.environ.get("OPENAI_API_KEY", "")

# Default OpenAI Model
DEFAULT_OPENAI_MODEL: str = "gpt-4"

# Add other AI-related configurations here