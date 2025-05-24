import ast
import argparse
import json
import logging
from pathlib import Path
from collections import defaultdict
import fnmatch
from typing import Dict, List

# Configure basic logging
logging.basicConfig(format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


def is_excluded(
    path: Path, project_root: Path, exclude_dirs: List[str], exclude_files: List[str]
) -> bool:
    """
    Check if a given file path should be excluded from scanning.

    Args:
        path: The path to check.
        project_root: The root directory of the project.
        exclude_dirs: A list of directory name patterns to exclude.
        exclude_files: A list of file name patterns to exclude.

    Returns:
        True if the path should be excluded, False otherwise.
    """
    abs_path = path.resolve()
    project_root_abs = project_root.resolve()

    # Check directory exclusions
    try:
        relative_path = abs_path.relative_to(project_root_abs)
        # Iterate over parent directory names
        for part in relative_path.parent.parts:
            for pattern in exclude_dirs:
                if fnmatch.fnmatch(part, pattern):
                    logger.debug(
                        f"Excluding '{path}' due to directory pattern "
                        f"'{pattern}' matching part '{part}'"
                    )
                    return True
    except ValueError:  # pragma: no cover
        # This can happen if path is not under project_root_abs,
        # though find_python_files should prevent this.
        logger.warning(
            f"Path '{path}' is not relative to project root "
            f"'{project_root_abs}'. Skipping exclusion check for directories."
        )
        pass

    # Check file exclusions
    for pattern in exclude_files:
        if fnmatch.fnmatch(path.name, pattern):
            logger.debug(f"Excluding '{path}' due to file pattern '{pattern}'")
            return True

    return False


def find_python_files(
    project_root: Path, exclude_dirs: List[str], exclude_files: List[str]
) -> List[Path]:
    """
    Recursively find all .py files in the project_root directory,
    respecting exclusions.

    Args:
        project_root: The root directory of the project.
        exclude_dirs: A list of directory name patterns to exclude.
        exclude_files: A list of file name patterns to exclude.

    Returns:
        A list of Path objects for Python files to be scanned.
    """
    python_files: List[Path] = []
    for file_path in project_root.rglob("*.py"):
        if not is_excluded(file_path, project_root, exclude_dirs, exclude_files):
            python_files.append(file_path)
    return python_files


def extract_symbol_name_from_target(target: ast.expr) -> List[str]:
    """
    Extract symbol name(s) from an assignment target.

    Args:
        target: An AST expression node representing the target of an
                assignment.

    Returns:
        A list of extracted symbol names.
    """
    names: List[str] = []
    if isinstance(target, ast.Name):
        names.append(target.id)
    elif isinstance(target, (ast.Tuple, ast.List)):
        for elt in target.elts:
            names.extend(extract_symbol_name_from_target(elt))
    # ast.Attribute, ast.Subscript are not top-level definitions
    # in this context
    return names


def extract_top_level_symbols_from_ast(
    tree: ast.Module, file_path_relative: Path
) -> Dict[str, str]:
    """
    Parse an AST to find top-level symbol definitions within a single file.

    Args:
        tree: The AST of the file.
        file_path_relative: The relative path of the file (as a string).

    Returns:
        A dictionary mapping symbol names defined in this file to their
        relative module path string.
    """
    symbols: Dict[str, str] = {}
    # Normalize path separators
    file_path_str = str(file_path_relative).replace("\\", "/")

    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            symbols[node.name] = file_path_str
        elif isinstance(node, ast.Assign):
            for target_node in node.targets:
                extracted_names = extract_symbol_name_from_target(target_node)
                for name in extracted_names:
                    symbols[name] = file_path_str
        elif isinstance(node, ast.AnnAssign):
            if isinstance(node.target, ast.Name):
                symbols[node.target.id] = file_path_str
        elif isinstance(node, ast.ImportFrom):
            for alias_node in node.names:
                if alias_node.asname:
                    symbols[alias_node.asname] = file_path_str
    return symbols


def argparse_setup() -> argparse.Namespace:
    """
    Set up and parse Command Line Interface (CLI) arguments.

    Returns:
        Parsed arguments namespace.
    """
    parser = argparse.ArgumentParser(
        description="Scan a Python project for duplicate top-level symbol definitions."
    )
    parser.add_argument(
        "--project-root",
        type=str,
        default=".",
        help="Root directory of the project to scan. Paths in the report "
        "will be relative to this root.",
    )
    parser.add_argument(
        "--output-file",
        type=str,
        default="dup_symbol_report.json",
        help="Path to save the JSON report.",
    )
    parser.add_argument(
        "--exclude-dirs",
        type=str,
        nargs="*",
        default=[
            ".venv",
            ".git",
            "__pycache__",
            "tests",
            "test",
            "docs",
            "build*",
            "dist*",
            "node_modules",
            "site-packages",
        ],
        help="Directory names/patterns to exclude. Applied to any part of "
        "the path. E.g., 'tests' or 'build*'.",
    )
    parser.add_argument(
        "--exclude-files",
        type=str,
        nargs="*",
        default=["setup.py", "*_pb2.py", "__init__.py", "manage.py", "conftest.py"],
        help="File names/patterns to exclude. E.g., 'conf.py' or '*_generated.py'.",
    )
    parser.add_argument(
        "--log-level",
        type=str,
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        help="Set the logging level.",
    )

    args = parser.parse_args()

    # Set logger level
    try:
        log_level_int = getattr(logging, args.log_level.upper())
        logger.setLevel(log_level_int)
    except AttributeError:  # pragma: no cover
        logger.setLevel(logging.INFO)
        logger.warning(f"Invalid log level '{args.log_level}'. Defaulting to INFO.")

    args.project_root = Path(args.project_root).resolve()
    args.output_file = Path(args.output_file)

    # Ensure output directory exists
    args.output_file.parent.mkdir(parents=True, exist_ok=True)

    return args


def main() -> None:
    """
    Main execution flow of the script.
    """
    args = argparse_setup()
    logger.info(f"Starting duplicate symbol scan for project: {args.project_root}")
    logger.info(f"Excluding directories matching: {args.exclude_dirs}")
    logger.info(f"Excluding files matching: {args.exclude_files}")

    all_symbols: Dict[str, List[str]] = defaultdict(list)

    python_files_to_scan = find_python_files(
        args.project_root, args.exclude_dirs, args.exclude_files
    )

    logger.info(f"Found {len(python_files_to_scan)} Python files to scan.")

    for file_path in python_files_to_scan:
        file_path_relative = file_path.relative_to(args.project_root)
        logger.debug(f"Scanning: {file_path_relative}")
        try:
            source_code = file_path.read_text(encoding="utf-8")
        except (IOError, UnicodeDecodeError) as e:
            logger.warning(f"Could not read file {file_path_relative}: {e}")
            continue

        try:
            tree = ast.parse(source_code, filename=str(file_path))
        except SyntaxError as e:
            logger.warning(f"Could not parse {file_path_relative}: {e}")
            continue

        current_file_symbols = extract_top_level_symbols_from_ast(
            tree, file_path_relative
        )
        for symbol_name, defining_module_str in current_file_symbols.items():
            all_symbols[symbol_name].append(defining_module_str)

    duplicates = {sym: paths for sym, paths in all_symbols.items() if len(paths) > 1}
    sorted_duplicates = {
        sym: sorted(list(set(paths))) for sym, paths in duplicates.items()
    }

    try:
        with open(args.output_file, "w", encoding="utf-8") as f:
            json.dump(sorted_duplicates, f, indent=2, ensure_ascii=False)
        logger.info(f"Report generated: {args.output_file.resolve()}")
    except IOError as e:  # pragma: no cover
        logger.error(f"Could not write report to {args.output_file.resolve()}: {e}")

    num_duplicates_found = len(sorted_duplicates)
    if num_duplicates_found > 0:
        logger.warning(
            f"Found {num_duplicates_found} duplicate symbol(s). See report for details."
        )
    else:
        logger.info("No duplicate symbols found.")

    logger.info("Scan complete.")


if __name__ == "__main__":  # pragma: no cover
    main()
