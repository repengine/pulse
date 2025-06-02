from pipeline.gpt_caller import GPTCaller
import unittest
import os
import openai  # Import openai
from unittest.mock import patch, MagicMock

# Ensure the path to the pipeline directory is in sys.path for importing gpt_caller
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


class TestGPTCaller(unittest.TestCase):
    @patch("pipeline.gpt_caller.openai.chat.completions.create")
    def test_generate_chat_completion(self, mock_create):
        """Tests generate method with a chat completion model."""
        # Mock the OpenAI API response
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = (
            'This is a raw text response with some JSON: ```json\n{"key": "value"}\n```'
        )
        mock_create.return_value = mock_response

        # Instantiate GPTCaller with a chat model
        caller = GPTCaller(api_key="fake_api_key", model="gpt-4")

        # Call the generate method
        prompt = "Test prompt"
        result = caller.generate(prompt)

        # Assertions
        mock_create.assert_called_once_with(
            model="gpt-4", messages=[{"role": "user", "content": prompt}]
        )
        self.assertIn("gpt_output", result)
        self.assertIn("gpt_struct", result)
        self.assertEqual(
            result["gpt_output"],
            'This is a raw text response with some JSON: ```json\n{"key": "value"}\n```',
        )
        self.assertEqual(result["gpt_struct"], {"key": "value"})

    @patch("pipeline.gpt_caller.openai.completions.create")
    def test_generate_completion(self, mock_create):
        """Tests generate method with a completion model."""
        # Mock the OpenAI API response
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].text = (
            'Raw text response with JSON: {"another_key": 123}'
        )
        mock_create.return_value = mock_response

        # Instantiate GPTCaller with a completion model
        caller = GPTCaller(api_key="fake_api_key", model="text-davinci-003")

        # Call the generate method
        prompt = "Another test prompt"
        result = caller.generate(prompt)

        # Assertions
        mock_create.assert_called_once_with(
            model="text-davinci-003",
            prompt=prompt,
            max_tokens=1024,  # Matches the default in GPTCaller
        )
        self.assertIn("gpt_output", result)
        self.assertIn("gpt_struct", result)
        self.assertEqual(
            result["gpt_output"], 'Raw text response with JSON: {"another_key": 123}'
        )
        self.assertEqual(result["gpt_struct"], {"another_key": 123})

    @patch("pipeline.gpt_caller.openai.chat.completions.create")
    def test_generate_no_json(self, mock_create):
        """Tests generate method when the response contains no JSON."""
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "This response has no JSON."
        mock_create.return_value = mock_response

        caller = GPTCaller(api_key="fake_api_key", model="gpt-4")
        result = caller.generate("Prompt without JSON")

        self.assertEqual(result["gpt_output"], "This response has no JSON.")
        self.assertEqual(result["gpt_struct"], {})  # Should be an empty dict

    @patch("pipeline.gpt_caller.openai.chat.completions.create")
    def test_generate_invalid_json(self, mock_create):
        """Tests generate method when the response contains invalid JSON."""
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = (
            "This response has invalid JSON: {'key': 'value'"  # Missing closing brace
        )
        mock_create.return_value = mock_response

        caller = GPTCaller(api_key="fake_api_key", model="gpt-4")
        result = caller.generate("Prompt with invalid JSON")

        self.assertEqual(
            result["gpt_output"], "This response has invalid JSON: {'key': 'value'"
        )
        self.assertEqual(result["gpt_struct"], {})  # Should be an empty dict

    @patch("pipeline.gpt_caller.os.environ.get")
    @patch("pipeline.gpt_caller.openai.chat.completions.create")
    def test_init_from_env(self, mock_create, mock_getenv):
        """Tests initialization when API key is from environment variable."""
        mock_getenv.return_value = "env_api_key"
        # Mock the API call to prevent actual network request during init
        mock_create.return_value = MagicMock(
            choices=[MagicMock(message=MagicMock(content="{}"))]
        )

        caller = GPTCaller()  # No api_key passed, should use env var

        self.assertEqual(caller.api_key, "env_api_key")
        # Verify openai.api_key was set
        self.assertEqual(openai.api_key, "env_api_key")

    @patch("pipeline.gpt_caller.os.environ.get")
    def test_init_no_api_key(self, mock_getenv):
        """Tests initialization when no API key is provided."""
        mock_getenv.return_value = None  # No env var set

        with self.assertRaises(ValueError) as cm:
            GPTCaller()

        self.assertIn(
            "OpenAI API key not provided and not found in environment variables.",
            str(cm.exception),
        )

    @patch("pipeline.gpt_caller.openai.chat.completions.create")
    def test_generate_api_error(self, mock_create):
        """Tests generate method when the OpenAI API call fails."""
        mock_create.side_effect = Exception("API call failed")

        caller = GPTCaller(api_key="fake_api_key", model="gpt-4")
        result = caller.generate("Prompt causing error")

        self.assertIn("Error: API call failed", result["gpt_output"])
        self.assertEqual(result["gpt_struct"], {})


if __name__ == "__main__":
    unittest.main()
