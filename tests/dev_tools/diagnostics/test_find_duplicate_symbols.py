import ast
import json
import logging
import subprocess
import sys
from pathlib import Path
from typing import List, Dict, Any, Callable, Tuple
from unittest.mock import patch, MagicMock

import pytest
from _pytest.logging import LogCaptureFixture

# Add the script's directory to sys.path to allow direct import
# This assumes the test is run from the project root or a similar context
# where 'dev_tools' is a sibling or findable.
SCRIPT_DIR = (
    Path(__file__).resolve().parent.parent.parent.parent / "dev_tools" / "diagnostics"
)
sys.path.insert(0, str(SCRIPT_DIR))

try:
    from find_duplicate_symbols import (  # type: ignore[import-not-found]
        is_excluded,
        find_python_files,
        extract_symbol_name_from_target,
        extract_top_level_symbols_from_ast,
        argparse_setup,
        main as find_duplicates_main,
    )
except ImportError as e:
    pytest.fail(
        f"Failed to import find_duplicate_symbols: {e}. "
        f"Check SCRIPT_DIR: {SCRIPT_DIR} and sys.path: {sys.path}"
    )

# Restore sys.path to avoid side effects
sys.path.pop(0)


# --- Fixtures ---


@pytest.fixture
def project_root(tmp_path: Path) -> Path:
    """Creates a temporary project root directory."""
    return tmp_path


@pytest.fixture
def mock_project_structure(project_root: Path) -> Path:
    """Creates a mock project structure for testing."""
    # Top-level files
    (project_root / "module1.py").write_text(
        "def func_a(): pass\nclass ClassA: pass\nVAR_A = 1"
    )
    (project_root / "module2.py").write_text(
        "def func_b(): pass\nfrom module1 import ClassA as RenamedA\n"
        "VAR_A = 2  # Duplicate"
    )
    (project_root / "module_with_syntax_error.py").write_text(
        "def func_c() pass"  # Syntax error
    )
    (project_root / "empty_module.py").write_text("# This is an empty module")
    (project_root / "module_with_unpack.py").write_text("x, y = 1, 2\n(z): int = 3")

    # Subdirectory 'pkg1'
    pkg1_dir = project_root / "pkg1"
    pkg1_dir.mkdir()
    (pkg1_dir / "sub_module1.py").write_text(
        "def func_a(): pass  # Duplicate\nclass SubClassA: pass"
    )
    (pkg1_dir / "__init__.py").write_text("# pkg1 init")

    # Subdirectory 'tests' (should be excluded by default)
    tests_dir = project_root / "tests"
    tests_dir.mkdir()
    (tests_dir / "test_module.py").write_text(
        "def func_a(): pass  # Should be excluded"
    )

    # Subdirectory '.venv' (should be excluded by default)
    venv_dir = project_root / ".venv"
    venv_dir.mkdir()
    (venv_dir / "lib" / "site-packages").mkdir(parents=True, exist_ok=True)
    (venv_dir / "lib" / "site-packages" / "some_lib.py").write_text(
        "class LibClass: pass"
    )

    # File to be excluded by name
    (project_root / "setup.py").write_text("SETUP_VAR = 0")
    (project_root / "pkg1" / "generated_code_pb2.py").write_text(
        "class Generated: pass"
    )

    return project_root


# --- Unit Tests ---


# 1. Test is_excluded
@pytest.mark.parametrize(
    "path_str, exclude_dirs, exclude_files, expected",
    [
        ("src/module.py", ["tests"], [], False),
        ("tests/module.py", ["tests"], [], True),
        ("src/tests_related/module.py", ["tests*"], [], True),
        ("src/module.py", [], ["*_test.py"], False),
        ("src/module_test.py", [], ["*_test.py"], True),
        ("src/module.py", ["build*"], ["conf.py"], False),
        ("build_output/module.py", ["build*"], ["conf.py"], True),
        ("docs/conf.py", ["build*"], ["conf.py"], True),
        (".venv/lib/module.py", [".venv"], [], True),
        ("project/sub/file.py", ["sub"], [], True),
        # 'sub' should match whole dir name
        ("project/sub_dir/file.py", ["sub"], [], False),
        ("project/sub/file.py", ["sub*"], [], True),
    ],
)
def test_is_excluded(
    project_root: Path,
    path_str: str,
    exclude_dirs: List[str],
    exclude_files: List[str],
    expected: bool,
) -> None:
    test_path = project_root / Path(path_str)
    test_path.parent.mkdir(parents=True, exist_ok=True)  # Ensure parent dirs
    if not test_path.exists():
        test_path.touch()

    # Ensure project_root itself exists for relative_to calculations
    if not project_root.exists():
        project_root.mkdir(parents=True, exist_ok=True)

    assert is_excluded(test_path, project_root, exclude_dirs, exclude_files) == expected


