# Module Analysis: `forecast_output/digest_exporter.py`

## Module Intent/Purpose

The primary role of [`digest_exporter.py`](forecast_output/digest_exporter.py:1) is to export forecasting digests (structured summary information) to various file formats, including Markdown, HTML, PDF, and JSON. It provides a consistent API for converting and saving forecast data to different formats depending on user requirements, with optional enhancements when specific dependencies are available.

## Operational Status/Completeness

The module is functional but partially complete:

- Markdown export is fully implemented
- HTML export is fully implemented with optional enhancements when dependencies are available
- JSON export is fully implemented
- PDF export is explicitly marked as a stub with a TODO comment

The module includes a deprecation warning indicating it has been migrated from a previous location (`foresight_architecture.digest_exporter`), suggesting ongoing refactoring or reorganization of the codebase.

## Implementation Gaps / Unfinished Next Steps

- **PDF Export Implementation:** The most significant gap is the PDF export functionality, which is currently a stub. The code includes a TODO comment stating: "Integrate ReportLab or WeasyPrint for real PDF export."
- **HTML Export Dependencies:** The HTML export has conditional paths based on whether optional dependencies (`markdown2` and `bleach`) are available, suggesting the module could be enhanced by making these dependencies required or providing more robust fallbacks.
- **Error Handling Refinement:** Error handling is basic (catching all exceptions and logging them), which could be expanded to handle specific types of errors differently or provide more detailed recovery strategies.

## Connections & Dependencies

- **Standard Libraries:** `json`, `logging`, `typing`
- **Optional External Dependencies:** 
  - `markdown2`: Used for converting Markdown to HTML
  - `bleach`: Used for sanitizing HTML output
- **Input/Output:** 
  - Input: String content in Markdown format or list of dictionaries for JSON
  - Output: Files written to the filesystem in specified formats (.md, .html, .pdf, .json)

## Function and Class Example Usages

- **Main export function:**
  ```python
  # Export markdown content to an HTML file with sanitization
  from forecast_output.digest_exporter import export_digest
  export_digest("# Forecast Results\n\nKey findings...", "results.html", fmt="html", sanitize_html=True)
  ```

- **JSON export:**
  ```python
  # Export a list of forecast dictionaries to JSON
  from forecast_output.digest_exporter import export_digest_json
  forecasts = [{"variable": "GDP", "value": 2.5, "confidence": 0.8}]
  export_digest_json(forecasts, "forecasts.json")
  ```

- **PDF export (stub):**
  ```python
  # Export markdown content to a placeholder PDF file
  from forecast_output.digest_exporter import export_digest
  export_digest("# Report\n\nFindings...", "report.pdf", fmt="pdf")
  ```

## Hardcoding Issues

- No significant hardcoded secrets, credentials, or sensitive paths
- HTML tag allowlist extensions (`{"h1", "h2", "h3"}`) are hardcoded when using the `bleach` library for sanitization
- Default encoding (`"utf-8"`) is hardcoded for file operations, which is generally appropriate

## Coupling Points

- **Expected Input Format:** The module assumes digest content is in Markdown format for non-JSON exports
- **Optional Dependencies:** Behavior changes based on the availability of `markdown2` and `bleach` libraries
- **File System Access:** Directly writes to the filesystem using file paths provided by the caller

## Existing Tests

No explicit tests are visible in the file itself (beyond example usage comments), and there is no apparent corresponding test file in the project structure. The example usage at the end of the file could serve as minimal manual testing instructions, but formal unit or integration tests are not evident.

## Module Architecture and Flow

The module follows a straightforward functional architecture:

1. **Main Export Function (`export_digest`):** 
   - Determines the appropriate export format based on the `fmt` parameter
   - Routes to the format-specific export function or performs the export directly
   - Handles HTML generation with markdown2 if available
   - Sanitizes HTML with bleach if requested and available

2. **Format-Specific Export Functions:**
   - `export_digest_json`: Handles JSON serialization and export
   - `export_digest_pdf`: Currently a stub that writes placeholder content

3. **Error Handling:**
   - All functions wrap file operations in try/except blocks
   - Errors are logged but not propagated back to the caller

## Naming Conventions

The module follows standard Python naming conventions:

- Function names use lowercase with underscores (`snake_case`): `export_digest`, `export_digest_json`, `export_digest_pdf`
- Parameters follow the same convention: `digest_str`, `path`, `fmt`, `sanitize_html`
- Module name is descriptive of its functionality: `digest_exporter.py`

