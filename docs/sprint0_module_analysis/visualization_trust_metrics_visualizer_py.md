# Analysis Report for visualization/trust_metrics_visualizer.py

## 1. Module Intent/Purpose

The primary role of the [`trust_metrics_visualizer.py`](visualization/trust_metrics_visualizer.py:1) module is to generate visualizations and an HTML dashboard for trust metrics and Bayesian statistics related to rules and variables within the Pulse system. It aims to provide a visual understanding of trust evolution, score distributions, and confidence levels.

## 2. Operational Status/Completeness

The module appears to be largely complete and operational for its defined scope.
*   It includes functions for plotting various aspects of trust data:
    *   [`plot_trust_evolution()`](visualization/trust_metrics_visualizer.py:18): Tracks trust scores over time for a specific entity.
    *   [`plot_trust_histogram()`](visualization/trust_metrics_visualizer.py:60): Shows the distribution of trust scores.
    *   [`plot_confidence_vs_trust()`](visualization/trust_metrics_visualizer.py:115): Scatter plot to visualize the relationship between confidence and trust.
*   The [`generate_trust_dashboard()`](visualization/trust_metrics_visualizer.py:196) function orchestrates the creation of multiple plots and an HTML report.
*   The [`generate_html_dashboard()`](visualization/trust_metrics_visualizer.py:235) function creates a static HTML page to display the generated visualizations and summary tables.
*   The `if __name__ == "__main__":` block ([`visualization/trust_metrics_visualizer.py:432`](visualization/trust_metrics_visualizer.py:432)) includes example usage with simulated data, suggesting it can be run independently for testing or demonstration.
*   There are no explicit "TODO" comments or obvious placeholders indicating unfinished core functionality.

## 3. Implementation Gaps / Unfinished Next Steps

While functional, potential areas for extension or refinement include:
*   **Interactivity:** The generated HTML dashboard is static. Future enhancements could involve using JavaScript libraries (like D3.js, Plotly.js, or Bokeh) for interactive charts (e.g., tooltips with more details, zooming, filtering).
*   **Customization:** Plot aesthetics (colors, styles, sizes) and HTML report layout are largely hardcoded. Adding configuration options or theming capabilities could be beneficial.
*   **Advanced Visualizations:**
    *   Could visualize the impact of specific events or interventions on trust scores.
    *   Network graphs showing relationships between rules/variables and their trust metrics.
*   **Data Sourcing Robustness:** The module relies on `bayesian_trust_tracker` and `generate_trust_report`. The robustness of these underlying data sources is critical. The current example data is simulated.
*   **Error Handling & Edge Cases:** While some basic checks exist (e.g., for empty timestamps in [`plot_trust_evolution()`](visualization/trust_metrics_visualizer.py:28)), more comprehensive error handling for data inconsistencies or missing data from dependencies could be added.
*   **Configuration for Report Generation:** Parameters like `min_samples` or the number of top/bottom entities to plot are hardcoded or have fixed defaults in [`generate_trust_dashboard()`](visualization/trust_metrics_visualizer.py:196). These could be made configurable.
*   **Alternative Output Formats:** Besides HTML and PNG, options for PDF reports or other image formats might be useful.

## 4. Connections & Dependencies

### Direct Project Module Imports:
*   `from core.bayesian_trust_tracker import bayesian_trust_tracker` ([`visualization/trust_metrics_visualizer.py:15`](visualization/trust_metrics_visualizer.py:15))
*   `from core.pulse_learning_log import generate_trust_report` ([`visualization/trust_metrics_visualizer.py:16`](visualization/trust_metrics_visualizer.py:16))

### External Library Dependencies:
*   `matplotlib.pyplot` as `plt` ([`visualization/trust_metrics_visualizer.py:9`](visualization/trust_metrics_visualizer.py:9))
*   `numpy` as `np` ([`visualization/trust_metrics_visualizer.py:10`](visualization/trust_metrics_visualizer.py:10))
*   `pandas` as `pd` ([`visualization/trust_metrics_visualizer.py:11`](visualization/trust_metrics_visualizer.py:11))
*   `typing` (Dict, List, Any, Optional) ([`visualization/trust_metrics_visualizer.py:12`](visualization/trust_metrics_visualizer.py:12))
*   `os` ([`visualization/trust_metrics_visualizer.py:13`](visualization/trust_metrics_visualizer.py:13))
*   `math` ([`visualization/trust_metrics_visualizer.py:14`](visualization/trust_metrics_visualizer.py:14))
*   `datetime` (imported within [`generate_html_dashboard()`](visualization/trust_metrics_visualizer.py:395))