def test_is_excluded_non_relative_path(
    project_root: Path, caplog: LogCaptureFixture
) -> None:
    """Test is_excluded when path is not under project_root."""
    non_relative_path = Path("/elsewhere/some_file.py")
    if sys.platform == "win32":  # pragma: no cover
        non_relative_path = Path("D:/elsewhere/some_file.py")

    non_relative_path.parent.mkdir(parents=True, exist_ok=True)
    non_relative_path.touch(exist_ok=True)

    with caplog.at_level(logging.WARNING):
        assert not is_excluded(non_relative_path, project_root, [], [])

    if non_relative_path.exists():  # pragma: no cover
        if non_relative_path.is_file():
            non_relative_path.unlink()
        if non_relative_path.parent.exists() and not any(
            non_relative_path.parent.iterdir()
        ):
            non_relative_path.parent.rmdir()


# 2. Test extract_symbol_name_from_target
@pytest.mark.parametrize(
    "code_snippet, expected_names",
    [
        ("x = 1", ["x"]),
        ("x, y = 1, 2", ["x", "y"]),
        ("(x, y) = 1, 2", ["x", "y"]),
        ("[x, y] = 1, 2", ["x", "y"]),
        ("x.attr = 1", []),
        ("x[0] = 1", []),
        ("((a,b), c) = ( (1,2), 3)", ["a", "b", "c"]),
    ],
)
def test_extract_symbol_name_from_target(
    code_snippet: str, expected_names: List[str]
) -> None:
    tree = ast.parse(code_snippet)
    assert isinstance(tree.body[0], ast.Assign)
    assign_node: ast.Assign = tree.body[0]
    target_node = assign_node.targets[0]
    assert extract_symbol_name_from_target(target_node) == expected_names


# 3. Test extract_top_level_symbols_from_ast
@pytest.mark.parametrize(
    "code_snippet, file_path_str, expected_symbols",
    [
        ("def func(): pass", "mod.py", {"func": "mod.py"}),
        ("async def async_func(): pass", "mod.py", {"async_func": "mod.py"}),
        ("class MyClass: pass", "mod.py", {"MyClass": "mod.py"}),
        ("VAR = 1", "mod.py", {"VAR": "mod.py"}),
        ("X, Y = 1, 2", "mod.py", {"X": "mod.py", "Y": "mod.py"}),
        ("Z: int = 3", "mod.py", {"Z": "mod.py"}),
        ("from os import path as p", "mod.py", {"p": "mod.py"}),
        ("from os import path", "mod.py", {}),  # Non-aliased import
        ("import os", "mod.py", {}),  # Simple import
        (
            """
def top_func():
    def nested_func(): pass
    val = 1
class TopClass:
    class NestedClass: pass
    method_var = 2
CONSTANT = 100
from sys import argv as my_args
""",
            "complex.py",
            {
                "top_func": "complex.py",
                "TopClass": "complex.py",
                "CONSTANT": "complex.py",
                "my_args": "complex.py",
            },
        ),
        ("MY_VAR = 1", "path\\to\\file.py", {"MY_VAR": "path/to/file.py"}),
    ],
)
def test_extract_top_level_symbols_from_ast(
    code_snippet: str, file_path_str: str, expected_symbols: Dict[str, str]
) -> None:
    tree = ast.parse(code_snippet)
    file_path = Path(file_path_str)
    assert extract_top_level_symbols_from_ast(tree, file_path) == expected_symbols


# --- Integration Tests ---


# 4. Test find_python_files
def test_find_python_files(mock_project_structure: Path) -> None:
    project_root = mock_project_structure
    exclude_dirs = [".venv", "tests", "build*", "dist*"]  # Default-like
    exclude_files = ["setup.py", "*_pb2.py", "__init__.py"]  # Default-like

    found_files = find_python_files(project_root, exclude_dirs, exclude_files)

    found_file_names = sorted(
        [str(p.relative_to(project_root)).replace("\\", "/") for p in found_files]
    )

    expected_files = sorted(
        [
            "module1.py",
            "module2.py",
            "module_with_syntax_error.py",
            "empty_module.py",
            "module_with_unpack.py",
            "pkg1/sub_module1.py",
        ]
    )
    assert found_file_names == expected_files


def test_find_python_files_custom_exclusions(mock_project_structure: Path) -> None:
    project_root = mock_project_structure
    exclude_dirs = ["pkg1"]
    exclude_files = ["module1.py", "__init__.py"]

    found_files = find_python_files(project_root, exclude_dirs, exclude_files)
    found_file_names = sorted(
        [str(p.relative_to(project_root)).replace("\\", "/") for p in found_files]
    )

    expected_files_corrected = sorted(
        [
            "module2.py",
            "module_with_syntax_error.py",
            "empty_module.py",
            "module_with_unpack.py",
            "tests/test_module.py",
            ".venv/lib/site-packages/some_lib.py",
            "setup.py",
        ]
    )
    assert found_file_names == expected_files_corrected


