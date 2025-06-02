#!/usr/bin/env python
"""
Launch script for the Pulse Conversational Interface GUI.

This script starts the conversational interface with optional configuration
for the LLM model type and name. By default, it uses the mock model which
doesn't require an API key.

Usage:
    python launch_conversational_ui.py
    python launch_conversational_ui.py --model-type openai --model-name gpt-3.5-turbo
    python launch_conversational_ui.py --model-type mock
"""

import os
import sys
import argparse
import logging
from chatmode.ui.conversational_gui import ConversationalGUI
from chatmode.conversational_core import ConversationalCore

# Set up logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("ConversationalUI")

# Add the parent directory to the path so we can import the modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


def main():
    """Main function to parse arguments and launch the GUI."""
    parser = argparse.ArgumentParser(
        description="Launch the Pulse Conversational Interface"
    )
    # Determine default model type based on environment
    default_model_type = "openai" if os.environ.get("OPENAI_API_KEY") else "mock"

    parser.add_argument(
        "--model-type",
        default=default_model_type,
        choices=["openai", "mock"],
        help=f"Type of LLM model to use (default: {default_model_type})",
    )
    parser.add_argument(
        "--model-name",
        default="gpt-3.5-turbo",
        help="Name of the model (default: gpt-3.5-turbo for OpenAI)",
    )
    parser.add_argument(
        "--api-key",
        default=None,
        help="API key for the model service (optional, will use env var if not provided)",
    )

    args = parser.parse_args()

    # If API key is provided, set it as an environment variable
    if args.api_key:
        os.environ["OPENAI_API_KEY"] = args.api_key
        # If API key is provided and model type is mock, switch to openai
        if args.model_type == "mock":
            args.model_type = "openai"
            logger.info("API key provided, switching to OpenAI model")

    # Log model configuration
    logger.info(
        f"Starting conversational UI with model type: {
            args.model_type}, model name: {
            args.model_name}")

    # Initialize and run the GUI
    app = ConversationalGUI()

    # Create a new ConversationalCore with the specified model parameters
    new_core = ConversationalCore(
        model_name=args.model_name, model_type=args.model_type
    )

    # Replace the default core in the GUI
    app.conversational_core = new_core
    logger.info(f"Using model: {args.model_type} - {args.model_name}")

    # Run the GUI main loop
    app.mainloop()


if __name__ == "__main__":
    main()
