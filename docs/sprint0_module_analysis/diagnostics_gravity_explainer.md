# Analysis: `diagnostics/gravity_explainer.py`

## 1. File Overview

*   **File Path:** [`diagnostics/gravity_explainer.py`](diagnostics/gravity_explainer.py:1)
*   **Purpose:** This module provides tools to explain and visualize the symbolic gravity corrections applied during simulations. It helps users understand why specific corrections were made by showing contributions from symbolic pillars and their underlying data points.
*   **Key Functionalities:**
    *   Text-based explanations of gravity corrections.
    *   Interactive HTML visualizations (Plotly preferred, Matplotlib fallback) of correction details, including deltas over time and pillar contributions.
    *   Extraction of trace data specific to a variable.
    *   Export of gravity correction data to JSON.
    *   Retrieval of top source data points influencing a specific pillar.

## 2. Module Structure and Components

*   **`display_correction_explanation(trace_data, variable_name)`:** Prints a textual breakdown of gravity corrections for a specified variable from simulation trace data, including causal vs. gravity deltas and dominant pillar contributions.
*   **`plot_gravity_correction_details_html(trace_data, variable_name, output_path, max_steps)`:** Generates an interactive HTML plot (using Plotly if available) or a static PNG image (using Matplotlib as a fallback) visualizing simulation deltas and pillar contributions for a variable.
    *   Includes JavaScript for basic interactivity in the Plotly version, though some features like detailed source data point display on click are noted as placeholders.
*   **`_plot_gravity_correction_details_matplotlib(...)`:** Internal helper function for Matplotlib-based plotting.
*   **`extract_trace_data_for_variable(trace_data, variable_name)`:** Filters full simulation trace data to extract entries relevant to a specific variable's gravity corrections.
*   **`export_gravity_explanation_json(trace_data, variable_name, output_path)`:** Exports the filtered gravity correction data for a variable to a JSON file.
*   **`get_top_source_data_points_for_pillar(trace_data, variable_name, pillar_name, top_n)`:** Identifies and returns the most influential source data points for a given pillar affecting a specific variable.

## 3. Dependencies

*   **Internal Pulse Modules:**
    *   [`core.path_registry`](core/path_registry.py:1) (specifically `PATHS`): Likely used for resolving output paths or accessing other project resources, though not directly visible in the provided functions' logic for path resolution.
    *   [`symbolic_system.gravity.symbolic_pillars`](symbolic_system/gravity/symbolic_pillars.py:1) (specifically `SymbolicPillar`, `SymbolicPillarSystem`): These are fundamental for understanding the structure of pillar data within the trace.
*   **External Libraries:**
    *   `logging`: For module-level logging.
    *   `json`: For handling JSON data (exporting).
    *   `os`: For path manipulation (e.g., `os.makedirs`, `os.path.dirname`).
    *   `typing`: For type hinting.
    *   `numpy`: For numerical operations, especially in plotting (e.g., `np.argsort`).
    *   `datetime`: For timestamping exports.
    *   `matplotlib.pyplot`: As a fallback for plotting if Plotly is not available.
    *   `plotly` (optional): For creating interactive HTML visualizations. `plotly.graph_objects` and `plotly.subplots` are used.

## 4. SPARC Principles Assessment

*   **Specification & Simplicity:** The module has a clear purpose: explaining gravity corrections. Functions are generally well-defined and aim to provide specific insights. The text explanation is straightforward.
*   **Architecture & Modularity:** The module is reasonably modular, with distinct functions for text explanation, plotting, data extraction, and JSON export. The separation of Plotly and Matplotlib logic is good.
*   **Testability:** No dedicated unit tests are immediately apparent from the file listing ([`tests/test_gravity_explainer.py`](tests/test_gravity_explainer.py:1) exists, its content would determine actual coverage). The functions appear testable given appropriate mock trace data.
*   **Maintainability & Readability:** The code is generally well-commented with docstrings explaining function purposes, parameters, and returns. Variable names are descriptive.
*   **Security (Hardcoding Secrets):** No hardcoded secrets (API keys, passwords) are apparent.
*   **Hardcoding (Other):**
    *   Default values for `top_n` in `get_top_source_data_points_for_pillar` ([`diagnostics/gravity_explainer.py:545`](diagnostics/gravity_explainer.py:545)) and display limits (e.g., showing up to 3 source points in text explanation ([`diagnostics/gravity_explainer.py:118`](diagnostics/gravity_explainer.py:118)), top 7 pillars in plots ([`diagnostics/gravity_explainer.py:259`](diagnostics/gravity_explainer.py:259))) are present but are generally acceptable for diagnostic display purposes.
    *   Plot colors and styling are hardcoded, which is typical for plotting functions.
*   **No `print` for Logging:** Uses `print()` for console output in `display_correction_explanation` ([`diagnostics/gravity_explainer.py:60`](diagnostics/gravity_explainer.py:60)), which is acceptable for a CLI-style display function. Uses `logging` for warnings and info messages elsewhere.

## 5. Overall Assessment

*   **Completeness:** The module provides a good set of tools for understanding gravity corrections. The core functionalities for explanation and visualization seem largely complete. The Plotly interactivity for source data points is noted as a partial implementation in the HTML output.
*   **Quality:** The code is well-structured, with clear functions and good use of type hints and docstrings. The fallback mechanism for plotting (Plotly to Matplotlib) enhances robustness.
*   **Potential Improvements:**
    *   Enhance the JavaScript interactivity in Plotly HTML outputs to fully display source data points on click, rather than a placeholder message.
    *   Consider making some display limits (e.g., number of pillars/source points shown) configurable.
    *   Ensure comprehensive unit test coverage in [`tests/test_gravity_explainer.py`](tests/test_gravity_explainer.py:1).

## 6. Role in `diagnostics/` Directory

The module plays a crucial role in the `diagnostics/` directory by providing explainability for the "symbolic gravity" system, which is a core component of Pulse's simulation and modeling. It allows developers and analysts to dissect and understand the impact of these automated adjustments.

## 7. Summary Note for Main Report

The [`diagnostics/gravity_explainer.py`](diagnostics/gravity_explainer.py:1) module offers robust tools for text-based and visual (HTML/PNG via Plotly/Matplotlib) explanations of symbolic gravity corrections in simulation traces, aiding in understanding model behavior.