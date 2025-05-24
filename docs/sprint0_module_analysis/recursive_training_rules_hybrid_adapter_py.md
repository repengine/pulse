# Module Analysis: `recursive_training.rules.hybrid_adapter`

## 1. Module Intent/Purpose

The primary role of the [`recursive_training/rules/hybrid_adapter.py`](../../recursive_training/rules/hybrid_adapter.py) module is to provide a flexible mechanism for converting rule representations. It features the [`HybridRuleAdapter`](../../recursive_training/rules/hybrid_adapter.py:76) class, which acts as a bridge between dictionary-based rule formats and strongly-typed, object-oriented (dataclass) representations. This allows the system to maintain compatibility with components that may expect dictionary-based rules while enabling new development to leverage the benefits of dataclasses, such as type hinting, validation, and easier maintenance.

## 2. Operational Status/Completeness

The module appears to be largely functional and complete for its core purpose of rule conversion and adaptation.
- Key functionalities like converting dictionaries to rule objects ([`to_object`](../../recursive_training/rules/hybrid_adapter.py:184)) and vice-versa ([`to_dict`](../../recursive_training/rules/hybrid_adapter.py:251)) are implemented.
- Registration of custom rule, condition, and action classes is supported ([`register_rule_class`](../../recursive_training/rules/hybrid_adapter.py:142), [`register_condition_class`](../../recursive_training/rules/hybrid_adapter.py:156), [`register_action_class`](../../recursive_training/rules/hybrid_adapter.py:170)).
- Basic validation ([`validate_rule`](../../recursive_training/rules/hybrid_adapter.py:376)) is present.
- The cost tracking mechanism ([`_track_conversion_cost`](../../recursive_training/rules/hybrid_adapter.py:328)) is explicitly noted as a "placeholder implementation" and would require further development for production use.

## 3. Implementation Gaps / Unfinished Next Steps

- **Cost Tracking:** The most significant unfinished part is the [`_track_conversion_cost`](../../recursive_training/rules/hybrid_adapter.py:328) method. The current implementation is a placeholder and does not reflect actual resource usage or complexity accurately. This needs to be replaced with a more robust cost calculation and tracking mechanism, potentially integrating more deeply with the [`CostController`](../../recursive_training/integration/cost_controller.py).
- **Specific Rule Types:** While the adapter supports registration of custom rule types, the module itself only defines generic base dataclasses ([`Rule`](../../recursive_training/rules/hybrid_adapter.py:55), [`RuleCondition`](../../recursive_training/rules/hybrid_adapter.py:26), [`RuleAction`](../../recursive_training/rules/hybrid_adapter.py:34)). A mature system would likely have more domain-specific rule component classes defined elsewhere and registered with this adapter.
- **Advanced Validation:** The current validation ([`validate_rule`](../../recursive_training/rules/hybrid_adapter.py:376)) is based on successful conversion. More sophisticated, schema-based, or business-logic-specific validation could be an extension.

## 4. Connections & Dependencies

### Internal Project Dependencies:
- [`recursive_training.integration.cost_controller`](../../recursive_training/integration/cost_controller.py): Imports [`get_cost_controller`](../../recursive_training/integration/cost_controller.py:0) for tracking the "cost" of conversion operations.
- [`recursive_training.config.default_config`](../../recursive_training/config/default_config.py): Imports [`get_config`](../../recursive_training/config/default_config.py:0) to fetch configuration settings specific to hybrid rules, such as `enable_dict_compatibility` and `prefer_object_representation`.

### External Library Dependencies:
- `logging`: Standard Python library for logging messages.
- `json`: Standard Python library for JSON processing (used in placeholder cost tracking).
- `inspect`: Standard Python library for introspection (used for checking dataclass types and hints).
- `datetime` (from `datetime`): Standard Python library for timestamping metadata.
- `typing`: Standard Python library for type hints (`Any`, `Dict`, `List`, `Optional`, `Union`, `Type`, `TypeVar`, `get_type_hints`).
- `dataclasses`: Standard Python library for creating dataclasses (`dataclass`, `field`, `asdict`, `is_dataclass`).

### Interactions:
- The module interacts with the configuration system to determine its behavior regarding preferred rule representation.
- It interacts with the cost control system by reporting (placeholder) costs for conversion operations.
- It does not directly interact with files, databases, or message queues for its primary function, but operates on in-memory Python objects and dictionaries.

## 5. Function and Class Example Usages

### [`HybridRuleAdapter`](../../recursive_training/rules/hybrid_adapter.py:76)
This is the main class for converting rules.

