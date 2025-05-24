# Module Analysis: `recursive_training.rules.rule_evaluator`

## 1. Module Intent/Purpose

The primary role of the [`recursive_training/rules/rule_evaluator.py`](recursive_training/rules/rule_evaluator.py) module is to implement the evaluation mechanism for rules within the recursive training system. Its responsibilities include:
*   Testing the effectiveness of rules.
*   Analyzing rule performance.
*   Gathering metrics to guide further rule refinement and improvement.

## 2. Operational Status/Completeness

The module appears to be structurally complete for its defined features, such as single rule evaluation, batch evaluation, and rule comparison. However, the core logic for several specific evaluation types is implemented as placeholders:
*   [`_init_test_datasets()`](recursive_training/rules/rule_evaluator.py:124) (line 124): Placeholder for loading or generating test datasets.
*   [`_evaluate_logic()`](recursive_training/rules/rule_evaluator.py:429) (line 429): Placeholder for logical consistency checks.
*   [`_evaluate_coverage()`](recursive_training/rules/rule_evaluator.py:461) (line 461): Placeholder for input space coverage analysis.
*   [`_evaluate_performance()`](recursive_training/rules/rule_evaluator.py:497) (line 497): Placeholder for computational efficiency analysis.
*   The [`_evaluate_syntax()`](recursive_training/rules/rule_evaluator.py:350) method (line 350) has some basic checks but also indicates it's a placeholder for more comprehensive syntax validation.
*   Historical evaluation lookup in [`get_evaluation_status()`](recursive_training/rules/rule_evaluator.py:581) (line 600) is explicitly marked as not implemented.

## 3. Implementation Gaps / Unfinished Next Steps

*   **Core Evaluation Logic:** The most significant gap is the placeholder nature of the detailed evaluation methods: [`_evaluate_logic()`](recursive_training/rules/rule_evaluator.py:429), [`_evaluate_coverage()`](recursive_training/rules/rule_evaluator.py:461), and [`_evaluate_performance()`](recursive_training/rules/rule_evaluator.py:497). These require actual implementation to fulfill the module's purpose.
*   **Test Dataset Initialization:** The [`_init_test_datasets()`](recursive_training/rules/rule_evaluator.py:124) method needs to be implemented to load or generate relevant data for testing rules against different scenarios.
*   **Historical Evaluation Status:** The functionality to retrieve the status of historical evaluations (older than the current one) in [`get_evaluation_status()`](recursive_training/rules/rule_evaluator.py:581) is missing.
*   **Refined Syntax Evaluation:** The [`_evaluate_syntax()`](recursive_training/rules/rule_evaluator.py:350) method could be expanded beyond basic field checks.
*   **Logical Next Steps:**
    *   Implement the placeholder evaluation methods with actual logic.
    *   Develop a robust system for managing and versioning test datasets.
    *   Integrate a mechanism for storing and retrieving historical evaluation results.

## 4. Connections & Dependencies

### Direct Project Module Imports:
*   [`recursive_training.integration.cost_controller`](recursive_training/integration/cost_controller.py) (specifically [`get_cost_controller()`](recursive_training/integration/cost_controller.py:20))
*   [`recursive_training.metrics.metrics_store`](recursive_training/metrics/metrics_store.py) (specifically [`get_metrics_store()`](recursive_training/metrics/metrics_store.py:21))
*   [`recursive_training.config.default_config`](recursive_training/config/default_config.py) (specifically [`get_config()`](recursive_training/config/default_config.py:22))

### External Library Dependencies:
*   `logging`
*   `json`
*   `time`
*   `datetime` (from `datetime` import `datetime`, `timezone`)
*   `typing` (Any, Dict, List, Optional, Union, Tuple, Callable, Set)
*   `enum` (Enum)
*   `concurrent.futures` (ProcessPoolExecutor, as_completed)
*   `os`
*   `functools`
*   `multiprocessing` ([`cpu_count`](recursive_training/rules/rule_evaluator.py:25))
*   `numpy` (as `np`)
*   `hashlib` (used in [`_compute_rule_hash()`](recursive_training/rules/rule_evaluator.py:607))

### Interactions via Shared Data:
*   Interacts with the `CostController` instance obtained via [`get_cost_controller()`](recursive_training/integration/cost_controller.py:20) to track and limit evaluation costs.
*   Interacts with the `MetricsStore` instance obtained via [`get_metrics_store()`](recursive_training/metrics/metrics_store.py:21) to log evaluation metrics.
*   Loads configuration, particularly `hybrid_rules` and `cost_control` sections, using [`get_config()`](recursive_training/config/default_config.py:22).

### Input/Output Files:
*   The module does not directly read from or write to files for rules or evaluation data.
*   It generates logs via the `logging` module.

## 5. Function and Class Example Usages

