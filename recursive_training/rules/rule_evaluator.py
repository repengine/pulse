"""
RecursiveRuleEvaluator Module

This module implements the evaluation mechanism for rules in the recursive training system.
It provides methods for testing rule effectiveness, analyzing rule performance,
and gathering metrics to guide further rule refinement.
"""

import logging
import json
import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple
from enum import Enum
from concurrent.futures import ProcessPoolExecutor, as_completed
import os

# Import recursive training components
from recursive_training.integration.cost_controller import get_cost_controller
from recursive_training.metrics.metrics_store import get_metrics_store
from recursive_training.config.default_config import get_config

# Performance optimization imports


class EvaluationScope(Enum):
    """Scope of rule evaluation."""

    SYNTAX = "syntax"  # Basic syntax and structure validation
    LOGIC = "logic"  # Logical consistency and completeness
    COVERAGE = "coverage"  # Coverage of input space
    PERFORMANCE = "performance"  # Computational efficiency
    COMPREHENSIVE = "comprehensive"  # All of the above


class EvaluationStatus(Enum):
    """Status of rule evaluation process."""

    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELED = "canceled"


class RecursiveRuleEvaluator:
    """
    Evaluates the effectiveness of rules in the recursive training system.

    Features:
    - Multiple evaluation strategies (syntax, logic, coverage, performance)
    - Cost-controlled evaluation with budget limits
    - Support for both dictionary and object-based rule representations
    - Comparative analysis of rule versions
    - Detailed feedback generation for rule improvement
    - Comprehensive logging and metrics tracking
    """

    # Singleton instance
    _instance = None

    @classmethod
    def get_instance(
        cls, config: Optional[Dict[str, Any]] = None
    ) -> "RecursiveRuleEvaluator":
        """
        Get or create the singleton instance of RecursiveRuleEvaluator.

        Args:
            config: Optional configuration dictionary

        Returns:
            RecursiveRuleEvaluator instance
        """
        if cls._instance is None:
            cls._instance = RecursiveRuleEvaluator(config)
        return cls._instance

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the RecursiveRuleEvaluator.

        Args:
            config: Optional configuration dictionary
        """
        self.logger = logging.getLogger("RecursiveRuleEvaluator")

        # Load configuration
        self.config = config or get_config().hybrid_rules
        self.cost_config = get_config().cost_control

        # Initialize dependencies
        self.cost_controller = get_cost_controller()
        self.metrics_store = get_metrics_store()

        # Initialize state
        self.evaluation_status = EvaluationStatus.NOT_STARTED
        self.current_eval_id = None

        # Configure default evaluation parameters
        self.default_scope = EvaluationScope.COMPREHENSIVE
        self.min_acceptable_score = 0.7  # 70% quality threshold
        self.max_workers = max(1, (os.cpu_count() or 4) - 1)  # Leave one core free

        # Setup test datasets
        self._init_test_datasets()

        # Caching to avoid redundant evaluations
        self._evaluation_cache = {}
        self._rule_hash_cache = {}

        # Track metrics
        self.metrics = {
            "total_evaluations": 0,
            "passed_evaluations": 0,
            "failed_evaluations": 0,
            "total_cost": 0.0,
            "average_quality_score": 0.0,
            "batch_evaluations": 0,
            "parallel_speedup": 0.0,
            "cache_hits": 0,
        }

        self.logger.info(
            f"RecursiveRuleEvaluator initialized with {
                self.max_workers} worker processes")

    def _init_test_datasets(self):
        """Initialize test datasets for rule evaluation."""
        # This is a placeholder - in a real implementation, this would
        # load or generate test datasets for different evaluation scenarios
        self.test_datasets = {
            "syntax": [],
            "logic": [],
            "coverage": [],
            "performance": [],
        }
        self.logger.debug("Test datasets initialized")

    def evaluate_rule(
        self,
        rule: Dict[str, Any],
        context: Dict[str, Any],
        scope: Optional[EvaluationScope] = None,
        cost_limit: Optional[float] = None,
    ) -> Dict[str, Any]:
        """
        Evaluate a rule based on the provided context and scope.

        Args:
            rule: Rule to evaluate
            context: Contextual information for evaluation
            scope: Scope of evaluation
            cost_limit: Maximum cost for this evaluation operation

        Returns:
            Evaluation results as a dictionary
        """
        # Set default values if not provided
        scope = scope or self.default_scope
        cost_limit = (
            cost_limit or self.cost_config.daily_cost_threshold_usd / 20
        )  # 5% of daily budget

        # Create an evaluation ID and update status
        self.current_eval_id = f"rule_eval_{int(time.time())}"
        self.evaluation_status = EvaluationStatus.IN_PROGRESS

        # Log the start of evaluation
        self.logger.info(
            f"Starting rule evaluation (ID: {
                self.current_eval_id}, Scope: {
                scope.value})")

        # Check cost budget
        if not self.cost_controller.can_make_api_call(check_cost=True):
            self.logger.error("Rule evaluation canceled due to cost limits")
            self.evaluation_status = EvaluationStatus.CANCELED
            return {"error": "Rule evaluation canceled due to cost limits"}

        # Initialize result structure
        evaluation_result = {
            "rule_id": rule.get("id", "unknown"),
            "evaluation_id": self.current_eval_id,
            "scope": scope.value,
            "timestamp": datetime.now().isoformat(),
            "overall_score": 0.0,
            "details": {},
            "passed": False,
            "issues": [],
            "recommendations": [],
        }

        # Initialize tracking metrics for this evaluation
        start_time = time.time()
        total_cost = 0.0

        try:
            # Syntax evaluation
            if scope in [EvaluationScope.SYNTAX, EvaluationScope.COMPREHENSIVE]:
                syntax_result = self._evaluate_syntax(rule)
                evaluation_result["details"]["syntax"] = syntax_result
                total_cost += syntax_result["evaluation_cost"]

                # Early return if syntax check fails
                if not syntax_result["passed"]:
                    evaluation_result["overall_score"] = syntax_result["score"]
                    evaluation_result["passed"] = False
                    evaluation_result["issues"].extend(syntax_result["issues"])
                    evaluation_result["recommendations"].extend(
                        syntax_result["recommendations"]
                    )

                    self.logger.warning(
                        f"Rule failed syntax evaluation: {rule.get('id', 'unknown')}"
                    )

                    # Update evaluation status
                    self.evaluation_status = EvaluationStatus.COMPLETED

                    # Track metrics
                    self._update_metrics(False, syntax_result["score"], total_cost)

                    return evaluation_result

            # Logic evaluation
            if scope in [EvaluationScope.LOGIC, EvaluationScope.COMPREHENSIVE]:
                # Check if cost limit would be exceeded
                if total_cost >= cost_limit:
                    self.logger.warning(
                        f"Cost limit reached before logic evaluation: ${total_cost:.2f}"
                    )
                else:
                    logic_result = self._evaluate_logic(rule, context)
                    evaluation_result["details"]["logic"] = logic_result
                    total_cost += logic_result["evaluation_cost"]

                    evaluation_result["issues"].extend(logic_result["issues"])
                    evaluation_result["recommendations"].extend(
                        logic_result["recommendations"]
                    )

            # Coverage evaluation
            if scope in [EvaluationScope.COVERAGE, EvaluationScope.COMPREHENSIVE]:
                # Check if cost limit would be exceeded
                if total_cost >= cost_limit:
                    self.logger.warning(
                        f"Cost limit reached before coverage evaluation: ${
                            total_cost:.2f}")
                else:
                    coverage_result = self._evaluate_coverage(rule, context)
                    evaluation_result["details"]["coverage"] = coverage_result
                    total_cost += coverage_result["evaluation_cost"]

                    evaluation_result["issues"].extend(coverage_result["issues"])
                    evaluation_result["recommendations"].extend(
                        coverage_result["recommendations"]
                    )

            # Performance evaluation
            if scope in [EvaluationScope.PERFORMANCE, EvaluationScope.COMPREHENSIVE]:
                # Check if cost limit would be exceeded
                if total_cost >= cost_limit:
                    self.logger.warning(
                        f"Cost limit reached before performance evaluation: ${
                            total_cost:.2f}")
                else:
                    performance_result = self._evaluate_performance(rule)
                    evaluation_result["details"]["performance"] = performance_result
                    total_cost += performance_result["evaluation_cost"]

                    evaluation_result["issues"].extend(performance_result["issues"])
                    evaluation_result["recommendations"].extend(
                        performance_result["recommendations"]
                    )

            # Calculate overall score (weighted average of all evaluations performed)
            scores = []
            weights = []

            if "syntax" in evaluation_result["details"]:
                scores.append(evaluation_result["details"]["syntax"]["score"])
                weights.append(0.3)  # 30% weight for syntax

            if "logic" in evaluation_result["details"]:
                scores.append(evaluation_result["details"]["logic"]["score"])
                weights.append(0.4)  # 40% weight for logic

            if "coverage" in evaluation_result["details"]:
                scores.append(evaluation_result["details"]["coverage"]["score"])
                weights.append(0.2)  # 20% weight for coverage

            if "performance" in evaluation_result["details"]:
                scores.append(evaluation_result["details"]["performance"]["score"])
                weights.append(0.1)  # 10% weight for performance

            # Compute weighted average
            if scores and weights:
                evaluation_result["overall_score"] = sum(
                    s * w for s, w in zip(scores, weights)
                ) / sum(weights)

            # Determine if the rule passed evaluation
            evaluation_result["passed"] = (
                evaluation_result["overall_score"] >= self.min_acceptable_score
            )

            # Sort issues and recommendations by importance
            evaluation_result["issues"].sort(
                key=lambda x: x.get("severity", 0), reverse=True
            )
            evaluation_result["recommendations"].sort(
                key=lambda x: x.get("importance", 0), reverse=True
            )

            # Update evaluation status
            self.evaluation_status = EvaluationStatus.COMPLETED

            # Track metrics
            self._update_metrics(
                evaluation_result["passed"],
                evaluation_result["overall_score"],
                total_cost,
            )

            # Log completion
            eval_time = time.time() - start_time
            self.logger.info(
                f"Rule evaluation completed (ID: {self.current_eval_id}, "
                f"Score: {evaluation_result['overall_score']:.2f}, "
                f"Passed: {evaluation_result['passed']}, "
                f"Time: {eval_time:.2f}s, "
                f"Cost: ${total_cost:.4f})"
            )

            return evaluation_result

        except Exception as e:
            self.logger.error(f"Error in rule evaluation: {e}")
            self.evaluation_status = EvaluationStatus.FAILED

            # Update metrics
            self.metrics["total_evaluations"] += 1
            self.metrics["failed_evaluations"] += 1
            self.metrics["total_cost"] += total_cost

            # Track in metrics store
            self.metrics_store.store_metric(
                {
                    "metric_type": "rule_evaluation_failure",
                    "evaluation_id": self.current_eval_id,
                    "rule_id": rule.get("id", "unknown"),
                    "error": str(e),
                    "cost": total_cost,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }
            )

            # Add error to result
            evaluation_result["error"] = str(e)
            evaluation_result["passed"] = False

            return evaluation_result

    def _update_metrics(self, passed: bool, score: float, cost: float):
        """Update metrics after an evaluation."""
        self.metrics["total_evaluations"] += 1
        if passed:
            self.metrics["passed_evaluations"] += 1
        else:
            self.metrics["failed_evaluations"] += 1

        self.metrics["total_cost"] += cost

        # Update average score
        self.metrics["average_quality_score"] = (
            self.metrics["average_quality_score"]
            * (self.metrics["total_evaluations"] - 1)
            + score
        ) / self.metrics["total_evaluations"]

        # Track in metrics store
        self.metrics_store.store_metric(
            {
                "metric_type": "rule_evaluation",
                "evaluation_id": self.current_eval_id,
                "passed": passed,
                "score": score,
                "cost": cost,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        )

    def _evaluate_syntax(self, rule: Dict[str, Any]) -> Dict[str, Any]:
        """
        Evaluate rule syntax and structure.

        Args:
            rule: Rule to evaluate

        Returns:
            Syntax evaluation results
        """
        # This is a placeholder - in a real implementation, this would:
        # 1. Check if the rule has all required fields
        # 2. Validate the structure of conditions and actions
        # 3. Check for syntax errors in rule expressions

        # Simulate processing cost tracking for demo purposes
        cost = 0.0005
        self.cost_controller.track_cost(direct_cost=cost)

        # Check for required fields
        required_fields = ["id", "type", "conditions", "actions"]
        missing_fields = [field for field in required_fields if field not in rule]

        issues = []
        if missing_fields:
            issues.append(
                {
                    "type": "missing_fields",
                    "description": f"Rule is missing required fields: {', '.join(missing_fields)}",
                    "severity": 3,  # High severity
                }
            )

        # Check conditions and actions
        if "conditions" in rule and not isinstance(rule["conditions"], list):
            issues.append(
                {
                    "type": "invalid_structure",
                    "description": "Conditions must be a list",
                    "severity": 2,  # Medium severity
                }
            )

        if "actions" in rule and not isinstance(rule["actions"], list):
            issues.append(
                {
                    "type": "invalid_structure",
                    "description": "Actions must be a list",
                    "severity": 2,  # Medium severity
                }
            )

        # Generate recommendations based on issues
        recommendations = []
        for issue in issues:
            if issue["type"] == "missing_fields":
                recommendations.append(
                    {
                        "description": f"Add the following fields to the rule: {', '.join(missing_fields)}",
                        "importance": 3,  # High importance
                    }
                )
            elif issue["type"] == "invalid_structure":
                recommendations.append(
                    {
                        "description": "Fix the structure of conditions and actions to be valid lists",
                        "importance": 2,  # Medium importance
                    }
                )

        # Calculate score based on issues
        base_score = 1.0
        penalty_per_issue = {
            3: 0.4,  # High severity issue
            2: 0.2,  # Medium severity issue
            1: 0.1,  # Low severity issue
        }

        score = base_score - sum(
            penalty_per_issue.get(issue["severity"], 0.1) for issue in issues
        )
        score = max(0.0, min(1.0, score))  # Clamp between 0 and 1

        return {
            "score": score,
            "passed": score >= 0.8,  # 80% threshold for syntax
            "issues": issues,
            "recommendations": recommendations,
            "evaluation_cost": cost,
        }

    def _evaluate_logic(
        self, rule: Dict[str, Any], context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Evaluate rule logic and consistency.

        Args:
            rule: Rule to evaluate
            context: Context for evaluation

        Returns:
            Logic evaluation results
        """
        # This is a placeholder - in a real implementation, this would:
        # 1. Check for logical consistency in conditions
        # 2. Detect contradictions or redundancies
        # 3. Analyze logical completeness

        # Simulate processing cost tracking for demo purposes
        cost = 0.001
        self.cost_controller.track_cost(direct_cost=cost)

        # Return placeholder evaluation results
        return {
            "score": 0.85,
            "passed": True,
            "issues": [],
            "recommendations": [
                {
                    "description": "Consider adding more specific conditions to improve precision",
                    "importance": 1,  # Low importance
                }
            ],
            "evaluation_cost": cost,
        }

    def _evaluate_coverage(
        self, rule: Dict[str, Any], context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Evaluate how well the rule covers the input space.

        Args:
            rule: Rule to evaluate
            context: Context for evaluation

        Returns:
            Coverage evaluation results
        """
        # This is a placeholder - in a real implementation, this would:
        # 1. Test rule against a variety of scenarios
        # 2. Measure false positive and false negative rates
        # 3. Analyze edge cases

        # Simulate processing cost tracking for demo purposes
        cost = 0.002
        self.cost_controller.track_cost(direct_cost=cost)

        # Return placeholder evaluation results
        return {
            "score": 0.75,
            "passed": True,
            "issues": [
                {
                    "type": "limited_coverage",
                    "description": "Rule may not handle certain edge cases",
                    "severity": 1,  # Low severity
                }
            ],
            "recommendations": [
                {
                    "description": "Add conditions to handle edge cases",
                    "importance": 2,  # Medium importance
                }
            ],
            "evaluation_cost": cost,
        }

    def _evaluate_performance(self, rule: Dict[str, Any]) -> Dict[str, Any]:
        """
        Evaluate rule computational efficiency.

        Args:
            rule: Rule to evaluate

        Returns:
            Performance evaluation results
        """
        # This is a placeholder - in a real implementation, this would:
        # 1. Measure execution time for rule evaluation
        # 2. Analyze computational complexity
        # 3. Check for inefficient patterns

        # Simulate processing cost tracking for demo purposes
        cost = 0.0005
        self.cost_controller.track_cost(direct_cost=cost)

        # Return placeholder evaluation results
        return {
            "score": 0.9,
            "passed": True,
            "issues": [],
            "recommendations": [],
            "evaluation_cost": cost,
        }

    def compare_rules(
        self,
        rules: List[Dict[str, Any]],
        context: Dict[str, Any],
        scope: Optional[EvaluationScope] = None,
    ) -> Dict[str, Any]:
        """
        Compare multiple rules to determine the most effective one.

        Args:
            rules: List of rules to compare
            context: Context for evaluation
            scope: Scope of evaluation

        Returns:
            Comparison results
        """
        if not rules:
            return {"error": "No rules provided for comparison"}

        # Set default scope if not provided
        scope = scope or self.default_scope

        # Evaluate each rule
        evaluations = []
        for rule in rules:
            eval_result = self.evaluate_rule(rule, context, scope)
            evaluations.append(
                {
                    "rule_id": rule.get("id", "unknown"),
                    "score": eval_result["overall_score"],
                    "passed": eval_result["passed"],
                    "evaluation": eval_result,
                }
            )

        # Sort evaluations by score (descending)
        evaluations.sort(key=lambda x: x["score"], reverse=True)

        # Determine the best rule
        best_rule = evaluations[0]

        # Calculate score improvements
        improvements = []
        if len(evaluations) > 1:
            for i in range(1, len(evaluations)):
                improvements.append(
                    {
                        "from_rule": evaluations[i]["rule_id"],
                        "to_rule": evaluations[0]["rule_id"],
                        "improvement": evaluations[0]["score"]
                        - evaluations[i]["score"],
                    }
                )

        return {
            "best_rule_id": best_rule["rule_id"],
            "best_score": best_rule["score"],
            "evaluations": evaluations,
            "improvements": improvements,
            "comparison_timestamp": datetime.now().isoformat(),
        }

    def get_evaluation_status(self, eval_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Get the status of rule evaluation.

        Args:
            eval_id: Optional evaluation ID to check specific evaluation

        Returns:
            Evaluation status information
        """
        # If checking current evaluation
        if eval_id is None or eval_id == self.current_eval_id:
            return {
                "evaluation_id": self.current_eval_id,
                "status": self.evaluation_status.value,
                "metrics": self.metrics,
            }

        # Otherwise, look up historical evaluation (not implemented in this placeholder)
        return {
            "evaluation_id": eval_id,
            "status": "unknown",
            "error": "Historical evaluation lookup not implemented",
        }

    def _compute_rule_hash(self, rule: Dict[str, Any]) -> str:
        """
        Compute a hash for a rule to use as a cache key.

        Args:
            rule: Rule to hash

        Returns:
            Hash string
        """
        import hashlib

        # Use rule id, type, and content for the hash
        try:
            # Extract fields likely to affect evaluation
            hash_dict = {
                "id": rule.get("id", ""),
                "type": rule.get("type", ""),
                "conditions": rule.get("conditions", []),
                "actions": rule.get("actions", []),
            }
            hash_input = json.dumps(hash_dict, sort_keys=True)
            return hashlib.md5(hash_input.encode()).hexdigest()
        except Exception as e:
            self.logger.warning(f"Error computing rule hash: {e}")
            # Fall back to rule ID
            return str(rule.get("id", hash(str(rule))))

    def evaluate_rules_batch(
        self,
        rules: List[Dict[str, Any]],
        context: Dict[str, Any],
        scope: Optional[EvaluationScope] = None,
        cost_limit: Optional[float] = None,
    ) -> List[Dict[str, Any]]:
        """
        Evaluate multiple rules in parallel for improved performance.

        Args:
            rules: List of rules to evaluate
            context: Context for rule evaluation
            scope: Scope of evaluation
            cost_limit: Maximum cost for this batch operation

        Returns:
            List of evaluation results
        """
        if not rules:
            return []

        # If batch size is 1, just use the regular method
        if len(rules) == 1:
            return [self.evaluate_rule(rules[0], context, scope, cost_limit)]

        # Set default values if not provided
        scope = scope or self.default_scope
        cost_limit = (
            cost_limit or self.cost_config.daily_cost_threshold_usd / 10
        )  # 10% of daily budget for batch

        # Create an evaluation ID and update status
        self.current_eval_id = f"batch_eval_{int(time.time())}"
        self.evaluation_status = EvaluationStatus.IN_PROGRESS

        # Log the start of batch evaluation
        self.logger.info(
            f"Starting batch rule evaluation (ID: {
                self.current_eval_id}, Batch size: {
                len(rules)}, Scope: {
                scope.value})")

        # Check cost budget
        if not self.cost_controller.can_make_api_call(check_cost=True):
            self.logger.error("Batch rule evaluation canceled due to cost limits")
            self.evaluation_status = EvaluationStatus.CANCELED
            return [{"error": "Rule evaluation canceled due to cost limits"}] * len(
                rules
            )

        # Initialize tracking metrics for this run
        start_time = time.time()
        total_cost = 0.0
        results = []
        cache_hits = 0

        # Check cache first
        cached_results = []
        rules_to_evaluate = []
        rule_indices = []

        for i, rule in enumerate(rules):
            rule_hash = self._compute_rule_hash(rule)
            cache_key = f"{rule_hash}_{scope.value}"

            if cache_key in self._evaluation_cache:
                # Use cached result
                cached_results.append((i, self._evaluation_cache[cache_key].copy()))
                cache_hits += 1
                self.metrics["cache_hits"] += 1
            else:
                # Mark for evaluation
                rules_to_evaluate.append(rule)
                rule_indices.append(i)

        # Sort cached results by original rule index
        cached_results.sort(key=lambda x: x[0])

        # Process remaining rules in parallel if there are any
        if rules_to_evaluate:
            # Allocate cost proportionally
            per_rule_cost_limit = cost_limit / max(1, len(rules_to_evaluate))

            # Evaluate in parallel
            with ProcessPoolExecutor(max_workers=self.max_workers) as executor:
                # Submit all tasks
                futures = []
                for i, rule in enumerate(rules_to_evaluate):
                    futures.append(
                        executor.submit(
                            self._evaluate_rule_task,
                            rule=rule,
                            context=context,
                            scope=scope,
                            cost_limit=per_rule_cost_limit,
                            task_id=i,
                        )
                    )

                # Process results as they complete
                for future in as_completed(futures):
                    try:
                        result, task_cost = future.result()
                        results.append(result)
                        total_cost += task_cost

                        # Check if we've exceeded the overall cost limit
                        if total_cost >= cost_limit:
                            self.logger.warning(
                                f"Cost limit reached during batch processing (${
                                    total_cost:.2f})")
                            break

                    except Exception as e:
                        self.logger.error(f"Error in parallel rule evaluation: {e}")
                        results.append(
                            {"error": str(e), "passed": False, "overall_score": 0.0}
                        )

        # Combine results from cache and parallel evaluation
        # Initialize with empty dictionaries instead of None to avoid type errors
        combined_results = [
            {"error": "Evaluation not completed", "passed": False, "overall_score": 0.0}
        ] * len(rules)

        # Insert cached results first
        for idx, result in cached_results:
            combined_results[idx] = result

        # Insert new evaluation results
        for i, result in enumerate(results):
            original_idx = rule_indices[i]
            combined_results[original_idx] = result

            # Cache this result for future use
            if isinstance(result, dict) and "error" not in result:
                rule_hash = self._compute_rule_hash(rules[original_idx])
                self._evaluation_cache[f"{rule_hash}_{scope.value}"] = result.copy()

        # Update generation status
        self.evaluation_status = EvaluationStatus.COMPLETED

        # Update metrics
        total_time = time.time() - start_time
        self.metrics["total_evaluations"] += len(rules)
        self.metrics["passed_evaluations"] += sum(
            1 for r in combined_results if r.get("passed", False)
        )
        self.metrics["failed_evaluations"] += sum(
            1 for r in combined_results if not r.get("passed", False)
        )
        self.metrics["total_cost"] += total_cost
        self.metrics["batch_evaluations"] += 1

        # Estimate sequential time for speedup calculation
        if len(rules_to_evaluate) > 0:
            estimated_sequential_time = (
                len(rules_to_evaluate) * 0.3
            )  # Rough estimate: 0.3s per rule
            if estimated_sequential_time > 0 and total_time > 0:
                speedup = estimated_sequential_time / total_time
                self.metrics["parallel_speedup"] = (
                    self.metrics["parallel_speedup"] + speedup
                ) / 2  # Running average

        # Track in metrics store
        self.metrics_store.store_metric(
            {
                "metric_type": "batch_rule_evaluation",
                "evaluation_id": self.current_eval_id,
                "batch_size": len(rules),
                "scope": scope.value,
                "successful_evaluations": sum(
                    1 for r in combined_results if r.get("passed", False)
                ),
                "failed_evaluations": sum(
                    1 for r in combined_results if not r.get("passed", False)
                ),
                "cache_hits": cache_hits,
                "cost": total_cost,
                "time": total_time,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        )

        self.logger.info(
            f"Batch rule evaluation completed (ID: {
                self.current_eval_id}, Evaluations: {
                len(rules)}, Cost: ${
                total_cost:.2f})")
        return combined_results

    def _evaluate_rule_task(
        self,
        rule: Dict[str, Any],
        context: Dict[str, Any],
        scope: EvaluationScope,
        cost_limit: float,
        task_id: int,
    ) -> Tuple[Dict[str, Any], float]:
        """
        Worker task for parallel rule evaluation.

        Args:
            rule: Rule to evaluate
            context: Context for evaluation
            scope: Scope of evaluation
            cost_limit: Cost limit for this task
            task_id: Task identifier

        Returns:
            Tuple of (evaluation_result, cost)
        """
        try:
            # Initialize result structure
            evaluation_result = {
                "rule_id": rule.get("id", "unknown"),
                "evaluation_id": f"{self.current_eval_id}_{task_id}",
                "scope": scope.value,
                "timestamp": datetime.now().isoformat(),
                "overall_score": 0.0,
                "details": {},
                "passed": False,
                "issues": [],
                "recommendations": [],
            }

            # Initialize tracking metrics for this evaluation
            total_cost = 0.0

            # Syntax evaluation
            if scope in [EvaluationScope.SYNTAX, EvaluationScope.COMPREHENSIVE]:
                syntax_result = self._evaluate_syntax(rule)
                evaluation_result["details"]["syntax"] = syntax_result
                total_cost += syntax_result["evaluation_cost"]

                # Early return if syntax check fails
                if not syntax_result["passed"]:
                    evaluation_result["overall_score"] = syntax_result["score"]
                    evaluation_result["passed"] = False
                    evaluation_result["issues"].extend(syntax_result["issues"])
                    evaluation_result["recommendations"].extend(
                        syntax_result["recommendations"]
                    )
                    return evaluation_result, total_cost

            # Logic evaluation
            if scope in [EvaluationScope.LOGIC, EvaluationScope.COMPREHENSIVE]:
                # Check if cost limit would be exceeded
                if total_cost >= cost_limit:
                    pass  # Skip this evaluation
                else:
                    logic_result = self._evaluate_logic(rule, context)
                    evaluation_result["details"]["logic"] = logic_result
                    total_cost += logic_result["evaluation_cost"]

                    evaluation_result["issues"].extend(logic_result["issues"])
                    evaluation_result["recommendations"].extend(
                        logic_result["recommendations"]
                    )

            # Coverage evaluation
            if scope in [EvaluationScope.COVERAGE, EvaluationScope.COMPREHENSIVE]:
                # Check if cost limit would be exceeded
                if total_cost >= cost_limit:
                    pass  # Skip this evaluation
                else:
                    coverage_result = self._evaluate_coverage(rule, context)
                    evaluation_result["details"]["coverage"] = coverage_result
                    total_cost += coverage_result["evaluation_cost"]

                    evaluation_result["issues"].extend(coverage_result["issues"])
                    evaluation_result["recommendations"].extend(
                        coverage_result["recommendations"]
                    )

            # Performance evaluation
            if scope in [EvaluationScope.PERFORMANCE, EvaluationScope.COMPREHENSIVE]:
                # Check if cost limit would be exceeded
                if total_cost >= cost_limit:
                    pass  # Skip this evaluation
                else:
                    performance_result = self._evaluate_performance(rule)
                    evaluation_result["details"]["performance"] = performance_result
                    total_cost += performance_result["evaluation_cost"]

                    evaluation_result["issues"].extend(performance_result["issues"])
                    evaluation_result["recommendations"].extend(
                        performance_result["recommendations"]
                    )

            # Calculate overall score (weighted average of all evaluations performed)
            scores = []
            weights = []

            if "syntax" in evaluation_result["details"]:
                scores.append(evaluation_result["details"]["syntax"]["score"])
                weights.append(0.3)  # 30% weight for syntax

            if "logic" in evaluation_result["details"]:
                scores.append(evaluation_result["details"]["logic"]["score"])
                weights.append(0.4)  # 40% weight for logic

            if "coverage" in evaluation_result["details"]:
                scores.append(evaluation_result["details"]["coverage"]["score"])
                weights.append(0.2)  # 20% weight for coverage

            if "performance" in evaluation_result["details"]:
                scores.append(evaluation_result["details"]["performance"]["score"])
                weights.append(0.1)  # 10% weight for performance

            # Compute weighted average
            if scores and weights:
                evaluation_result["overall_score"] = sum(
                    s * w for s, w in zip(scores, weights)
                ) / sum(weights)

            # Determine if the rule passed evaluation
            evaluation_result["passed"] = (
                evaluation_result["overall_score"] >= self.min_acceptable_score
            )

            # Sort issues and recommendations by importance
            evaluation_result["issues"].sort(
                key=lambda x: x.get("severity", 0), reverse=True
            )
            evaluation_result["recommendations"].sort(
                key=lambda x: x.get("importance", 0), reverse=True
            )

            return evaluation_result, total_cost

        except Exception as e:
            # Create error result
            error_result = {
                "rule_id": rule.get("id", "unknown"),
                "evaluation_id": f"{self.current_eval_id}_{task_id}",
                "error": str(e),
                "passed": False,
                "overall_score": 0.0,
            }
            return error_result, 0.0


def get_rule_evaluator(
    config: Optional[Dict[str, Any]] = None,
) -> RecursiveRuleEvaluator:
    """
    Get the singleton instance of RecursiveRuleEvaluator.

    Args:
        config: Optional configuration dictionary

    Returns:
        RecursiveRuleEvaluator instance
    """
    return RecursiveRuleEvaluator.get_instance(config)
