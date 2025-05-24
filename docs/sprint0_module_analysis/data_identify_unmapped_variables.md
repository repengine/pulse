# Module Analysis: `data/identify_unmapped_variables.py`

## 1. Module Intent/Purpose

The primary purpose of the [`data/identify_unmapped_variables.py`](data/identify_unmapped_variables.py:1) script is to analyze the [`VARIABLE_REGISTRY`](data/identify_unmapped_variables.py:21) (imported from [`core.variable_registry`](core/variable_registry.py:1)) and identify which variables are not currently mapped to any data sources by the simulated mapping logic within the script. This logic mimics how variables might be assigned to data providers like FRED, World Bank, Alpha Vantage, etc., based on their descriptions or types.

Its role within the `data/` directory is to serve as a utility for maintaining data coverage and ensuring that variables defined in the central registry have corresponding data sources. It helps in identifying gaps in data ingestion pipelines. The script outputs a list of unmapped variables to [`data/ground_truth_dataset/unmapped_variables.txt`](data/ground_truth_dataset/unmapped_variables.txt:26).

## 2. Key Functionalities

*   **Path Setup**: Adds the project root to `sys.path` to ensure correct module imports ([`sys.path.insert(0, str(Path(__file__).resolve().parent.parent))`](data/identify_unmapped_variables.py:18)).
*   **Output Directory Creation**: Ensures the output directory ([`data/ground_truth_dataset`](data/identify_unmapped_variables.py:24)) exists.
*   **Mapping Simulation ([`simulate_mapping()`](data/identify_unmapped_variables.py:29))**:
    *   Iterates through [`VARIABLE_REGISTRY`](data/identify_unmapped_variables.py:21).
    *   Attempts to map variables to data sources (FRED, World Bank, Alpha Vantage, Finnhub, NASDAQ) based on keywords in their `description` (e.g., "FRED:", "Yahoo Finance:") or `type` (e.g., "economic", "market").
    *   Includes a hardcoded set of `manual_mappings` that are considered mapped.
    *   Returns a dictionary of variables mapped by source and a set of unmapped variable names.
*   **Variable Grouping ([`group_variables_by_type(variable_names)`](data/identify_unmapped_variables.py:120))**:
    *   Takes a set of variable names.
    *   Groups them by their `type` (e.g., "economic", "market", "unknown") as defined in [`VARIABLE_REGISTRY`](data/identify_unmapped_variables.py:21).
    *   Sorts the variable names within each group alphabetically.
*   **Output Formatting ([`format_output(unmapped_variables)`](data/identify_unmapped_variables.py:148))**:
    *   Takes the grouped unmapped variables.
    *   Formats them into a human-readable string, including total counts and descriptions for each unmapped variable.
*   **Main Execution ([`main()`](data/identify_unmapped_variables.py:178))**:
    *   Calls [`simulate_mapping()`](data/identify_unmapped_variables.py:29) to get mapped and unmapped variables.
    *   Calls [`group_variables_by_type()`](data/identify_unmapped_variables.py:120) to organize unmapped variables.
    *   Calls [`format_output()`](data/identify_unmapped_variables.py:148) to prepare the report.
    *   Writes the report to [`data/ground_truth_dataset/unmapped_variables.txt`](data/ground_truth_dataset/unmapped_variables.txt:26).
    *   Prints a summary of total variables, mapped variables (count and percentage), unmapped variables (count and percentage), and source coverage to the console.

## 3. Dependencies

### External Libraries:
*   `os`: Used implicitly via `Path` and for path operations.
*   `sys`: Used for modifying `sys.path`.
*   `pathlib.Path`: Used for path manipulation and directory creation.
*   `typing` (Dict, Any, Set, List, Tuple): Used for type hinting.

### Internal Pulse Modules:
*   [`core.variable_registry`](core/variable_registry.py:1): Specifically, the `VARIABLE_REGISTRY` dictionary is imported from this module. This is a critical dependency as it provides the list of all variables to be analyzed.

## 4. SPARC Principles Assessment

### Operational Status/Completeness
*   The script is operational and appears complete for its defined task: identifying variables in [`VARIABLE_REGISTRY`](data/identify_unmapped_variables.py:21) that are not covered by its internal simulated mapping logic.
*   The completeness of the *analysis itself* depends on how accurately the [`simulate_mapping()`](data/identify_unmapped_variables.py:29) function reflects the actual or intended mapping logic in `ground_truth_generator.py` (which is mentioned in the header but not directly used).

### Implementation Gaps / Unfinished Next Steps
*   **Synchronization with Actual Mapping**: The script's mapping logic in [`simulate_mapping()`](data/identify_unmapped_variables.py:29) is a *simulation*. If the actual mapping logic in `ground_truth_generator.py` (or elsewhere) changes, this script must be updated manually to reflect those changes. There's no dynamic link.
*   **Error Handling in Simulation**: The `try-except Exception: pass` blocks ([`simulate_mapping()`](data/identify_unmapped_variables.py:58), [`simulate_mapping()`](data/identify_unmapped_variables.py:77)) in [`simulate_mapping()`](data/identify_unmapped_variables.py:29) are very broad and could hide actual issues in parsing descriptions or variable info. More specific exception handling or logging would be beneficial.
*   **Configuration of Mapping Rules**: The mapping rules are hardcoded within [`simulate_mapping()`](data/identify_unmapped_variables.py:29). If these rules become complex or numerous, managing them directly in the code could be difficult.
*   **No External Configuration**: The script does not take external arguments for paths or configurations, relying on hardcoded values (e.g., output directory).

