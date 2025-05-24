# Module Analysis: `recursive_training.rules.rule_generator`

**File Path:** [`recursive_training/rules/rule_generator.py`](../../recursive_training/rules/rule_generator.py)

## 1. Module Intent/Purpose

The primary role of the `RecursiveRuleGenerator` module is to generate, refine, and optimize rules for the recursive training system. It is designed to use a GPT-Symbolic feedback loop, allowing for various generation methods including GPT-only, Symbolic-only, and hybrid approaches. It aims to support both dictionary-based and object-oriented rule representations.

## 2. Operational Status/Completeness

The module presents a foundational structure for rule generation but is not fully operational. Key functionalities are implemented as placeholders:

*   **Core Logic Placeholders:**
    *   [`_initialize_gpt_system()`](../../recursive_training/rules/rule_generator.py:123): Placeholder for GPT model initialization.
    *   [`_initialize_symbolic_system()`](../../recursive_training/rules/rule_generator.py:129): Placeholder for symbolic system initialization.
    *   [`_generate_with_gpt()`](../../recursive_training/rules/rule_generator.py:331): Simulates GPT rule generation, returns a hardcoded rule structure.
    *   [`_generate_with_symbolic()`](../../recursive_training/rules/rule_generator.py:396): Simulates symbolic rule generation, returns a hardcoded rule structure.
    *   [`_refine_rule()`](../../recursive_training/rules/rule_generator.py:423): Simulates rule refinement based on feedback.
    *   [`_evaluate_rule_quality()`](../../recursive_training/rules/rule_generator.py:458): Simulates rule quality evaluation, returns a hardcoded quality score and feedback.
*   **Implemented Features:**
    *   Singleton pattern for the generator class.
    *   Iterative rule generation loop with configurable iterations and improvement thresholds.
    *   Integration with `CostController` for budget management.
    *   Integration with `MetricsStore` for tracking generation metrics.
    *   Batch rule generation using `concurrent.futures.ProcessPoolExecutor` for parallelism.
    *   Basic caching mechanism for GPT-generated rules based on context hash.
    *   Enum types for `RuleGenerationMethod` and `RuleGenerationStatus`.
    *   Logging throughout the process.

The module appears to be in an early to mid-stage of development, with the overall framework and supporting utilities (cost control, metrics, batching) in place, but the core intelligent rule generation and refinement capabilities are yet to be implemented.

## 3. Implementation Gaps / Unfinished Next Steps

*   **GPT Integration:** The actual interaction with a GPT model (prompt engineering, API calls, response parsing) is missing in [`_generate_with_gpt()`](../../recursive_training/rules/rule_generator.py:331) and [`_refine_rule()`](../../recursive_training/rules/rule_generator.py:423).
*   **Symbolic System Integration:** The actual symbolic reasoning logic for rule generation and evaluation is missing in [`_generate_with_symbolic()`](../../recursive_training/rules/rule_generator.py:396) and [`_evaluate_rule_quality()`](../../recursive_training/rules/rule_generator.py:458).
*   **Rule Representation:** While the docstring mentions support for "dictionary-based and object-oriented rule representations," the current implementation primarily deals with dictionaries. The object-oriented aspect is not evident.
*   **Advanced Refinement Logic:** The [`_refine_rule()`](../../recursive_training/rules/rule_generator.py:423) method currently performs a simplistic modification. A more sophisticated mechanism to interpret feedback and apply meaningful changes is needed.
*   **Sophisticated Evaluation:** The [`_evaluate_rule_quality()`](../../recursive_training/rules/rule_generator.py:458) method returns a fixed score. A robust evaluation mechanism (e.g., testing against data, logical consistency checks) is required.
*   **Hybrid Adaptive Method:** The `HYBRID_ADAPTIVE` method in [`RuleGenerationMethod`](../../recursive_training/rules/rule_generator.py:28) lacks specific implementation details differentiating it from `GPT_SYMBOLIC_LOOP` in the current placeholder logic.
*   **Historical Run Lookup:** The [`get_generation_status()`](../../recursive_training/rules/rule_generator.py:508) function notes that "Historical run lookup not implemented" (line 530).
*   **Error Handling in Placeholders:** Placeholder methods might need more specific error handling related to potential issues from actual GPT or symbolic system calls.

## 4. Connections & Dependencies

