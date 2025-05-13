# Task GTB14-001: Address PydanticDeprecatedSince20 Warnings

## Objective
Refactor all Pydantic models in the project using the deprecated class-based `config` to use `ConfigDict` instead, addressing `PydanticDeprecatedSince20` warnings.

## Plan

1.  **Gather Documentation:** Use the `context7` MCP server to obtain the latest Pydantic documentation on `ConfigDict` and migration from class-based `config`. (Completed)
2.  **Document Plan:** Create this markdown file to document the steps. (Completed)
3.  **Identify Models:** Search the project for all Pydantic models using the deprecated `config` class.
4.  **Refactor Models:** For each identified model:
    *   Read the file content.
    *   Replace the inner `class Config:` with `model_config = ConfigDict(...)`.
    *   Ensure all configuration options are correctly migrated to `ConfigDict`.
    *   Add or update code-level documentation for the modified models.
5.  **Verify Changes:**
    *   Run `pytest -q` to confirm the absence of `PydanticDeprecatedSince20` warnings.
    *   Run the full test suite (`pytest`) to ensure no regressions were introduced.
6.  **Update Documentation:** Update this file with the outcome of the refactoring and verification.
7.  **Complete Task:** Use the `attempt_completion` tool to summarize the work.

## Progress
- [x] Gather Pydantic `ConfigDict` documentation using `context7`.
- [x] Document the plan in `tasks/GTB14-001_pydantic_config_refactor.md`.
- [x] Identify Pydantic models using deprecated `config`. (Found one in `intelligence/forecast_schema.py`)
- [x] Refactor identified models to use `ConfigDict`. (Updated `intelligence/forecast_schema.py`)
- [x] Verify changes by running tests. (`pytest -q` showed no `PydanticDeprecatedSince20` warnings related to `class Config:`, and the full `pytest` suite passed.)
- [ ] Update task documentation with outcome.
- [ ] Use `attempt_completion`.

## Outcome
The `PydanticDeprecatedSince20` warning related to the deprecated `class Config:` in Pydantic models has been addressed by refactoring the `ForecastSchema` model in `intelligence/forecast_schema.py` to use `ConfigDict`. The change was verified by running `pytest -q`, which no longer shows the specific warning, and by running the full test suite, which passed without regressions.