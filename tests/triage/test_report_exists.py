import os
import json
import pytest


def test_triage_report_exists_and_is_not_empty() -> None:
    """
    Verify that the triage_report.json file exists in the project root
    and is not empty. Optionally, assert that it can be loaded as valid JSON.
    """
    project_root = os.getcwd()
    report_path = os.path.join(project_root, "triage_report.json")

    assert os.path.exists(report_path), f"triage_report.json not found at {report_path}"
    assert os.path.getsize(report_path) > 0, (
        f"triage_report.json at {report_path} is empty"
    )

    try:
        with open(report_path, "r", encoding="utf-8") as f:
            json.load(f)
    except json.JSONDecodeError:
        pytest.fail(f"triage_report.json at {report_path} is not valid JSON")
    except Exception as e:
        pytest.fail(
            f"An unexpected error occurred while reading triage_report.json: {e}"
        )