*   **`RecursiveRuleEvaluator` Class:**
    *   Typically instantiated as a singleton using [`RecursiveRuleEvaluator.get_instance()`](recursive_training/rules/rule_evaluator.py:62) or the helper function [`get_rule_evaluator()`](recursive_training/rules/rule_evaluator.py:933).
    ```python
    from recursive_training.rules.rule_evaluator import get_rule_evaluator

    evaluator = get_rule_evaluator()
    ```

*   **[`evaluate_rule(rule, context, scope, cost_limit)`](recursive_training/rules/rule_evaluator.py:136):**
    *   Evaluates a single rule.
    ```python
    rule_to_test = {"id": "rule1", "type": "basic", "conditions": [], "actions": []}
    eval_context = {"param1": "value1"}
    results = evaluator.evaluate_rule(rule_to_test, eval_context)
    print(results["overall_score"], results["passed"])
    ```

*   **[`evaluate_rules_batch(rules, context, scope, cost_limit)`](recursive_training/rules/rule_evaluator.py:636):**
    *   Evaluates a list of rules, potentially in parallel.
    ```python
    rules_list = [
        {"id": "rule1", "type": "basic", "conditions": [], "actions": []},
        {"id": "rule2", "type": "advanced", "conditions": [], "actions": []}
    ]
    batch_results = evaluator.evaluate_rules_batch(rules_list, eval_context)
    for res in batch_results:
        print(f"Rule {res.get('rule_id')}: Score {res.get('overall_score')}")
    ```

*   **[`compare_rules(rules, context, scope)`](recursive_training/rules/rule_evaluator.py:525):**
    *   Compares multiple rules and identifies the best one based on evaluation scores.
    ```python
    comparison = evaluator.compare_rules(rules_list, eval_context)
    print(f"Best rule: {comparison['best_rule_id']} with score {comparison['best_score']}")
    ```

## 6. Hardcoding Issues

*   **Default Score Threshold:** [`min_acceptable_score = 0.7`](recursive_training/rules/rule_evaluator.py:100) (70% quality threshold for a rule to pass).
*   **Cost Limit Defaults:**
    *   In [`evaluate_rule()`](recursive_training/rules/rule_evaluator.py:136), the default `cost_limit` is `self.cost_config.daily_cost_threshold_usd / 20` (line 155), i.e., 5% of the daily budget.
    *   In [`evaluate_rules_batch()`](recursive_training/rules/rule_evaluator.py:636), the default `cost_limit` is `self.cost_config.daily_cost_threshold_usd / 10` (line 662), i.e., 10% of the daily budget.
*   **Score Weights:**
    *   The weights for calculating the `overall_score` from different evaluation scopes (syntax, logic, coverage, performance) are hardcoded in [`evaluate_rule()`](recursive_training/rules/rule_evaluator.py:136) (lines 256-268) and [`_evaluate_rule_task()`](recursive_training/rules/rule_evaluator.py:799) (lines 894-906):
        *   Syntax: 30%
        *   Logic: 40%
        *   Coverage: 20%
        *   Performance: 10%
*   **Syntax Evaluation Threshold:** In [`_evaluate_syntax()`](recursive_training/rules/rule_evaluator.py:350), a rule passes syntax check if `score >= 0.8` (line 423).
*   **Penalty Per Issue (Syntax):** In [`_evaluate_syntax()`](recursive_training/rules/rule_evaluator.py:350), severity-based penalties are hardcoded (lines 412-416).
*   **Simulated Costs:** Placeholder evaluation methods ([`_evaluate_syntax()`](recursive_training/rules/rule_evaluator.py:350), [`_evaluate_logic()`](recursive_training/rules/rule_evaluator.py:429), [`_evaluate_coverage()`](recursive_training/rules/rule_evaluator.py:461), [`_evaluate_performance()`](recursive_training/rules/rule_evaluator.py:497)) use hardcoded simulated costs (e.g., `cost = 0.0005` on line 366).
*   **Estimated Sequential Time:** In [`evaluate_rules_batch()`](recursive_training/rules/rule_evaluator.py:636), `estimated_sequential_time` per rule for speedup calculation is roughly estimated as `0.3` seconds (line 777).
*   **Required Rule Fields:** The list `required_fields = ["id", "type", "conditions", "actions"]` is hardcoded in [`_evaluate_syntax()`](recursive_training/rules/rule_evaluator.py:370).

## 7. Coupling Points

*   **Configuration:** Tightly coupled to the global configuration obtained via [`get_config()`](recursive_training/config/default_config.py:22), especially the `hybrid_rules` and `cost_control` sections.
*   **Cost Controller:** Directly depends on the `CostController` obtained from [`get_cost_controller()`](recursive_training/integration/cost_controller.py:20) for managing and tracking evaluation costs.
*   **Metrics Store:** Directly depends on the `MetricsStore` obtained from [`get_metrics_store()`](recursive_training/metrics/metrics_store.py:21) for logging various evaluation metrics.
*   **Rule Structure:** Assumes a specific dictionary structure for rules (e.g., presence of "id", "type", "conditions", "actions"). Changes to this structure would require updates in the evaluator.
*   **`EvaluationScope` Enum:** The evaluation logic branches based on the members of the [`EvaluationScope`](recursive_training/rules/rule_evaluator.py:28) enum.