### Internal Project Dependencies:
*   [`recursive_training.integration.cost_controller`](../../recursive_training/integration/cost_controller.py): Uses [`get_cost_controller()`](../../recursive_training/integration/cost_controller.py) for managing and tracking API call costs.
*   [`recursive_training.metrics.metrics_store`](../../recursive_training/metrics/metrics_store.py): Uses [`get_metrics_store()`](../../recursive_training/metrics/metrics_store.py) for logging rule generation metrics.
*   [`recursive_training.config.default_config`](../../recursive_training/config/default_config.py): Uses [`get_config()`](../../recursive_training/config/default_config.py) to fetch configuration for hybrid rules and cost control.

### External Library Dependencies:
*   `logging`: For application logging.
*   `json`: For handling JSON data, particularly in context hashing.
*   `time`: For timestamps and performance measurement.
*   `datetime`: For timestamps.
*   `typing`: For type hinting.
*   `enum`: For defining `RuleGenerationMethod` and `RuleGenerationStatus`.
*   `concurrent.futures`: Specifically `ProcessPoolExecutor` and `as_completed` for parallel batch processing.
*   `os`: Used for `os.cpu_count()`.
*   `functools`: (Not directly used in the provided snippet, but imported).
*   `multiprocessing`: Specifically `cpu_count` (though `os.cpu_count()` is used).
*   `numpy`: (Imported but not directly used in the provided snippet).
*   `hashlib`: For [`_compute_context_hash()`](../../recursive_training/rules/rule_generator.py:378).

### Shared Data Interactions:
*   Interacts with the `CostController` instance to check budget and track costs.
*   Interacts with the `MetricsStore` instance to persist operational metrics.
*   Reads configuration data provided by the `default_config` module.

### Input/Output:
*   **Input:** Context dictionaries and rule types for generation. Configuration settings.
*   **Output:** Generated rules (as dictionaries with metadata). Logs extensively to the logging system. Metrics are sent to the `MetricsStore`.
*   No direct reading from or writing to persistent files for rules themselves, but relies on other modules (config, metrics store) which might have their own persistence.

## 5. Function and Class Example Usages

### `RecursiveRuleGenerator` Class
Singleton class for generating rules.

**Obtaining an instance:**
```python
from recursive_training.rules.rule_generator import get_rule_generator
from recursive_training.rules.rule_generator import RuleGenerationMethod # Required for method enum

generator = get_rule_generator()
# or
# from recursive_training.rules.rule_generator import RecursiveRuleGenerator
# generator = RecursiveRuleGenerator.get_instance()
```

### [`generate_rule()`](../../recursive_training/rules/rule_generator.py:135)
Generates a single rule based on context.
```python
context_data = {"user_points": 150, "last_purchase_days": 10}
rule_type_spec = "user_segmentation"
generated_rule = generator.generate_rule(
    context=context_data,
    rule_type=rule_type_spec,
    method=RuleGenerationMethod.GPT_SYMBOLIC_LOOP, # Optional
    max_iterations=3, # Optional
    cost_limit=0.50 # Optional
)
if "error" not in generated_rule:
    print(f"Generated Rule ID: {generated_rule.get('id')}")
    print(f"Quality: {generated_rule.get('metadata', {}).get('quality')}")
else:
    print(f"Error generating rule: {generated_rule['error']}")
```

### [`generate_rules_batch()`](../../recursive_training/rules/rule_generator.py:534)
Generates multiple rules in parallel.
```python
contexts_list = [
    {"item_category": "electronics", "price": 200},
    {"item_category": "books", "price": 50}
]
rule_types_list = ["discount_promo", "shipping_promo"]

batch_generated_rules = generator.generate_rules_batch(
    contexts=contexts_list,
    rule_types=rule_types_list,
    cost_limit=1.00 # Optional: cost limit for the entire batch
)

for rule in batch_generated_rules:
    if "error" not in rule:
        print(f"Batch Generated Rule ID: {rule.get('id')}, Type: {rule.get('metadata', {}).get('rule_type')}")
    else:
        print(f"Error in batch generation: {rule['error']}")
```

### [`get_generation_status()`](../../recursive_training/rules/rule_generator.py:508)
Retrieves the status of the current or a specific rule generation run.
```python
status_info = generator.get_generation_status() # For the latest run
# status_info = generator.get_generation_status(run_id="rule_gen_1678886400") # For a specific run (currently placeholder)
print(f"Run ID: {status_info.get('run_id')}, Status: {status_info.get('status')}")
```

## 6. Hardcoding Issues