### Connections & Dependencies
*   Critically dependent on the structure and content of [`core.variable_registry.VARIABLE_REGISTRY`](core/variable_registry.py:1).
*   The output file path ([`data/ground_truth_dataset/unmapped_variables.txt`](data/ground_truth_dataset/unmapped_variables.txt:26)) is hardcoded.
*   The logic for distributing symbols to Alpha Vantage, Finnhub, or NASDAQ based on `var_type` and name patterns (e.g., `crypto_`, `_stock`) is specific and hardcoded.

### Function and Class Example Usages
This script is designed to be run directly.
```bash
python data/identify_unmapped_variables.py
```
This will:
1.  Read [`core.variable_registry.VARIABLE_REGISTRY`](core/variable_registry.py:1).
2.  Simulate mapping these variables to data sources.
3.  Generate a report at [`data/ground_truth_dataset/unmapped_variables.txt`](data/ground_truth_dataset/unmapped_variables.txt:26) listing variables that couldn't be mapped by the script's logic.
4.  Print a summary to the console.

### Hardcoding Issues
*   **Output Directory/File**: [`output_dir = Path("data/ground_truth_dataset")`](data/identify_unmapped_variables.py:24) and [`output_file = output_dir / "unmapped_variables.txt"`](data/identify_unmapped_variables.py:26).
*   **Mapping Logic**: All rules for assigning variables to sources (FRED, Yahoo Finance keywords, World Bank patterns, manual mappings list) are hardcoded within the [`simulate_mapping()`](data/identify_unmapped_variables.py:29) function.
*   **Manual Mappings List**: The `manual_mappings` set ([`simulate_mapping()`](data/identify_unmapped_variables.py:94-99)) is hardcoded.

### Coupling Points
*   **[`VARIABLE_REGISTRY`](data/identify_unmapped_variables.py:21)**: Tightly coupled to the exact structure (expected keys like "description", "type") and content of this dictionary.
*   **Simulated Mapping Logic**: The script's utility is directly tied to how well its internal mapping simulation mirrors the target mapping system it's trying to analyze.

### Existing Tests
*   No automated tests are provided within this module or mentioned. Testing would involve:
    *   Creating mock [`VARIABLE_REGISTRY`](data/identify_unmapped_variables.py:21) data.
    *   Verifying the console output.
    *   Verifying the content of the generated [`unmapped_variables.txt`](data/identify_unmapped_variables.py:26) file.

### Module Architecture and Flow
*   **Procedural Script**: The script follows a procedural approach.
*   **Import and Setup**: Imports necessary modules, sets up `sys.path`, defines output paths.
*   **Main Function ([`main()`](data/identify_unmapped_variables.py:178))**: Orchestrates the core logic:
    1.  Calls [`simulate_mapping()`](data/identify_unmapped_variables.py:29) to perform the core analysis.
    2.  Calls [`group_variables_by_type()`](data/identify_unmapped_variables.py:120) for better report organization.
    3.  Calls [`format_output()`](data/identify_unmapped_variables.py:148) to create the report string.
    4.  Writes the report to a file.
    5.  Prints a summary to standard output.
*   Helper functions ([`simulate_mapping()`](data/identify_unmapped_variables.py:29), [`group_variables_by_type()`](data/identify_unmapped_variables.py:120), [`format_output()`](data/identify_unmapped_variables.py:148)) encapsulate distinct steps of the process.

### Naming Conventions
*   Functions and variables generally use snake_case (e.g., [`simulate_mapping`](data/identify_unmapped_variables.py:29), `unmapped_variables`).
*   Constants like `VARIABLE_REGISTRY` are in UPPER_SNAKE_CASE (as imported).
*   The script filename [`identify_unmapped_variables.py`](data/identify_unmapped_variables.py:1) is descriptive.
*   Type hints are used, improving readability.

## 5. Overall Assessment

### Completeness
The script is complete for its specific, stated goal: to identify variables from [`VARIABLE_REGISTRY`](data/identify_unmapped_variables.py:21) that are not mapped according to its *own internal, simulated logic*. The value of its output is directly proportional to how accurately this internal logic reflects the *actual* data source mapping rules used elsewhere in the Pulse project (presumably in `ground_truth_generator.py`).

### Quality
*   **Clarity**: The code is generally well-structured with clear function separation and descriptive names. Docstrings explain the purpose of functions.
*   **Simplicity**: The core logic within each function is relatively straightforward.
*   **Maintainability**:
    *   High if the actual mapping rules are stable and simple.
    *   Low if the actual mapping rules are complex or change frequently, as this script's simulated logic would need constant manual updates. The hardcoded rules in [`simulate_mapping()`](data/identify_unmapped_variables.py:29) are a significant point of fragility.
*   **Robustness**:
    *   The broad `except Exception: pass` clauses reduce robustness by potentially hiding errors.
    *   It correctly handles cases where "type" or "description" might be missing from `var_info`.
*   **Extensibility**: Adding new mapping rules or sources requires direct modification of the [`simulate_mapping()`](data/identify_unmapped_variables.py:29) function. It's not designed for easy extension without code changes.

The script is a useful diagnostic tool for data pipeline maintainers. Its main weakness is the hardcoded simulation of mapping logic, which could easily diverge from the actual system's mapping rules, leading to inaccurate reports.