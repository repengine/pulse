"""
Script to discover and create a comprehensive list of variables available
through existing ingestion vectors (plugins in the iris/ directory).

This script:
1. Explores the iris/iris_plugins_variable_ingestion/ directory
2. Identifies all available plugins
3. Queries each plugin to determine what variables it can provide
4. Compiles all discovered variables into a list
5. Creates a markdown file with the comprehensive list
"""

import os
import sys
import importlib
import inspect
import logging
from pathlib import Path
import json
import re

# Add project root to path to enable imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Constants
IRIS_PLUGINS_DIR = "iris/iris_plugins_variable_ingestion"
OUTPUT_FILE = "data/historical_timeline/available_variables.md"


def get_plugins_list():
    """
    Get a list of all available plugins in the iris_plugins_variable_ingestion directory.

    Returns:
        List of plugin filenames (without extension)
    """
    plugins_dir = Path(IRIS_PLUGINS_DIR)
    if not plugins_dir.exists():
        logger.error(f"Plugins directory not found: {IRIS_PLUGINS_DIR}")
        return []

    # Get all Python files in the directory, excluding __init__.py
    plugin_files = [f.stem for f in plugins_dir.glob("*.py") if f.name != "__init__.py"]

    logger.info(f"Found {len(plugin_files)} potential plugins")
    return plugin_files


def get_variable_catalog():
    """
    Load the variable catalog to get known variables.

    Returns:
        Dictionary containing variable catalog data, or empty dict if not found
    """
    catalog_path = Path("data/historical_timeline/variable_catalog.json")
    if not catalog_path.exists():
        logger.warning("Variable catalog not found")
        return {}

    try:
        with open(catalog_path, "r") as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Error loading variable catalog: {e}")
        return {}


def discover_plugin_variables(plugin_name):
    """
    Discover variables provided by a specific plugin.

    This function attempts several methods to identify variables:
    1. Look for explicitly defined dictionaries/lists of variables
    2. Inspect the plugin code for patterns indicating variable names
    3. Try to instantiate the plugin and call its methods to get variables

    Args:
        plugin_name: Name of the plugin file (without extension)

    Returns:
        List of variable names provided by the plugin
    """
    variables = []
    module_path = f"iris.iris_plugins_variable_ingestion.{plugin_name}"

    try:
        # Attempt to import the plugin module
        plugin_module = importlib.import_module(module_path)
        logger.info(f"Successfully imported {plugin_name}")

        # Method 1: Look for explicitly defined dictionaries of variables
        # Common variable dictionary patterns in the code
        potential_var_dicts = [
            "STOCK_SYMBOLS",
            "CRYPTO_SYMBOLS",
            "FOREX_SYMBOLS",
            "ECONOMIC_INDICATORS",
            "VARIABLES",
            "EXTERNAL_DATA_MAP",
        ]

        for dict_name in potential_var_dicts:
            if hasattr(plugin_module, dict_name):
                var_dict = getattr(plugin_module, dict_name)
                if isinstance(var_dict, dict):
                    logger.info(
                        f"Found variable dictionary {dict_name} in {plugin_name}"
                    )
                    variables.extend(var_dict.keys())

        # Method 2: Check for plugin classes
        for name, obj in inspect.getmembers(plugin_module):
            # Look for plugin classes (usually end with 'Plugin')
            if inspect.isclass(obj) and name.endswith("Plugin"):
                logger.info(f"Found plugin class: {name}")

                # Check for class attributes that might contain variables
                for attr_name in dir(obj):
                    if attr_name.upper() == attr_name and not attr_name.startswith("_"):
                        attr_value = getattr(obj, attr_name)
                        if isinstance(attr_value, dict):
                            variables.extend(attr_value.keys())

                # Try to instantiate the plugin and call methods to get variables
                try:
                    instance = obj()
                    if hasattr(instance, "fetch_signals"):
                        # Don't actually call fetch_signals as it might make API calls
                        # Just note that this plugin can provide variables
                        logger.info(f"{name} has fetch_signals method")

                    # Check for specific get_available_variables method that might exist
                    if hasattr(instance, "get_available_variables"):
                        try:
                            avail_vars = instance.get_available_variables()
                            if isinstance(avail_vars, list):
                                variables.extend(avail_vars)
                        except Exception as e:
                            logger.warning(f"Error getting available variables from {name}: {e}")
                except Exception as e:
                    logger.warning(f"Could not instantiate {name}: {e}")

        # Method 3: Analyze the plugin source code directly
        plugin_path = Path(IRIS_PLUGINS_DIR) / f"{plugin_name}.py"
        if plugin_path.exists():
            with open(plugin_path, "r") as f:
                source_code = f.read()

                # Look for variable name patterns in the code
                # This is a heuristic approach and may need refinement
                var_patterns = [
                    # Matches variable assignments like var_name = ...
                    r'["\']([\w_]+)["\']:\s*{',  # Dictionary key definitions
                    r'["\']([\w_]+)["\'].*source',  # Strings that might be variable names near "source"
                    r'variable_name["\']\s*:\s*["\']([^"\']+)["\']',  # variable_name: "name" pattern
                    r'["\']([\w_]+_price|[\w_]+_rate|[\w_]+_index|[\w_]+_level)["\']',  # Common variable name patterns
                ]

                for pattern in var_patterns:
                    matches = re.findall(pattern, source_code)
                    for match in matches:
                        if isinstance(match, tuple):
                            variables.extend(match)
                        else:
                            variables.append(match)

    except ImportError:
        logger.warning(f"Could not import {module_path}")
    except Exception as e:
        logger.warning(f"Error processing {plugin_name}: {e}")

    # Remove duplicates and return
    return list(set(variables))


