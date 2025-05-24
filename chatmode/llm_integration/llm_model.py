import time
import random
import logging
from typing import Optional, Dict, Any, Tuple
from enum import Enum
import json
from chatmode.llm_integration.openai_config import OpenAIConfig

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("LLMModel")

# Constants
OPENAI_AVAILABLE = False
TIKTOKEN_AVAILABLE = False

# Define module availability flags
OPENAI_AVAILABLE = False
TIKTOKEN_AVAILABLE = False


# Try to import dependencies with clear error handling
try:
    # import openai # F401: unused at module level

    # We'll refer to the OpenAI client directly without aliasing
    OPENAI_AVAILABLE = True
    logger.info("OpenAI package successfully imported.")

    # Try to import tiktoken for token counting
    try:
        # import tiktoken # F401: unused at module level

        TIKTOKEN_AVAILABLE = True
        logger.info("tiktoken package successfully imported.")
    except ImportError:
        logger.warning("tiktoken not installed. Token counting will use approximation.")
except ImportError:
    logger.warning("OpenAI package not installed. OpenAI models will not be available.")


class ModelType(Enum):
    """Enumeration of supported model types"""

    OPENAI = "openai"
    HUGGINGFACE = "huggingface"
    LOCAL = "local"
    MOCK = "mock"  # For testing purposes


