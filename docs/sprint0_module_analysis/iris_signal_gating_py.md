# Module Analysis: `iris/signal_gating.py`

## 1. Module Intent/Purpose

The primary role of the `iris/signal_gating.py` module is to act as a **Symbolic Trust Filter**. It filters signals, presumably originating from a scraper module (e.g., `scraper.py`), based on their symbolic mapping (e.g., "hope", "despair"), anomaly status, and Symbolic Trust Index (STI). The module implements rules for symbolic flood control, defines STI acceptance thresholds per symbolic domain, and handles the escalation of certain signals to the `PulseGrow` system for further processing or intake. It aims to ensure that only relevant and trustworthy signals proceed, while managing anomalous or low-trust data.

## 2. Operational Status/Completeness

The module appears largely complete for its defined scope.
- It successfully loads gating rules from an external YAML file ([`iris/signal_gating_rules.yaml`](iris/signal_gating_rules.yaml)) and includes a hardcoded fallback mechanism if the file is missing or corrupted.
- Integration with `PulseGrow` (from `memory.pulsegrow`) for escalated signals is present, with a try-except block to handle cases where `PulseGrow` might not be available.
- The core logic for accepting, suppressing, and escalating signals based on STI and anomaly counts is implemented.
- Logging of decisions is included.
- There are no explicit "TODO" comments or obvious major placeholders within the provided code, suggesting it fulfills its immediate intended functions.

## 3. Implementation Gaps / Unfinished Next Steps

- **Persistent Anomaly Counting:** The [`symbolic_anomaly_counter`](iris/signal_gating.py:55) is an in-memory dictionary. This means its counts reset if the module or application restarts, potentially weakening long-term flood control effectiveness. A persistent storage mechanism (e.g., a simple database or file) could be an improvement.
- **`PulseGrow` Integration Depth:** The current interaction with [`PulseGrow`](iris/signal_gating.py:25) is a simple registration of escalated variables ([`pulse_grow.register_variable()`](iris/signal_gating.py:87)). More sophisticated interactions, such as providing more context or receiving feedback from `PulseGrow`, might have been intended or could be future enhancements.
- **Escalation Logic Nuance:** The escalation criteria primarily rely on a hardcoded STI threshold ([`sti >= 0.4`](iris/signal_gating.py:81)). More nuanced or configurable escalation rules could be developed (e.g., based on combinations of factors, signal velocity, or specific symbolic patterns).
- **Configuration of Thresholds:** While `min_sti` and `max_anomalies` are configurable per symbolic domain via YAML, the escalation STI threshold (`0.4`) is hardcoded. This could be moved to the configuration file.

## 4. Connections & Dependencies

-   **Direct Imports from Other Project Modules:**
    *   `from memory.pulsegrow import PulseGrow` (conditionally imported, attempts to instantiate [`pulse_grow = PulseGrow()`](iris/signal_gating.py:26))
-   **External Library Dependencies:**
    *   `logging`
    *   `typing` (List, Dict, Any, Tuple)
    *   `os`
    *   `yaml`
-   **Interaction with Other Modules via Shared Data:**
    *   **Configuration File:** Reads gating rules from [`iris/signal_gating_rules.yaml`](iris/signal_gating_rules.yaml).
    *   **`PulseGrow` System:** Sends escalated signals to an instance of `PulseGrow` via its [`register_variable()`](iris/signal_gating.py:87) method.
-   **Input/Output Files:**
    *   **Input:** [`iris/signal_gating_rules.yaml`](iris/signal_gating_rules.yaml) (for configuration).
    *   **Output:** Logs decisions and errors using the `logging` module. No other direct file outputs.

## 5. Function and Class Example Usages

-   **[`load_gating_rules() -> Dict`](iris/signal_gating.py:34):**
    *   **Purpose:** Loads gating rules from [`GATING_RULES_PATH`](iris/signal_gating.py:33) ([`iris/signal_gating_rules.yaml`](iris/signal_gating_rules.yaml)). If loading fails, it returns hardcoded default rules. It also converts a 'null' key in the YAML to `None` for fallback rules.
    *   **Usage:** Called internally at module load to initialize the `GATING_RULES` global variable.
        ```python
        # Internal usage:
        # GATING_RULES = load_gating_rules()
        ```