### Interaction with Other Modules via Shared Data:
*   Relies heavily on the data structures and methods provided by the `bayesian_trust_tracker` object (e.g., `timestamps`, `get_confidence_interval`, `get_trust`).
*   Consumes the dictionary structure returned by the `generate_trust_report` function.

### Input/Output Files:
*   **Input:** Implicitly, data from `bayesian_trust_tracker` and `generate_trust_report`. No direct file inputs are read by this module itself, other than what its dependencies might read.
*   **Output:**
    *   PNG image files for various plots (e.g., `trust_histogram_all.png`, `confidence_vs_trust_rules.png`, `trust_evolution_R001.png`). These are saved in the `output_dir` specified in [`generate_trust_dashboard()`](visualization/trust_metrics_visualizer.py:196).
    *   An `index.html` file, which forms the dashboard, saved in the `output_dir`.

## 5. Function and Class Example Usages

The module does not define classes. Key functions are used as follows:

*   **[`plot_trust_evolution(key: str, kind: str = "variable", save_path: Optional[str] = None)`](visualization/trust_metrics_visualizer.py:18):**
    *   Called by [`generate_trust_dashboard()`](visualization/trust_metrics_visualizer.py:222) to plot trust over time for specific high/low trust entities.
    *   Example: `plot_trust_evolution("R001", "rule", save_path="output/trust_R001.png")`

*   **[`plot_trust_histogram(kind: str = "all", min_samples: int = 5, save_path: Optional[str] = None)`](visualization/trust_metrics_visualizer.py:60):**
    *   Called by [`generate_trust_dashboard()`](visualization/trust_metrics_visualizer.py:209) to create histograms for all entities, rules, and variables.
    *   Example: `plot_trust_histogram("rule", save_path="output/hist_rules.png")`

*   **[`plot_confidence_vs_trust(kind: str = "all", min_samples: int = 5, save_path: Optional[str] = None)`](visualization/trust_metrics_visualizer.py:115):**
    *   Called by [`generate_trust_dashboard()`](visualization/trust_metrics_visualizer.py:214) to create scatter plots for all entities, rules, and variables.
    *   Example: `plot_confidence_vs_trust("variable", save_path="output/conf_trust_vars.png")`

*   **[`generate_trust_dashboard(output_dir: str = "trust_dashboard")`](visualization/trust_metrics_visualizer.py:196):**
    *   This is the main entry point for generating the full dashboard.
    *   The `if __name__ == "__main__":` block ([`visualization/trust_metrics_visualizer.py:432`](visualization/trust_metrics_visualizer.py:432)) shows its direct usage: `generate_trust_dashboard()`.

*   **[`generate_html_dashboard(output_dir: str, report: Dict[str, Any])`](visualization/trust_metrics_visualizer.py:235):**
    *   Called internally by [`generate_trust_dashboard()`](visualization/trust_metrics_visualizer.py:231) to assemble the HTML file.

## 6. Hardcoding Issues

Several hardcoded values and configurations are present:
*   **Default Output Directory:** `"trust_dashboard"` is the default for `output_dir` in [`generate_trust_dashboard()`](visualization/trust_metrics_visualizer.py:196).
*   **Plot Styling:**
    *   Colors: e.g., `'b-'` ([`visualization/trust_metrics_visualizer.py:39`](visualization/trust_metrics_visualizer.py:39)), `'r'` ([`visualization/trust_metrics_visualizer.py:44`](visualization/trust_metrics_visualizer.py:44)), `'g'` ([`visualization/trust_metrics_visualizer.py:46`](visualization/trust_metrics_visualizer.py:46)), `'blue'` ([`visualization/trust_metrics_visualizer.py:101`](visualization/trust_metrics_visualizer.py:101)).
    *   Linestyles: e.g., `'--'` ([`visualization/trust_metrics_visualizer.py:44`](visualization/trust_metrics_visualizer.py:44)).
    *   Alpha values: e.g., `0.5` ([`visualization/trust_metrics_visualizer.py:44`](visualization/trust_metrics_visualizer.py:44)), `0.3` ([`visualization/trust_metrics_visualizer.py:51`](visualization/trust_metrics_visualizer.py:51)), `0.7` ([`visualization/trust_metrics_visualizer.py:101`](visualization/trust_metrics_visualizer.py:101)).
    *   Figure sizes: `(10, 6)` ([`visualization/trust_metrics_visualizer.py:38`](visualization/trust_metrics_visualizer.py:38)), `(12, 6)` ([`visualization/trust_metrics_visualizer.py:98`](visualization/trust_metrics_visualizer.py:98)), `(12, 8)` ([`visualization/trust_metrics_visualizer.py:155`](visualization/trust_metrics_visualizer.py:155)).
    *   Font sizes: `fontsize=8` for annotations ([`visualization/trust_metrics_visualizer.py:178`](visualization/trust_metrics_visualizer.py:178)).
    *   Marker sizes in scatter plot: `marker_sizes = [20 + 5 * min(20, s) for s in sample_sizes]` ([`visualization/trust_metrics_visualizer.py:158`](visualization/trust_metrics_visualizer.py:158)).
    *   Colormap: `cmap='viridis'` ([`visualization/trust_metrics_visualizer.py:162`](visualization/trust_metrics_visualizer.py:162)).
    *   Histogram bins: `bins=10` ([`visualization/trust_metrics_visualizer.py:101`](visualization/trust_metrics_visualizer.py:101)).
