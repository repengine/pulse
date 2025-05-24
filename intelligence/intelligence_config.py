# intelligence/intelligence_config.py

"""
Centralized configuration for the Pulse Intelligence system.

This file contains constants and settings used across various components
of the intelligence module, including the Function Router, Observer,
Upgrade Sandbox Manager, and Simulation Executor.
"""

import os

# Function Router Configuration
FUNCTION_ROUTER_MAX_RETRIES: int = 3
FUNCTION_ROUTER_RETRY_SLEEP: float = 1.5  # seconds

# Intelligence Observer Configuration
OBSERVER_MEMORY_DIR: str = "data/intelligence_observer_memory"

# Upgrade Sandbox Manager Configuration
UPGRADE_SANDBOX_DIR: str = "data/upgrade_sandbox"

# WorldState Loader Configuration
WORLDSTATE_DEFAULT_SOURCE: str = "data/baselines/default.csv"
WORLDSTATE_INJECT_LIVE_DEFAULT: bool = True

# Simulation Executor Configuration

# --- GPT Configuration ---
# Fallback model name if the configured model is not a string
GPT_FALLBACK_MODEL: str = "gpt-4"
# Maximum number of retries for GPT calls
MAX_GPT_RETRIES: int = 3
# Sleep time between GPT retries in seconds
GPT_RETRY_SLEEP: int = 5

# --- Gemini Configuration ---
# Load Gemini API Key from environment variable
GEMINI_API_KEY: str | None = os.getenv("GEMINI_API_KEY")
# Default Gemini model name
GEMINI_DEFAULT_MODEL: str = "gemini-pro"  # Or specify another suitable model
# Maximum number of retries for Gemini calls
MAX_GEMINI_RETRIES: int = 3
# Sleep time between Gemini retries in seconds
GEMINI_RETRY_SLEEP: int = 5
# Flag to select the LLM provider ('gpt' or 'gemini')
LLM_PROVIDER: str = os.getenv("LLM_PROVIDER", "gpt").lower()  # Default to GPT

# Add other intelligence-specific configurations here
