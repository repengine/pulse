"""
Auto-generates Pulse module files, test stubs, and doc entries.
Edit MODULES_TO_GENERATE to match your roadmap.

- Add new module ranges to MODULES_TO_GENERATE as your roadmap expands.
- All generated files are UTF-8 encoded.
- Use dry-run mode for previewing changes (not yet implemented).
"""
import os
import ast
import json
import logging
import sys
from typing import List, Dict, Tuple, Any
from hook_utils import scan_for_hooks
from operator_interface.pulse_prompt_logger import log_prompt

logging.basicConfig(level=logging.INFO)

SEARCH_PATHS = ["dev_tools", "simulation_engine/forecasting"]
HOOKS_JSON = "dev_tools/pulse_hooks_config.json"

MODULES_TO_GENERATE: List[Tuple[int, int, str]] = [
    (0, 9, "simulation_engine"),
    (10, 19, "forecast_engine"),
    (20, 29, "signal_ingestion"),
    (30, 39, "symbolic_system"),
    (40, 49, "diagnostics"),
    (50, 59, "strategic_interface"),
    (60, 69, "memory"),
    (70, 79, "planning"),
    (80, 89, "future_tools"),
    (90, 99, "simulation_engine"),
    (100, 109, "forecast_engine"),
    # Extend as needed...
]

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
UTILS_IMPORT = "from utils.log_utils import get_logger\nfrom utils.error_utils import PulseError\nfrom utils.performance_utils import profile\n"

MODULE_TEMPLATE = '''"""
Module {module_num:04d}: [Short description of module purpose]
"""

{utils_import}
from core.pulse_config import MODULES_ENABLED
from core.module_registry import MODULE_REGISTRY

logger = get_logger(__name__)

class Module{module_num:04d}Error(PulseError):
    """Custom exception for Module {module_num:04d}."""

@profile
def main_function(input_data: list[int]) -> int:
    """
    [Describe what this function does.]

    Args:
        input_data (list[int]): [Description]

    Returns:
        int: [Description]

    Raises:
        Module{module_num:04d}Error: [When/why this is raised]
    """
    # Gating logic using module registry and config
    module_key = __name__.split('.')[-1]
    if not MODULE_REGISTRY.get(module_key, {}).get("enabled", MODULES_ENABLED.get(module_key, True)):
        logger.warning(f"{{module_key}} is disabled in module registry.")
        raise Module{module_num:04d}Error(f"{{module_key}} is disabled in module registry.")
    logger.info("Starting main_function in Module {module_num:04d}")
    if not isinstance(input_data, list):
        logger.error("Input data must be a list of integers.")
        raise Module{module_num:04d}Error("Input data must be a list of integers.")
    # ...module logic here...
    result = len(input_data)
    logger.info(f"main_function result: {{result}}")
    return result
'''

TEST_TEMPLATE = '''import pytest
from {subpackage}.module_{module_num:04d} import main_function, Module{module_num:04d}Error

def test_main_function_valid():
    assert main_function([1, 2, 3]) == 3

def test_main_function_invalid():
    with pytest.raises(Module{module_num:04d}Error):
        main_function("not a list")
'''

DOC_ENTRY_TEMPLATE = '''
.. automodule:: {subpackage}.module_{module_num:04d}
    :members:
    :undoc-members:
    :show-inheritance:
'''

def ensure_init_py(path: str) -> None:
    """Ensure __init__.py exists in the given path."""
    init_path = os.path.join(path, "__init__.py")
    if not os.path.exists(init_path):
        with open(init_path, "w", encoding="utf-8") as f:
            f.write("")

def write_hook_summary(modules: List[Dict[str, Any]]) -> None:
    """Write hookable modules summary to HOOKS_JSON."""
    with open(HOOKS_JSON, 'w', encoding='utf-8') as f:
        json.dump(modules, f, indent=2)
    logging.info(f"✅ Hook summary written to {HOOKS_JSON}")

def print_shell_templates(modules: List[Dict[str, Any]]) -> None:
    """Print suggested CLI shell modes for discovered hooks."""
    logging.info("\n📎 Suggested CLI shell modes:")
    for mod in modules:
        name = mod["module"].split(".")[-1]
        flag = mod["hook_type"]
        logging.info(f"elif args.mode == '{name}':")
        logging.info(f"    from {mod['module']} import {mod['function']}")
        logging.info(f"    {mod['function']}()\n")

def main() -> None:
    """
    Main entry point for module/test/doc generation and hook scanning.
    Scans for hookable modules, generates module stubs, test stubs, and doc entries.
    """
    # Scan for CLI hookable modules
    hookable_modules, metadata = scan_for_hooks(SEARCH_PATHS)
    logging.info(f"✅ Found {len(hookable_modules)} hookable modules.")
    full_data = {
        "active_hooks": {mod["module"]: True for mod in hookable_modules},
        "metadata": metadata
    }
    os.makedirs(os.path.dirname(HOOKS_JSON), exist_ok=True)
    write_hook_summary(hookable_modules)

    docs_path = os.path.join(BASE_DIR, "docs", "api_reference.rst")
    os.makedirs(os.path.dirname(docs_path), exist_ok=True)
    doc_entries = []

    modules_created = 0
    tests_created = 0

    for start, end, subpackage in MODULES_TO_GENERATE:
        subpkg_path = os.path.join(BASE_DIR, subpackage)
        os.makedirs(subpkg_path, exist_ok=True)
        ensure_init_py(subpkg_path)

        for idx in range(start, end + 1):
            module_fname = f"module_{idx:04d}.py"
            module_path = os.path.join(subpkg_path, module_fname)
            if not os.path.exists(module_path):
                with open(module_path, "w", encoding="utf-8") as f:
                    f.write(MODULE_TEMPLATE.format(
                        module_num=idx,
                        utils_import=UTILS_IMPORT
                    ))
                logging.info(f"Created {module_path}")
                modules_created += 1

            # Test file
            test_fname = f"test_{subpackage}_module_{idx:04d}.py"
            test_path = os.path.join(BASE_DIR, "tests", test_fname)
            if not os.path.exists(test_path):
                with open(test_path, "w", encoding="utf-8") as f:
                    f.write(TEST_TEMPLATE.format(
                        subpackage=subpackage,
                        module_num=idx
                    ))
                logging.info(f"Created {test_path}")
                tests_created += 1

            # Doc entry
            doc_entries.append(DOC_ENTRY_TEMPLATE.format(
                subpackage=subpackage,
                module_num=idx
            ))

    # Append doc entries to api_reference.rst
    with open(docs_path, "a", encoding="utf-8") as f:
        f.writelines(doc_entries)
    logging.info(f"Updated {docs_path}")

    print_shell_templates(hookable_modules)

    # Print summary
    logging.info(f"\nSummary: {modules_created} modules created, {tests_created} tests created, {len(doc_entries)} doc entries appended.")

if __name__ == "__main__":
    main()