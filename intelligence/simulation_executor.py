# intelligence/simulation_executor.py
"""Pulse Simulation Executor (stable v1.3)

Executes simulation and retrodiction forecasts, integrating with the
Function Router, GPT Caller, and forecast compression.
Handles chunked simulation runs and Monte Carlo paths.
"""
from __future__ import annotations

import random
import sys
import warnings
import time
import json
import os
import google.generativeai as genai # Import at top level
from typing import List, Dict, Optional, Any, Callable, Union, Tuple

import tempfile
import os

import numpy as np
from forecast_engine.forecast_compressor import compress_mc_samples
from intelligence.forecast_schema import ForecastSchema
from pydantic import ValidationError

from intelligence.function_router import FunctionRouter
from pipeline.gpt_caller import GPTCaller
# Import specific config items
from intelligence.intelligence_config import (
    GPT_FALLBACK_MODEL, MAX_GPT_RETRIES, GPT_RETRY_SLEEP,
    GEMINI_API_KEY, GEMINI_DEFAULT_MODEL, MAX_GEMINI_RETRIES,
    GEMINI_RETRY_SLEEP, LLM_PROVIDER
)
from config import ai_config # Keep for OPENAI_API_KEY for now
from core.variable_registry import VARIABLE_REGISTRY
from simulation_engine.causal_rules import RULES
from simulation_engine.worldstate import WorldState

