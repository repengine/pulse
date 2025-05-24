# Module Analysis: symbolic_system.gravity.symbolic_pillars

**File Path:** [`symbolic_system/gravity/symbolic_pillars.py`](symbolic_system/gravity/symbolic_pillars.py:)

## Module Intent/Purpose

This module implements the concept of "Symbolic Pillars." These pillars are dynamic data structures representing abstract symbolic concepts (e.g., Hope, Despair). They function as vertically stacked data points that can grow or shrink in intensity. Collectively, these pillars form the basis of the "Symbolic Gravity Fabric," and their cumulative state and interactions are intended to influence simulation corrections or other dynamics within the larger system.

## Operational Status/Completeness

The module appears to be largely complete and operational for its defined scope. It provides two main classes, [`SymbolicPillar`](symbolic_system/gravity/symbolic_pillars.py:24) and [`SymbolicPillarSystem`](symbolic_system/gravity/symbolic_pillars.py:278), with comprehensive methods for managing individual pillars and the overall system. This includes functionality for adding data, decay, interactions, state querying, and serialization. An example usage block (`if __name__ == "__main__":`) demonstrates its core functionality. No explicit TODOs or major placeholders are evident in the core logic.

## Implementation Gaps / Unfinished Next Steps

*   **Advanced Decay Models:** The current decay mechanism in [`SymbolicPillar.decay()`](symbolic_system/gravity/symbolic_pillars.py:121) is linear. Future enhancements could include more sophisticated models (e.g., exponential, time-dependent).
*   **Dynamic Basis Functions:** A comment in [`SymbolicPillar.get_basis_value()`](symbolic_system/gravity/symbolic_pillars.py:203) suggests the potential for dynamic basis functions where data point weights could vary based on recency or other factors.
*   **Enhanced Configuration:** While the [`SymbolicPillarSystem`](symbolic_system/gravity/symbolic_pillars.py:278) accepts a configuration object, its current use is limited. Expanding this could allow for more granular control over pillar behavior, interaction dynamics, and thresholds.
*   **Data Point Specificity:** The `data_point: Any` typing is flexible but could be refined with more specific types or handlers for structured data if required by the application.
*   **Dynamic Interaction Matrix:** The `interaction_matrix` is currently set manually. A significant extension would be to allow these interactions to be learned or adapted dynamically by the system.
*   **Automated Pillar Management:** Pillars are registered manually. Future development could explore mechanisms for automatic discovery or registration of pillars based on system events or data patterns.
*   **Configurable Thresholds:** Several internal thresholds (e.g., history length, growth rate calculation window, visualization parameters) are hardcoded and could be made configurable.

## Connections & Dependencies

*   **Internal Project Imports:**
    *   [`symbolic_system.symbolic_utils.symbolic_tension_score`](symbolic_system/symbolic_utils.py:) (conditionally used, with a fallback)
    *   [`symbolic_system.gravity.visualization.visualize_gravity_fabric`](symbolic_system/gravity/visualization.py:) (used in the `if __name__ == "__main__":` example)
*   **External Library Dependencies:**
    *   `logging`
    *   `math`
    *   `numpy` (imported as `np`, though not directly used in the visible code)
    *   `typing` (Dict, List, Tuple, Any, Optional, Set, Union)
    *   `datetime` (datetime, timedelta)
    *   `collections` (deque, though not directly used in the visible code)
*   **Shared Data Interactions:**
    *   The system is designed to output its state (e.g., pillar intensities via [`SymbolicPillarSystem.as_dict()`](symbolic_system/gravity/symbolic_pillars.py:723)) for other components, notably a "residual gravity engine."
    *   Interacts with a configuration system via an optional `config` object passed to [`SymbolicPillarSystem`](symbolic_system/gravity/symbolic_pillars.py:278).
