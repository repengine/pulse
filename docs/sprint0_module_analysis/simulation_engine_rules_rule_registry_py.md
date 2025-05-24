# Module Analysis: `simulation_engine.rules.rule_registry`

**File Path:** [`simulation_engine/rules/rule_registry.py`](../../simulation_engine/rules/rule_registry.py)

## 1. Module Intent/Purpose

The `rule_registry.py` module serves as a centralized system for managing all types of rules (static, fingerprint, and candidate) within the Pulse simulation engine. Its primary responsibilities include:

*   Loading rules from various sources (Python modules and JSON files).
*   Storing and organizing these rules.
*   Providing methods to access, query (e.g., by type or tag), and group rules.
*   Delegating the validation of rule structures and uniqueness to the [`simulation_engine.rules.rule_coherence_checker`](../../simulation_engine/rules/rule_coherence_checker.py) module.
*   Offering functionalities to add new rules, promote candidate rules to active status, update rule trust scores, and disable rules.
*   Exporting the current set of rules to a JSON file.
*   Ensuring that all interactions with rules occur through this registry for consistency and centralized control.

## 2. Operational Status/Completeness

The module appears to be largely complete and functional for its defined scope.
*   It successfully loads rules from static definitions, fingerprint files, and candidate rule files.
*   Core functionalities like adding, promoting, updating trust, and disabling rules are implemented.
*   A command-line interface (CLI) is provided for basic administrative operations on the rules.
*   Error handling for file loading operations is present (e.g., `try-except` blocks in loading methods).
*   The presence of a debug print statement (`print(f"[DEBUG] PATHS type in rule_registry: {type(PATHS)}")` at line 18) suggests recent debugging or a temporary diagnostic check.

## 3. Implementation Gaps / Unfinished Next Steps

*   **TODOs/Placeholders:** No explicit "TODO" comments or major placeholders are visible in the provided code.
*   **Extensibility:**
    *   The CLI is functional but basic. Future enhancements could include more sophisticated querying capabilities (e.g., filtering by multiple criteria, regex matching on rule content) or bulk management operations.
    *   While `RULES_LOG_PATH` is defined, it's not actively used for file-based logging within the visible code. Formalizing logging (e.g., using the `logging` module) instead of `print` statements for errors and actions could be an improvement.
*   **Implied Features:** The system for managing different rule types (static, fingerprint, candidate) is well-defined. The promotion mechanism for candidate rules implies a workflow where rules are proposed, evaluated, and then activated, which seems to be supported.

## 4. Connections & Dependencies

### Internal Project Dependencies:
*   [`core.path_registry`](../../core/path_registry.py): Used to fetch configured file paths (e.g., `RULE_FINGERPRINTS`, `CANDIDATE_RULES`, `WORLDSTATE_LOG_DIR`) via the `PATHS` dictionary.
*   [`core.pulse_config`](../../core/pulse_config.py): Imports `MODULES_ENABLED`, though its direct usage isn't apparent in the snippet, suggesting potential conditional logic elsewhere or for future use.
*   [`simulation_engine.rules.rule_coherence_checker`](../../simulation_engine/rules/rule_coherence_checker.py): Crucial for validating rule schemas and uniqueness via the [`validate_rule_schema()`](../../simulation_engine/rules/rule_coherence_checker.py:25) function. It also imports [`get_all_rule_fingerprints_dict()`](../../simulation_engine/rules/rule_coherence_checker.py:25), though its direct use isn't visible in this module's code.
*   [`simulation_engine.rules.static_rules`](../../simulation_engine/rules/static_rules.py): This module is dynamically imported using `importlib` to load static rules. It's expected to have a `build_static_rules()` method.

### External Library Dependencies:
*   `importlib`: For dynamic module loading (used for `static_rules`).
*   `json`: For serializing and deserializing rules from/to JSON files.
*   `pathlib`: For object-oriented file system path manipulation (e.g., `FINGERPRINTS_PATH`, `CANDIDATE_RULES_PATH`).
*   `argparse`: Used to create the command-line interface for the module.

### Data Interactions:
*   **Input Files:**
    *   Reads fingerprint rules from a JSON file, typically [`simulation_engine/rules/rule_fingerprints.json`](../../simulation_engine/rules/rule_fingerprints.json) (path configurable via `PATHS["RULE_FINGERPRINTS"]`).
    *   Reads candidate rules from a JSON file, typically [`data/candidate_rules.json`](../../data/candidate_rules.json) (path configurable via `PATHS["CANDIDATE_RULES"]`).
