# Definition of Done Lite (dod.md)

This document outlines the minimum criteria that must be met for a task or feature to be considered "Done".

## Criteria

1.  **All Imports Succeed:**
    *   All import statements in the codebase must resolve correctly.
    *   There should be no `ImportError` or similar issues at runtime or during static analysis.

2.  **All Tests Pass:**
    *   All automated unit tests must pass.
    *   All automated integration tests relevant to the changes must pass.
    *   Test coverage should meet or exceed project standards (if defined).

3.  **CI Linting Score >= 9.0:**
    *   The Continuous Integration (CI) pipeline's linting stage must complete successfully.
    *   The reported linting score (e.g., Pylint, Flake8) must be greater than or equal to 9.0 out of 10.0.

4.  **MCP Smoke Tests Pass:**
    *   **context7 MCP Server:** Basic smoke tests verifying the connectivity and core functionality of the `context7` MCP server must pass. This includes, but is not limited to:
        *   Successful resolution of a known library ID.
        *   Successful retrieval of basic documentation for a known library ID.
    *   **memory-bank MCP Server (if applicable):** Basic smoke tests verifying the connectivity and core functionality of the `memory-bank` MCP server must pass. This includes, but is not limited to:
        *   Successful read operations from standard Memory Bank files.
        *   Successful write/append operations to standard Memory Bank files (if part of the test).

---

*This Definition of Done Lite is intended to be a lightweight, actionable checklist. More comprehensive DoD criteria may be defined elsewhere.*