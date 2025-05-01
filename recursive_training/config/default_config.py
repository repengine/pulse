"""
Default Configuration for Recursive Training

This module provides default configuration values for the recursive training system,
including cost control settings, data pipeline configurations, and feature processing
parameters.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Union, Any


@dataclass
class CostControlConfig:
    """Configuration for cost control in recursive training."""
    
    # Token usage limits
    max_tokens_per_request: int = 8000
    max_total_tokens_per_day: int = 100000
    token_buffer_percentage: float = 0.1  # 10% buffer for safety
    
    # Request limits
    max_requests_per_minute: int = 10
    max_requests_per_hour: int = 100
    max_requests_per_day: int = 1000
    
    # Cost thresholds for automated throttling
    daily_cost_threshold_usd: float = 10.0
    emergency_shutdown_threshold_usd: float = 50.0
    
    # Retry and backoff settings
    max_retries: int = 3
    retry_delay_seconds: int = 5
    retry_backoff_factor: float = 2.0
    
    # Alert thresholds (percentage of limits)
    usage_alert_threshold: float = 0.8  # 80% of limit


@dataclass
class DataIngestionConfig:
    """Configuration for data ingestion in recursive training."""
    
    # Source settings
    data_sources: List[str] = field(default_factory=lambda: ["local", "api"])
    api_endpoint: Optional[str] = None
    api_key_env_var: str = "PULSE_API_KEY"
    
    # Ingestion parameters
    batch_size: int = 32
    parallel_ingestion: bool = True
    max_workers: int = 4
    
    # Validation and filtering
    validate_schema: bool = True
    filter_invalid_data: bool = True
    
    # Caching
    enable_cache: bool = True
    cache_ttl_seconds: int = 3600  # 1 hour


@dataclass
class DataStoreConfig:
    """Configuration for the data store in recursive training."""
    
    # Storage settings
    storage_path: str = "./data/recursive_training"
    use_compression: bool = True
    compression_level: int = 6  # For gzip, range 0-9
    
    # Data management
    max_storage_size_mb: int = 1000  # 1GB
    cleanup_threshold_percentage: float = 0.9  # 90% full triggers cleanup
    retention_days: int = 30
    
    # Indexing and access
    enable_indexing: bool = True
    index_fields: List[str] = field(default_factory=lambda: ["id", "timestamp", "source"])
    
    # Versioning
    enable_versioning: bool = True
    max_versions_per_item: int = 5


@dataclass
class FeatureProcessingConfig:
    """Configuration for feature processing in recursive training."""
    
    # Processing options
    default_processors: List[str] = field(default_factory=lambda: ["normalize", "tokenize"])
    enable_auto_scaling: bool = True
    
    # Feature extraction
    feature_extraction_methods: List[str] = field(default_factory=lambda: ["basic", "dict_rules", "object_rules"])
    embedding_model: str = "default"
    embedding_dimensions: int = 768
    
    # Caching and performance
    cache_processed_features: bool = True
    feature_cache_size: int = 1000  # Number of feature sets to cache
    parallel_processing: bool = True
    
    # Filtering
    min_feature_frequency: int = 5
    max_features_per_sample: int = 1000


@dataclass
class HybridRulesConfig:
    """Configuration for the hybrid rules approach in recursive training."""
    
    # Compatibility settings
    enable_dict_compatibility: bool = True
    prefer_object_representation: bool = False
    
    # Rule storage
    rules_path: str = "./data/rules"
    backup_rules: bool = True
    max_rule_backups: int = 10
    
    # Rule validation
    validate_rules: bool = True
    schema_validation_level: str = "strict"  # Options: "none", "basic", "strict"
    
    # Rule statistics
    track_rule_usage: bool = True
    track_rule_performance: bool = True


@dataclass
class LoggingConfig:
    """Configuration for logging in recursive training."""
    
    # Log levels
    console_log_level: str = "INFO"
    file_log_level: str = "DEBUG"
    
    # Log file settings
    log_dir: str = "./logs/recursive_training"
    max_log_file_size_mb: int = 10
    max_log_files: int = 10
    
    # Metrics logging
    log_metrics: bool = True
    metrics_interval_seconds: int = 60
    
    # Special logging
    log_cost_related_events: bool = True
    log_rule_changes: bool = True
    log_data_validation_issues: bool = True


@dataclass
class IntegrationConfig:
    """Configuration for integration with Pulse's systems."""
    
    # PulseAdapter settings
    enable_pulse_adapter: bool = True
    event_system_connection: bool = True
    symbolic_system_connection: bool = True
    register_event_handlers: bool = True
    
    # Event handling
    events_to_subscribe: List[str] = field(default_factory=lambda: [
        "pulse.model.trained",
        "pulse.rule.updated",
        "pulse.metrics.request"
    ])
    events_to_emit: List[str] = field(default_factory=lambda: [
        "recursive_training.rule.processed",
        "recursive_training.metrics.response",
        "recursive_training.cost.alert"
    ])
    
    # Cost Controller settings
    enable_cost_controller: bool = True
    daily_cost_limit_usd: float = 10.0
    monthly_cost_limit_usd: float = 100.0
    total_cost_limit_usd: float = 1000.0
    warning_threshold_percentage: int = 70
    critical_threshold_percentage: int = 90
    
    # API rate limits (used by Cost Controller)
    max_calls_per_minute: int = 60
    max_calls_per_hour: int = 500
    max_calls_per_day: int = 5000
    
    # General integration
    integrate_with_pulse_config: bool = True
    pulse_config_path: str = "../core/pulse_config.py"
    pulse_components_path: str = "../core"
    symbolic_system_path: str = "../symbolic_system"
    
    # Data conversion
    automatic_format_conversion: bool = True
    preserve_original_data: bool = True
    
    # Error handling
    max_integration_retries: int = 3
    retry_delay_seconds: int = 5
    fallback_to_local_operation: bool = True


@dataclass
class RecursiveTrainingConfig:
    """Master configuration for recursive training."""
    
    # Core settings
    enabled: bool = True
    environment: str = "development"  # Options: "development", "testing", "production"
    debug_mode: bool = False
    
    # Component configurations
    cost_control: CostControlConfig = field(default_factory=CostControlConfig)
    data_ingestion: DataIngestionConfig = field(default_factory=DataIngestionConfig)
    data_store: DataStoreConfig = field(default_factory=DataStoreConfig)
    feature_processing: FeatureProcessingConfig = field(default_factory=FeatureProcessingConfig)
    hybrid_rules: HybridRulesConfig = field(default_factory=HybridRulesConfig)
    logging: LoggingConfig = field(default_factory=LoggingConfig)
    integration: IntegrationConfig = field(default_factory=IntegrationConfig)


# Default configuration instance
default_config = RecursiveTrainingConfig()


def get_config() -> RecursiveTrainingConfig:
    """
    Get the current configuration for recursive training.
    
    Returns:
        RecursiveTrainingConfig: The current configuration
    """
    return default_config


def update_config(config_updates: Dict[str, Any]) -> RecursiveTrainingConfig:
    """
    Update the configuration with the provided values.
    
    Args:
        config_updates: Dictionary of configuration updates to apply
        
    Returns:
        RecursiveTrainingConfig: The updated configuration
    """
    # This is a placeholder for a more sophisticated config update mechanism
    # that would handle nested updates, validation, etc.
    global default_config
    
    # In a real implementation, we'd recursively update nested dataclasses
    # For now, this is a simple demonstration
    
    return default_config