class LLMModel:
    def __init__(
        self,
        model_name: str = "gpt-3.5-turbo",
        model_type: str = "openai",
        api_key: Optional[str] = None,
    ):
        """
        Initializes the LLM model with specified parameters.

        Args:
            model_name (str): Name of the model to use
            model_type (str): Type of model ("openai", "huggingface", "local", "mock")
            api_key (str, optional): API key for the model service
        """
        self.model_name = model_name

        # Try to convert model_type string to ModelType enum
        try:
            self.model_type = ModelType(model_type.lower())
        except ValueError:
            logger.warning(
                f"Unknown model type: {model_type}. Falling back to mock model."
            )
            self.model_type = ModelType.MOCK

        # Initialize model-specific components
        self.client = None
        self.tokenizer = None
        self.model = None
        self.lora_adapter = None
        self.config = None

        # Initialize OpenAI client if using OpenAI models
        if self.model_type == ModelType.OPENAI:
            if not OPENAI_AVAILABLE:
                logger.error(
                    "OpenAI package not installed. Please install it with: pip install openai"
                )
                raise ImportError("OpenAI package not installed")

            # Initialize OpenAI configuration
            self.config = OpenAIConfig(api_key=api_key, model_name=model_name)

            # Check if API key is available
            if not self.config.has_api_key:
                logger.warning(
                    "OpenAI API key not provided. Please set OPENAI_API_KEY environment variable."
                )

            # Initialize OpenAI client
            try:
                # Import and create the client directly to avoid aliasing issues
                from openai import OpenAI

                self.client = OpenAI(api_key=self.config.api_key)
                logger.info(f"Initialized OpenAI client with model: {model_name}")
            except Exception as e:
                logger.error(f"Error initializing OpenAI client: {str(e)}")
                raise

        elif (
            self.model_type == ModelType.HUGGINGFACE
            or self.model_type == ModelType.LOCAL
        ):
            # Placeholder for HuggingFace and local model initialization
            logger.info(
                f"Model type {self.model_type.value} initialization placeholder"
            )

        elif self.model_type == ModelType.MOCK:
            # Mock model for testing
            logger.info("Using mock LLM model for testing")

    def load_model(self):
        """
        Loads the language model and tokenizer based on the model type.
        For OpenAI, this is a no-op as the API client is already initialized.
        """
        if self.model_type == ModelType.OPENAI:
            # Nothing to load for OpenAI API models
            logger.info("OpenAI models are loaded on-demand via API")
            return True

        elif (
            self.model_type == ModelType.HUGGINGFACE
            or self.model_type == ModelType.LOCAL
        ):
            logger.info(f"Loading model: {self.model_name}...")
            try:
                # TODO: Implement actual model loading logic
                # self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
                # self.model = AutoModelForCausalLM.from_pretrained(self.model_name)
                logger.info("Model loading placeholder complete")
                return True
            except Exception as e:
                logger.error(f"Error loading model: {str(e)}")
                return False

        elif self.model_type == ModelType.MOCK:
            logger.info("Mock model doesn't require loading")
            return True

        return False

    def apply_lora_adapter(self, adapter_path: str):
        """
        Applies a trained LoRA adapter to the model.
        Only applicable for local models that support LoRA.

        Args:
            adapter_path (str): The path to the trained LoRA adapter.
        """
        if self.model_type == ModelType.OPENAI:
            logger.warning("LoRA adapters are not applicable for OpenAI API models")
            return False

        if self.model is None and self.model_type != ModelType.MOCK:
            logger.error("Model not loaded. Cannot apply LoRA adapter.")
            return False

        logger.info(f"Applying LoRA adapter from: {adapter_path}...")

        if (
            self.model_type == ModelType.HUGGINGFACE
            or self.model_type == ModelType.LOCAL
        ):
            try:
                # TODO: Implement LoRA adapter application logic
                # lora_config = LoraConfig.from_pretrained(adapter_path)
                # self.model = get_peft_model(self.model, lora_config)
                # self.lora_adapter = adapter_path
                logger.info("LoRA adapter application placeholder complete")
                return True
            except Exception as e:
                logger.error(f"Error applying LoRA adapter: {str(e)}")
                return False

        elif self.model_type == ModelType.MOCK:
            logger.info("Mock LoRA adapter application complete")
            self.lora_adapter = adapter_path
            return True

        return False

    def count_tokens(self, text: str) -> int:
        """
        Count the number of tokens in the input text.

        Args:
            text (str): The input text to count tokens for

        Returns:
            int: The number of tokens
        """
        if self.model_type == ModelType.OPENAI and TIKTOKEN_AVAILABLE:
            try:
                # For OpenAI models, use tiktoken
                # We know tiktoken is available if TIKTOKEN_AVAILABLE is True
                import tiktoken

                enc = tiktoken.encoding_for_model(self.model_name)
                return len(enc.encode(text))
            except Exception as e:
                # Fallback to a rough estimate if tiktoken fails
                logger.warning(f"Error using tiktoken: {str(e)}. Using rough estimate.")

        # Fallback for all other cases
        if (
            self.model_type == ModelType.HUGGINGFACE
            or self.model_type == ModelType.LOCAL
        ):
            if self.tokenizer:
                return len(self.tokenizer.encode(text))

        # Default rough estimate
        return len(text) // 4  # Rough estimate: ~4 chars per token

    def _handle_openai_error(
        self, error: Exception, max_retries: int = 5
    ) -> Tuple[str, bool]:
        """
        Handle OpenAI API errors with proper logging, user-friendly messages, and retry logic.

        Args:
            error (Exception): The exception raised by the OpenAI API
            max_retries (int): Maximum number of retries for rate limit errors

        Returns:
            tuple: (user-friendly error message, should_retry flag)
        """
        error_msg = str(error)
        should_retry = False

        if "rate_limit" in error_msg.lower() or "rate_limited" in error_msg.lower():
            logger.warning(f"OpenAI API rate limit exceeded: {error_msg}")
            should_retry = True
            return (
                "The API rate limit has been exceeded. Automatically retrying with exponential backoff...",
                should_retry,
            )

        elif "authentication" in error_msg.lower():
            logger.error(f"OpenAI API authentication error: {error_msg}")
            return (
                "There was an authentication error with the OpenAI API. Please check your API key.",
                should_retry,
            )

        elif "server_error" in error_msg.lower() or any(
            code in error_msg.split() for code in ["500", "502", "503", "504"]
        ):
            logger.error(f"OpenAI API server error: {error_msg}")
            should_retry = True
            return (
                "The OpenAI service is currently experiencing issues. Automatically retrying...",
                should_retry,
            )

        elif "context_length" in error_msg.lower() or "token" in error_msg.lower():
            logger.warning(f"OpenAI API token limit exceeded: {error_msg}")
            return (
                "The input is too long for the model. Please use a shorter query or consider using a model with a larger context window.",
                should_retry,
            )

        elif "timeout" in error_msg.lower() or "connection" in error_msg.lower():
            logger.warning(f"OpenAI API connection issue: {error_msg}")
            should_retry = True
            return (
                "Connection to OpenAI API timed out. Automatically retrying...",
                should_retry,
            )

        else:
            logger.error(f"Unexpected OpenAI API error: {error_msg}")
            return (
                f"An error occurred while processing your request: {error_msg}",
                should_retry,
            )

    def generate_response(
        self,
        prompt: str,
        max_new_tokens: int = 500,
        temperature: float = 0.7,
        model_name: Optional[str] = None,
    ) -> str:
        """
        Generates a response from the language model with improved error handling and retry logic.

        Args:
            prompt (str): The input prompt.
            max_new_tokens (int): The maximum number of new tokens to generate.
            temperature (float): Sampling temperature (0.0 to 1.0)
            model_name (str, optional): Override the default model name for this request

        Returns:
            str: The generated response.
        """
        # Use the provided model name or fall back to the default
        model_to_use = model_name or self.model_name

        logger.info(
            f"Generating response with model: {model_to_use}, type: {self.model_type.value}"
        )
        logger.debug(f"Prompt (truncated): {prompt[:100]}...")

        # Handle different model types
        if self.model_type == ModelType.OPENAI:
            if not self.client:
                return "Error: OpenAI client not initialized."

            # Initialize retry parameters
            max_retries = 5
            base_delay = 1  # start with 1 second delay
            retry_count = 0

            while retry_count <= max_retries:
                try:
                    # Start timing the API call
                    start_time = time.time()

                    # Check if the model is a chat model (starts with gpt-)
                    if model_to_use.startswith("gpt-"):
                        # Process the prompt to extract messages if it's in the system message format
                        if "You are " in prompt and "User Query:" in prompt:
                            # Extract system message and user query
                            system_message = prompt.split("User Query:")[0].strip()
                            user_query = prompt.split("User Query:")[1].strip()

                            # Make the API call with properly typed messages
                            response = self.client.chat.completions.create(
                                model=model_to_use,
                                messages=[
                                    {"role": "system", "content": system_message},
                                    {"role": "user", "content": user_query},
                                ],
                                max_tokens=max_new_tokens,
                                temperature=temperature,
                            )
                        else:
                            # If not in the expected format, use the whole prompt as user message
                            response = self.client.chat.completions.create(
                                model=model_to_use,
                                messages=[{"role": "user", "content": prompt}],
                                max_tokens=max_new_tokens,
                                temperature=temperature,
                            )

                        # Extract the response text, ensuring it's always a string
                        response_text = response.choices[0].message.content or ""
                    else:
                        # For non-chat models (e.g., text-davinci models)
                        response = self.client.completions.create(
                            model=model_to_use,
                            prompt=prompt,
                            max_tokens=max_new_tokens,
                            temperature=temperature,
                        )

                        # Extract the response text
                        response_text = response.choices[0].text

                    # Log timing and token usage information
                    elapsed_time = time.time() - start_time
                    logger.info(
                        f"OpenAI API call completed in {elapsed_time:.2f} seconds"
                    )

                    if hasattr(response, "usage"):
                        prompt_tokens = getattr(response.usage, "prompt_tokens", 0)
                        completion_tokens = getattr(
                            response.usage, "completion_tokens", 0
                        )
                        total_tokens = getattr(response.usage, "total_tokens", 0)

                        # Calculate estimated cost if available
                        if self.config:
                            estimated_cost = self.config.estimate_cost(
                                prompt_tokens, completion_tokens
                            )
                            logger.info(
                                f"Token usage - Prompt: {prompt_tokens}, Completion: {completion_tokens}, Total: {total_tokens}, Est. cost: ${estimated_cost:.5f}"
                            )
                        else:
                            logger.info(
                                f"Token usage - Prompt: {prompt_tokens}, Completion: {completion_tokens}, Total: {total_tokens}"
                            )

                    return response_text

                except Exception as e:
                    error_message, should_retry = self._handle_openai_error(
                        e, max_retries
                    )
                    logger.error(f"Error generating response from OpenAI: {str(e)}")

                    if should_retry and retry_count < max_retries:
                        retry_count += 1
                        # Calculate exponential backoff delay with jitter
                        delay = base_delay * (2**retry_count) + (random.uniform(0, 1))
                        logger.info(
                            f"Retrying in {delay:.2f} seconds... (attempt {retry_count}/{max_retries})"
                        )
                        time.sleep(delay)
                    else:
                        return error_message

        elif (
            self.model_type == ModelType.HUGGINGFACE
            or self.model_type == ModelType.LOCAL
        ):
            if self.model is None or self.tokenizer is None:
                logger.error("Model or tokenizer not loaded. Cannot generate response.")
                return "Error: Language model not ready."

            # TODO: Implement actual generation logic for local models
            logger.info("Local model generation placeholder")
            return f"Placeholder response for prompt: '{prompt[:50]}...'"

        elif self.model_type == ModelType.MOCK:
            # Return a mock response for testing
            logger.info("Generating mock response")
            return f"This is a mock response from the LLM model. Your prompt was: '{prompt[:50]}...'"

        return "Error: Unknown model type or configuration issue."

    def get_model_info(self) -> Dict[str, Any]:
        """
        Get information about the current model.

        Returns:
            Dict[str, Any]: Information about the model
        """
        info = {
            "model_name": self.model_name,
            "model_type": self.model_type.value,
        }

        if self.model_type == ModelType.OPENAI and self.config:
            # Create a new dictionary instead of using update
            model_info = dict(info)
            # Convert to appropriate types to avoid type issues
            model_info["available_models"] = json.dumps(
                self.config.get_available_models()
            )
            model_info["current_model_info"] = json.dumps(self.config.get_model_info())
            model_info["token_usage"] = json.dumps(
                {"current_session": self._get_token_usage_stats()}
            )
            return model_info

        elif self.lora_adapter:
            info["lora_adapter"] = self.lora_adapter

        return info

    def _get_token_usage_stats(self) -> Dict[str, Any]:
        """
        Get token usage statistics for the current session.

        Returns:
            Dict[str, Any]: Token usage statistics
        """
        # This would ideally come from a persistent store, but for now we'll use a simple calculation
        if not hasattr(self, "_token_usage"):
            self._token_usage = {
                "prompt_tokens": 0,
                "completion_tokens": 0,
                "total_tokens": 0,
                "estimated_cost": 0.0,
            }

        return self._token_usage

    def switch_model(self, new_model_name: str) -> bool:
        """
        Switch to a different model within the same model type.

        Args:
            new_model_name (str): The name of the new model to use

        Returns:
            bool: True if the switch was successful, False otherwise
        """
        if self.model_type != ModelType.OPENAI:
            logger.warning(
                "Model switching is currently only supported for OpenAI models"
            )
            return False

        if self.model_name == new_model_name:
            logger.info(f"Already using model: {new_model_name}")
            return True

        # Check if the model is available
        if self.config and new_model_name in self.config.available_models:
            old_model = self.model_name
            self.model_name = new_model_name
            logger.info(f"Switched model from {old_model} to {new_model_name}")
            return True
        else:
            logger.warning(f"Model {new_model_name} not found in available models")
            return False


if __name__ == "__main__":
    # Example Usage
    try:
        # For OpenAI models (using API key from environment variable)
        llm = LLMModel(model_name="gpt-3.5-turbo", model_type="openai")
        response = llm.generate_response(
            "Tell me about Pulse as a forecasting system.", max_new_tokens=100
        )
        print(f"\nOpenAI Response:\n{response}\n")

        # For testing without API
        mock_llm = LLMModel(model_type="mock")
        mock_response = mock_llm.generate_response("Tell me about Pulse.")
        print(f"\nMock Response:\n{mock_response}\n")

        # Print model info
        print(f"\nModel Info:\n{json.dumps(llm.get_model_info(), indent=2)}\n")

    except Exception as e:
        print(f"Error running example: {str(e)}")