*   **HTML Structure and CSS:** The entire HTML template and CSS styles are embedded as a multi-line string within [`generate_html_dashboard()`](visualization/trust_metrics_visualizer.py:243-392).
*   **Minimum Samples:** `min_samples` defaults to `5` in [`plot_trust_histogram()`](visualization/trust_metrics_visualizer.py:60), [`plot_confidence_vs_trust()`](visualization/trust_metrics_visualizer.py:115), and is used with this value in [`generate_trust_dashboard()`](visualization/trust_metrics_visualizer.py:206).
*   **Entity Kind Prefixes:** String prefixes like `"R"` for rules and `"V"` for variables are used to filter items (e.g., [`visualization/trust_metrics_visualizer.py:88`](visualization/trust_metrics_visualizer.py:88), [`visualization/trust_metrics_visualizer.py:143`](visualization/trust_metrics_visualizer.py:143), [`visualization/trust_metrics_visualizer.py:210-211`](visualization/trust_metrics_visualizer.py:210-211)).
*   **Top N Annotations:** `top_n = min(10, len(labels))` for annotations in [`plot_confidence_vs_trust()`](visualization/trust_metrics_visualizer.py:170).
*   **Number of Top/Bottom Entities for Evolution Plots:** Fixed at `5` in [`generate_trust_dashboard()`](visualization/trust_metrics_visualizer.py:219-220).
*   **Plot Filenames:** Specific filenames like `"trust_histogram_all.png"`, `"confidence_vs_trust_rules.png"` are hardcoded within [`generate_trust_dashboard()`](visualization/trust_metrics_visualizer.py:209-216) and for evolution plots ([`visualization/trust_metrics_visualizer.py:224`](visualization/trust_metrics_visualizer.py:224), [`visualization/trust_metrics_visualizer.py:228`](visualization/trust_metrics_visualizer.py:228)).
*   **Time Conversion:** Time is converted to hours by dividing by `3600` in [`plot_trust_evolution()`](visualization/trust_metrics_visualizer.py:36).

## 7. Coupling Points

*   **High Coupling with `core.bayesian_trust_tracker`:** The module directly accesses and uses the global `bayesian_trust_tracker` object for fetching raw trust data, timestamps, and confidence intervals. Changes to the structure or interface of `bayesian_trust_tracker` would directly impact this visualizer.
*   **High Coupling with `core.pulse_learning_log.generate_trust_report`:** The module relies on the output structure (dictionary keys like `"high_trust"`, `"low_trust"`, `"summary"`, etc.) of the `generate_trust_report` function. Changes to this report structure would break the visualizer.
*   **Implicit Data Schema:** The code assumes certain keys (`"key"`, `"trust"`, `"confidence"`, `"sample_size"`) exist in the items within the lists returned by `generate_trust_report`.
*   **Matplotlib Dependency:** Tightly coupled with Matplotlib for all plotting. Switching to a different plotting library would require significant rewrites.

## 8. Existing Tests

*   No dedicated test files (e.g., `tests/visualization/test_trust_metrics_visualizer.py`) were found.
*   The `if __name__ == "__main__":` block ([`visualization/trust_metrics_visualizer.py:432-444`](visualization/trust_metrics_visualizer.py:432-444)) provides a basic smoke test and example usage by simulating data for `bayesian_trust_tracker` and then calling `generate_trust_dashboard()`. This is useful for manual testing and demonstration but does not constitute a formal test suite (e.g., no assertions or checks for specific outputs).