## 8. Existing Tests

*   A corresponding test file exists at [`tests/recursive_training/rules/test_rule_evaluator.py`](tests/recursive_training/rules/test_rule_evaluator.py).
*   The nature, coverage, and completeness of these tests would require a separate review of the test file itself. Given the placeholder nature of some core evaluation logic in the module, the tests might primarily cover the structural aspects, parameter handling, and flow, rather than the detailed correctness of the evaluation types.

## 9. Module Architecture and Flow

*   **Singleton Pattern:** The `RecursiveRuleEvaluator` class (line 46) is designed as a singleton, accessible via [`RecursiveRuleEvaluator.get_instance()`](recursive_training/rules/rule_evaluator.py:62) or [`get_rule_evaluator()`](recursive_training/rules/rule_evaluator.py:933).
*   **Main Operations:**
    *   [`evaluate_rule()`](recursive_training/rules/rule_evaluator.py:136): Evaluates a single rule.
    *   [`evaluate_rules_batch()`](recursive_training/rules/rule_evaluator.py:636): Evaluates multiple rules, using `ProcessPoolExecutor` for parallel processing of rules not found in the cache.
    *   [`compare_rules()`](recursive_training/rules/rule_evaluator.py:525): Evaluates a list of rules and ranks them.
*   **Evaluation Scopes:** Evaluation can be performed at different levels of detail defined by the [`EvaluationScope`](recursive_training/rules/rule_evaluator.py:28) enum (SYNTAX, LOGIC, COVERAGE, PERFORMANCE, COMPREHENSIVE).
*   **Evaluation Process (Single Rule):**
    1.  Initialize evaluation ID and status.
    2.  Check cost budget via `CostController`.
    3.  Perform evaluations based on the specified `scope`:
        *   Syntax evaluation ([`_evaluate_syntax()`](recursive_training/rules/rule_evaluator.py:350)). If fails, returns early.
        *   Logic evaluation ([`_evaluate_logic()`](recursive_training/rules/rule_evaluator.py:429)).
        *   Coverage evaluation ([`_evaluate_coverage()`](recursive_training/rules/rule_evaluator.py:461)).
        *   Performance evaluation ([`_evaluate_performance()`](recursive_training/rules/rule_evaluator.py:497)).
    4.  Each sub-evaluation checks cost limits and contributes to `total_cost`.
    5.  Calculate an `overall_score` as a weighted average of the scores from performed evaluations.
    6.  Determine if the rule `passed` based on `min_acceptable_score`.
    7.  Update internal metrics and log results to `MetricsStore`.
*   **Batch Evaluation Process:**
    1.  Checks cache ([`_evaluation_cache`](recursive_training/rules/rule_evaluator.py:107)) for pre-computed results using a hash of the rule ([`_compute_rule_hash()`](recursive_training/rules/rule_evaluator.py:607)).
    2.  For uncached rules, submits tasks to a `ProcessPoolExecutor`, calling [`_evaluate_rule_task()`](recursive_training/rules/rule_evaluator.py:799) for each.
    3.  [`_evaluate_rule_task()`](recursive_training/rules/rule_evaluator.py:799) mirrors the single rule evaluation flow but is designed to run in a separate process.
    4.  Combines cached and newly computed results.
    5.  Updates metrics, including parallel speedup estimation.
*   **Caching:** Implements an in-memory cache ([`_evaluation_cache`](recursive_training/rules/rule_evaluator.py:107)) to store evaluation results, keyed by a hash of the rule and the evaluation scope.
*   **Cost Control:** Integrates with `CostController` at various stages to ensure evaluations do not exceed budget limits.
*   **Metrics Tracking:** Maintains internal metrics (e.g., `total_evaluations`, `total_cost`) and logs detailed metrics to `MetricsStore`.

## 10. Naming Conventions

*   **Classes:** `RecursiveRuleEvaluator`, `EvaluationScope`, `EvaluationStatus` use PascalCase, adhering to PEP 8.
*   **Methods & Functions:** `evaluate_rule`, `_evaluate_syntax`, `get_rule_evaluator` use snake_case, adhering to PEP 8. Private/internal helper methods are prefixed with a single underscore.
*   **Variables:** `min_acceptable_score`, `current_eval_id` use snake_case.
*   **Constants/Enums:** Enum members like `EvaluationScope.SYNTAX` are UPPER_CASE. The singleton instance `_instance` is lowercase with a leading underscore.
*   **Overall:** Naming conventions are generally consistent and follow Python community standards (PEP 8). No obvious AI-related naming errors or significant deviations were noted.