*   **Output Files:**
    *   Can export all loaded rules to a user-specified JSON file via the [`export_rules()`](../../simulation_engine/rules/rule_registry.py:79) method or CLI.
*   **Logging:**
    *   Outputs informational messages and errors to the console using `print()` statements.
    *   The `RULES_LOG_PATH` variable is defined using `PATHS` but not explicitly used for writing to a log file in the provided code.

## 5. Function and Class Example Usages

### `RuleRegistry` Class

The `RuleRegistry` class is the core of the module.

```python
from simulation_engine.rules.rule_registry import RuleRegistry

# Initialize the registry
registry = RuleRegistry()

# Load all types of rules
registry.load_all_rules()

# Get a list of all loaded rules
all_rules = registry.rules

# Get rules of a specific type (e.g., "static")
static_rules_list = registry.get_rules_by_type("static")

# Validate the loaded rules
validation_errors = registry.validate()
if validation_errors:
    print(f"Validation Errors Found: {validation_errors}")
else:
    print("All rules are valid.")

# Add a new rule (example structure)
new_rule_data = {
    "id": "example_new_rule_001", # or "rule_id"
    "symbolic_tags": ["example_tag", "new_addition"],
    "source": "manual_entry",
    "trust_weight": 0.75,
    "enabled": True,
    "type": "candidate", # Or other valid types
    "description": "An example rule added programmatically.",
    # ... other rule-specific fields ...
}
try:
    registry.add_rule(new_rule_data)
except ValueError as e:
    print(f"Error adding rule: {e}")

# Promote a candidate rule to be an active rule
candidate_id_to_promote = "some_candidate_rule_id"
registry.promote_candidate(candidate_id_to_promote)

# Update the trust score of a rule
rule_id_for_trust_update = "existing_rule_id_007"
trust_delta = -0.1 # Decrease trust
registry.update_trust_score(rule_id_for_trust_update, trust_delta)

# Get rules by a specific symbolic tag
rules_with_tag = registry.get_rules_by_symbolic_tag("example_tag")

# Export all rules to a file
registry.export_rules("output/all_current_rules.json")
```

### Command-Line Interface (CLI) Usage

The module can be run directly from the command line:

```bash
python simulation_engine/rules/rule_registry.py --list
python simulation_engine/rules/rule_registry.py --validate
python simulation_engine/rules/rule_registry.py --export output/exported_rules_cli.json
python simulation_engine/rules/rule_registry.py --promote <candidate_rule_id>
python simulation_engine/rules/rule_registry.py --disable <rule_id>
python simulation_engine/rules/rule_registry.py --trust <rule_id> <delta_value>
```

## 6. Hardcoding Issues

*   **Default File Paths:**
    *   `STATIC_RULES_MODULE`: Hardcoded to `"simulation_engine.rules.static_rules"`. This is a structural dependency.
    *   `FINGERPRINTS_PATH`: Defaults to `"simulation_engine/rules/rule_fingerprints.json"` if `PATHS["RULE_FINGERPRINTS"]` is not set in [`core.path_registry`](../../core/path_registry.py).
    *   `CANDIDATE_RULES_PATH`: Defaults to `"data/candidate_rules.json"` if `PATHS["CANDIDATE_RULES"]` is not set.
*   **Rule Schema:** The [`add_rule()`](../../simulation_engine/rules/rule_registry.py:84) method checks for a hardcoded list of `required_fields`: `["symbolic_tags", "source", "trust_weight", "enabled", "type"]`. This defines the basic schema for a rule to be added.
*   **Default Trust Weight:** In [`update_trust_score()`](../../simulation_engine/rules/rule_registry.py:104), if a rule doesn't have a `trust_weight`, it's assumed to be `1.0` before applying the delta.

## 7. Coupling Points

*   **Rule Object Structure:** The module is tightly coupled to the expected dictionary structure of rule objects and specific keys like `"id"`, `"rule_id"`, `"type"`, `"enabled"`, `"trust_weight"`, and `"symbolic_tags"`.
*   **`core.path_registry`:** Relies on this module to provide paths for rule files. Changes to `PATHS` keys or structure could impact this module.
*   **`simulation_engine.rules.rule_coherence_checker`:** Strong coupling for rule validation. The API of [`validate_rule_schema()`](../../simulation_engine/rules/rule_coherence_checker.py:25) is a critical dependency.
*   **`simulation_engine.rules.static_rules`:** Depends on this module existing and providing a `build_static_rules()` function that returns a list of rule dictionaries.
*   **File System & Format:** Direct dependency on JSON file format for fingerprint and candidate rules, and for exporting rules.

