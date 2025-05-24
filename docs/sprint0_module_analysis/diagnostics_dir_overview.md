# Overview of the `diagnostics/` Directory

## Directory Path
`diagnostics/`

## Overall Purpose & Role
The `diagnostics/` directory houses tools and utilities designed to analyze, explain, and monitor aspects of the Pulse system's simulation and modeling components, particularly focusing on the "gravity model" and its interactions with the "causal model." These tools aid in understanding model behavior, debugging, and ensuring the stability and reliability of the system's predictions and corrections.

## Key Diagnostic Utilities/Data Provided
The directory contains the following key utilities:

1.  **[`diagnostics/gravity_explainer.py`](diagnostics/gravity_explainer.py:1):**
    *   **Purpose:** Provides textual and HTML-based explanations and visualizations for "gravity corrections" applied during simulations.
    *   **Functionality:** Helps users understand why specific corrections were applied to variables by detailing the contribution of various "symbolic pillars" and their underlying data points. It can compare causal vs. gravity deltas over time and export explanation data to JSON.

2.  **[`diagnostics/shadow_model_monitor.py`](diagnostics/shadow_model_monitor.py:1):**
    *   **Purpose:** Monitors the influence of the "gravity model" on critical system variables.
    *   **Functionality:** Tracks the proportion of variance explained by the gravity model compared to the causal model over a rolling window. It triggers an alert if the gravity model's influence exceeds a predefined threshold for any critical variable, indicating potential over-reliance on corrective mechanisms.

3.  **[`diagnostics/dependency_graph.dot`](diagnostics/dependency_graph.dot:1):**
    *   **Purpose:** Intended for visualizing dependencies within the system or specific modules.
    *   **Functionality:** A `.dot` file format, typically used with Graphviz to generate visual graphs. Currently, the file is empty (`digraph dependencies {}`), suggesting it's a placeholder or an unused/incomplete feature.

## Common Themes/Patterns
*   **Focus on "Gravity Model":** Both Python scripts are heavily centered around understanding and monitoring the "gravity model," "gravity corrections," and "symbolic pillars." This suggests that the gravity model is a significant component requiring specialized diagnostic tools.
*   **Simulation Analysis:** The tools are designed to work with simulation trace data, indicating their use in post-simulation analysis and debugging.
*   **Monitoring and Alerting:** [`diagnostics/shadow_model_monitor.py`](diagnostics/shadow_model_monitor.py:1) includes functionality for setting thresholds and triggering alerts, highlighting a need for proactive monitoring of model behavior.
*   **Explainability:** [`diagnostics/gravity_explainer.py`](diagnostics/gravity_explainer.py:1) emphasizes making the model's decisions (specifically gravity corrections) understandable to users.
*   **Visualization:** Both Python scripts incorporate visualization capabilities (HTML, Matplotlib/Plotly) to aid in the interpretation of complex data. The `.dot` file also points to visualization as a theme.

## Support for System Understanding/Debugging
These utilities provide crucial support for:
*   **Understanding Model Behavior:** By explaining gravity corrections and pillar contributions, developers and analysts can gain insights into how the symbolic gravity system influences simulation outcomes.
*   **Debugging Issues:** If simulations produce unexpected results, these tools can help pinpoint whether the gravity model is a contributing factor and why. For instance, identifying which pillars are driving a large correction.
*   **Monitoring System Health:** The `ShadowModelMonitor` helps ensure that the gravity model doesn't overshadow the primary causal model, maintaining a balance in the system's predictive mechanisms.
*   **Validating Model Changes:** When updates are made to the gravity model or related components, these diagnostic tools can be used to assess the impact of those changes.
*   **Visualizing Dependencies:** The [`diagnostics/dependency_graph.dot`](diagnostics/dependency_graph.dot:1) file, if populated, would help in understanding relationships between different parts of the system.

## General Observations & Impressions
*   The `diagnostics/` directory appears to be a specialized toolkit for a core, complex part of the Pulse system related to "gravity" and "symbolic pillars."
*   The tools are geared towards developers or analysts with a deep understanding of the system's internal modeling concepts.
*   The presence of an empty [`diagnostics/dependency_graph.dot`](diagnostics/dependency_graph.dot:1) file might indicate an incomplete or deprecated feature for visualizing broader system dependencies.
*   The emphasis on explainability and monitoring suggests a mature approach to managing a complex modeling component.