*   **Input/Output Files:**
    *   Uses the `logging` module for output.
    *   Serialization methods ([`to_dict()`](symbolic_system/gravity/symbolic_pillars.py:230), [`from_dict()`](symbolic_system/gravity/symbolic_pillars.py:760)) suggest potential for saving/loading state from files, though file I/O is not directly handled by this module.

## Function and Class Example Usages

### [`SymbolicPillar`](symbolic_system/gravity/symbolic_pillars.py:24)

```python
# Initialization
pillar = SymbolicPillar(name="hope", initial_intensity=0.7, max_capacity=1.0)

# Adding data
pillar.add_data_point(data_point="Significant positive event", weight=0.3)

# Applying decay
decay_amount = pillar.decay(decay_rate=0.01)

# Setting intensity directly
pillar.set_intensity(0.5)

# Getting information
current_intensity = pillar.intensity
growth = pillar.get_growth_rate()
pillar_dict = pillar.to_dict()
```

### [`SymbolicPillarSystem`](symbolic_system/gravity/symbolic_pillars.py:278)

(Example from the module's `if __name__ == "__main__":` block)
```python
system = SymbolicPillarSystem()

# Register pillars
system.register_pillar("hope", 0.7)
system.register_pillar("despair", 0.3)
system.register_pillar("rage", 0.5)

# Set interactions
system.set_interaction("hope", "despair", -0.5)  # Opposing
system.set_interaction("hope", "rage", -0.3)     # Opposing

# Advance system state
system.step()

# Get system state
basis_vector = system.get_basis_vector()
# print("Basis vector:", basis_vector)

visualization_data = system.generate_visualization_data()
# print("Fabric metrics:", visualization_data["fabric_metrics"])

system_dict = system.to_dict()
# new_system = SymbolicPillarSystem.from_dict(system_dict)
```

## Hardcoding Issues

*   **History Length Caps:** The intensity history for pillars is capped at 100 entries (e.g., [`SymbolicPillar._update_intensity()`](symbolic_system/gravity/symbolic_pillars.py:91) line 115).
*   **Growth Rate Calculation:** The window for growth rate calculation in [`SymbolicPillar.get_growth_rate()`](symbolic_system/gravity/symbolic_pillars.py:178) uses the last 5 history points and a normalization factor of 10.
*   **Serialization Details:** In [`SymbolicPillar.to_dict()`](symbolic_system/gravity/symbolic_pillars.py:230), the number of recent data points (10) and string truncation length (50 characters) are fixed. The height scaling factor for visualization (100) is also hardcoded.
*   **Default Parameters:** Default `decay_rate` (0.01) and `interaction_strength` (0.1) in [`SymbolicPillarSystem`](symbolic_system/gravity/symbolic_pillars.py:278) if no configuration is provided.
*   **Numerical Thresholds:** A small epsilon (1e-6) is used in [`SymbolicPillarSystem._apply_interactions()`](symbolic_system/gravity/symbolic_pillars.py:421) to check for near-zero intensities.
*   **Visualization Parameters:**
    *   Number of top pillars for visualization (`n=10` in [`SymbolicPillarSystem.generate_visualization_data()`](symbolic_system/gravity/symbolic_pillars.py:641)).
    *   Number of recent data points for timeline (`20`).
    *   Thresholds for `growth_indicator` (0.1).
    *   Threshold for significant interactions (0.01).
*   **Fallback Tension Score:** The fallback implementation of [`SymbolicPillarSystem.symbolic_tension_score()`](symbolic_system/gravity/symbolic_pillars.py:602) hardcodes specific pillar names ("hope", "despair", "rage", "trust", "fatigue") and their interaction logic.

## Coupling Points

*   **`symbolic_system.symbolic_utils.symbolic_tension_score`:** The module is coupled with this utility for its primary tension calculation, though a fallback is provided.
*   **`symbolic_system.gravity.visualization.visualize_gravity_fabric`:** Indicates coupling with a specific visualization component.
*   **Configuration Object:** The structure and expected attributes (`decay_rate`, `interaction_strength`, `log_level`) of the `config` object passed to [`SymbolicPillarSystem`](symbolic_system/gravity/symbolic_pillars.py:278) create a dependency.
*   **Residual Gravity Engine:** The [`SymbolicPillarSystem.as_dict()`](symbolic_system/gravity/symbolic_pillars.py:723) method is explicitly designed for a "residual gravity engine," implying a functional coupling.

## Existing Tests

*   The module contains an `if __name__ == "__main__":` block (lines 798-828) which serves as a basic execution and integration test, demonstrating core functionalities like pillar registration, interaction setting, system stepping, and data retrieval for basis vectors and visualization.
*   No dedicated test file (e.g., `tests/symbolic_system/gravity/test_symbolic_pillars.py`) was found in the `tests/symbolic_system/gravity/` directory. Comprehensive unit tests are recommended.

## Module Architecture and Flow

*   **Architecture:**
    *   **[`SymbolicPillar`](symbolic_system/gravity/symbolic_pillars.py:24) Class:** Encapsulates a single symbolic concept. It manages its intensity, the data points contributing to this intensity, its rate of change (velocity), and a history of its intensity. Key methods involve adding data, applying decay, and calculating its "basis value" (current intensity).
    *   **[`SymbolicPillarSystem`](symbolic_system/gravity/symbolic_pillars.py:278) Class:** Orchestrates a collection of [`SymbolicPillar`](symbolic_system/gravity/symbolic_pillars.py:24) instances. It handles their registration, defines interactions between them using an `interaction_matrix`, and manages system-wide temporal progression via a `step()` method. This method applies decay to all pillars and then processes their interactions. The system can provide various views of its state, including a collective "basis vector," data for visualization, and a "symbolic tension score." It also supports serialization and deserialization.
*   **Primary Data/Control Flow:**
    1.  A [`SymbolicPillarSystem`](symbolic_system/gravity/symbolic_pillars.py:278) instance is created, optionally configured.
    2.  Individual [`SymbolicPillar`](symbolic_system/gravity/symbolic_pillars.py:24)s are registered within the system.
    3.  Interactions (enhancing or opposing) between pairs of pillars are defined in the system's `interaction_matrix`.
    4.  External events or data feeds lead to updates in individual pillars, either by adding weighted `data_points` or by directly setting their `intensity`. This changes the pillar's internal state.
    5.  The `SymbolicPillarSystem.step()` method is called, typically periodically:
        *   Each pillar's intensity is reduced by a `decay_rate`.
        *   Interactions are applied: the intensity of interacting pillars can be adjusted based on their current intensities and the defined `interaction_strength` and type (enhancing/opposing).
    6.  The system's state (individual pillar intensities, overall tension, etc.) can be queried at any time for analysis, visualization, or to feed into other system components (like the "residual gravity engine").

## Naming Conventions

*   The module generally adheres to PEP 8 standards: `CapWords` for class names ([`SymbolicPillar`](symbolic_system/gravity/symbolic_pillars.py:24), [`SymbolicPillarSystem`](symbolic_system/gravity/symbolic_pillars.py:278)) and `snake_case` for methods, functions, and variables.
*   Names are largely descriptive and clear (e.g., `initial_intensity`, `max_capacity`, `interaction_matrix`, `get_basis_vector`).
*   The use of `Any` for `data_point` in [`SymbolicPillar.add_data_point()`](symbolic_system/gravity/symbolic_pillars.py:75) is a common practice for highly generic components but might lack specificity for some use cases.
*   Methods like [`to_dict()`](symbolic_system/gravity/symbolic_pillars.py:230) and [`from_dict()`](symbolic_system/gravity/symbolic_pillars.py:760) follow common Python conventions for serialization. The distinction of [`as_dict()`](symbolic_system/gravity/symbolic_pillars.py:723) for a specific output format is also clear.
*   No significant deviations from project standards or potential AI assumption errors in naming were observed.