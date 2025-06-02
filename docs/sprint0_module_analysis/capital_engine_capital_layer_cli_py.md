# Analysis of capital_engine/capital_layer_cli.py

## Module Intent/Purpose
This CLI script demonstrates and tests functionalities of `capital_engine.capital_layer`. It initializes a mock `WorldState`, runs a shortview forecast, and prints the forecast, exposure summary, and portfolio alignment tags to the console. It's designed for direct execution.

## Operational Status/Completeness
Operational as a basic demonstration/testing script. It successfully uses `capital_layer` functions with mock data. Complete for its simple execution purpose.

## Implementation Gaps / Unfinished Next Steps
- **Command-Line Arguments:** Uses hardcoded `mock_vars`. `argparse` could allow user-specified `WorldState` params, forecast duration, etc.
- **Loading Real `WorldState`:** Could be enhanced to load `WorldState` from a file.
- **Output Formatting:** Raw dictionary prints; could use `capital_engine.capital_digest_formatter` for readable Markdown.
- **Error Handling:** Lacks explicit error handling for `WorldState` init or `capital_layer` calls.

## Connections & Dependencies
- **Direct Project Module Imports:**
    - From `capital_engine.capital_layer`: `run_shortview_forecast`, `summarize_exposure`, `portfolio_alignment_tags`.
    - From `engine.worldstate`: `WorldState` class.
- **External Library Dependencies:** None.
- **Input/Output Files:** Input from hardcoded `mock_vars`; output to console.

## Function and Class Example Usages
- **`ws = WorldState(**mock_vars)`**: Demonstrates `WorldState` initialization.
- **`forecast = run_shortview_forecast(ws)`**: Shows `run_shortview_forecast` usage.
- **`print(summarize_exposure(ws))`**: Shows `summarize_exposure` usage.
- **`print(portfolio_alignment_tags(ws))`**: Shows `portfolio_alignment_tags` usage.

## Hardcoding Issues
- `mock_vars`: Entire initial `WorldState` is hardcoded.
- Print statement headers.

## Coupling Points
- Tightly coupled to function signatures/returns of `capital_engine.capital_layer` and `WorldState` constructor.
- Assumes `forecast` object is a dictionary for printing.

## Existing Tests
- Acts as an integration/smoke test for `capital_layer` with mock data.
- Not a formal, automated test suite.

## Module Architecture and Flow
1.  Imports functions/classes.
2.  Defines `mock_vars` for `WorldState` initialization.
3.  In `if __name__ == "__main__":` block:
    a.  Creates `WorldState` instance.
    b.  Calls `run_shortview_forecast`.
    c.  Prints forecast, exposure summary, and alignment tags.

## Naming Conventions
- Adheres to PEP 8. Clear variable names. No apparent deviations.