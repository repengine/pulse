"""
HybridRuleAdapter Module

This module provides an adapter for converting between dictionary-based and
object-oriented rule representations. It ensures compatibility with existing Pulse
components while providing the benefits of strong typing and OOP features.
"""

import logging
import json
import inspect
from datetime import datetime
from typing import Any, Dict, List, Optional, Union, Type, TypeVar, get_type_hints
from dataclasses import dataclass, field, asdict, is_dataclass

# Import recursive training components
from recursive_training.integration.cost_controller import get_cost_controller
from recursive_training.config.default_config import get_config


# Type variable for rule classes
T = TypeVar("T")


@dataclass
class RuleCondition:
    """Base class for rule conditions."""

    type: str
    parameters: Dict[str, Any] = field(default_factory=dict)
    description: Optional[str] = None


@dataclass
class RuleAction:
    """Base class for rule actions."""

    type: str
    parameters: Dict[str, Any] = field(default_factory=dict)
    description: Optional[str] = None


@dataclass
class RuleMetadata:
    """Metadata for rules."""

    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())
    version: int = 1
    status: str = "active"
    generator: Optional[str] = None
    previous_version: Optional[int] = None
    source: Optional[str] = None
    tags: List[str] = field(default_factory=list)


@dataclass
class Rule:
    """Object representation of a rule."""

    id: str
    type: str
    conditions: List[RuleCondition] = field(default_factory=list)
    actions: List[RuleAction] = field(default_factory=list)
    priority: int = 1
    description: Optional[str] = None
    metadata: RuleMetadata = field(default_factory=RuleMetadata)
    enabled: bool = True

    def to_dict(self) -> Dict[str, Any]:
        """Convert rule to dictionary representation."""
        return asdict(self)


class ConversionError(Exception):
    """Exception raised when conversion between formats fails."""

    pass