```python
from recursive_training.rules.hybrid_adapter import get_hybrid_adapter, Rule, RuleCondition, RuleAction

# Get the singleton adapter instance
adapter = get_hybrid_adapter()

# Example dictionary rule
dict_rule = {
    "id": "sample_rule_001",
    "type": "data_validation",
    "conditions": [
        {"type": "value_greater_than", "parameters": {"field_name": "temperature", "threshold": 100}}
    ],
    "actions": [
        {"type": "log_alert", "parameters": {"level": "warning", "message": "Temperature threshold exceeded"}}
    ],
    "priority": 5,
    "description": "Logs a warning if temperature exceeds 100.",
    "enabled": True
}

# Convert dictionary to Rule object
try:
    rule_object = adapter.to_object(dict_rule)
    print(f"Converted to object: ID - {rule_object.id}, Type - {rule_object.type}")
    print(f"First condition type: {rule_object.conditions[0].type}")

    # Convert Rule object back to dictionary
    new_dict_rule = adapter.to_dict(rule_object)
    print(f"Converted back to dict: {new_dict_rule['id']}")

    # Validate a rule (can be dict or object)
    if adapter.validate_rule(rule_object):
        print("Rule object is valid.")
    if adapter.validate_rule(dict_rule):
        print("Rule dictionary is valid.")

except ConversionError as e:
    print(f"Conversion failed: {e}")

# Registering custom classes (conceptual)
# @dataclass
# class MyCustomCondition(RuleCondition):
#     custom_param: str = "default"
#
# adapter.register_condition_class("my_custom_type", MyCustomCondition)
```

### Dataclasses: [`Rule`](../../recursive_training/rules/hybrid_adapter.py:55), [`RuleCondition`](../../recursive_training/rules/hybrid_adapter.py:26), [`RuleAction`](../../recursive_training/rules/hybrid_adapter.py:34), [`RuleMetadata`](../../recursive_training/rules/hybrid_adapter.py:42)
These are used to structure rule data in an object-oriented manner.

```python
from recursive_training.rules.hybrid_adapter import Rule, RuleCondition, RuleAction, RuleMetadata
from datetime import datetime

# Creating rule components
condition1 = RuleCondition(type="sensor_reading", parameters={"sensor_id": "temp_A", "operator": ">", "value": 30.0})
action1 = RuleAction(type="trigger_alarm", parameters={"alarm_level": "high", "target_system": "HVAC"})
metadata = RuleMetadata(
    created_at=datetime.now().isoformat(),
    updated_at=datetime.now().isoformat(),
    version=2,
    status="active",
    generator="manual_v2",
    source="engineering_spec_rev2",
    tags=["safety", "temperature_control"]
)

# Creating a full Rule object
complex_rule = Rule(
    id="TC-005",
    type="temperature_safety_interlock",
    conditions=[condition1],
    actions=[action1],
    priority=10,
    description="High priority safety interlock for temperature excursions.",
    metadata=metadata,
    enabled=True
)

# Accessing data
print(f"Rule ID: {complex_rule.id}")
print(f"Condition type: {complex_rule.conditions[0].type}")
print(f"Metadata source: {complex_rule.metadata.source}")

# Convert to dictionary
rule_dict_representation = complex_rule.to_dict()
print(f"Dictionary representation 'enabled' status: {rule_dict_representation['enabled']}")
```

## 6. Hardcoding Issues

- **Default Rule Type:** The string `"generic"` is hardcoded as a fallback rule type if a specific type is not found during conversion in [`HybridRuleAdapter.to_object()`](../../recursive_training/rules/hybrid_adapter.py:199) and in the initial `rule_classes` dictionary ([`HybridRuleAdapter.__init__()`](../../recursive_training/rules/hybrid_adapter.py:123)).
- **Default Metadata Status:** [`RuleMetadata.status`](../../recursive_training/rules/hybrid_adapter.py:47) defaults to `"active"`.
- **Cost Tracking Magic Numbers:** The [`_track_conversion_cost`](../../recursive_training/rules/hybrid_adapter.py:328) method uses hardcoded numerical values for calculating complexity and cost (e.g., `1000` for KB conversion, `0.0001` for cost factors). This is explicitly a placeholder.
- **Logger Name:** The logger is named `"HybridRuleAdapter"` ([`HybridRuleAdapter.__init__()`](../../recursive_training/rules/hybrid_adapter.py:113)). While common, this could be configurable if desired.

## 7. Coupling Points

- **Configuration System:** The adapter is coupled to the project's configuration system via [`get_config().hybrid_rules`](../../recursive_training/config/default_config.py:0) to determine its operational preferences.
- **Cost Controller:** It's coupled to the [`CostController`](../../recursive_training/integration/cost_controller.py:0) (obtained via [`get_cost_controller()`](../../recursive_training/integration/cost_controller.py:0)) for reporting conversion costs. Changes in the cost controller's API could impact this module.
- **Dataclasses Module:** The core functionality heavily relies on Python's `dataclasses` module. Any significant changes or deprecations in `dataclasses` could affect this adapter.
- **Registered Classes:** The adapter's behavior depends on the structure and types of dataclasses registered with it. If these external classes change their structure (e.g., field names, types) without corresponding updates to the data being converted, errors will occur.

## 8. Existing Tests

