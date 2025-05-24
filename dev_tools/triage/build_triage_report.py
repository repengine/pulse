#!/usr/bin/env python3
"""
Build Triage Report Script

This script generates a triage report by:
1. Parsing modules and descriptions from docs/pulse_inventory.md
2. Overriding descriptions with first line of docs/<module>.md if available
3. Recursively walking module directories, filtering text files by extension
4. Scanning files for keywords: TODO, FIXME, Hardcoded, NotImplementedError
5. Aggregating issues into a JSON structure
6. Writing the result to triage_report.json

Example:
    $ python dev_tools/triage/build_triage_report.py
"""

import json
import os

# import re  # F401: Unused import
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any


# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


# Constants
KEYWORDS = ["TODO", "FIXME", "Hardcoded", "NotImplementedError"]
TEXT_FILE_EXTENSIONS = {
    ".py",
    ".md",
    ".txt",
    ".yaml",
    ".yml",
    ".json",
    ".html",
    ".css",
    ".js",
}
BINARY_EXTENSIONS = {
    ".pyc",
    ".png",
    ".jpg",
    ".jpeg",
    ".gif",
    ".ico",
    ".pdf",
    ".zip",
    ".gz",
}
MAX_EXCERPT_LENGTH = 160


def parse_inventory_file(inventory_path: Path) -> Dict[str, Dict[str, Any]]:
    """
    Parse the pulse_inventory.md file to extract module paths and descriptions.

    Args:
        inventory_path: Path to the pulse_inventory.md file

    Returns:
        Dictionary mapping module paths to their metadata

    Example:
        >>> modules = parse_inventory_file(Path("docs/pulse_inventory.md"))
        >>> print(list(modules.keys())[0])
        'pulse/config/loader.py'
    """
    modules_data: Dict[str, Dict[str, Any]] = {}

    try:
        with open(inventory_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
    except FileNotFoundError:
        logger.error(f"Inventory file not found at {inventory_path}")
        return modules_data
    except Exception as e:
        logger.error(f"Error reading inventory file: {e}")
        return modules_data

    # Skip header and separator lines
    table_started = False
    for line in lines:
        line = line.strip()
        if not line:
            continue

        if "Module Path/Name" in line and "Description" in line:
            table_started = True
            continue

        if table_started and line.startswith("|---"):  # Separator line
            continue

        if not table_started or not line.startswith("|"):
            continue

        # Split by | and remove empty start/end
        parts = [part.strip() for part in line.split("|")[1:-1]]
        if len(parts) < 2:
            continue

        # Extract module path, removing backticks
        module_path_raw = parts[0].replace("`` `", "").replace("` ``", "")
        module_path_raw = module_path_raw.replace("`", "")
        description = parts[1]

        # Extract companion markdown path if available
        # companion_md_path = None  # F841
        if len(parts) >= 3:
            # link_match = re.search(  # F841
            #     r"\[`Link`\]\((.*?)\)", parts[2]
            # )
            # The companion_md_path logic was removed as it's not used.
            pass  # Keep if block structure if other logic might be added later
        # This assignment should be outside the `if len(parts) >= 3:` block,
        # aligned with the `module_path_raw = ...` and `description = ...`
        # lines.
        modules_data[module_path_raw] = {"description": description, "issues": []}

    return modules_data


def get_module_description_from_md(
    module_path: str, project_root: Path
) -> Optional[str]:
    """
    Extract the first line of the module's markdown file as its description.

    Args:
        module_path: Path to the module
        project_root: Root directory of the project

    Returns:
        First line of the markdown file or None if not found

    Example:
        >>> desc = get_module_description_from_md(
        ...     "pulse/config/loader.py", Path(".")
        ... )
        >>> print(desc)
        'Configuration loader for the Pulse system'
    """
    # Convert module path to expected markdown path
    module_name = os.path.basename(module_path).split(".")[0]
    module_dir = os.path.dirname(module_path).replace("/", "_")
    module_dir = module_dir.replace("\\", "_")

    if module_dir:
        md_filename = f"{module_dir}_{module_name}.md"
    else:
        md_filename = f"{module_name}.md"

    md_path = project_root / "docs" / md_filename

    # Try direct module name if the constructed path doesn't exist
    if not md_path.exists():
        md_path = project_root / "docs" / f"{module_name}.md"

    if md_path.exists():
        try:
            with open(md_path, "r", encoding="utf-8") as f:
                first_line = f.readline().strip()
                if first_line.startswith("#"):
                    # If it's a heading, get content after the # symbols
                    return first_line.lstrip("#").strip()
                return first_line
        except Exception as e:
            logger.warning(f"Error reading markdown file {md_path}: {e}")

    return None


def scan_file_for_issues(file_path: Path) -> List[str]:
    """
    Scan a file for keywords and return a list of issue excerpts found.

    Args:
        file_path: Path to the file to scan

    Returns:
        List of issues found in the file

    Example:
        >>> issues = scan_file_for_issues(Path("example.py"))
        >>> print(issues[0] if issues else "No issues")
        {'keyword': 'TODO', 'line': 10,
         'excerpt': 'TODO: Implement this function'}
    """
    issues: List[str] = []

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
    except UnicodeDecodeError:
        logger.debug(f"Skipping binary or non-UTF8 file: {file_path}")
        return issues
    except Exception as e:
        logger.warning(f"Error reading file {file_path}: {e}")
        return issues

    for i, line in enumerate(lines, 1):
        for keyword in KEYWORDS:
            if keyword in line:
                excerpt = line.strip()
                if len(excerpt) > MAX_EXCERPT_LENGTH:
                    excerpt = excerpt[:MAX_EXCERPT_LENGTH] + "..."

                # Only append the excerpt string to conform to the schema
                issues.append(f"{keyword} (Line {i}): {excerpt}")

    return issues


def is_python_package(path: Path) -> bool:
    """Checks if a given path is a Python package directory."""
    return path.is_dir() and (path / "__init__.py").is_file()


def get_owning_module(
    file_rel_path_str: str,
    inventory_paths_and_types: Dict[str, str],
    project_root: Path,
) -> Optional[str]:
    """
    Determines the most specific module from the inventory that owns this file.

    An inventory module "owns" a file if it's an exact match (for file modules)
    or if it's the longest directory prefix (for package modules) that
    contains the file.
    """
    candidate_owners = []
    normalized_file_rel_path = file_rel_path_str.replace("\\", "/")

    for inv_path_str, inv_type in inventory_paths_and_types.items():
        normalized_inv_path = inv_path_str.replace("\\", "/")
        if inv_type == "file":
            if normalized_file_rel_path == normalized_inv_path:
                candidate_owners.append(inv_path_str)
        elif inv_type == "package":
            dir_inv_path_prefix = (
                normalized_inv_path
                if normalized_inv_path.endswith("/")
                else normalized_inv_path + "/"
            )
            if normalized_file_rel_path.startswith(dir_inv_path_prefix):
                candidate_owners.append(inv_path_str)
    return max(candidate_owners, key=len) if candidate_owners else None


def build_triage_report(project_root: Path) -> Dict[str, Dict[str, Any]]:
    """
    Build the complete triage report.

    Args:
        project_root: Root directory of the project

    Returns:
        Dictionary containing the triage report
    """
    inventory_path = project_root / "docs" / "pulse_inventory.md"
    modules_data = parse_inventory_file(inventory_path)

    if not modules_data:
        logger.error("No modules found in inventory file")
        return {}

    logger.info(f"Found {len(modules_data)} entries in inventory")

    triage_report_data_init: Dict[str, Dict[str, Any]] = {}
    inventory_paths_and_types: Dict[str, str] = {}

    for module_path_str, data in modules_data.items():
        description = data.get("description", "N/A")
        md_description = get_module_description_from_md(module_path_str, project_root)
        if md_description:
            description = md_description

        triage_report_data_init[module_path_str] = {
            "description": description,
            "issues": [],
        }

        full_inv_path = project_root / module_path_str
        if full_inv_path.is_file() and module_path_str.endswith(".py"):
            inventory_paths_and_types[module_path_str] = "file"
        elif is_python_package(full_inv_path):
            inventory_paths_and_types[module_path_str] = "package"

    # Scan all .py files and attribute issues to their owning module
    # Consider walking only known source directories if performance is an issue
    source_dirs_to_scan = ["."]  # Scan from project root
    all_py_files_in_project: List[Path] = []
    for start_dir_str in source_dirs_to_scan:
        start_path = project_root / start_dir_str
        for py_file_path_obj in start_path.rglob("*.py"):
            # Basic ignore for common virtual environment and SCM folders
            if any(
                part in py_file_path_obj.parts
                for part in [
                    ".git",
                    ".venv",
                    "node_modules",
                    "__pycache__",
                    "env",
                    "venv",
                ]
            ):
                continue
            all_py_files_in_project.append(py_file_path_obj)

    for py_file_abs_path in all_py_files_in_project:
        py_file_rel_path_str = str(py_file_abs_path.relative_to(project_root)).replace(
            "\\", "/"
        )

        owner_module_key = get_owning_module(
            py_file_rel_path_str, inventory_paths_and_types, project_root
        )

        if owner_module_key:
            file_issues = scan_file_for_issues(py_file_abs_path)
            if file_issues:
                if owner_module_key in triage_report_data_init:
                    formatted_issues = [
                        f"{issue_str} (File: {py_file_rel_path_str})"
                        for issue_str in file_issues
                    ]
                    triage_report_data_init[owner_module_key]["issues"].extend(
                        formatted_issues
                    )
                else:
                    # This case should ideally not happen if
                    # inventory_paths_and_types is derived correctly
                    logger.warning(
                        f"Owner module key '{owner_module_key}' for file "
                        f"'{py_file_rel_path_str}' not in report. "
                        f"Issues not added."
                    )
        else:
            logger.debug(
                f"File {py_file_rel_path_str} not attributed to any "
                f"module in inventory."
            )

    # Filter the final report to include only modules that were classified as
    # "file" or "package". This ensures that inventory entries like ".md"
    # files (if any) that are not actual code modules are excluded from
    # having issues.
    final_report: Dict[str, Dict[str, Any]] = {}
    # Iterate only over keys that are valid code modules
    for inv_key in inventory_paths_and_types:
        if inv_key in triage_report_data_init:
            final_report[inv_key] = triage_report_data_init[inv_key]

    return final_report


def main() -> None:
    """
    Main function to build and save the triage report.

    Example:
        >>> main()
        INFO - Found 150 modules in inventory
        INFO - Triage report saved to triage_report.json
    """
    # Determine the project root directory
    script_dir = Path(__file__).resolve().parent
    project_root = script_dir.parent.parent

    logger.info(f"Building triage report from {project_root}")

    # Build the triage report
    triage_report = build_triage_report(project_root)

    # Save the report to a JSON file
    output_path = project_root / "triage_report.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(triage_report, f, indent=2)

    logger.info(f"Triage report saved to {output_path}")


if __name__ == "__main__":
    main()