# --- End-to-End Tests ---
RunScriptE2EReturn = Tuple[subprocess.CompletedProcess[str], Dict[str, Any], Path]
RunScriptE2ECallable = Callable[[Path, List[str]], RunScriptE2EReturn]


@pytest.fixture
def run_script_e2e(tmp_path: Path) -> RunScriptE2ECallable:
    """Helper function to run the script as a subprocess for E2E tests."""

    def _run(project_dir: Path, args: List[str]) -> RunScriptE2EReturn:
        script_path = SCRIPT_DIR / "find_duplicate_symbols.py"
        cmd = [
            sys.executable,
            str(script_path),
            "--project-root",
            str(project_dir),
        ] + args

        output_file_path = tmp_path / "e2e_report.json"
        if "--output-file" not in " ".join(args):
            cmd.extend(["--output-file", str(output_file_path)])
        else:
            for i, arg_val in enumerate(args):
                if arg_val == "--output-file" and i + 1 < len(args):
                    specified_output_name = args[i + 1]
                    output_file_path = tmp_path / specified_output_name
                    cmd[cmd.index(specified_output_name)] = str(output_file_path)
                    break

        process = subprocess.run(cmd, capture_output=True, text=True, cwd=project_dir)

        report_content: Dict[str, Any] = {}
        if output_file_path.exists():
            try:
                with open(output_file_path, "r", encoding="utf-8") as f:
                    report_content = json.load(f)
            except json.JSONDecodeError:  # pragma: no cover
                print(f"Warning: Could not decode JSON from {output_file_path}")
                pass

        return process, report_content, output_file_path

    return _run


def test_e2e_basic_duplicates(
    mock_project_structure: Path,
    run_script_e2e: RunScriptE2ECallable,
    caplog: LogCaptureFixture,
) -> None:
    """Test basic duplicate detection with default exclusions."""
    project_dir = mock_project_structure
    process, report, _ = run_script_e2e(project_dir, ["--log-level", "DEBUG"])

    assert process.returncode == 0

    normalized_report: Dict[str, List[str]] = {}
    for symbol, paths in report.items():
        normalized_report[symbol] = sorted([p.replace("\\", "/") for p in paths])

    expected_duplicates = {
        "func_a": sorted(["module1.py", "pkg1/sub_module1.py"]),
        "VAR_A": sorted(["module1.py", "module2.py"]),
    }
    assert normalized_report == expected_duplicates

    assert (
        "Could not parse module_with_syntax_error.py" in process.stdout
        or "Could not parse module_with_syntax_error.py" in process.stderr
    )


def test_e2e_no_duplicates(
    project_root: Path, run_script_e2e: RunScriptE2ECallable
) -> None:
    """Test a project with no duplicates."""
    (project_root / "file1.py").write_text("def unique_func(): pass\nVAR_X = 1")
    (project_root / "file2.py").write_text("class UniqueClass: pass\nVAR_Y = 2")

    process, report, _ = run_script_e2e(project_root, [])
    assert process.returncode == 0
    assert report == {}
    assert (
        "No duplicate symbols found" in process.stdout
        or "No duplicate symbols found" in process.stderr
    )


def test_e2e_custom_output_file(
    mock_project_structure: Path, run_script_e2e: RunScriptE2ECallable, tmp_path: Path
) -> None:
    """Test using a custom output file name."""
    custom_output_name = "my_custom_report.json"
    process, report, output_file = run_script_e2e(
        mock_project_structure, ["--output-file", custom_output_name]
    )
    assert process.returncode == 0
    assert output_file.name == custom_output_name
    assert output_file.exists()
    assert len(report) > 0


def test_e2e_custom_exclusions(
    mock_project_structure: Path, run_script_e2e: RunScriptE2ECallable
) -> None:
    """Test with custom exclusion rules that change the outcome."""
    args = [
        "--exclude-dirs",
        "pkg1",
        ".venv",
        "tests",
        "--exclude-files",
        "module2.py",
        "setup.py",
        "*_pb2.py",
        "__init__.py",
    ]
    process, report, _ = run_script_e2e(mock_project_structure, args)

    assert process.returncode == 0
    assert report == {}
    assert (
        "No duplicate symbols found" in process.stdout
        or "No duplicate symbols found" in process.stderr
    )


