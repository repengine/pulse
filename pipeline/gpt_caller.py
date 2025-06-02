import os
import json
import openai
from typing import Optional


class GPTCaller:
    def __init__(self, api_key: Optional[str] = None, model: str = "gpt-4"):
        """
        Initializes the GPTCaller.

        Args:
            api_key: The OpenAI API key. If None, loads from OPENAI_API_KEY environment variable.
            model: The OpenAI model to use (e.g., "gpt-4", "gpt-3.5-turbo").
        """
        self.api_key = (
            api_key if api_key is not None else os.environ.get("OPENAI_API_KEY")
        )
        if not self.api_key:
            raise ValueError(
                "OpenAI API key not provided and not found in environment variables."
            )
        openai.api_key = self.api_key
        self.model = model

    def generate(self, prompt: str) -> dict:
        """
        Calls the OpenAI API to generate a response based on the prompt.

        Args:
            prompt: The input prompt for the GPT model.

        Returns:
            A dictionary containing the raw GPT output and a parsed JSON structure.
        """
        try:
            if self.model.startswith("gpt-3.5-turbo") or self.model.startswith("gpt-4"):
                # Use chat completions for newer models
                response = openai.chat.completions.create(
                    model=self.model, messages=[{"role": "user", "content": prompt}]
                )
                raw_output = response.choices[0].message.content
            else:
                # Use completion for older models (if needed, though chat is preferred)
                response = openai.completions.create(
                    model=self.model,
                    prompt=prompt,
                    max_tokens=1024,  # Example max tokens, adjust as needed
                )
                raw_output = response.choices[0].text

            gpt_output = raw_output
            gpt_struct = {}

            # Attempt to parse JSON from the raw output
            if raw_output:  # Ensure raw_output is not None
                try:
                    # Look for JSON block, assuming it's within curly braces
                    json_start = raw_output.find("{")
                    json_end = raw_output.rfind("}")
                    if json_start != -1 and json_end != -1 and json_end > json_start:
                        json_string = raw_output[json_start: json_end + 1]
                        gpt_struct = json.loads(json_string)
                    else:
                        # If no JSON block found, try parsing the whole output if it's
                        # just JSON
                        gpt_struct = json.loads(raw_output)
                except json.JSONDecodeError:
                    # If JSON parsing fails, gpt_struct remains an empty dict
                    pass

            return {"gpt_output": gpt_output, "gpt_struct": gpt_struct}

        except Exception as e:
            print(f"Error calling OpenAI API: {e}")
            return {"gpt_output": f"Error: {e}", "gpt_struct": {}}


if __name__ == "__main__":
    # Example Usage (requires OPENAI_API_KEY environment variable)
    # Or pass api_key explicitly: caller = GPTCaller(api_key="YOUR_API_KEY")
    try:
        caller = GPTCaller()
        test_prompt = "Generate a JSON object with a 'greeting' key and 'message' key."
        result = caller.generate(test_prompt)
        print("GPT Output:", result["gpt_output"])
        print("GPT Struct:", result["gpt_struct"])
    except ValueError as e:
        print(e)
