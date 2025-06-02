"""
Evaluator
---------
Runs model evaluation benchmarks against the Pulse simulation outputs.
"""

from typing import Dict, List
from adapters.gpt_symbolic_convergence_loss import (
    compute_symbolic_convergence_loss,
    decompose_loss_components,
)
from intelligence.forecast_schema import ForecastSchema
from pydantic import ValidationError  # Import ValidationError
import pandas as pd  # Assuming feature_path is a path to a parquet file
import json
import os


class Evaluator:
    def __init__(self) -> None:
        """
        Initialize any evaluation resources (e.g., simulation engine clients).
        """
        # TODO: set up simulation_client or other services
        pass  # Placeholder

    def evaluate(self, model_info: Dict, feature_path: str) -> Dict:
        """
        Execute evaluation for the specified model on the feature dataset.
        Compares Pulse and GPT outputs and generates feedback.

        Args:
            model_info (Dict): Information about the model being evaluated.
            feature_path (str): Path to the feature dataset (assumed to contain forecast episodes).

        Returns:
            metrics (dict): Evaluation results (retrodiction error, alignment, trust delta).
        """
        metrics = {
            "retrodiction_mae": 0.0,
            "symbolic_alignment": 0.0,
            "trust_delta": 0.0,
            "total_symbolic_convergence_loss": 0.0,
        }

        try:
            # Load forecast data - Assuming feature_path is a parquet file
            # TODO: Replace with actual data loading mechanism if different
            forecast_data = pd.read_parquet(feature_path)

            total_loss = 0.0
            num_forecasts = 0
            all_proposed_changes = []  # Initialize list to collect changes

            for index, row in forecast_data.iterrows():
                # Assuming each row is a forecast episode
                f = row.to_dict()

                # Ensure pulse_output and gpt_struct are available and are dictionaries
                if (
                    "pulse_output" in f
                    and isinstance(f["pulse_output"], dict)
                    and "gpt_struct" in f
                    and isinstance(f["gpt_struct"], dict)
                ):
                    try:
                        # Create ForecastSchema objects
                        pulse_forecast = ForecastSchema(**f["pulse_output"])
                        gpt_forecast = ForecastSchema(
                            **f["gpt_struct"]
                        )  # Assuming gpt_struct matches ForecastSchema

                        # Compute divergence metrics
                        loss = compute_symbolic_convergence_loss(
                            pulse_forecast, gpt_forecast
                        )
                        loss_components = decompose_loss_components(
                            pulse_forecast, gpt_forecast
                        )

                        total_loss += loss
                        num_forecasts += 1

                        # Generate feedback and propose rule changes
                        print(f"Forecast Episode {index}:")
                        print(f"  Total Symbolic Convergence Loss: {loss}")
                        print(f"  Loss Components: {loss_components}")

                        # Analyze feedback and propose rule changes
                        proposed_rule_changes = self.analyze_and_propose_rule_changes(
                            pulse_forecast, gpt_forecast, loss_components
                        )

                        # Log proposed changes (as per scope)
                        if proposed_rule_changes:
                            print("  Proposed Rule Changes:")
                            for change in proposed_rule_changes:
                                print(f"    - {change}")
                            all_proposed_changes.extend(
                                proposed_rule_changes
                            )  # Collect changes

                        # TODO: Implement more sophisticated feedback generation and storage
                        # e.g., log to a file, store in a database, trigger alerts
                        # TODO: Integrate proposed_rule_changes into a management
                        # mechanism

                    except ValidationError as e:
                        print(f"Validation error for forecast episode {index}: {e}")
                    except Exception as e:
                        print(f"Error processing forecast episode {index}: {e}")
                else:
                    print(
                        f"Skipping forecast episode {index} due to missing or invalid pulse_output or gpt_struct")

            if num_forecasts > 0:
                metrics["total_symbolic_convergence_loss"] = total_loss / num_forecasts

            # Save proposed rule changes to a file
            output_dir = "pipeline/rule_proposals"
            os.makedirs(
                output_dir, exist_ok=True
            )  # Create directory if it doesn't exist
            output_path = os.path.join(output_dir, "proposed_rule_changes.json")
            with open(output_path, "w") as f:
                json.dump(all_proposed_changes, f, indent=4)
            print(f"\nSaved proposed rule changes to {output_path}")

            # TODO: implement evaluation logic calling engine.simulate_forward
            # TODO: Incorporate historical forecast data for evaluation and training

        except FileNotFoundError:
            print(f"Error: Feature file not found at {feature_path}")
        except Exception as e:
            print(f"Error loading or processing feature file: {e}")

        return metrics

    def analyze_and_propose_rule_changes(
        self,
        pulse_forecast: ForecastSchema,
        gpt_forecast: ForecastSchema,
        loss_components: Dict,
    ) -> List[Dict]:
        """
        Analyzes evaluation feedback (loss components) and proposes rule changes.

        Args:
            pulse_forecast (ForecastSchema): The forecast generated by Pulse.
            gpt_forecast (ForecastSchema): The forecast generated by GPT (ground truth).
            loss_components (Dict): Detailed breakdown of the symbolic convergence loss.

        Returns:
            List[Dict]: A list of proposed rule changes (e.g., add, modify, prune).
        """
        proposed_changes = []

        print("\nAnalyzing feedback and proposing rule changes...")
        # Assuming ForecastSchema has 'actions', 'state', and potentially 'rationale' fields
        # print(f"  Pulse Actions: {pulse_forecast.actions}")
        # print(f"  GPT Actions: {gpt_forecast.actions}")
        # print(f"  Pulse State: {pulse_forecast.state}")
        # print(f"  GPT State: {gpt_forecast.state}")
        # print(f"  Pulse Rationale: {getattr(pulse_forecast, 'rationale', 'N/A')}") # Use getattr for safety
        # print(f"  GPT Rationale: {getattr(gpt_forecast, 'rationale', 'N/A')}") #
        # Use getattr for safety

        # Analyze Action Divergence
        if (
            loss_components.get("action_divergence", 0) > 0
        ):  # Check if there is any action divergence
            print("  Action divergence detected.")
            # Compare actions directly
            pulse_actions = set(
                getattr(pulse_forecast, "actions", [])
            )  # Use getattr with default empty list
            gpt_actions = set(
                getattr(gpt_forecast, "actions", [])
            )  # Use getattr with default empty list

            missing_in_pulse = list(gpt_actions - pulse_actions)
            extra_in_pulse = list(pulse_actions - gpt_actions)

            if missing_in_pulse:
                proposed_changes.append(
                    {
                        "type": "add_rule",
                        "reason": "GPT forecast includes actions missing in Pulse forecast.",
                        "details": f"Missing actions: {missing_in_pulse}. Consider adding rules that lead to these actions.",
                        # Suggest basis for new rule
                        "suggested_rule_basis": f"Analyze GPT rationale and state leading to actions: {missing_in_pulse}",
                    }
                )
            if extra_in_pulse:
                proposed_changes.append(
                    {
                        "type": "prune_rule",
                        "reason": "Pulse forecast includes actions not present in GPT forecast.",
                        "details": f"Extra actions: {extra_in_pulse}. Consider pruning or modifying rules that lead to these actions.",
                        # Suggest basis for pruning/modification
                        "suggested_rule_basis": f"Analyze Pulse rules leading to actions: {extra_in_pulse}",
                    }
                )

        # Analyze State Divergence
        # A simple state comparison; a real implementation would need deeper state
        # structure analysis
        if (
            loss_components.get("state_divergence", 0) > 0
        ):  # Check if there is any state divergence
            print("  State divergence detected.")
            # Simple comparison of state dictionaries
            pulse_state = getattr(
                pulse_forecast, "state", {}
            )  # Use getattr with default empty dict
            gpt_state = getattr(
                gpt_forecast, "state", {}
            )  # Use getattr with default empty dict

            if pulse_state != gpt_state:
                proposed_changes.append(
                    {
                        "type": "modify_rule",  # Or add/prune depending on analysis
                        "reason": "Pulse and GPT forecasts resulted in different states.",
                        "details": f"Pulse state: {pulse_state}, GPT state: {gpt_state}. Analyze rules affecting these state differences.",
                        "suggested_rule_basis": "Analyze rules active during state transition.",
                    }
                )

        # Analyze Rationale Divergence (Assuming rationale exists)
        pulse_rationale = getattr(pulse_forecast, "rationale", None)
        gpt_rationale = getattr(gpt_forecast, "rationale", None)
        if (
            pulse_rationale is not None
            and gpt_rationale is not None
            and pulse_rationale != gpt_rationale
        ):
            print("  Rationale divergence detected.")
            proposed_changes.append(
                {
                    "type": "add_rule",  # Or modify
                    "reason": "Pulse and GPT rationales differ.",
                    "details": f"Pulse rationale: {pulse_rationale}, GPT rationale: {gpt_rationale}. Consider generating a rule based on GPT rationale.",
                    "suggested_rule_basis": f"GPT Rationale: {gpt_rationale}",
                }
            )

        # Simple Pruning Strategy based on high total loss
        if sum(loss_components.values()) > 0.5:  # Example threshold for high divergence
            print(
                "  Very high total divergence. Proposing review/pruning of related rules."
            )
            proposed_changes.append(
                {
                    "type": "prune_or_review_rules",
                    "reason": "Very high total divergence in this episode.",
                    "details": "Identify rules active in this episode for potential pruning or modification.",
                    "suggested_rule_basis": "Analyze rules active in this forecast episode.",
                })

        # TODO: Implement more sophisticated rule generation/pruning logic
        # This might involve:
        # - Using GPT rationale (if available) to suggest new rules.
        # - Tracing which rules were active during this forecast episode.
        # - Using historical performance data of rules.

        return proposed_changes