def test_e2e_logging_level(
    mock_project_structure: Path, run_script_e2e: RunScriptE2ECallable
) -> None:
    """Test different logging levels."""
    process_debug, _, _ = run_script_e2e(
        mock_project_structure, ["--log-level", "DEBUG"]
    )
    assert process_debug.returncode == 0
    debug_output = process_debug.stdout + process_debug.stderr
    assert "Scanning: module1.py" in debug_output

    process_warning, _, _ = run_script_e2e(
        mock_project_structure, ["--log-level", "WARNING"]
    )
    assert process_warning.returncode == 0
    warning_output = process_warning.stdout + process_warning.stderr
    assert "Could not parse module_with_syntax_error.py" in warning_output
    assert "Scanning: module1.py" not in warning_output


def test_argparse_setup_defaults_and_conversion(tmp_path: Path) -> None:
    """Test argparse_setup for default values and type conversions."""
    with patch("sys.argv", ["script_name"]):
        args = argparse_setup()

    assert args.project_root == Path(".").resolve()
    assert args.output_file == Path("dup_symbol_report.json")
    assert isinstance(args.exclude_dirs, list)
    assert isinstance(args.exclude_files, list)
    assert args.log_level == "INFO"

    custom_project_root_str = str(tmp_path / "my_project")
    custom_output_file_str = str(tmp_path / "reports" / "my_report.json")

    (tmp_path / "my_project").mkdir(exist_ok=True)

    with patch(
        "sys.argv",
        [
            "script_name",
            "--project-root",
            custom_project_root_str,
            "--output-file",
            custom_output_file_str,
            "--log-level",
            "DEBUG",
        ],
    ):
        args = argparse_setup()

    assert args.project_root == Path(custom_project_root_str).resolve()
    assert args.output_file == Path(custom_output_file_str)
    assert args.log_level == "DEBUG"
    assert (tmp_path / "reports").exists()


def test_main_function_integration(
    mock_project_structure: Path, tmp_path: Path, caplog: LogCaptureFixture
) -> None:
    """More direct test of the main() function using mocks for argparse."""
    output_report_path = tmp_path / "main_test_report.json"

    mock_args = MagicMock()
    mock_args.project_root = mock_project_structure.resolve()
    mock_args.output_file = output_report_path
    mock_args.exclude_dirs = [
        ".venv",
        "tests",
        "build*",
        "dist*",
        "node_modules",
        "site-packages",
    ]
    mock_args.exclude_files = [
        "setup.py",
        "*_pb2.py",
        "__init__.py",
        "manage.py",
        "conftest.py",
    ]
    mock_args.log_level = "INFO"

    script_module_logger = logging.getLogger("find_duplicate_symbols")
    original_level = script_module_logger.level
    script_module_logger.setLevel(logging.INFO)

    with patch("find_duplicate_symbols.argparse_setup", return_value=mock_args):
        with caplog.at_level(logging.INFO, logger="find_duplicate_symbols"):
            find_duplicates_main()

    assert output_report_path.exists()
    with open(output_report_path, "r", encoding="utf-8") as f:
        report_data = json.load(f)

    normalized_report: Dict[str, List[str]] = {}
    for symbol, paths in report_data.items():
        normalized_report[symbol] = sorted([p.replace("\\", "/") for p in paths])

    expected_duplicates = {
        "func_a": sorted(["module1.py", "pkg1/sub_module1.py"]),
        "VAR_A": sorted(["module1.py", "module2.py"]),
    }
    assert normalized_report == expected_duplicates

    assert (
        "Starting duplicate symbol scan for project: "
        f"{mock_project_structure.resolve()}"
    ) in caplog.text
    assert "Found 2 Python files to scan." not in caplog.text
    assert f"Report generated: {output_report_path.resolve()}" in caplog.text
    assert "Found 2 duplicate symbol(s)." in caplog.text
    assert "Could not parse module_with_syntax_error.py" in caplog.text

    script_module_logger.setLevel(original_level)


def test_empty_project(
    project_root: Path, run_script_e2e: RunScriptE2ECallable
) -> None:
    """Test behavior with an empty project (no .py files)."""
    process, report, _ = run_script_e2e(project_root, [])
    assert process.returncode == 0
    assert report == {}
    combined_output = process.stdout + process.stderr
    assert "Found 0 Python files to scan." in combined_output
    assert "No duplicate symbols found" in combined_output


def test_project_with_only_excluded_files(
    project_root: Path, run_script_e2e: RunScriptE2ECallable
) -> None:
    """Test a project where all .py files are excluded."""
    (project_root / "tests").mkdir()
    (project_root / "tests" / "a_test.py").write_text("def x(): pass")
    (project_root / "__init__.py").write_text("# root init")

    process, report, _ = run_script_e2e(project_root, [])
    assert process.returncode == 0
    assert report == {}
    combined_output = process.stdout + process.stderr
    assert "Found 0 Python files to scan." in combined_output
    assert "No duplicate symbols found" in combined_output