## 8. Existing Tests

*   The existence and nature of dedicated unit tests (e.g., in a file like `tests/simulation_engine/rules/test_rule_registry.py`) cannot be confirmed without inspecting the `tests` directory.
*   The `if __name__ == "__main__":` block provides a CLI that serves as a form of integration/manual test suite for the module's core functionalities. This allows for direct invocation and verification of rule loading, validation, export, and manipulation.

## 9. Module Architecture and Flow

The `RuleRegistry` class is the central architectural component.

1.  **Initialization (`__init__`)**:
    *   Initializes empty lists: `self.rules`, `self.static_rules`, `self.fingerprint_rules`, `self.candidate_rules`.

2.  **Rule Loading (`load_all_rules()` calls individual loaders):**
    *   [`load_static_rules()`](../../simulation_engine/rules/rule_registry.py:38): Dynamically imports `STATIC_RULES_MODULE` and calls its `build_static_rules()` method. Populates `self.static_rules`.
    *   [`load_fingerprint_rules()`](../../simulation_engine/rules/rule_registry.py:46): Reads from `FINGERPRINTS_PATH` (JSON file) into `self.fingerprint_rules`.
    *   [`load_candidate_rules()`](../../simulation_engine/rules/rule_registry.py:54): Reads from `CANDIDATE_RULES_PATH` (JSON file, if it exists) into `self.candidate_rules`.
    *   After individual loading, `self.rules` is populated by concatenating these three lists.

3.  **Rule Operations:**
    *   [`get_rules_by_type(rule_type)`](../../simulation_engine/rules/rule_registry.py:71): Filters `self.rules` based on the `"type"` key.
    *   [`get_rules_by_symbolic_tag(tag)`](../../simulation_engine/rules/rule_registry.py:114): Filters `self.rules` if the tag is present in the rule's `"symbolic_tags"` list.
    *   [`validate()`](../../simulation_engine/rules/rule_registry.py:74): Prepares a dictionary of rules (keyed by "rule\_id" or "id") and passes it to [`validate_rule_schema()`](../../simulation_engine/rules/rule_coherence_checker.py:25).
    *   [`add_rule(rule)`](../../simulation_engine/rules/rule_registry.py:84): Checks for required fields and appends the rule to `self.rules`.
    *   [`promote_candidate(rule_id)`](../../simulation_engine/rules/rule_registry.py:93): Finds a rule in `self.candidate_rules`, sets `"enabled": True`, appends it to `self.rules`, and removes it from `self.candidate_rules`.
    *   [`update_trust_score(rule_id, delta)`](../../simulation_engine/rules/rule_registry.py:104): Modifies the `"trust_weight"` of a specified rule in `self.rules`.
    *   [`export_rules(path)`](../../simulation_engine/rules/rule_registry.py:79): Writes `self.rules` to a JSON file.

4.  **CLI Interaction (within `if __name__ == "__main__":`)**:
    *   Parses command-line arguments using `argparse`.
    *   Instantiates `RuleRegistry` and calls `load_all_rules()`.
    *   Executes actions based on arguments (list, validate, export, promote, disable, update trust).

## 10. Naming Conventions

*   **Class Names:** `RuleRegistry` follows PascalCase (PEP 8).
*   **Method Names:** Methods like [`load_static_rules()`](../../simulation_engine/rules/rule_registry.py:38), [`get_rules_by_type()`](../../simulation_engine/rules/rule_registry.py:71) use snake\_case (PEP 8).
*   **Variable Names:** Local variables (e.g., `static_mod`, `rule_type`) and instance variables (e.g., `self.static_rules`) use snake\_case (PEP 8).
*   **Constants:** Module-level constants like `STATIC_RULES_MODULE`, `FINGERPRINTS_PATH` use UPPER\_SNAKE\_CASE (PEP 8).
*   **Consistency:**
    *   The module consistently uses `"rule_id"` and `"id"` as potential keys for rule identification, often checking for both (e.g., `r.get("rule_id", r.get("id", str(i)))`). This suggests an attempt to handle variations in rule data.
*   **Clarity:** Names are generally descriptive and clearly indicate their purpose.
*   No significant deviations from PEP 8 or obvious AI-induced naming errors were observed. The debug print on line 18 is stylistically out of place for final code but understandable during development.