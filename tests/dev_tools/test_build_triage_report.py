#!/usr/bin/env python3
"""
Tests for the build_triage_report.py script.
"""

# import json # Unused
# import tempfile # Unused
from pathlib import Path
from unittest import mock

import pytest

from dev_tools.triage.build_triage_report import (
    parse_inventory_file,
    get_module_description_from_md,
    scan_file_for_issues,
    build_triage_report,
)


class TestParseInventoryFile:
    """Tests for the parse_inventory_file function."""

    def test_parse_empty_file(self, tmp_path):
        """Test parsing an empty inventory file."""
        # Create an empty inventory file
        inventory_path = tmp_path / "empty_inventory.md"
        inventory_path.write_text("")

        # Parse the empty inventory file
        result = parse_inventory_file(inventory_path)

        # Check that the result is an empty dictionary
        assert result == {}

    def test_parse_valid_inventory(self, tmp_path):
        """Test parsing a valid inventory file."""
        # Create a valid inventory file
        inventory_content = """# Pulse Module Inventory

This inventory lists modules within the Pulse project.

| Module Path/Name | Description | Analysis Report |
|------------------|-------------|-----------------|
| `` `module1.py` `` | Description 1 | [`Link`](docs/module1.md) |
| `` `module2.py` `` | Description 2 | N/A |
"""
        inventory_path = tmp_path / "valid_inventory.md"
        inventory_path.write_text(inventory_content)

        # Parse the valid inventory file
        result = parse_inventory_file(inventory_path)

        # Check that the result contains the expected modules
        assert len(result) == 2
        assert "module1.py" in result
        assert "module2.py" in result
        assert result["module1.py"]["description"] == "Description 1"
        # companion_md_path is no longer in the output
        assert result["module2.py"]["description"] == "Description 2"
        assert result["module2.py"].get("companion_md_path") is None

    def test_parse_nonexistent_file(self):
        """Test parsing a nonexistent inventory file."""
        # Parse a nonexistent inventory file
        result = parse_inventory_file(Path("/nonexistent/file.md"))

        # Check that the result is an empty dictionary
        assert result == {}


class TestGetModuleDescriptionFromMd:
    """Tests for the get_module_description_from_md function."""

    def test_get_description_from_existing_file(self, tmp_path):
        """Test getting a description from an existing markdown file."""
        # Create a markdown file
        md_content = "# Module Description\n\nThis is a test module."
        docs_dir = tmp_path / "docs"
        docs_dir.mkdir()
        md_path = docs_dir / "module1.md"
        md_path.write_text(md_content)

        # Get the description from the markdown file
        result = get_module_description_from_md("module1.py", tmp_path)

        # Check that the result is the expected description
        assert result == "Module Description"

    def test_get_description_from_nonexistent_file(self, tmp_path):
        """Test getting a description from a nonexistent markdown file."""
        # Create the docs directory
        docs_dir = tmp_path / "docs"
        docs_dir.mkdir()

        # Get the description from a nonexistent markdown file
        result = get_module_description_from_md("nonexistent.py", tmp_path)

        # Check that the result is None
        assert result is None


class TestScanFileForIssues:
    """Tests for the scan_file_for_issues function."""

    def test_scan_file_with_issues(self, tmp_path):
        """Test scanning a file with issues."""
        # Create a file with issues
        file_content = """
def example_function():
    # TODO: Implement this function
    pass

def another_function():
    # FIXME: This is broken
    return None
"""
        file_path = tmp_path / "example.py"
        file_path.write_text(file_content)

        # Scan the file for issues
        result = scan_file_for_issues(file_path)

        # Check that the result contains the expected issues
        assert len(result) == 2
        assert "TODO (Line 3): # TODO: Implement this function" in result
        assert "FIXME (Line 7): # FIXME: This is broken" in result

    def test_scan_file_without_issues(self, tmp_path):
        """Test scanning a file without issues."""
        # Create a file without issues
        file_content = """
def example_function():
    return "Hello, world!"
"""
        file_path = tmp_path / "example.py"
        file_path.write_text(file_content)

        # Scan the file for issues
        result = scan_file_for_issues(file_path)

        # Check that the result is an empty list
        assert result == []

    def test_scan_binary_file(self, tmp_path):
        """Test scanning a binary file."""
        # Create a binary file
        file_path = tmp_path / "binary.bin"
        with open(file_path, "wb") as f:
            f.write(b"\x00\x01\x02\x03")

        # Scan the binary file for issues
        result = scan_file_for_issues(file_path)

        # Check that the result is an empty list
        assert result == []