*   **Default Parameters:**
    *   `self.max_iterations = 5` ([line 101](../../recursive_training/rules/rule_generator.py:101))
    *   `self.improvement_threshold = 0.05` ([line 102](../../recursive_training/rules/rule_generator.py:102))
    *   Default cost limit for `generate_rule` is 10% of daily budget ([line 157](../../recursive_training/rules/rule_generator.py:157)).
    *   Default cost limit for `generate_rules_batch` is 20% of daily budget ([line 563](../../recursive_training/rules/rule_generator.py:563)).
*   **Placeholder Logic Values:**
    *   Rule structure in [`_generate_with_gpt()`](../../recursive_training/rules/rule_generator.py:361-371) (e.g., `{"variable": "price", "operator": ">", "value": 100}`).
    *   Rule structure in [`_generate_with_symbolic()`](../../recursive_training/rules/rule_generator.py:414-421).
    *   Quality score `0.7` in [`_evaluate_rule_quality()`](../../recursive_training/rules/rule_generator.py:479).
    *   Cost estimates in [`_estimate_iteration_cost()`](../../recursive_training/rules/rule_generator.py:498-506) (e.g., GPT_ONLY: `0.02`).
*   **Test-Specific Hardcoding:**
    *   The string "Refined:" is prepended to descriptions during refinement, likely to satisfy test expectations ([line 210](../../recursive_training/rules/rule_generator.py:210), [line 447](../../recursive_training/rules/rule_generator.py:447)).
    *   A specific condition `{"variable": "customer_type", "operator": "==", "value": "premium"}` is added to rules under certain conditions, also likely for testing purposes ([lines 213-216](../../recursive_training/rules/rule_generator.py:213-216), [lines 451-454](../../recursive_training/rules/rule_generator.py:451-454)).
*   **Magic Numbers/Strings:**
    *   `max_workers = max(1, (os.cpu_count() or 4) - 1)` ([line 103](../../recursive_training/rules/rule_generator.py:103)): The fallback `4` for `cpu_count` and subtracting `1`.
    *   Token usage simulation values (e.g., `1000` in [`_generate_with_gpt()`](../../recursive_training/rules/rule_generator.py:358), `800` in [`_refine_rule()`](../../recursive_training/rules/rule_generator.py:441)).
    *   Direct cost simulation values (e.g., `0.001` in [`_generate_with_symbolic()`](../../recursive_training/rules/rule_generator.py:411)).
    *   "Rough estimate" for `estimated_sequential_time` calculation ([line 632](../../recursive_training/rules/rule_generator.py:632)).

## 7. Coupling Points

*   **High Coupling with Core Services:** Tightly coupled with:
    *   `CostController`: For all cost-related operations and budget checks.
    *   `MetricsStore`: For logging all significant events and performance data.
    *   Project Configuration (`get_config()`): For operational parameters.
*   **Intended Coupling (Currently Placeholders):**
    *   GPT Model/Service: The core generation and refinement logic will be tightly coupled once implemented.
    *   Symbolic Reasoning System: The symbolic generation and evaluation logic will be tightly coupled once implemented.
*   **Data Structure Coupling:** Assumes rules are represented as dictionaries. Changes to the rule structure would require updates in multiple methods.
*   **Process Coupling:** The [`generate_rules_batch()`](../../recursive_training/rules/rule_generator.py:534) method uses `ProcessPoolExecutor`, coupling its performance and error handling characteristics to this specific concurrency model.

## 8. Existing Tests

*   The existence of a test file at `tests/recursive_training/rules/test_rule_generator.py` is implied by standard project structure and is confirmed by code comments.
*   The code contains specific modifications and logging statements apparently tailored for test cases:
    *   Lines [206-217](../../recursive_training/rules/rule_generator.py:206-217): Special handling for `GPT_SYMBOLIC_LOOP` method in `generate_rule()` to add "Refined:" and a specific condition.
    *   Lines [446-454](../../recursive_training/rules/rule_generator.py:446-454): In `_refine_rule()`, "Refined:" is added, and a specific condition related to `customer_type` is appended.
    *   Line [255](../../recursive_training/rules/rule_generator.py:255): A condition `iteration >= 2` for stopping early, potentially to ensure tests run a certain number of iterations.
*   These suggest that the tests likely verify:
    *   The iterative refinement process (at least with placeholder logic).
    *   The application of specific "refinements" by the placeholder methods.
    *   Cost tracking and metric updates.
    *   Batch processing functionality.
