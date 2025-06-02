"""
Domain Adapter module that implements the adapter pattern for language models.
Provides a lightweight domain adaptation layer using Low-Rank Adaptation (LoRA) techniques.
"""

import os
import logging
from typing import Optional, List
import json

# Set up logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("DomainAdapter")

# Define constants
PEFT_AVAILABLE = False
TRANSFORMERS_AVAILABLE = False

# Try to import optional dependencies
# Try to import optional dependencies
try:
    from peft import LoraConfig, get_peft_model, PeftModel

    PEFT_AVAILABLE = True
    logger.info("PEFT library successfully loaded. LoRA adaptation is available.")
except ImportError:
    logger.warning("PEFT library not found. LoRA adaptation will be simulated.")
    PEFT_AVAILABLE = False

# TRANSFORMERS_AVAILABLE is set to False by default and remains so if torch/transformers are not imported.
# If they were needed by PEFT, PEFT_AVAILABLE would be False.
# No need to explicitly import torch/transformers if they are not directly used elsewhere.


class DomainAdapter:
    """
    Domain adapter using LoRA (Low-Rank Adaptation) for efficient fine-tuning.

    This class implements the adapter pattern to modify the behavior of language models
    without changing their original implementation, focusing on domain-specific adaptations.
    """

    def __init__(
        self,
        adapter_path: Optional[str] = None,
        r: int = 8,
        lora_alpha: int = 16,
        lora_dropout: float = 0.1,
        target_modules: Optional[List[str]] = None,
    ):
        """
        Initializes the DomainAdapter with LoRA configuration.

        Args:
            adapter_path (str, optional): The path to a pre-trained LoRA adapter. Defaults to None.
            r (int): LoRA attention dimension (rank of the update matrices).
            lora_alpha (int): The alpha parameter for LoRA scaling.
            lora_dropout (float): The dropout probability for LoRA layers.
            target_modules (List[str], optional): List of module names to apply LoRA to.
        """
        self.adapter_path = adapter_path
        self.r = r
        self.lora_alpha = lora_alpha
        self.lora_dropout = lora_dropout
        self.target_modules = target_modules or ["q_proj", "v_proj"]
        self.lora_config = None
        self.metrics = {"training_loss": [], "validation_loss": []}
        self.is_applied = False

        logger.info(
            f"Initialized DomainAdapter with config: r={r}, lora_alpha={lora_alpha}, "
            f"lora_dropout={lora_dropout}, target_modules={self.target_modules}"
        )

        if adapter_path and os.path.exists(adapter_path):
            logger.info(f"Adapter path specified: {adapter_path}")
            self._load_adapter_config()

    def _load_adapter_config(self):
        """Load configuration from an existing adapter if available."""
        if not self.adapter_path or not os.path.exists(self.adapter_path):
            logger.warning(f"Adapter path not found: {self.adapter_path}")
            return False

        try:
            # Try to load adapter-specific configuration
            adapter_config_path = os.path.join(self.adapter_path, "adapter_config.json")
            if os.path.exists(adapter_config_path):
                with open(adapter_config_path, "r") as f:
                    config = json.load(f)

                # Extract LoRA parameters if available
                if "r" in config:
                    self.r = config["r"]
                if "lora_alpha" in config:
                    self.lora_alpha = config["lora_alpha"]
                if "lora_dropout" in config:
                    self.lora_dropout = config["lora_dropout"]
                if "target_modules" in config:
                    self.target_modules = config["target_modules"]

                logger.info(f"Loaded adapter configuration from {adapter_config_path}")
                return True

        except Exception as e:
            logger.error(f"Error loading adapter configuration: {str(e)}")

        return False

    def create_lora_config(self):
        """
        Creates a LoRA configuration object.

        Returns:
            LoraConfig or dict: The LoRA configuration
        """
        if not PEFT_AVAILABLE:
            logger.warning(
                "PEFT library not available. Creating simulated configuration."
            )
            # Create a dictionary simulating the LoRA config
            self.lora_config = {
                "r": self.r,
                "lora_alpha": self.lora_alpha,
                "lora_dropout": self.lora_dropout,
                "target_modules": self.target_modules,
                "bias": "none",
                "task_type": "CAUSAL_LM",
            }
            return self.lora_config

        try:
            logger.info("Creating LoRA configuration...")
            # Create actual LoRA configuration
            self.lora_config = LoraConfig(
                r=self.r,
                lora_alpha=self.lora_alpha,
                lora_dropout=self.lora_dropout,
                target_modules=self.target_modules,
                bias="none",
                task_type="CAUSAL_LM",
            )
            logger.info("LoRA configuration created.")
            return self.lora_config
        except Exception as e:
            logger.error(f"Error creating LoRA configuration: {str(e)}")
            return None

    def apply_to_model(self, model):
        """
        Applies the LoRA adapter to a given language model.

        Args:
            model: The language model to apply the adapter to.

        Returns:
            The model with the applied adapter.
        """
        if self.is_applied:
            logger.warning("Adapter already applied to model.")
            return model

        if not PEFT_AVAILABLE or not TRANSFORMERS_AVAILABLE:
            logger.warning(
                "Required libraries not available. Cannot apply adapter to model."
            )
            return model

        # Create configuration if not already done
        if self.lora_config is None:
            self.create_lora_config()
            if self.lora_config is None:
                logger.error(
                    "Failed to create LoRA configuration. Cannot apply adapter."
                )
                return model

        try:
            logger.info("Applying LoRA adapter to model...")

            # If adapter path is specified and exists, load the pre-trained adapter
            if self.adapter_path and os.path.exists(self.adapter_path):
                try:
                    # Load adapter directly if it's a PeftModel checkpoint
                    adapted_model = PeftModel.from_pretrained(model, self.adapter_path)
                    logger.info(f"Loaded pre-trained adapter from {self.adapter_path}")
                except Exception as e:
                    logger.warning(f"Failed to load adapter directly: {str(e)}")
                    # Apply fresh configuration and warn
                    adapted_model = get_peft_model(model, self.lora_config)
                    logger.warning("Applied fresh LoRA configuration instead.")
            else:
                # Apply fresh configuration
                adapted_model = get_peft_model(model, self.lora_config)
                logger.info("Applied fresh LoRA configuration.")

            self.is_applied = True
            return adapted_model

        except Exception as e:
            logger.error(f"Error applying LoRA adapter: {str(e)}")
            return model

    def save_adapter(self, save_path: str):
        """
        Save the adapter weights and configuration.

        Args:
            save_path (str): Directory to save the adapter

        Returns:
            bool: True if successful, False otherwise
        """
        if not self.is_applied:
            logger.error(
                "Cannot save adapter: No adapter has been applied to a model yet."
            )
            return False

        try:
            os.makedirs(save_path, exist_ok=True)

            # Save adapter configuration
            config_path = os.path.join(save_path, "adapter_config.json")
            with open(config_path, "w") as f:
                if isinstance(self.lora_config, dict):
                    json.dump(self.lora_config, f, indent=2)
                else:
                    # If it's a LoraConfig object, convert to dict first
                    config_dict = {
                        "r": self.r,
                        "lora_alpha": self.lora_alpha,
                        "lora_dropout": self.lora_dropout,
                        "target_modules": self.target_modules,
                        "bias": "none",
                        "task_type": "CAUSAL_LM",
                    }
                    json.dump(config_dict, f, indent=2)

            # Save training metrics if available
            if self.metrics:
                metrics_path = os.path.join(save_path, "training_metrics.json")
                with open(metrics_path, "w") as f:
                    json.dump(self.metrics, f, indent=2)

            logger.info(f"Adapter configuration and metrics saved to {save_path}")
            return True

        except Exception as e:
            logger.error(f"Error saving adapter: {str(e)}")
            return False

    def get_adapter_info(self):
        """
        Get information about the adapter.

        Returns:
            dict: Information about the adapter configuration and status
        """
        return {
            "adapter_path": self.adapter_path,
            "configuration": {
                "r": self.r,
                "lora_alpha": self.lora_alpha,
                "lora_dropout": self.lora_dropout,
                "target_modules": self.target_modules,
            },
            "is_applied": self.is_applied,
            "libraries_available": {
                "peft": PEFT_AVAILABLE,
                "transformers": TRANSFORMERS_AVAILABLE,
            },
        }


# Testing functionality
if __name__ == "__main__":
    # Example Usage
    adapter = DomainAdapter(r=16, lora_alpha=32)
    config = adapter.create_lora_config()
    print(f"LoRA Configuration: {config}")

    # Print adapter info
    adapter_info = adapter.get_adapter_info()
    print(f"Adapter Info: {json.dumps(adapter_info, indent=2)}")

    # Example of saving adapter configuration
    adapter.save_adapter("./test_adapter")
    print("Test complete.")