class TestBuildTriageReport:
    """Tests for the build_triage_report function."""

    @mock.patch("dev_tools.triage.build_triage_report.parse_inventory_file")
    @mock.patch("dev_tools.triage.build_triage_report.get_module_description_from_md")
    @mock.patch("dev_tools.triage.build_triage_report.scan_file_for_issues")
    def test_build_report(self, mock_scan, mock_get_desc, mock_parse, tmp_path):
        """Test building a triage report."""
        # Create dummy files and directories in tmp_path
        module1_file = tmp_path / "module1.py"
        module1_file.write_text(
            "# Test content for module1.py\n# TODO: A todo in module1"
        )

        dir_path = tmp_path / "dir"
        dir_path.mkdir()
        module2_file = dir_path / "module2.py"
        module2_file.write_text(
            "# Test content for module2.py\n# FIXME: A fixme in module2"
        )

        # Mock the parse_inventory_file function
        # These paths should be relative to tmp_path for the test
        mock_inventory = {
            "module1.py": {"description": "Description 1", "issues": []},
            "dir/module2.py": {"description": "Description 2", "issues": []},
        }
        mock_parse.return_value = mock_inventory

        # Mock the get_module_description_from_md function
        # It will be called for each key in mock_inventory
        mock_get_desc.return_value = "Updated Description"

        # Mock the scan_file_for_issues function
        # This will be called for module1.py and dir/module2.py
        # We can make it return different things based on the path
        def scan_side_effect(file_path_obj):
            if file_path_obj == module1_file:
                return ["TODO (Line 2): # TODO: A todo in module1"]
            if file_path_obj == module2_file:
                return ["FIXME (Line 2): # FIXME: A fixme in module2"]
            return []

        mock_scan.side_effect = scan_side_effect

        # No need to mock Path.exists or Path.is_file globally anymore,
        # as we are creating actual files.
        # is_python_package will work correctly with actual files.

        # Build the triage report using tmp_path as project_root
        result = build_triage_report(tmp_path)

        # Check that the result contains the expected modules
        assert len(result) == 2, (
            f"Expected 2 modules, got {len(result)}. Result: {result}"
        )
        assert "module1.py" in result
        assert "dir/module2.py" in result

        # Check that the descriptions were updated
        assert result["module1.py"]["description"] == "Updated Description"
        assert result["dir/module2.py"]["description"] == "Updated Description"

        # Check that the issues were added correctly
        assert len(result["module1.py"]["issues"]) == 1, (
            f"Issues for module1.py: {result['module1.py']['issues']}"
        )
        assert (
            "TODO (Line 2): # TODO: A todo in module1 (File: module1.py)"
            in result["module1.py"]["issues"]
        )

        assert len(result["dir/module2.py"]["issues"]) == 1, (
            f"Issues for dir/module2.py: {result['dir/module2.py']['issues']}"
        )
        assert (
            "FIXME (Line 2): # FIXME: A fixme in module2 (File: dir/module2.py)"
            in result["dir/module2.py"]["issues"]
        )

        # Check that the mock functions were called with the expected arguments
        mock_parse.assert_called_once_with(tmp_path / "docs" / "pulse_inventory.md")

        # get_module_description_from_md is called for each module in inventory
        assert mock_get_desc.call_count == len(mock_inventory)
        mock_get_desc.assert_any_call("module1.py", tmp_path)
        mock_get_desc.assert_any_call("dir/module2.py", tmp_path)

        # scan_file_for_issues is called for each .py file found by rglob
        # that is owned by a module in the inventory
        assert (
            mock_scan.call_count >= 2
        )  # Could be more if other .py files are in tmp_path
        mock_scan.assert_any_call(module1_file)
        mock_scan.assert_any_call(module2_file)


if __name__ == "__main__":
    pytest.main(["-v", __file__])