class SimulationExecutor:
    """
    Executes simulation and retrodiction forecasts.
    """

    def __init__(self, router: Optional[FunctionRouter] = None) -> None:
        """
        Initializes the SimulationExecutor.

        Args:
            router: An optional FunctionRouter instance. If None, a new one is created.
        """
        self.router: FunctionRouter = router or FunctionRouter()
        openai_api_key: Optional[str] = getattr(ai_config, "OPENAI_API_KEY", None)
        gpt_model: Optional[str] = getattr(ai_config, "DEFAULT_OPENAI_MODEL", None)

        # Ensure GPT model is a string, fallback to default if None.
        if not isinstance(gpt_model, str):
            fallback: str = GPT_FALLBACK_MODEL
            print(
                f"[Executor] Warning: Configured GPT model '{gpt_model}' is not a string."
                f" Falling back to '{fallback}'."
            )
            gpt_model = fallback

        self.gpt_caller: Optional[GPTCaller] = None
        self.gemini_client = None
        self.llm_provider: str = LLM_PROVIDER

        if self.llm_provider == "gpt":
            try:
                if openai_api_key and isinstance(openai_api_key, str):
                    self.gpt_caller = GPTCaller(api_key=openai_api_key, model=gpt_model)
                    print(f"[Executor] GPTCaller initialized with model: {gpt_model}")
                else:
                    print("[Executor] OpenAI API key not found or invalid. GPT calls will be skipped.")
                    self.llm_provider = "none"
            except Exception as e:
                print(f"[Executor] Error initializing GPTCaller: {e}. GPT calls will be skipped.")
                self.llm_provider = "none"
        elif self.llm_provider == "gemini":
            if GEMINI_API_KEY:
                try:
                    # Configure and initialize Gemini client
                    genai.configure(api_key=GEMINI_API_KEY)
                    self.gemini_client = genai.GenerativeModel(GEMINI_DEFAULT_MODEL)
                    print(f"[Executor] Gemini client initialized with model: {GEMINI_DEFAULT_MODEL}")
                except ImportError: # Should not happen now, but good practice
                    print("[Executor] 'google-generativeai' library seems unavailable despite installation. Gemini calls will be skipped.")
                    self.llm_provider = "none"
                except AttributeError as ae: # Catch if configure/GenerativeModel don't exist
                     print(f"[Executor] Error initializing Gemini client (likely library version issue): {ae}. Gemini calls will be skipped.")
                     self.llm_provider = "none"
                except Exception as e:
                    print(f"[Executor] Error initializing Gemini client: {e}. Gemini calls will be skipped.")
                    self.llm_provider = "none"
            else:
                print("[Executor] GEMINI_API_KEY not found in environment. Gemini calls will be skipped.")
                self.llm_provider = "none"
        else: # Handles LLM_PROVIDER being neither 'gpt' nor 'gemini' or invalid
             print(f"[Executor] LLM_PROVIDER set to '{self.llm_provider}'. No LLM calls will be made.")
             self.llm_provider = "none"

    # Correctly indented method within the class
    def _call_llm(self, prompt: str) -> Dict[str, Any]:
        """
        Calls the configured LLM (GPT or Gemini) with retry logic.

        Args:
            prompt: The prompt to send to the LLM.

        Returns:
            A dictionary containing the LLM output ('output'), structured data ('struct'),
            or an error message ('error'). Standardizes keys to 'output' and 'struct'.
        """
        result: Dict[str, Any] = {}
        if self.llm_provider == "none" or not prompt:
            result["error"] = "LLM provider not configured or empty prompt."
            return result

        caller_func: Optional[Callable[[str], Dict[str, Any]]] = None
        retries: int = 0
        sleep_time: int = 0
        provider_name: str = ""

        if self.llm_provider == "gpt":
            if not self.gpt_caller:
                result["error"] = "GPT provider selected but caller not initialized."
                return result
            retries = MAX_GPT_RETRIES
            sleep_time = GPT_RETRY_SLEEP
            caller_func = self.gpt_caller.generate # This already returns dict with 'gpt_output', 'gpt_struct'
            provider_name = "GPT"

        elif self.llm_provider == "gemini":
            if not self.gemini_client:
                result["error"] = "Gemini provider selected but client not initialized."
                return result
            retries = MAX_GEMINI_RETRIES
            sleep_time = GEMINI_RETRY_SLEEP
            provider_name = "Gemini"

            # Define a wrapper for the Gemini call to match expected input/output
            def gemini_caller_wrapper(p: str) -> Dict[str, Any]:
                try:
                    response = self.gemini_client.generate_content(p)

                    # Basic safety check for response structure
                    if not hasattr(response, 'text'):
                         # Handle cases where response might be blocked or empty
                         safety_ratings = getattr(response, 'prompt_feedback', {}).get('safety_ratings', [])
                         block_reason = getattr(response, 'prompt_feedback', {}).get('block_reason', 'Unknown')
                         if safety_ratings:
                              raise ValueError(f"Gemini response blocked or empty. Reason: {block_reason}. Ratings: {safety_ratings}")
                         else:
                              raise ValueError("Gemini response missing 'text' attribute and no clear block reason.")

                    text_output = response.text
                    struct_output = None
                    try:
                        # Look for a JSON block within the text
                        json_start = text_output.find('{')
                        json_end = text_output.rfind('}') + 1
                        if json_start != -1 and json_end != -1 and json_start < json_end:
                            json_str = text_output[json_start:json_end]
                            struct_output = json.loads(json_str)
                            # Keep full text output for context, don't remove JSON part
                        else:
                             struct_output = {"raw_text": text_output} # Fallback
                    except (json.JSONDecodeError, ValueError) as json_err:
                        print(f"[Executor] Gemini JSON parsing error: {json_err}")
                        struct_output = {"parsing_error": str(json_err), "raw_text": text_output}

                    # Return standardized keys
                    return {"output": text_output.strip(), "struct": struct_output}
                except AttributeError as ae:
                     print(f"[Executor] Gemini response format error: {ae}")
                     raise ValueError(f"Unexpected Gemini response format: {ae}") from ae
                except Exception as gemini_err:
                    # Propagate other errors (like API errors, ValueErrors from blocking)
                    raise gemini_err

            caller_func = gemini_caller_wrapper
        else:
             result["error"] = f"Unknown LLM provider: {self.llm_provider}"
             return result

        # --- Retry Logic ---
        success: bool = False
        attempt: int = 0
        last_exception: Optional[Exception] = None
        while attempt < retries and not success:
            try:
                print(f"[Executor] {provider_name} call attempt {attempt + 1}/{retries}")
                llm_raw_result: Dict[str, Any] = caller_func(prompt)

                # Standardize keys after the call
                if self.llm_provider == "gpt":
                    result["output"] = llm_raw_result.get("gpt_output")
                    result["struct"] = llm_raw_result.get("gpt_struct")
                elif self.llm_provider == "gemini":
                     result["output"] = llm_raw_result.get("output")
                     result["struct"] = llm_raw_result.get("struct")

                # Basic check if output seems valid (can be refined)
                if result.get("output") is not None or result.get("struct") is not None:
                     success = True
                else:
                     # Treat empty/None results as potential transient issues if not an explicit error
                     raise ValueError(f"{provider_name} returned empty result.")

            except Exception as exc:
                last_exception = exc
                attempt += 1
                print(f"[Executor] {provider_name} call attempt {attempt}/{retries} failed: {exc}")
                if attempt < retries:
                    # Exponential backoff
                    time.sleep(sleep_time * (2 ** (attempt -1)))
                else:
                    err_msg = f"{provider_name} call failed after {retries} attempts: {last_exception}"
                    result["error"] = err_msg
                    print(f"[Executor] {provider_name} call failed permanently: {last_exception}")

        return result

    def run_chunked_forecast(
        self,
        start_year: int,
        total_turns: int = 312,
        chunk_size: int = 52,
        *,
        on_chunk_end: Optional[Callable[[int], None]] = None,
        n_paths: int = 1,
        mc_seed: Optional[int] = None,
    ) -> Tuple[Optional[WorldState], Union[List[Dict[str, Any]], Any]]:
        """
        Runs a chunked forward simulation forecast with optional Monte Carlo paths.
        """
        if mc_seed is not None:
            random.seed(mc_seed)

        ws: Optional[WorldState] = None
        temp_file = None
        temp_file_path: Optional[str] = None
        final_result: Union[List[Dict[str, Any]], Any] = [] # Initialize final_result

        try:
            # Create a temporary file to store samples
            temp_file = tempfile.NamedTemporaryFile(mode='w+', delete=False, suffix='.jsonl')
            temp_file_path = temp_file.name
            print(f"[Executor] Using temporary file for MC samples: {temp_file_path}")

            for path_idx in range(n_paths):
                ws = self.router.run_function("turn_engine.initialize_worldstate", start_year=start_year)
                done: int = 0

                while done < total_turns:
                    step: int = min(chunk_size, total_turns - done)
                    for _ in range(step):
                        self.router.run_function("turn_engine.run_turn", state=ws)
                    done += step
                    if on_chunk_end:
                        on_chunk_end(done)
                    print(f"[Executor] 🚀 Completed {done}/{total_turns} turns (path {path_idx+1}/{n_paths})")

                forecast: Dict[str, Any] = {}
                try:
                    generated: Any = self.router.run_function("forecast_engine.generate_forecast", state=ws)
                    if isinstance(generated, dict):
                        forecast.update(generated)
                    else:
                        forecast["error"] = "Non-dict forecast"
                        forecast["original_type"] = str(type(generated))
                        print(f"[Executor] Warning: Forecast generator returned {type(generated)}.")
                except Exception as e:
                    forecast["error"] = str(e)
                    print(f"[Executor] Error calling generate_forecast: {e}")

                forecast["pulse_domains"] = list(VARIABLE_REGISTRY.keys())
                forecast["pulse_rules"] = RULES # Consider if this is too large/needed per sample

                # --- LLM Analysis Call (using _call_llm) ---
                if self.llm_provider != "none" and "error" not in forecast:
                    prompt_data: Any = ws.snapshot() if ws is not None and hasattr(ws, "snapshot") else {}
                    prompt: str = ""
                    try:
                        # Construct the prompt (remains the same for now, adapt if needed for Gemini)
                        prompt_template = """You are an AI assisting in analyzing a simulation of a complex system.
    Below is the current state of the simulation. The simulation is governed by a set of rules and operates on variables defined in a registry.

    Current World State Snapshot:
    {}

    Analyze this state and provide:
    1. A structured JSON object containing key observations or potential future states based on the rules (though the rules themselves are not provided in detail here to save token space).
    2. A concise natural language summary of your analysis.

    Ensure your response is formatted clearly, with the JSON object and the summary distinctly separated.
    """
                        worldstate_json = json.dumps(prompt_data, default=str, indent=2)
                        prompt = prompt_template.format(worldstate_json)
                    except TypeError as err:
                        forecast["llm_error"] = f"Error creating prompt: {err}"
                        print(f"[Executor] Error creating LLM prompt: {err}")

                    if prompt:
                        llm_result = self._call_llm(prompt) # Call the unified helper method
                        if "error" in llm_result:
                            forecast["llm_error"] = llm_result["error"]
                        else:
                            # Use standardized keys from _call_llm
                            forecast["llm_output"] = llm_result.get("output")
                            forecast["llm_struct"] = llm_result.get("struct")
                elif self.llm_provider == "none":
                     print("[Executor] LLM provider not configured, skipping analysis.")
                # --- End LLM Analysis Call ---

                try:
                    ForecastSchema(**forecast)
                except ValidationError as ve:
                    forecast["schema_validation_error"] = str(ve)
                    print(f"[Executor] Schema validation warning: {ve}")

                # Write the forecast to the temporary file
                json.dump(forecast, temp_file)
                temp_file.write('\n')
                temp_file.flush() # Ensure data is written

            # After the loop, close the file for writing
            temp_file.close()

            # Read samples back from the temporary file
            read_mc_samples: List[Dict[str, Any]] = []
            with open(temp_file_path, 'r') as f:
                for line in f:
                    if line.strip():
                        try:
                            read_mc_samples.append(json.loads(line))
                        except json.JSONDecodeError as json_err:
                             print(f"[Executor] Warning: Skipping invalid JSON line in temp file: {json_err}")


            # Compress or return raw samples
            try:
                if read_mc_samples: # Only compress if there are samples
                     compressed: Any = compress_mc_samples(read_mc_samples, alpha=0.9)
                     final_result = compressed
                else:
                     print("[Executor] No valid samples read from temp file.")
                     final_result = [] # Return empty list if no samples
            except Exception as e:
                final_result = read_mc_samples # Fallback to raw samples on compression error
                print(f"[Executor] Compression error: {e}. Returning raw samples.")

        finally:
            # Clean up the temporary file
            if temp_file and not temp_file.closed:
                 temp_file.close()
            if temp_file_path and os.path.exists(temp_file_path):
                try:
                    os.unlink(temp_file_path)
                    print(f"[Executor] Cleaned up temporary file: {temp_file_path}")
                except Exception as e:
                    print(f"[Executor] Error cleaning up temp file {temp_file_path}: {e}")


        if ws is None and not final_result: # Handle case where no paths ran AND no results exist
            return None, []
        return ws, final_result # Return final state of last path and the (compressed) result


    def run_retrodiction_forecast(self, start_date: str, days: int = 30) -> Any:
        """
        Attempts to run a retrodiction forecast. Falls back to forward simulation on failure.
        """
        try:
            # Assuming retrodiction doesn't use the LLM call currently
            return self.router.run_function("retrodiction.run_retrodiction_test", start_date=start_date)
        except Exception as e:
            print(f"[Executor] Retrodiction failed: {e}. Using forward fallback.")
            loader: Optional[Any] = None
            try:
                loader = self.router.run_function(
                    "retrodiction.get_snapshot_loader", start_date=start_date, days=days
                )
            except Exception:
                pass # Ignore error getting loader if retrodiction failed anyway
            initial: WorldState = self.router.run_function("turn_engine.initialize_worldstate")
            # Assuming forward simulation fallback also doesn't use LLM here
            return self.router.run_function(
                "simulation_engine.simulator_core.simulate_forward",
                state=initial,
                turns=days,
                retrodiction_mode=True,
                retrodiction_loader=loader,
            )
