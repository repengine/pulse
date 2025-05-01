"""
RecursiveDataIngestionManager

Responsible for ingesting data from various sources into the recursive training system.
Handles data collection, validation, transformation, and preprocessing before storage.
Includes cost control mechanisms for API requests and supports hybrid rules representation.
"""

import json
import logging
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Union, Tuple, Set, Iterator

import pandas as pd
from pydantic import BaseModel, ValidationError

# Import relevant Pulse components
from core.pulse_config import get_config
from core.bayesian_trust_tracker import bayesian_trust_tracker
from core.schemas import ForecastRecord
from learning.output_data_reader import OutputDataReader


class DataSource(BaseModel):
    """Base model for data source configuration"""
    source_id: str
    source_type: str
    enabled: bool = True
    priority: int = 1


class APISource(DataSource):
    """Configuration for API data sources"""
    endpoint: str
    auth_type: str = "api_key"
    headers: Dict[str, str] = {}
    rate_limit: Optional[int] = None
    token_usage_tracking: bool = True


class FileSource(DataSource):
    """Configuration for file-based data sources"""
    path: str
    file_pattern: str = "*.*"
    archive_after_ingestion: bool = False


class DatabaseSource(DataSource):
    """Configuration for database data sources"""
    connection_string: str
    query: str
    parameters: Dict[str, Any] = {}


