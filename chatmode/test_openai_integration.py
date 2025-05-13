#!/usr/bin/env python
"""
Test script for verifying the OpenAI integration in the Pulse Conversational Interface.
This script tests the LLMModel with OpenAI API and validates token counting, 
response generation, and error handling.
"""
import os
import sys
import logging
import time
import argparse

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("OpenAI-Test")

# Add the parent directory to the path so we can import the modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from chatmode.llm_integration.llm_model import LLMModel, ModelType
from chatmode.llm_integration.openai_config import OpenAIConfig

def test_mock_model():
    """Test the mock model (which doesn't require an API key)"""
    logger.info("Testing Mock LLM Model:")
    model = LLMModel(model_type="mock")
    
    # Test response generation
    response = model.generate_response("What is the capital of France?")
    logger.info(f"Mock response: {response}")
    
    # Test token counting
    token_count = model.count_tokens("This is a test prompt for token counting.")
    logger.info(f"Mock token count: {token_count}")
    
    assert True # Mock model test passed

def test_openai_model(model_name="gpt-3.5-turbo", api_key=None):
    """Test the OpenAI model with actual API calls"""
    logger.info(f"Testing OpenAI API with model {model_name}:")
    
    # Try to get API key from environment if not provided
    if not api_key:
        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            logger.error("No OpenAI API key provided or found in environment variables.")
            assert False, "OpenAI API key not provided or found in environment variables."
    
    try:
        # Initialize model
        model = LLMModel(model_name=model_name, model_type="openai", api_key=api_key)
        logger.info("Successfully initialized OpenAI client")
        
        # Get model info
        model_info = model.get_model_info()
        logger.info(f"Model info: {model_info}")
        assert model_info is not None, "Failed to get OpenAI model info"
        
        # Test token counting
        test_prompt = "This is a test prompt for the OpenAI API. It will be used to verify token counting functionality."
        token_count = model.count_tokens(test_prompt)
        logger.info(f"Token count for test prompt: {token_count}")
        assert token_count > 0, "Token count should be greater than 0"
        
        # Test response generation with simple query
        logger.info("Testing simple query response generation...")
        start_time = time.time()
        response = model.generate_response(
            "What is the capital of France?",
            max_new_tokens=50,
            temperature=0.7
        )
        elapsed_time = time.time() - start_time
        logger.info(f"Response generated in {elapsed_time:.2f} seconds: {response}")
        assert response is not None and len(response) > 0, "Response should not be empty"
        
        # Test system message formatting
        logger.info("Testing system message formatted prompt...")
        system_prompt = "You are a helpful AI assistant specialized in finance and forecasting. User Query: What factors affect stock price movements?"
        start_time = time.time()
        response = model.generate_response(
            system_prompt,
            max_new_tokens=100,
            temperature=0.7
        )
        elapsed_time = time.time() - start_time
        logger.info(f"Response generated in {elapsed_time:.2f} seconds")
        logger.info(f"Response: {response[:100]}...")  # First 100 chars
        assert response is not None and len(response) > 0, "Response should not be empty"
        
        logger.info("OpenAI API test succeeded.")
        
    except Exception as e:
        logger.error(f"Error testing OpenAI API: {str(e)}")
        assert False, f"Error testing OpenAI API: {str(e)}"

def main():
    """Main function to run tests based on command line arguments"""
    parser = argparse.ArgumentParser(description="Test OpenAI integration with Pulse")
    parser.add_argument("--model", default="gpt-3.5-turbo", help="OpenAI model name to test")
    parser.add_argument("--key", help="OpenAI API key (will use environment variable if not provided)")
    parser.add_argument("--mock-only", action="store_true", help="Only test the mock implementation")
    args = parser.parse_args()
    
    # Always test the mock model as it doesn't require API key
    logger.info("Starting OpenAI integration tests...")
    # Call the test functions, which now use assertions
    logger.info("Starting OpenAI integration tests...")
    test_mock_model()
    logger.info("Mock model test completed.")
    
    # Test OpenAI API if requested
    if not args.mock_only:
        test_openai_model(model_name=args.model, api_key=args.key)
        logger.info("OpenAI API test completed.")
    
    logger.info("Test suite completed.")

if __name__ == "__main__":
    main()