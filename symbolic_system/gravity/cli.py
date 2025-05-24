"""
cli.py

Provides CLI integration for the Symbolic Gravity system, allowing
the system to be enabled, disabled, and configured through command-line arguments.

Author: Pulse v3.5
"""

import argparse
import logging
from typing import Dict, Any, Optional

from symbolic_system.gravity.gravity_config import ResidualGravityConfig
from symbolic_system.gravity.integration import (
    initialize_gravity_system,
    enable_gravity_system,
    disable_gravity_system,
    get_gravity_fabric,
    get_pillar_system,
)

logger = logging.getLogger(__name__)


def add_gravity_arguments(parser: argparse.ArgumentParser) -> None:
    """
    Add Symbolic Gravity command-line arguments to an argument parser.

    Parameters
    ----------
    parser : argparse.ArgumentParser
        The argument parser to add arguments to
    """
    gravity_group = parser.add_argument_group("Symbolic Gravity Options")

    gravity_group.add_argument(
        "--enable-gravity",
        action="store_true",
        dest="enable_gravity",
        help="Enable the Symbolic Gravity system for residual corrections",
    )

    gravity_group.add_argument(
        "--disable-gravity",
        action="store_true",
        dest="disable_gravity",
        help="Disable the Symbolic Gravity system",
    )

    gravity_group.add_argument(
        "--gravity-lambda",
        type=float,
        dest="gravity_lambda",
        help="Set the gravity strength coefficient (0-1)",
    )

    gravity_group.add_argument(
        "--gravity-eta",
        type=float,
        dest="gravity_eta",
        help="Set the learning rate for gravity updates",
    )

    gravity_group.add_argument(
        "--gravity-reg",
        type=float,
        dest="gravity_reg",
        help="Set the regularization coefficient for gravity weights",
    )

    gravity_group.add_argument(
        "--gravity-debug",
        action="store_true",
        dest="gravity_debug",
        help="Enable detailed logging for the gravity system",
    )


def handle_gravity_arguments(args: argparse.Namespace) -> Optional[Dict[str, Any]]:
    """
    Handle Symbolic Gravity command-line arguments.

    Parameters
    ----------
    args : argparse.Namespace
        Parsed command-line arguments

    Returns
    -------
    Optional[Dict[str, Any]]
        Dictionary of configuration values if any gravity options were specified
    """
    gravity_options = {}

    # Check for gravity options
    if hasattr(args, "enable_gravity") and args.enable_gravity:
        gravity_options["enabled"] = True

    if hasattr(args, "disable_gravity") and args.disable_gravity:
        gravity_options["enabled"] = False

    if hasattr(args, "gravity_lambda") and args.gravity_lambda is not None:
        gravity_options["lambda_"] = args.gravity_lambda

    if hasattr(args, "gravity_eta") and args.gravity_eta is not None:
        gravity_options["eta"] = args.gravity_eta

    if hasattr(args, "gravity_reg") and args.gravity_reg is not None:
        gravity_options["regularization"] = args.gravity_reg

    if hasattr(args, "gravity_debug") and args.gravity_debug:
        gravity_options["debug_logging"] = True

    # Return None if no gravity options were specified
    if not gravity_options:
        return None

    return gravity_options


def initialize_from_args(args: argparse.Namespace) -> bool:
    """
    Initialize the Symbolic Gravity system from command-line arguments.

    Parameters
    ----------
    args : argparse.Namespace
        Parsed command-line arguments

    Returns
    -------
    bool
        True if the gravity system was initialized, False otherwise
    """
    # Handle gravity arguments
    gravity_options = handle_gravity_arguments(args)

    if gravity_options is None:
        # No gravity options specified
        return False

    # Extract enable/disable option
    enabled = gravity_options.pop("enabled", True)

    # Create config from remaining options
    config = ResidualGravityConfig(**gravity_options)

    # Initialize the gravity system
    initialize_gravity_system(config)

    # Enable or disable based on argument
    if enabled:
        enable_gravity_system()
        logger.info("Symbolic Gravity system enabled via CLI")
    else:
        disable_gravity_system()
        logger.info("Symbolic Gravity system disabled via CLI")

    return True


def print_gravity_status() -> None:
    """Print the current status of the Symbolic Gravity system."""
    fabric = get_gravity_fabric()
    pillar_system = get_pillar_system()

    print("\n--- Symbolic Gravity System Status ---")

    # Get diagnostic report
    report = fabric.generate_diagnostic_report()

    # Print engine stats
    print("\nEngine Statistics:")
    print(f"  RMS Weight: {report['engine_stats']['rms_weight']:.4f}")
    print("  Top Contributors:")
    for name, weight in report["engine_stats"]["top_contributors"]:
        print(f"    {name}: {weight:.4f}")
    print(f"  Fragility: {report['engine_stats']['fragility']:.4f}")

    # Print pillar stats
    print("\nPillar Status:")
    pillar_values = pillar_system.as_dict()
    for name, value in pillar_values.items():
        print(f"  {name}: {value:.4f}")

    print(f"\nSymbolic Tension: {report['pillar_stats']['tension']:.4f}")

    # Print variable improvements if any
    if report["fabric_stats"]["variables"]:
        print("\nVariable Improvements:")
        for var in report["fabric_stats"]["variables"]:
            if var in report["fabric_stats"]["variable_improvements"]:
                impr = report["fabric_stats"]["variable_improvements"][var]
                print(f"  {var}: {impr['percentage_improvement']:.2f}% improvement")
                print(f"    Original MAE: {impr['original_mae']:.4f}")
                print(f"    Corrected MAE: {impr['corrected_mae']:.4f}")

    print("\n------------------------------------\n")