*   The actual coverage and nature of tests (unit, integration) for the non-placeholder parts would require examining the test file itself. Given the placeholders, tests for the core GPT/Symbolic logic are likely minimal or test the placeholder behavior.

## 9. Module Architecture and Flow

*   **Design Pattern:** Implements the Singleton pattern for `RecursiveRuleGenerator` via `get_instance()` and [`get_rule_generator()`](../../recursive_training/rules/rule_generator.py:743).
*   **Main Components:**
    *   `RecursiveRuleGenerator` class: Central orchestrator for rule generation.
    *   `RuleGenerationMethod` (Enum): Defines strategies for generation (GPT, Symbolic, Hybrid).
    *   `RuleGenerationStatus` (Enum): Tracks the state of generation tasks.
*   **Control Flow (Single Rule Generation - `generate_rule()`):**
    1.  Initialization: Sets defaults, run ID, status.
    2.  Cost Check: Verifies budget with `CostController`.
    3.  Iterative Loop (`max_iterations`):
        *   Cost Check: Per iteration against `cost_limit`.
        *   Generation/Refinement:
            *   Iteration 0: Calls [`_generate_with_gpt()`](../../recursive_training/rules/rule_generator.py:331) or [`_generate_with_symbolic()`](../../recursive_training/rules/rule_generator.py:396) based on `method`.
            *   Subsequent Iterations: Calls [`_refine_rule()`](../../recursive_training/rules/rule_generator.py:423) with feedback.
        *   Evaluation: Calls [`_evaluate_rule_quality()`](../../recursive_training/rules/rule_generator.py:458) to get quality score and feedback.
        *   Cost Tracking: Estimates and records iteration cost.
        *   Best Rule Update: Tracks the rule with the highest quality.
        *   Continuation Check: Stops if improvement is below `improvement_threshold` (after a few iterations).
    4.  Result Finalization: Selects the best rule, adds metadata (method, iterations, quality, cost, time).
    5.  Status Update & Metrics: Sets status to `COMPLETED` (or `FAILED`), updates internal metrics, and logs to `MetricsStore`.
*   **Control Flow (Batch Rule Generation - `generate_rules_batch()`):**
    1.  Initialization: Similar to single rule, but for a batch.
    2.  Cost Check: For the entire batch.
    3.  Parallel Execution:
        *   Uses `ProcessPoolExecutor` to submit multiple `_generate_rule_task` calls.
        *   Each task gets a proportional cost limit.
        *   Results are collected as completed.
    4.  Overall Cost Check: Monitors cumulative cost during batch processing.
    5.  Result Aggregation & Metrics: Updates status, aggregates costs, calculates speedup, logs to `MetricsStore`.
*   **Helper Methods:**
    *   [`_initialize_gpt_system()`](../../recursive_training/rules/rule_generator.py:123), [`_initialize_symbolic_system()`](../../recursive_training/rules/rule_generator.py:129): Placeholders for system setup.
    *   [`_compute_context_hash()`](../../recursive_training/rules/rule_generator.py:378): Generates a hash for caching.
    *   [`_estimate_iteration_cost()`](../../recursive_training/rules/rule_generator.py:488): Placeholder for cost estimation.
*   **Caching:** A simple dictionary-based cache (`_rule_cache`) is used, keyed by context hash, to store results from [`_generate_with_gpt()`](../../recursive_training/rules/rule_generator.py:331).

## 10. Naming Conventions

*   **Classes:** `RecursiveRuleGenerator`, `RuleGenerationMethod`, `RuleGenerationStatus` use PascalCase, adhering to PEP 8.
*   **Methods & Functions:** `generate_rule`, `_generate_with_gpt`, `get_rule_generator` use snake_case, adhering to PEP 8.
*   **Private/Internal Methods:** Prefixed with a single underscore (e.g., `_initialize_gpt_system`, `_compute_context_hash`), which is a common Python convention.
*   **Variables:** Generally use snake_case (e.g., `max_iterations`, `cost_limit`, `best_rule`, `current_run_id`).
*   **Constants/Enums:** Enum members are uppercase (e.g., `GPT_ONLY`, `NOT_STARTED`).
*   **Clarity:** Names are generally descriptive and indicate their purpose (e.g., `cost_controller`, `metrics_store`, `improvement_threshold`).
*   **Consistency:** Naming is consistent throughout the module.
*   **AI Assumption Errors:** No obvious errors in naming that would suggest misinterpretation by an AI developer or significant deviations from standard Python practices. The naming aligns well with PEP 8 and common Python idioms.