def discover_all_plugins_variables():
    """
    Discover variables from all available plugins.

    Returns:
        Dictionary mapping plugin names to lists of their variables
    """
    plugins = get_plugins_list()
    variables_by_plugin = {}

    # Also get variables from the catalog for reference
    catalog = get_variable_catalog()
    catalog_vars = set()
    if catalog and "variables" in catalog:
        catalog_vars = {var["variable_name"] for var in catalog["variables"]}
        logger.info(f"Found {len(catalog_vars)} variables in the catalog")

    # Process each plugin
    for plugin in plugins:
        logger.info(f"Processing plugin: {plugin}")
        variables = discover_plugin_variables(plugin)

        # Also check catalog for variables from this plugin
        if catalog and "variables" in catalog:
            catalog_plugin_vars = [
                var["variable_name"]
                for var in catalog["variables"]
                if var.get("source") == plugin
            ]
            # Add catalog variables to the discovered ones
            variables.extend(catalog_plugin_vars)

        # Deduplicate
        variables = list(set(variables))

        if variables:
            logger.info(f"Discovered {len(variables)} variables from {plugin}")
            variables_by_plugin[plugin] = variables
        else:
            logger.warning(f"No variables discovered from {plugin}")

    return variables_by_plugin


def create_markdown_file(variables_by_plugin):
    """
    Create a markdown file with the discovered variables.

    Args:
        variables_by_plugin: Dictionary mapping plugin names to lists of their variables
    """
    output_path = Path(OUTPUT_FILE)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Generate markdown content
    content = "# Available Variables in Pulse Ingestion System\n\n"
    content += (
        f"*Generated on: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*\n\n"
    )
    content += "This document lists all variables that can be accessed through the Pulse ingestion plugins.\n\n"

    # Add summary table
    content += "## Summary\n\n"
    content += "| Plugin | Variable Count |\n"
    content += "|--------|---------------|\n"

    total_vars = 0
    for plugin, variables in variables_by_plugin.items():
        var_count = len(variables)
        total_vars += var_count
        content += f"| {plugin} | {var_count} |\n"

    content += f"| **Total** | **{total_vars}** |\n\n"

    # Add detailed variable listings by plugin
    content += "## Variables by Plugin\n\n"

    for plugin, variables in sorted(variables_by_plugin.items()):
        content += f"### {plugin}\n\n"
        if variables:
            content += "| Variable Name |\n"
            content += "|---------------|\n"
            for var in sorted(variables):
                content += f"| {var} |\n"
        else:
            content += "*No variables discovered*\n"
        content += "\n"

    # Write the content to the file
    with open(output_path, "w") as f:
        f.write(content)

    logger.info(f"Created markdown file with {total_vars} variables at {output_path}")
    return output_path


def main():
    """Main function to discover and list available variables"""
    logger.info("Starting discovery of available variables")

    # Discover variables from all plugins
    variables_by_plugin = discover_all_plugins_variables()

    # Create markdown file
    output_path = create_markdown_file(variables_by_plugin)

    logger.info(f"Variable discovery complete. Results saved to {output_path}")
    return 0


if __name__ == "__main__":
    # Add missing import
    import datetime

    sys.exit(main())