-   **[`gate_signals(signals: List[Dict[str, Any]]) -> Tuple[List[Dict], List[Dict], List[Dict]]`](iris/signal_gating.py:57):**
    *   **Purpose:** The main function of the module. It processes a list of signal dictionaries, applying gating rules to categorize them.
    *   **Input `signals` structure:** Each dictionary in the list is expected to contain keys like:
        *   `"name"` (str): Identifier for the signal.
        *   `"symbolic"` (str/None): The symbolic domain of the signal (e.g., "hope", "despair").
        *   `"sti"` (float): The Symbolic Trust Index score (defaults to `0.0` if missing).
        *   `"anomaly"` (bool): Flag indicating if the signal is considered an anomaly (defaults to `False` if missing).
    *   **Output:** Returns a tuple containing three lists: `(accepted_signals, suppressed_signals, escalated_signals)`.
    *   **Example Usage:**
        ```python
        # from iris.signal_gating import gate_signals # Assuming appropriate import
        
        signals_to_process = [
            {"name": "HighTrustSignal", "symbolic": "hope", "sti": 0.85, "anomaly": False},
            {"name": "LowTrustSignal", "symbolic": "despair", "sti": 0.2, "anomaly": False},
            {"name": "AnomalousSignal", "symbolic": "hope", "sti": 0.6, "anomaly": True},
            {"name": "EscalationCandidate", "symbolic": "rage", "sti": 0.45, "anomaly": False},
            {"name": "UnknownSymbolicSignal", "symbolic": "unknown", "sti": 0.55, "anomaly": False}
        ]
        
        accepted, suppressed, escalated = gate_signals(signals_to_process)
        
        # print(f"Accepted: {accepted}")
        # print(f"Suppressed: {suppressed}")
        # print(f"Escalated: {escalated}")
        ```

## 6. Hardcoding Issues

-   **Fallback Gating Rules:** If [`signal_gating_rules.yaml`](iris/signal_gating_rules.yaml) fails to load (lines [`43-51`](iris/signal_gating.py:43-51)), the module uses hardcoded default rules:
    *   `"hope": {"min_sti": 0.5, "max_anomalies": 2}`
    *   `"despair": {"min_sti": 0.6, "max_anomalies": 1}`
    *   `"rage": {"min_sti": 0.7, "max_anomalies": 1}`
    *   `"fatigue": {"min_sti": 0.4, "max_anomalies": 3}`
    *   `None: {"min_sti": 0.5, "max_anomalies": 2}` (default for unknown/None symbolics)
-   **STI Threshold for Escalation:** The STI threshold for a signal to be escalated (if not accepted) is hardcoded at `0.4` ([`elif sti >= 0.4:`](iris/signal_gating.py:81)). This could be made configurable.
-   **Default STI Value:** If the `"sti"` key is missing in an incoming signal, it defaults to `0.0` ([`sti = sig.get("sti", 0.0)`](iris/signal_gating.py:67)).
-   **Default Anomaly Value:** If the `"anomaly"` key is missing, it defaults to `False` ([`anomaly = sig.get("anomaly", False)`](iris/signal_gating.py:68)).
-   **PulseGrow Escalation Reason:** The reason string sent to `PulseGrow` upon escalation is hardcoded: `"Escalated from signal_gating"` ([line 89](iris/signal_gating.py:89)).
-   **Default Signal Name for PulseGrow:** If a signal's `name` is not a valid string or is missing during `PulseGrow` escalation, it defaults to `"unknown_signal"` ([line 86](iris/signal_gating.py:86)).

## 7. Coupling Points

-   **[`iris/signal_gating_rules.yaml`](iris/signal_gating_rules.yaml):** The module is tightly coupled to the existence and structure of this YAML file for its primary operational rules. The fallback mechanism mitigates complete failure but relies on potentially outdated hardcoded rules.
-   **`memory.pulsegrow.PulseGrow`:** The module is coupled to the `PulseGrow` class from the `memory` module for escalating signals. It includes a graceful degradation (setting `pulse_grow` to `None`) if the import fails.
-   **Input Signal Structure:** The [`gate_signals`](iris/signal_gating.py:57) function expects incoming signals to be a list of dictionaries, each with specific keys (`"name"`, `"symbolic"`, `"sti"`, `"anomaly"`). Changes to this data contract from upstream modules (e.g., `scraper.py`) would break the gating logic.