A test file exists for this module at [`tests/recursive_training/rules/test_hybrid_adapter.py`](../../tests/recursive_training/rules/test_hybrid_adapter.py). This indicates that unit tests are in place to verify the functionality of the `HybridRuleAdapter` and its associated components. The specific coverage and depth of these tests would require examination of the test file itself.

## 9. Module Architecture and Flow

The module is architected around the singleton [`HybridRuleAdapter`](../../recursive_training/rules/hybrid_adapter.py:76) class.
1.  **Dataclass Definitions:** It starts by defining several dataclasses ([`RuleCondition`](../../recursive_training/rules/hybrid_adapter.py:26), [`RuleAction`](../../recursive_training/rules/hybrid_adapter.py:34), [`RuleMetadata`](../../recursive_training/rules/hybrid_adapter.py:42), and [`Rule`](../../recursive_training/rules/hybrid_adapter.py:55)) that model the object-oriented representation of a rule.
2.  **Adapter Initialization ([`__init__`](../../recursive_training/rules/hybrid_adapter.py:106)):**
    *   Sets up logging.
    *   Loads configuration (e.g., `prefer_object_representation`).
    *   Initializes a [`CostController`](../../recursive_training/integration/cost_controller.py:0) instance.
    *   Initializes dictionaries (`rule_classes`, `condition_classes`, `action_classes`) to store registered custom types, with a default "generic" [`Rule`](../../recursive_training/rules/hybrid_adapter.py:55) type.
3.  **Class Registration:** Methods like [`register_rule_class()`](../../recursive_training/rules/hybrid_adapter.py:142) allow other parts of the system to register their specific dataclass types for rules, conditions, and actions, associating them with a string identifier (e.g., "my_custom_rule_type").
4.  **Dictionary to Object Conversion ([`to_object()`](../../recursive_training/rules/hybrid_adapter.py:184)):**
    *   Takes a rule dictionary as input.
    *   Determines the appropriate rule dataclass based on the `type` field in the dictionary or falls back to the registered class or the generic [`Rule`](../../recursive_training/rules/hybrid_adapter.py:55).
    *   Recursively converts nested "conditions", "actions", and "metadata" dictionaries into their respective dataclass objects using the [`_dict_to_dataclass()`](../../recursive_training/rules/hybrid_adapter.py:282) helper. This helper intelligently handles field types and nested dataclasses.
    *   Instantiates the main rule object with the processed arguments.
    *   Tracks the (placeholder) cost of the operation.
5.  **Object to Dictionary Conversion ([`to_dict()`](../../recursive_training/rules/hybrid_adapter.py:251)):**
    *   Takes a rule dataclass object as input.
    *   Uses `dataclasses.asdict()` for a straightforward conversion.
    *   Tracks the (placeholder) cost.
6.  **Adaptation & Validation:**
    *   [`adapt_rule()`](../../recursive_training/rules/hybrid_adapter.py:353): Converts a rule to the preferred format (dict or object) based on configuration.
    *   [`validate_rule()`](../../recursive_training/rules/hybrid_adapter.py:376): Validates a rule by attempting to convert it (dict to object, or object to dict and back to object).
7.  **Singleton Access:** The [`get_hybrid_adapter()`](../../recursive_training/rules/hybrid_adapter.py:409) function provides global access to the singleton instance of [`HybridRuleAdapter`](../../recursive_training/rules/hybrid_adapter.py:76).

The overall flow is designed to be flexible, allowing the system to work with rules in two formats and to extend the types of rules it understands through registration.

## 10. Naming Conventions

- **Classes:** Use `CapWords` (e.g., [`HybridRuleAdapter`](../../recursive_training/rules/hybrid_adapter.py:76), [`RuleCondition`](../../recursive_training/rules/hybrid_adapter.py:26)), adhering to PEP 8.
- **Methods and Functions:** Use `snake_case` (e.g., [`to_object`](../../recursive_training/rules/hybrid_adapter.py:184), [`_track_conversion_cost`](../../recursive_training/rules/hybrid_adapter.py:328), [`get_hybrid_adapter`](../../recursive_training/rules/hybrid_adapter.py:409)), adhering to PEP 8.
- **Variables:** Generally use `snake_case` (e.g., `rule_dict`, `start_time`).
- **Type Variable:** `T` is used as a generic type variable, which is conventional.
- **Constants/Configuration Keys:** Strings like `"generic"`, `"active"`, `"enable_dict_compatibility"` are used.
- **Private Methods:** Prefixed with a single underscore (e.g., [`_dict_to_dataclass`](../../recursive_training/rules/hybrid_adapter.py:282), [`_track_conversion_cost`](../../recursive_training/rules/hybrid_adapter.py:328)).

The naming conventions are consistent within the module and largely follow PEP 8 guidelines. There are no obvious signs of AI misinterpretations or significant deviations from standard Python naming practices. The names are generally descriptive and contribute to the readability of the code.