Parameter naming is consistent across functions, with `path` consistently used for output file locations. The module maintains internal naming consistency with a clear pattern of `export_digest_<format>` for format-specific functions.
# Module Analysis: `forecast_output/digest_exporter.py`

## Module Intent/Purpose

The primary role of `digest_exporter.py` is to facilitate the export of "strategos digests" and forecast batches into various file formats, including Markdown, JSON, HTML, and (as a stub) PDF. It provides a centralized utility for generating output files from processed forecast data.

## Operational Status/Completeness

The module is partially complete. It provides functional export capabilities for Markdown and JSON formats. HTML export is also implemented, including optional conversion from Markdown and sanitization if the necessary libraries (`markdown2`, `bleach`) are installed. The PDF export functionality is explicitly marked as a "stub" and is not yet implemented. A deprecation warning indicates the module was moved from a previous location.

## Implementation Gaps / Unfinished Next Steps

- **PDF Export:** The `export_digest_pdf` function is a stub (`TODO: Integrate ReportLab or WeasyPrint`), indicating that PDF export is a planned but unfinished feature.
- **Dependency Handling:** While it logs warnings if `markdown2` or `bleach` are not installed, the module doesn't enforce their presence for HTML export, leading to potentially unformatted or unsanitized output. Dependency management could be more explicit.

## Connections & Dependencies

- **Direct imports from other project modules:** None.
- **External library dependencies:**
    - `json`: Used for serializing forecast batches to JSON.
    - `logging`: Used for logging informational messages and errors.
    - `typing`: Used for type hints (`Any`, `List`).
    - `warnings`: Used to issue a deprecation warning.
    - `markdown2` (optional): Used for converting Markdown to HTML.
    - `bleach` (optional): Used for sanitizing HTML output.
- **Interaction with other modules via shared data:**
    - It receives digest content as strings (`digest_str`) or forecast data as a list of dictionaries (`forecast_batch`). These data structures are presumably generated by other modules within the forecast or strategos pipeline.
- **Input/output files:**
    - **Input:** Receives data in memory (strings or lists of dicts).
    - **Output:** Writes formatted data to a file path specified by the `path` argument.

## Function and Class Example Usages

- `export_digest(digest_str: str, path: str, fmt: str = "markdown", sanitize_html: bool = False) -> None`: Exports a digest string to a file.
    ```python
    from forecast_output.digest_exporter import export_digest
    digest_content = "# My Digest\nThis is the content."
    export_digest(digest_content, "output/my_digest.md", fmt="markdown")
    export_digest(digest_content, "output/my_digest.html", fmt="html", sanitize_html=True)
    ```
- `export_digest_json(forecast_batch: List[Any], path: str) -> None`: Exports a list of forecasts as a JSON file.
    ```python
    from forecast_output.digest_exporter import export_digest_json
    forecasts = [{"id": 1, "value": 100}, {"id": 2, "value": 200}]
    export_digest_json(forecasts, "output/forecasts.json")
    ```
- `export_digest_pdf(digest_str: str, path: str) -> None`: Stub function for PDF export.
    ```python
    from forecast_output.digest_exporter import export_digest_pdf
    digest_content = "PDF content here."
    export_digest_pdf(digest_content, "output/my_digest.pdf") # This will output a text file with a stub message
    ```

## Hardcoding Issues

- The string "PDF export not implemented.\n\n" is hardcoded within the `export_digest_pdf` stub function.

## Coupling Points

- Coupled with the file system for writing output files.
- Loosely coupled with `markdown2` and `bleach` (optional dependencies).
- Implicitly coupled with the format/structure of the `digest_str` and `forecast_batch` data provided by other modules.

## Existing Tests

- Based on the `environment_details`, a test file [`tests/test_digest_exporter.py`](tests/test_digest_exporter.py:1) exists, indicating that there is dedicated test coverage for this module. The extent and nature of these tests would require examining the test file itself.

## Module Architecture and Flow

The module has a simple procedural structure. The main entry point is the `export_digest` function, which acts as a dispatcher calling format-specific helper functions (`export_digest_pdf`, `export_digest_json`, and the inline logic for markdown/html) based on the `fmt` parameter. Error handling is included using `try...except` blocks for file operations and potential issues with optional imports.

## Naming Conventions

Naming conventions follow Python standards (snake_case for functions and variables). Names like `digest_str`, `path`, `fmt`, `sanitize_html`, `forecast_batch` are descriptive and clear. No obvious AI assumption errors or deviations from PEP 8 were noted.