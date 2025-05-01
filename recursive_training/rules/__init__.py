"""
Rules Module for Recursive Training

This module provides components for rule generation, evaluation, and management
within the recursive training system. It implements a hybrid approach supporting
both dictionary-based and object-oriented rule representations.

Components:
- RecursiveRuleGenerator: Generates rules using GPT-Symbolic feedback loops
- RecursiveRuleEvaluator: Evaluates effectiveness of generated rules
- RuleRepository: Stores, versions, and queries rules
- HybridRuleAdapter: Converts between dictionary and object rule formats
"""

from recursive_training.rules.rule_generator import RecursiveRuleGenerator, get_rule_generator
from recursive_training.rules.rule_evaluator import RecursiveRuleEvaluator, get_rule_evaluator
from recursive_training.rules.rule_repository import RuleRepository, get_rule_repository
from recursive_training.rules.hybrid_adapter import HybridRuleAdapter, get_hybrid_adapter

__all__ = [
    'RecursiveRuleGenerator',
    'RecursiveRuleEvaluator',
    'RuleRepository',
    'HybridRuleAdapter',
    'get_rule_generator',
    'get_rule_evaluator',
    'get_rule_repository',
    'get_hybrid_adapter',
]