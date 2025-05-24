# Triage Report Builder

The Triage Report Builder is a tool that generates a comprehensive report of issues found in the Pulse codebase. It helps identify areas that need attention by scanning for keywords like `TODO`, `FIXME`, `Hardcoded`, and `NotImplementedError`.

## Overview

The tool performs the following steps:

1. Parses modules and descriptions from `docs/pulse_inventory.md`
2. Overrides descriptions with first line of corresponding `docs/<module>.md` if available
3. Recursively walks module directories, filtering text files by extension
4. Scans files for keywords: TODO, FIXME, Hardcoded, NotImplementedError
5. Aggregates issues into a JSON structure
6. Writes the result to `triage_report.json`

## Usage

Run the script from the project root directory:

```bash
python dev_tools/triage/build_triage_report.py
```

This will generate a `triage_report.json` file in the project root directory.

## Output Format

The output JSON file has the following structure:

```json
{
  "module_path": {
    "description": "Module description",
    "companion_md_path": "docs/module.md",
    "issues": [
      {
        "keyword": "TODO",
        "line": 42,
        "excerpt": "TODO: Implement this function",
        "file": "module_path"
      }
    ]
  }
}
```

## Configuration

The script uses the following constants that can be modified if needed:

- `KEYWORDS`: List of keywords to scan for (`TODO`, `FIXME`, `Hardcoded`, `NotImplementedError`)
- `TEXT_FILE_EXTENSIONS`: Set of file extensions to scan (`.py`, `.md`, `.txt`, etc.)
- `BINARY_EXTENSIONS`: Set of file extensions to skip (`.pyc`, `.png`, `.jpg`, etc.)
- `MAX_EXCERPT_LENGTH`: Maximum length of issue excerpts (default: 160 characters)

## Integration with Foundation Sprint

This tool is part of the T-0 Foundation Sprint, specifically the "T0-α. Bootstrap triage builder" subtask. It helps identify areas of the codebase that need attention, which is crucial for establishing a solid foundation for the project.

## Future Enhancements

Potential future enhancements include:

- Adding severity levels to issues
- Integrating with CI/CD pipelines to track issue trends over time
- Adding support for custom keywords per module
- Generating HTML reports with interactive filtering and sorting