class RecursiveDataIngestionManager:
    """
    Manages data ingestion for recursive training from multiple sources.
    
    Features:
    - Multi-source data collection (files, APIs, databases)
    - Data validation and schema enforcement
    - Incremental ingestion with change detection
    - Cost tracking and limiting for external API calls
    - Rate limiting and backoff strategies
    - Source prioritization
    
    Integrates with Pulse's existing data structures and handles hybrid rules representation.
    """
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize the RecursiveDataIngestionManager.
        
        Args:
            config_path: Optional path to configuration file
        """
        self.logger = logging.getLogger("RecursiveDataIngestionManager")
        
        # Get system configuration with fallback
        if PULSE_CONFIG_AVAILABLE:
            try:
                pulse_config = get_config()
                self.base_data_path = Path(pulse_config.get("data_path", "./data"))
            except Exception as e:
                self.logger.warning(f"Could not get Pulse config: {e}")
                self.base_data_path = Path("./data")
        else:
            self.base_data_path = Path("./data")
        
        # Load configuration if provided
        self.config = self._load_config(config_path)
        
        # Set up data sources
        self.sources: Dict[str, DataSource] = {}
        self._init_data_sources()
        
        # Track cost and usage
        self.api_call_count: Dict[str, int] = {}
        self.token_usage: Dict[str, int] = {}
        self.cost_tracker: Dict[str, float] = {}
        
        # Initialize OutputDataReader for accessing Pulse output data if available
        if OUTPUT_READER_AVAILABLE:
            try:
                self.output_reader = OutputDataReader(str(self.base_data_path))
            except Exception as e:
                self.logger.warning(f"Could not initialize OutputDataReader: {e}")
                self.output_reader = None
        else:
            self.output_reader = None
        
        # Track processed data for deduplication
        self.processed_data_hashes: Set[str] = set()
        
    def _load_config(self, config_path: Optional[str]) -> Dict[str, Any]:
        """
        Load configuration from file or use defaults.
        
        Args:
            config_path: Path to configuration file
            
        Returns:
            Configuration dictionary
        """
        if config_path and os.path.exists(config_path):
            try:
                with open(config_path, 'r') as f:
                    return json.load(f)
            except Exception as e:
                self.logger.error(f"Failed to load configuration from {config_path}: {e}")
        
        # Use default configuration from recursive_training.config if available
        try:
            # Import locally to avoid circular imports
            from recursive_training.config.default_config import get_config as get_rt_config
            return {"data_ingestion": get_rt_config().data_ingestion.__dict__}
        except ImportError:
            self.logger.warning("Could not import default config, using built-in defaults")
        
        # Built-in default configuration
        return {
            "batch_size": 32,
            "parallel_ingestion": True,
            "max_workers": 4,
            "validate_schema": True,
            "filter_invalid_data": True,
            "enable_cache": True,
            "cache_ttl_seconds": 3600,  # 1 hour
            "max_tokens_per_request": 8000,
            "max_total_tokens_per_day": 100000,
            "max_requests_per_minute": 10,
            "max_requests_per_hour": 100,
            "max_requests_per_day": 1000,
            "daily_cost_threshold_usd": 10.0,
            "emergency_shutdown_threshold_usd": 50.0,
        }
    
    def _init_data_sources(self) -> None:
        """
        Initialize data sources from configuration.
        """
        # Add default internal data sources
        self.sources["pulse_forecasts"] = FileSource(
            source_id="pulse_forecasts",
            source_type="file",
            path=str(self.base_data_path / "forecast_output"),
            file_pattern="*.json",
            priority=1
        )
        
        self.sources["symbolic_logs"] = FileSource(
            source_id="symbolic_logs",
            source_type="file",
            path=str(self.base_data_path / "symbolic_logs"),
            file_pattern="*.json",
            priority=1
        )
        
        self.sources["trust_logs"] = FileSource(
            source_id="trust_logs",
            source_type="file",
            path=str(self.base_data_path / "trust_logs"),
            file_pattern="*.json",
            priority=1
        )
        
        # Add configured sources from config
        for source_config in self.config.get("data_sources", []):
            source_id = source_config.get("source_id")
            source_type = source_config.get("source_type")
            
            if not source_id or not source_type:
                self.logger.warning(f"Skipping source with missing ID or type: {source_config}")
                continue
                
            try:
                if source_type == "api":
                    self.sources[source_id] = APISource(**source_config)
                elif source_type == "file":
                    self.sources[source_id] = FileSource(**source_config)
                elif source_type == "database":
                    self.sources[source_id] = DatabaseSource(**source_config)
                else:
                    self.logger.warning(f"Unknown source type: {source_type}")
            except ValidationError as e:
                self.logger.error(f"Invalid source configuration for {source_id}: {e}")
    
    def ingest_from_source(self, source_id: str) -> Tuple[int, int]:
        """
        Ingest data from a specific source.
        
        Args:
            source_id: ID of the source to ingest from
            
        Returns:
            Tuple of (records processed, records ingested)
        """
        if source_id not in self.sources:
            self.logger.error(f"Unknown source: {source_id}")
            return (0, 0)
            
        source = self.sources[source_id]
        
        if not source.enabled:
            self.logger.info(f"Source {source_id} is disabled")
            return (0, 0)
            
        self.logger.info(f"Ingesting data from {source_id}")
        
        if source.source_type == "api":
            return self._ingest_from_api(source_id, cast(APISource, source))
        elif source.source_type == "file":
            return self._ingest_from_file(source_id, cast(FileSource, source))
        elif source.source_type == "database":
            return self._ingest_from_database(source_id, cast(DatabaseSource, source))
        else:
            self.logger.error(f"Unsupported source type: {source.source_type}")
            return (0, 0)
    
    def _ingest_from_api(self, source_id: str, source: APISource) -> Tuple[int, int]:
        """
        Ingest data from an API source.
        
        Args:
            source_id: ID of the source
            source: API source configuration
            
        Returns:
            Tuple of (records processed, records ingested)
        """
        # Check rate limits and cost thresholds
        if not self._check_rate_limits(source_id):
            self.logger.warning(f"Rate limit exceeded for {source_id}")
            return (0, 0)
            
        if not self._check_cost_threshold(source_id):
            self.logger.warning(f"Cost threshold exceeded for {source_id}")
            return (0, 0)
            
        try:
            import requests
            
            # Make the API request
            response = requests.get(
                source.endpoint,
                headers=source.headers,
                timeout=30
            )
            
            # Update API call tracking
            self.api_call_count[source_id] = self.api_call_count.get(source_id, 0) + 1
            
            if response.status_code != 200:
                self.logger.error(f"API request failed: {response.status_code} - {response.text}")
                return (0, 0)
                
            # Parse the response
            data = response.json()
            
            # Update token usage tracking if enabled
            if source.token_usage_tracking:
                response_size = len(response.text)
                tokens_estimate = response_size / 4  # Rough estimate: 4 chars per token
                self.token_usage[source_id] = self.token_usage.get(source_id, 0) + int(tokens_estimate)
                
            # Process the data
            return self._process_data(source_id, data)
            
        except Exception as e:
            self.logger.error(f"Error ingesting from API {source_id}: {e}")
            return (0, 0)
    
    def _ingest_from_file(self, source_id: str, source: FileSource) -> Tuple[int, int]:
        """
        Ingest data from file sources.
        
        Args:
            source_id: ID of the source
            source: File source configuration
            
        Returns:
            Tuple of (records processed, records ingested)
        """
        import glob
        
        path_pattern = os.path.join(source.path, source.file_pattern)
        files = glob.glob(path_pattern)
        
        if not files:
            self.logger.info(f"No files found for pattern: {path_pattern}")
            return (0, 0)
            
        total_processed = 0
        total_ingested = 0
        
        for file_path in files:
            try:
                # Load data based on file extension
                if file_path.endswith('.json'):
                    with open(file_path, 'r') as f:
                        data = json.load(f)
                elif file_path.endswith('.csv'):
                    data = pd.read_csv(file_path).to_dict('records')
                else:
                    self.logger.warning(f"Unsupported file type: {file_path}")
                    continue
                    
                # Process the data
                processed, ingested = self._process_data(source_id, data)
                total_processed += processed
                total_ingested += ingested
                
                # Archive the file if configured
                if source.archive_after_ingestion:
                    archive_dir = os.path.join(os.path.dirname(file_path), "archived")
                    os.makedirs(archive_dir, exist_ok=True)
                    archive_path = os.path.join(archive_dir, os.path.basename(file_path))
                    os.rename(file_path, archive_path)
                    self.logger.info(f"Archived {file_path} to {archive_path}")
                
            except Exception as e:
                self.logger.error(f"Error processing file {file_path}: {e}")
        
        return (total_processed, total_ingested)
    
    def _ingest_from_database(self, source_id: str, source: DatabaseSource) -> Tuple[int, int]:
        """
        Ingest data from a database source.
        
        Args:
            source_id: ID of the source
            source: Database source configuration
            
        Returns:
            Tuple of (records processed, records ingested)
        """
        try:
            import sqlalchemy
            
            # Create database engine
            engine = sqlalchemy.create_engine(source.connection_string)
            
            # Execute the query
            with engine.connect() as connection:
                result = connection.execute(sqlalchemy.text(source.query), source.parameters)
                data = [dict(row) for row in result]
                
            # Process the data
            return self._process_data(source_id, data)
            
        except ImportError:
            self.logger.error("sqlalchemy not installed, cannot connect to database")
            return (0, 0)
        except Exception as e:
            self.logger.error(f"Error ingesting from database {source_id}: {e}")
            return (0, 0)
    
    def _process_data(self, source_id: str, data: Union[List[Dict[str, Any]], Dict[str, Any]]) -> Tuple[int, int]:
        """
        Process and validate ingested data.
        
        Args:
            source_id: ID of the source
            data: The data to process
            
        Returns:
            Tuple of (records processed, records ingested)
        """
        if isinstance(data, dict):
            data = [data]
        
        records_processed = len(data)
        records_ingested = 0
        
        # Get the RecursiveDataStore instance - import locally to avoid circular imports
        # We use a function to delay the import until needed
        def get_data_store():
            from recursive_training.data.data_store import RecursiveDataStore
            return RecursiveDataStore.get_instance()
            
        data_store = get_data_store()
        
        for record in data:
            # Skip already processed records
            record_hash = hash(frozenset(record.items()) if hasattr(record, 'items') else str(record))
            if record_hash in self.processed_data_hashes:
                continue
                
            # Validate schema if configured and validation is available
            if self.config.get("validate_schema", True):
                try:
                    # Attempt to validate using appropriate schema
                    if source_id == "pulse_forecasts" and FORECAST_RECORD_AVAILABLE:
                        ForecastRecord(**record)
                        # Additional schema validations could be added here
                    elif source_id == "pulse_forecasts":
                        self.logger.warning("ForecastRecord schema not available for validation")
                except ValidationError as e:
                    self.logger.warning(f"Schema validation failed for record from {source_id}: {e}")
                    if self.config.get("filter_invalid_data", True):
                        continue
                except Exception as e:
                    self.logger.warning(f"Unexpected error during schema validation: {e}")
                    if self.config.get("filter_invalid_data", True):
                        continue
            
            # Store the record
            data_store.store(
                record,
                metadata={
                    "source_id": source_id,
                    "ingestion_timestamp": datetime.now(timezone.utc).isoformat(),
                    "source_type": self.sources[source_id].source_type
                }
            )
            
            # Mark as processed
            self.processed_data_hashes.add(str(record_hash))  # Convert to string for type safety
            records_ingested += 1
        
        self.logger.info(f"Processed {records_processed} records from {source_id}, ingested {records_ingested}")
        return (records_processed, records_ingested)
    
    def ingest_all(self, priority_threshold: Optional[int] = None) -> Dict[str, Tuple[int, int]]:
        """
        Ingest data from all enabled sources.
        
        Args:
            priority_threshold: Optional priority threshold (only ingest from sources with priority <= threshold)
            
        Returns:
            Dictionary mapping source IDs to (processed, ingested) counts
        """
        results = {}
        
        # Sort sources by priority
        sorted_sources = sorted(
            [(source_id, source) for source_id, source in self.sources.items() if source.enabled],
            key=lambda x: x[1].priority
        )
        
        for source_id, source in sorted_sources:
            if priority_threshold is not None and source.priority > priority_threshold:
                continue
                
            processed, ingested = self.ingest_from_source(source_id)
            results[source_id] = (processed, ingested)
        
        return results
    
    def ingest_pulse_outputs(self) -> Dict[str, Tuple[int, int]]:
        """
        Ingest data specifically from Pulse output files.
        
        Returns:
            Dictionary mapping source IDs to (processed, ingested) counts
        """
        results = {}
        pulse_source_ids = ["pulse_forecasts", "symbolic_logs", "trust_logs"]
        
        for source_id in pulse_source_ids:
            if source_id in self.sources and self.sources[source_id].enabled:
                processed, ingested = self.ingest_from_source(source_id)
                results[source_id] = (processed, ingested)
        
        return results
    
    def get_rule_data(self) -> List[Dict[str, Any]]:
        """
        Get rule-related data for recursive training.
        
        Returns:
            List of rule data records
        """
        try:
            # Attempt to load rule data from various sources
            rule_data = []
            
            # From simulation engine
            try:
                # Changed to safer approach - check if module exists and contains the function
                import importlib
                sim_engine = importlib.import_module('simulation_engine.causal_rules')
                if hasattr(sim_engine, 'get_active_rules'):
                    active_rules = sim_engine.get_active_rules()
                    for rule_id, rule in active_rules.items():
                        trust_score = 0.5  # Default value
                        if BAYESIAN_TRUST_AVAILABLE:
                            trust_score = bayesian_trust_tracker.get_trust(rule_id)
                            
                        rule_data.append({
                            "rule_id": rule_id,
                            "rule_type": "causal",
                            "rule_definition": rule,
                            "trust_score": trust_score
                        })
            except (ImportError, AttributeError, ModuleNotFoundError) as e:
                self.logger.warning(f"Could not load causal rules: {str(e)}")
            
            # From symbolic system
            try:
                # Changed to safer approach - check if module exists and contains the function
                import importlib
                sym_system = importlib.import_module('symbolic_system.symbolic_utils')
                if hasattr(sym_system, 'get_active_symbolic_rules'):
                    symbolic_rules = sym_system.get_active_symbolic_rules()
                    for rule_id, rule in symbolic_rules.items():
                        trust_score = 0.5  # Default value
                        if BAYESIAN_TRUST_AVAILABLE:
                            trust_score = bayesian_trust_tracker.get_trust(rule_id)
                            
                        rule_data.append({
                            "rule_id": rule_id,
                            "rule_type": "symbolic",
                            "rule_definition": rule,
                            "trust_score": trust_score
                        })
            except (ImportError, AttributeError, ModuleNotFoundError) as e:
                self.logger.warning(f"Could not load symbolic rules: {str(e)}")
                
            return rule_data
            
        except Exception as e:
            self.logger.error(f"Error retrieving rule data: {e}")
            return []
            
    def get_system_metadata(self) -> Dict[str, Any]:
        """
        Get system metadata for recursive training.
        
        Returns:
            Dictionary of system metadata
        """
        metadata = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "active_sources": [s for s in self.sources.keys() if self.sources[s].enabled],
            "rule_count": len(self.get_rule_data()),
            "token_usage": sum(self.token_usage.values()),
            "api_call_count": sum(self.api_call_count.values())
        }
        
        # Add pulse version if available
        if PULSE_CONFIG_AVAILABLE:
            try:
                metadata["pulse_version"] = get_config().get("version", "unknown")
            except Exception as e:
                self.logger.warning(f"Could not get Pulse version: {e}")
                metadata["pulse_version"] = "unknown"
        else:
            metadata["pulse_version"] = "unknown"
            
        return metadata
    
    def _check_rate_limits(self, source_id: str) -> bool:
        """
        Check if source is within rate limits.
        
        Args:
            source_id: ID of the source to check
            
        Returns:
            Whether the source is within rate limits
        """
        # Implementation would depend on how rate limits are tracked
        # This is a simplified placeholder
        current_rate = self.api_call_count.get(source_id, 0)
        max_rate = self.config.get("max_requests_per_hour", 100)
        return current_rate < max_rate
    
    def _check_cost_threshold(self, source_id: str) -> bool:
        """
        Check if source is within cost thresholds.
        
        Args:
            source_id: ID of the source to check
            
        Returns:
            Whether the source is within cost thresholds
        """
        # Implementation would depend on how costs are tracked and calculated
        # This is a simplified placeholder
        current_cost = self.cost_tracker.get(source_id, 0.0)
        max_cost = self.config.get("daily_cost_threshold_usd", 10.0)
        return current_cost < max_cost
    
    def get_cost_summary(self) -> Dict[str, Any]:
        """
        Get a summary of cost-related metrics.
        
        Returns:
            Dictionary of cost metrics
        """
        return {
            "total_api_calls": sum(self.api_call_count.values()),
            "total_tokens": sum(self.token_usage.values()),
            "estimated_cost_usd": sum(self.cost_tracker.values()),
            "by_source": {
                source_id: {
                    "api_calls": self.api_call_count.get(source_id, 0),
                    "tokens": self.token_usage.get(source_id, 0),
                    "cost_usd": self.cost_tracker.get(source_id, 0.0)
                }
                for source_id in self.sources.keys()
            }
        }


# Singleton instance
_instance = None

def get_ingestion_manager(config_path: Optional[str] = None) -> RecursiveDataIngestionManager:
    """
    Get the singleton instance of RecursiveDataIngestionManager.
    
    Args:
        config_path: Optional path to configuration file
        
    Returns:
        RecursiveDataIngestionManager instance
    """
    global _instance
    if _instance is None:
        _instance = RecursiveDataIngestionManager(config_path)
    return _instance