## 8. Existing Tests

-   Based on the provided file list and common project structures, there is no apparent dedicated test file for this module (e.g., `tests/iris/test_signal_gating.py` or `tests/test_signal_gating.py`).
-   **Assessment:** It is likely that specific unit tests for `signal_gating.py` are missing or are located in a place not immediately obvious from the context. Comprehensive testing for various signal conditions, rule configurations, and `PulseGrow` interactions would be beneficial.

## 9. Module Architecture and Flow

1.  **Initialization Phase:**
    *   A logger instance is obtained.
    *   The path to the gating rules YAML file ([`GATING_RULES_PATH`](iris/signal_gating.py:33)) is constructed.
    *   The [`load_gating_rules()`](iris/signal_gating.py:34) function is invoked to parse the YAML file or use hardcoded defaults. The result is stored in the global `GATING_RULES` dictionary.
    *   An attempt is made to import `PulseGrow` from [`memory.pulsegrow`](iris/signal_gating.py:25) and instantiate it. If this fails, `pulse_grow` is set to `None`.
    *   An empty dictionary, [`symbolic_anomaly_counter`](iris/signal_gating.py:55), is initialized to track anomalies per symbolic type for flood control.

2.  **Signal Processing ([`gate_signals()`](iris/signal_gating.py:57) function):**
    *   The function takes a list of `signals` (each a dictionary) as input.
    *   It initializes three empty lists: `accepted`, `suppressed`, and `escalated`.
    *   It iterates through each `sig` in the `signals` list:
        a.  Extracts `name`, `symbolic`, `sti` (defaulting to `0.0`), and `anomaly` (defaulting to `False`) from the signal.
        b.  Retrieves the applicable `rules` from `GATING_RULES` based on the signal's `symbolic` value. If the symbolic type is not found, it uses rules associated with the `None` key (default rules).
        c.  **Anomaly Tracking:** If `sig` is an `anomaly`, the `symbolic_anomaly_counter` for its `symbolic` type is incremented.
        d.  **Gating Decision Logic:**
            i.  `too_anomalous` flag is set if the `symbolic_anomaly_counter` for the current `symbolic` type exceeds `rules["max_anomalies"]`.
            ii. If `sti` is greater than or equal to `rules["min_sti"]` AND the signal is not `too_anomalous`, it's added to the `accepted` list.
            iii. Else, if `sti` is greater than or equal to `0.4` (hardcoded threshold), it's added to the `escalated` list. If `pulse_grow` is available, an attempt is made to register the variable with `PulseGrow`.
            iv. Otherwise (low STI or too anomalous without meeting escalation criteria), the signal is added to the `suppressed` list.
        e.  A log message is generated indicating the decision (accepted, suppressed, or escalated) for the signal.
    *   The function returns the `accepted`, `suppressed`, and `escalated` lists.

## 10. Naming Conventions

-   **Module Name:** `signal_gating.py` (snake_case, standard Python).
-   **Function Names:** [`load_gating_rules`](iris/signal_gating.py:34), [`gate_signals`](iris/signal_gating.py:57) (snake_case, PEP 8 compliant, descriptive).
-   **Constant Variables:** `GATING_RULES_PATH`, `GATING_RULES` (UPPER_SNAKE_CASE, PEP 8 compliant).
-   **Global Variables:** [`symbolic_anomaly_counter`](iris/signal_gating.py:55) (snake_case).
-   **Local Variables:** `logger`, `pulse_grow`, `signals`, `accepted`, `suppressed`, `escalated`, `sig`, `name`, `symbolic`, `sti`, `anomaly`, `rules`, `too_anomalous`, `safe_name` (snake_case or descriptive, generally PEP 8 compliant).
-   **YAML Keys (in code):** `"min_sti"`, `"max_anomalies"` (snake_case). Symbolic keys like `"hope"`, `"despair"` are descriptive. The use of `'null'` in YAML (converted to `None` in Python) for default rules is a clear convention.
-   **Overall:** Naming conventions are generally consistent and adhere well to PEP 8. Variable and function names are descriptive of their purpose. There are no obvious AI assumption errors or significant deviations from standard Python practices. The terminology used (e.g., "STI", "symbolic", "gating") is specific to the module's domain and applied consistently.