class HybridRuleAdapter:
    """
    Adapter for converting between dictionary and object rule representations.

    Features:
    - Bidirectional conversion between dict and object formats
    - Custom rule class registration
    - Validation during conversion
    - Support for nested rule structures
    - Cost tracking for conversion operations
    """

    # Singleton instance
    _instance = None

    @classmethod
    def get_instance(
        cls, config: Optional[Dict[str, Any]] = None
    ) -> "HybridRuleAdapter":
        """
        Get or create the singleton instance of HybridRuleAdapter.

        Args:
            config: Optional configuration dictionary

        Returns:
            HybridRuleAdapter instance
        """
        if cls._instance is None:
            cls._instance = HybridRuleAdapter(config)
        return cls._instance

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the HybridRuleAdapter.

        Args:
            config: Optional configuration dictionary
        """
        self.logger = logging.getLogger("HybridRuleAdapter")

        # Load configuration
        self.config = config or get_config().hybrid_rules

        # Initialize cost controller
        self.cost_controller = get_cost_controller()

        # Initialize registered rule classes
        self.rule_classes = {"generic": Rule}

        # Initialize registered condition classes
        self.condition_classes = {}

        # Initialize registered action classes
        self.action_classes = {}

        # Configure adapter settings
        if isinstance(self.config, dict):
            self.enable_dict_compatibility = self.config.get(
                "enable_dict_compatibility", True
            )
            self.prefer_object_representation = self.config.get(
                "prefer_object_representation", False
            )
        else:
            self.enable_dict_compatibility = self.config.enable_dict_compatibility
            self.prefer_object_representation = self.config.prefer_object_representation

        self.logger.info("HybridRuleAdapter initialized")

    def register_rule_class(self, rule_type: str, rule_class: Type[Any]) -> None:
        """
        Register a custom rule class for a specific rule type.

        Args:
            rule_type: Type of rule
            rule_class: Custom rule class
        """
        if not is_dataclass(rule_class):
            raise ValueError(f"Rule class {rule_class.__name__} must be a dataclass")

        self.rule_classes[rule_type] = rule_class
        self.logger.debug(
            f"Registered rule class {rule_class.__name__} for type {rule_type}"
        )

    def register_condition_class(
        self, condition_type: str, condition_class: Type[Any]
    ) -> None:
        """
        Register a custom condition class for a specific condition type.

        Args:
            condition_type: Type of condition
            condition_class: Custom condition class
        """
        if not is_dataclass(condition_class):
            raise ValueError(
                f"Condition class {condition_class.__name__} must be a dataclass"
            )

        self.condition_classes[condition_type] = condition_class
        self.logger.debug(
            f"Registered condition class {condition_class.__name__} for type {condition_type}"
        )

    def register_action_class(self, action_type: str, action_class: Type[Any]) -> None:
        """
        Register a custom action class for a specific action type.

        Args:
            action_type: Type of action
            action_class: Custom action class
        """
        if not is_dataclass(action_class):
            raise ValueError(
                f"Action class {action_class.__name__} must be a dataclass"
            )

        self.action_classes[action_type] = action_class
        self.logger.debug(
            f"Registered action class {action_class.__name__} for type {action_type}"
        )

    def to_object(
        self, rule_dict: Dict[str, Any], rule_class: Optional[Type[T]] = None
    ) -> T:
        """
        Convert a rule dictionary to an object representation.

        Args:
            rule_dict: Rule in dictionary format
            rule_class: Optional specific rule class to use

        Returns:
            Rule object
        """
        start_time = datetime.now()

        try:
            # Determine rule type and class
            rule_type = rule_dict.get("type", "generic")

            if rule_class is None:
                rule_class = self.rule_classes.get(
                    rule_type, self.rule_classes["generic"]
                )

            # Convert conditions to objects
            conditions = []
            for cond_dict in rule_dict.get("conditions", []):
                cond_type = cond_dict.get("type", "")
                condition_class = self.condition_classes.get(cond_type, RuleCondition)
                conditions.append(self._dict_to_dataclass(cond_dict, condition_class))

            # Convert actions to objects
            actions = []
            for act_dict in rule_dict.get("actions", []):
                act_type = act_dict.get("type", "")
                action_class = self.action_classes.get(act_type, RuleAction)
                actions.append(self._dict_to_dataclass(act_dict, action_class))

            # Convert metadata
            metadata_dict = rule_dict.get("metadata", {})
            metadata = self._dict_to_dataclass(metadata_dict, RuleMetadata)

            # Prepare rule constructor arguments
            rule_args = rule_dict.copy()

            # Remove fields that we've processed separately
            for field in ["conditions", "actions", "metadata"]:
                if field in rule_args:
                    del rule_args[field]

            # Create rule object
            rule_object = rule_class(
                **rule_args, conditions=conditions, actions=actions, metadata=metadata
            )

            # Track cost
            self._track_conversion_cost("to_object", rule_dict, start_time)

            return rule_object

        except Exception as e:
            self.logger.error(f"Error converting rule dictionary to object: {e}")
            self._track_conversion_cost("to_object_failed", rule_dict, start_time)
            raise ConversionError(f"Failed to convert rule dictionary to object: {e}")

    def to_dict(self, rule_object: Any) -> Dict[str, Any]:
        """
        Convert a rule object to a dictionary representation.

        Args:
            rule_object: Rule object

        Returns:
            Rule dictionary
        """
        start_time = datetime.now()

        try:
            # Check if the object is a dataclass
            if not is_dataclass(rule_object):
                raise ValueError("Rule object must be a dataclass")

            # Convert to dictionary
            rule_dict = asdict(rule_object)

            # Track cost
            self._track_conversion_cost("to_dict", rule_dict, start_time)

            return rule_dict

        except Exception as e:
            self.logger.error(f"Error converting rule object to dictionary: {e}")
            # Estimate cost based on object complexity
            self._track_conversion_cost("to_dict_failed", {"error": str(e)}, start_time)
            raise ConversionError(f"Failed to convert rule object to dictionary: {e}")

    def _dict_to_dataclass(self, data_dict: Dict[str, Any], target_class: Type[T]) -> T:
        """
        Convert a dictionary to a dataclass instance.

        Args:
            data_dict: Dictionary to convert
            target_class: Target dataclass

        Returns:
            Dataclass instance
        """
        if not is_dataclass(target_class):
            raise ValueError(f"{target_class.__name__} is not a dataclass")

        # Get field information for the dataclass
        type_hints = get_type_hints(target_class)

        # Prepare constructor arguments
        constructor_args = {}

        for field_name, field_type in type_hints.items():
            if field_name in data_dict:
                field_value = data_dict[field_name]

                # Handle nested dataclasses
                if (
                    inspect.isclass(field_type)
                    and is_dataclass(field_type)
                    and isinstance(field_value, dict)
                ):
                    constructor_args[field_name] = self._dict_to_dataclass(
                        field_value, field_type
                    )

                # Handle lists of dataclasses
                elif (
                    getattr(field_type, "__origin__", None) is list
                    and inspect.isclass(getattr(field_type, "__args__", [None])[0])
                    and is_dataclass(getattr(field_type, "__args__", [None])[0])
                    and isinstance(field_value, list)
                ):
                    item_class = field_type.__args__[0]
                    constructor_args[field_name] = [
                        self._dict_to_dataclass(item, item_class)
                        if isinstance(item, dict)
                        else item
                        for item in field_value
                    ]

                else:
                    constructor_args[field_name] = field_value

        return target_class(**constructor_args)

    def _track_conversion_cost(
        self, operation: str, data: Dict[str, Any], start_time: datetime
    ) -> None:
        """
        Track the cost of conversion operations.

        Args:
            operation: Name of the operation
            data: Data being converted
            start_time: Start time of the operation
        """
        # This is a placeholder implementation. In a real system, you would
        # track actual costs based on complexity, resource usage, etc.

        # Calculate complexity based on rule structure
        data_str = json.dumps(data)
        complexity = len(data_str) / 1000  # Complexity per KB

        # Calculate duration
        duration = (datetime.now() - start_time).total_seconds()

        # Base cost plus complexity and duration factors
        cost = 0.0001 + (complexity * 0.0001) + (duration * 0.0001)

        # Track using cost controller
        self.cost_controller.track_cost(direct_cost=cost)

    def adapt_rule(
        self, rule: Union[Dict[str, Any], Any]
    ) -> Union[Dict[str, Any], Any]:
        """
        Adapt a rule to the preferred representation format.

        Args:
            rule: Rule in either dictionary or object format

        Returns:
            Rule in the preferred format
        """
        # Determine current format
        is_dict = isinstance(rule, dict)
        is_object = is_dataclass(rule) if not is_dict else False

        # Convert if needed based on preference
        if self.prefer_object_representation and is_dict:
            return self.to_object(rule)
        elif not self.prefer_object_representation and is_object:
            return self.to_dict(rule)

        # Already in preferred format
        return rule

    def validate_rule(self, rule: Union[Dict[str, Any], Any]) -> bool:
        """
        Validate a rule in either format.

        Args:
            rule: Rule in either dictionary or object format

        Returns:
            True if valid, False otherwise
        """
        # Determine format
        is_dict = isinstance(rule, dict)

        try:
            # For dict format, try converting to object to validate
            if is_dict:
                self.to_object(rule)
            else:
                # For object format, validate dataclass structure
                if not is_dataclass(rule):
                    return False

                # Convert to dict and back to validate
                rule_dict = self.to_dict(rule)
                self.to_object(rule_dict)

            return True

        except Exception as e:
            self.logger.warning(f"Rule validation failed: {e}")
            return False


def get_hybrid_adapter(config: Optional[Dict[str, Any]] = None) -> HybridRuleAdapter:
    """
    Get the singleton instance of HybridRuleAdapter.

    Args:
        config: Optional configuration dictionary

    Returns:
        HybridRuleAdapter instance
    """
    return HybridRuleAdapter.get_instance(config)