**Recommendations for Testing:**
*   Create unit tests for individual plotting functions. This might involve mocking `matplotlib.pyplot` calls to check if plot functions are called with expected parameters, or by saving plots to temporary files and comparing them (though image comparison can be brittle).
*   Test `generate_html_dashboard` by checking if the output HTML contains expected elements and data based on a sample report.
*   Mock the `bayesian_trust_tracker` and `generate_trust_report` dependencies to provide controlled input data for tests.

## 9. Module Architecture and Flow

1.  **Data Acquisition:**
    *   Trust evolution data is fetched directly from `bayesian_trust_tracker.timestamps` and `bayesian_trust_tracker.get_confidence_interval()`.
    *   Aggregated trust report data (high/low trust entities, summaries) is obtained by calling `generate_trust_report()` from `core.pulse_learning_log`.

2.  **Plotting Functions:**
    *   [`plot_trust_evolution()`](visualization/trust_metrics_visualizer.py:18): Takes an entity `key` and `kind` (variable/rule). Fetches its timestamped trust values, converts times to relative hours, and plots trust score vs. time. Optionally adds confidence interval lines.
    *   [`plot_trust_histogram()`](visualization/trust_metrics_visualizer.py:60): Takes a `kind` (all/variable/rule). Fetches data from `generate_trust_report`, filters by `kind`, and plots a histogram of trust scores.
    *   [`plot_confidence_vs_trust()`](visualization/trust_metrics_visualizer.py:115): Similar to histogram, but creates a scatter plot of confidence vs. trust, with marker size indicating sample size and color indicating trust score. Annotates top N points.

3.  **Dashboard Generation Orchestration ([`generate_trust_dashboard()`](visualization/trust_metrics_visualizer.py:196)):**
    *   Creates the specified `output_dir`.
    *   Calls `generate_trust_report()` once to get the data.
    *   Calls `plot_trust_histogram()` and `plot_confidence_vs_trust()` for "all", "rules" (key starts with "R"), and "variables" (key starts with "V"), saving plots as PNGs in `output_dir`.
    *   Identifies top 5 high-trust and bottom 5 low-trust entities from the report.
    *   Calls `plot_trust_evolution()` for each of these top/bottom entities, saving plots as PNGs.
    *   Calls [`generate_html_dashboard()`](visualization/trust_metrics_visualizer.py:235) to create the `index.html` file.

4.  **HTML Report Generation ([`generate_html_dashboard()`](visualization/trust_metrics_visualizer.py:235)):**
    *   Uses a large f-string containing the HTML structure and inline CSS.
    *   Replaces placeholders in the HTML string with data from the `report` (summary statistics, tables of high/low trust entities) and paths to the generated PNG images.
    *   Writes the final HTML content to `index.html` in the `output_dir`.

5.  **Execution (if run as script):**
    *   The `if __name__ == "__main__":` block simulates data by populating `bayesian_trust_tracker` with random rule successes/failures.
    *   Then calls `generate_trust_dashboard()` to produce the example output.

## 10. Naming Conventions

*   **Functions:** Use `snake_case` (e.g., [`plot_trust_evolution`](visualization/trust_metrics_visualizer.py:18), [`generate_html_dashboard`](visualization/trust_metrics_visualizer.py:235)), which is consistent with PEP 8. Names are generally descriptive of their purpose.
*   **Variables:** Use `snake_case` (e.g., `trust_scores`, `output_dir`, `rel_times`). Names are clear and understandable.
*   **Parameters:** Use `snake_case` (e.g., `save_path`, `min_samples`).
*   **Constants/Placeholders in HTML:** Uppercase with underscores (e.g., `TOTAL_ENTITIES`, `HIGH_TRUST_TABLE`) are used as placeholders in the HTML string, which is a common convention.
*   **Module Name:** `trust_metrics_visualizer.py` is descriptive.
*   **Clarity:** The parameter `key` is used generically for a rule or variable identifier, which is acceptable given its context. The `kind` parameter (`"variable"`, `"rule"`, `"all"`) is clear.
*   **AI Assumption Errors:** No obvious naming issues suggest AI misinterpretations or significant deviations from Python community standards (PEP 8). The author tag "Pulse v0.32" suggests AI generation or significant AI contribution, but the naming itself is conventional.