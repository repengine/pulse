"""
MetricsStore

Responsible for storing, retrieving, and querying metrics for the
recursive training system. Provides a centralized repository for tracking
training metrics, model performance, and associated costs.
"""

import json
import logging
import os
import pickle
import gzip
import hashlib
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Union, Tuple, Set, Iterator, Callable
from collections import defaultdict

try:
    import numpy as np
    NUMPY_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False

try:
    import pandas as pd
    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False

# Import relevant Pulse components with graceful fallbacks
try:
    from core.pulse_config import PulseConfig
    PULSE_CONFIG_AVAILABLE = True
except ImportError:
    PULSE_CONFIG_AVAILABLE = False
    # Define a minimal config class as fallback
    class PulseConfig:
        """Minimal PulseConfig implementation for fallback."""
        def __init__(self):
            pass
            
        def get(self, key, default=None):
            return default


class MetricsStore:
    """
    Centralized storage system for recursive training metrics.
    
    Features:
    - Specialized for time series metrics data
    - Efficient storage and retrieval of metrics
    - Support for metric aggregation and analysis
    - Cost tracking for API and token usage
    - Integration with model evaluation metrics
    - Support for metric visualization and reporting
    
    Designed to complement RecursiveDataStore and support the recursive training
    evaluation process.
    """
    
    # Singleton instance
    _instance = None
    
    @classmethod
    def get_instance(cls, config: Optional[Dict[str, Any]] = None) -> 'MetricsStore':
        """
        Get or create the singleton instance of MetricsStore.
        
        Args:
            config: Optional configuration dictionary
            
        Returns:
            MetricsStore instance
        """
        if cls._instance is None:
            cls._instance = MetricsStore(config)
        return cls._instance
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the MetricsStore.
        
        Args:
            config: Optional configuration dictionary
        """
        self.logger = logging.getLogger("MetricsStore")
        
        # Load configuration with fallback
        try:
            if PULSE_CONFIG_AVAILABLE:
                pulse_config = PulseConfig()
            else:
                pulse_config = PulseConfig()  # Fallback implementation
        except Exception as e:
            self.logger.warning(f"Could not initialize PulseConfig: {e}")
            pulse_config = PulseConfig()  # Fallback implementation
        self.config = config or {}
        
        # Set up storage paths
        base_path = self.config.get("metrics_path", "./data/recursive_training/metrics")
        self.base_path = Path(base_path)
        self.metrics_path = self.base_path / "data"
        self.index_path = self.base_path / "indices"
        self.meta_path = self.base_path / "metadata"
        
        # Create directories if they don't exist
        self.metrics_path.mkdir(parents=True, exist_ok=True)
        self.index_path.mkdir(parents=True, exist_ok=True)
        self.meta_path.mkdir(parents=True, exist_ok=True)
        
        # Initialize metrics storage
        self.metrics_cache = {}
        self.metrics_indices = self._load_indices()
        
        # Configure storage options
        self.use_compression = self.config.get("use_compression", True)
        self.compression_level = self.config.get("compression_level", 6)
        self.enable_caching = self.config.get("enable_caching", True)
        self.max_cache_size = self.config.get("max_cache_size", 1000)
        
        # Initialize cost tracking
        self.cost_thresholds = {
            "warning_threshold": self.config.get("warning_cost_threshold", 10.0),
            "critical_threshold": self.config.get("critical_cost_threshold", 50.0),
            "shutdown_threshold": self.config.get("shutdown_cost_threshold", 100.0)
        }
        
        # Load existing metrics summary
        self._load_metrics_summary()

    def _load_indices(self) -> Dict[str, Dict[str, List[str]]]:
        """
        Load metrics indices from disk or create new ones.
        
        Returns:
            Dictionary of index dictionaries
        """
        indices_file = self.index_path / "metrics_indices.json"
        if os.path.exists(indices_file):
            try:
                with open(indices_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                self.logger.error(f"Failed to load metrics indices, creating new ones: {e}")
        
        # Default indices
        return {
            "by_type": {},
            "by_model": {},
            "by_date": {},
            "by_tag": {}
        }
    
    def _save_indices(self) -> None:
        """Save indices to disk."""
        indices_file = self.index_path / "metrics_indices.json"
        try:
            with open(indices_file, 'w') as f:
                json.dump(self.metrics_indices, f)
        except Exception as e:
            self.logger.error(f"Failed to save metrics indices: {e}")
    
    def _load_metrics_summary(self) -> None:
        """Load metrics summary from disk."""
        summary_file = self.meta_path / "metrics_summary.json"
        if os.path.exists(summary_file):
            try:
                with open(summary_file, 'r') as f:
                    self.metrics_summary = json.load(f)
            except Exception as e:
                self.logger.error(f"Failed to load metrics summary: {e}")
                self.metrics_summary = self._create_default_summary()
        else:
            self.metrics_summary = self._create_default_summary()
    
    def _create_default_summary(self) -> Dict[str, Any]:
        """
        Create a default metrics summary.
        
        Returns:
            Default metrics summary dictionary
        """
        return {
            "total_metrics": 0,
            "metrics_by_type": {},
            "time_range": {
                "start": None,
                "end": None
            },
            "models": set(),
            "tags": set(),
            "cost_tracking": {
                "total_cost": 0.0,
                "api_calls": 0,
                "token_usage": 0
            }
        }
    
    def _save_metrics_summary(self) -> None:
        """Save metrics summary to disk."""
        # Convert sets to lists for JSON serialization
        summary_to_save = self.metrics_summary.copy()
        summary_to_save["models"] = list(summary_to_save["models"])
        summary_to_save["tags"] = list(summary_to_save["tags"])
        
        summary_file = self.meta_path / "metrics_summary.json"
        try:
            with open(summary_file, 'w') as f:
                json.dump(summary_to_save, f)
        except Exception as e:
            self.logger.error(f"Failed to save metrics summary: {e}")
    
    def _generate_metric_id(self, metric_data: Dict[str, Any]) -> str:
        """
        Generate a unique ID for a metric.
        
        Args:
            metric_data: The metric data
            
        Returns:
            Unique metric ID
        """
        # Use timestamp, metric type, and model as the basis for ID
        timestamp = metric_data.get("timestamp", datetime.now(timezone.utc).isoformat())
        metric_type = metric_data.get("metric_type", "unknown")
        model = metric_data.get("model", "unknown")
        
        # Create a string representation
        id_base = f"{timestamp}_{metric_type}_{model}"
        
        # Hash the string
        return hashlib.md5(id_base.encode()).hexdigest()
    
    def _get_metric_path(self, metric_id: str) -> Path:
        """
        Get the path for storing a metric.
        
        Args:
            metric_id: The metric ID
            
        Returns:
            Path object for the storage location
        """
        # Use first few chars of the ID for directory structure
        prefix = metric_id[:2]
        metric_file = self.metrics_path / prefix / f"{metric_id}.json"
        metric_file.parent.mkdir(parents=True, exist_ok=True)
        return metric_file
    
    def _update_indices(self, metric_id: str, metric_data: Dict[str, Any]) -> None:
        """
        Update indices with a new or updated metric.
        
        Args:
            metric_id: The metric ID
            metric_data: The metric data
        """
        # Update type index
        metric_type = metric_data.get("metric_type", "unknown")
        if metric_type not in self.metrics_indices["by_type"]:
            self.metrics_indices["by_type"][metric_type] = []
        if metric_id not in self.metrics_indices["by_type"][metric_type]:
            self.metrics_indices["by_type"][metric_type].append(metric_id)
        
        # Update model index
        model = metric_data.get("model", "unknown")
        if model not in self.metrics_indices["by_model"]:
            self.metrics_indices["by_model"][model] = []
        if metric_id not in self.metrics_indices["by_model"][model]:
            self.metrics_indices["by_model"][model].append(metric_id)
        
        # Update date index
        timestamp = metric_data.get("timestamp", datetime.now(timezone.utc).isoformat())
        date_part = timestamp.split("T")[0] if "T" in timestamp else timestamp.split(" ")[0]
        if date_part not in self.metrics_indices["by_date"]:
            self.metrics_indices["by_date"][date_part] = []
        if metric_id not in self.metrics_indices["by_date"][date_part]:
            self.metrics_indices["by_date"][date_part].append(metric_id)
        
        # Update tag index
        tags = metric_data.get("tags", [])
        for tag in tags:
            if tag not in self.metrics_indices["by_tag"]:
                self.metrics_indices["by_tag"][tag] = []
            if metric_id not in self.metrics_indices["by_tag"][tag]:
                self.metrics_indices["by_tag"][tag].append(metric_id)
        
        # Save indices
        self._save_indices()
    
    def _update_summary(self, metric_data: Dict[str, Any]) -> None:
        """
        Update metrics summary with new metric data.
        
        Args:
            metric_data: The metric data
        """
        # Update total metrics count
        self.metrics_summary["total_metrics"] += 1
        
        # Update metrics by type
        metric_type = metric_data.get("metric_type", "unknown")
        if metric_type not in self.metrics_summary["metrics_by_type"]:
            self.metrics_summary["metrics_by_type"][metric_type] = 0
        self.metrics_summary["metrics_by_type"][metric_type] += 1
        
        # Update time range
        timestamp = metric_data.get("timestamp")
        if timestamp:
            if self.metrics_summary["time_range"]["start"] is None or timestamp < self.metrics_summary["time_range"]["start"]:
                self.metrics_summary["time_range"]["start"] = timestamp
            if self.metrics_summary["time_range"]["end"] is None or timestamp > self.metrics_summary["time_range"]["end"]:
                self.metrics_summary["time_range"]["end"] = timestamp
        
        # Update models and tags
        model = metric_data.get("model")
        if model:
            self.metrics_summary["models"].add(model)
        
        tags = metric_data.get("tags", [])
        for tag in tags:
            self.metrics_summary["tags"].add(tag)
        
        # Update cost tracking if present
        cost = metric_data.get("cost", 0.0)
        api_calls = metric_data.get("api_calls", 0)
        token_usage = metric_data.get("token_usage", 0)
        
        self.metrics_summary["cost_tracking"]["total_cost"] += cost
        self.metrics_summary["cost_tracking"]["api_calls"] += api_calls
        self.metrics_summary["cost_tracking"]["token_usage"] += token_usage
        
        # Save updated summary
        self._save_metrics_summary()
    
    def store_metric(self, metric_data: Dict[str, Any]) -> str:
        """
        Store a metric record.
        
        Args:
            metric_data: The metric data to store
            
        Returns:
            Metric ID of the stored data
        """
        # Ensure timestamp is present
        if "timestamp" not in metric_data:
            metric_data["timestamp"] = datetime.now(timezone.utc).isoformat()
        
        # Generate ID if not provided
        metric_id = metric_data.get("id")
        if metric_id is None:
            metric_id = self._generate_metric_id(metric_data)
            metric_data["id"] = metric_id
        
        # Store the metric
        metric_path = self._get_metric_path(metric_id)
        try:
            with open(metric_path, 'w') as f:
                json.dump(metric_data, f)
            
            # Update indices and summary
            self._update_indices(metric_id, metric_data)
            self._update_summary(metric_data)
            
            # Store in cache if enabled
            if self.enable_caching:
                self.metrics_cache[metric_id] = metric_data
                
                # Trim cache if too large
                if len(self.metrics_cache) > self.max_cache_size:
                    # Remove oldest items (simplistic approach)
                    keys_to_remove = sorted(self.metrics_cache.keys())[:len(self.metrics_cache) - self.max_cache_size]
                    for key in keys_to_remove:
                        del self.metrics_cache[key]
            
            return metric_id
            
        except Exception as e:
            self.logger.error(f"Failed to store metric: {e}")
            raise
    
    def get_metric(self, metric_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve a metric by ID.
        
        Args:
            metric_id: The metric ID
            
        Returns:
            The metric data or None if not found
        """
        # Check cache first if enabled
        if self.enable_caching and metric_id in self.metrics_cache:
            return self.metrics_cache[metric_id]
        
        # Otherwise load from disk
        metric_path = self._get_metric_path(metric_id)
        if not os.path.exists(metric_path):
            return None
        
        try:
            with open(metric_path, 'r') as f:
                metric_data = json.load(f)
            
            # Add to cache if enabled
            if self.enable_caching:
                self.metrics_cache[metric_id] = metric_data
                
            return metric_data
            
        except Exception as e:
            self.logger.error(f"Failed to retrieve metric {metric_id}: {e}")
            return None
    
    def query_metrics(self, 
                    metric_types: Optional[List[str]] = None,
                    models: Optional[List[str]] = None,
                    tags: Optional[List[str]] = None,
                    start_date: Optional[str] = None,
                    end_date: Optional[str] = None,
                    limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Query metrics based on criteria.
        
        Args:
            metric_types: Optional list of metric types to filter by
            models: Optional list of models to filter by
            tags: Optional list of tags to filter by
            start_date: Optional start date (ISO format)
            end_date: Optional end date (ISO format)
            limit: Optional maximum number of results
            
        Returns:
            List of metrics matching the criteria
        """
        matching_ids = set()
        id_sets = []
        
        # Filter by metric type
        if metric_types:
            type_ids = set()
            for metric_type in metric_types:
                if metric_type in self.metrics_indices["by_type"]:
                    type_ids.update(self.metrics_indices["by_type"][metric_type])
            id_sets.append(type_ids)
        
        # Filter by model
        if models:
            model_ids = set()
            for model in models:
                if model in self.metrics_indices["by_model"]:
                    model_ids.update(self.metrics_indices["by_model"][model])
            id_sets.append(model_ids)
        
        # Filter by tags
        if tags:
            tag_ids = set()
            for tag in tags:
                if tag in self.metrics_indices["by_tag"]:
                    tag_ids.update(self.metrics_indices["by_tag"][tag])
            id_sets.append(tag_ids)
        
        # Filter by date range
        date_ids = set()
        if start_date or end_date:
            all_dates = sorted(self.metrics_indices["by_date"].keys())
            
            start_idx = 0
            if start_date:
                for i, date in enumerate(all_dates):
                    if date >= start_date:
                        start_idx = i
                        break
            
            end_idx = len(all_dates)
            if end_date:
                for i, date in enumerate(all_dates):
                    if date > end_date:
                        end_idx = i
                        break
            
            for date in all_dates[start_idx:end_idx]:
                date_ids.update(self.metrics_indices["by_date"][date])
            
            id_sets.append(date_ids)
        
        # Find intersection of all criteria
        if id_sets:
            matching_ids = id_sets[0]
            for id_set in id_sets[1:]:
                matching_ids = matching_ids.intersection(id_set)
        else:
            # No filters applied, get all metrics
            for metric_type in self.metrics_indices["by_type"]:
                matching_ids.update(self.metrics_indices["by_type"][metric_type])
        
        # Retrieve the matching metrics
        results = []
        for metric_id in matching_ids:
            metric = self.get_metric(metric_id)
            if metric:
                results.append(metric)
        
        # Sort by timestamp (newest first)
        results.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
        
        # Apply limit if specified
        if limit is not None and limit > 0:
            results = results[:limit]
        
        return results
    
    def get_metrics_summary(self) -> Dict[str, Any]:
        """
        Get a summary of all stored metrics.
        
        Returns:
            Dictionary with metrics summary information
        """
        return {
            "total_metrics": self.metrics_summary["total_metrics"],
            "metrics_by_type": self.metrics_summary["metrics_by_type"],
            "time_range": self.metrics_summary["time_range"],
            "models": list(self.metrics_summary["models"]),
            "tags": list(self.metrics_summary["tags"]),
            "cost_tracking": self.metrics_summary["cost_tracking"]
        }
    
    def track_cost(self, cost: float, api_calls: int = 0, token_usage: int = 0) -> Dict[str, Any]:
        """
        Track API and token usage costs.
        
        Args:
            cost: Cost in USD
            api_calls: Number of API calls
            token_usage: Number of tokens used
            
        Returns:
            Updated cost tracking information
        """
        # Update cost tracking in summary
        self.metrics_summary["cost_tracking"]["total_cost"] += cost
        self.metrics_summary["cost_tracking"]["api_calls"] += api_calls
        self.metrics_summary["cost_tracking"]["token_usage"] += token_usage
        
        # Save updated summary
        self._save_metrics_summary()
        
        # Check against thresholds
        total_cost = self.metrics_summary["cost_tracking"]["total_cost"]
        status = "ok"
        
        if total_cost >= self.cost_thresholds["shutdown_threshold"]:
            status = "shutdown"
            self.logger.critical(f"Cost threshold exceeded: ${total_cost:.2f} >= ${self.cost_thresholds['shutdown_threshold']:.2f}")
        elif total_cost >= self.cost_thresholds["critical_threshold"]:
            status = "critical"
            self.logger.error(f"Cost threshold warning: ${total_cost:.2f} >= ${self.cost_thresholds['critical_threshold']:.2f}")
        elif total_cost >= self.cost_thresholds["warning_threshold"]:
            status = "warning"
            self.logger.warning(f"Cost threshold warning: ${total_cost:.2f} >= ${self.cost_thresholds['warning_threshold']:.2f}")
        
        return {
            "total_cost": total_cost,
            "api_calls": self.metrics_summary["cost_tracking"]["api_calls"],
            "token_usage": self.metrics_summary["cost_tracking"]["token_usage"],
            "status": status
        }
    
    def export_to_dataframe(self, query: Optional[Dict[str, Any]] = None) -> Optional[Any]:
        """
        Export metrics to a pandas DataFrame.
        
        Args:
            query: Optional query parameters to filter metrics
            
        Returns:
            DataFrame containing the metrics or None if pandas is not available
        """
        if not PANDAS_AVAILABLE:
            self.logger.warning("pandas is not available, cannot export to DataFrame")
            return None
        
        # Import pandas locally to avoid issues
        import pandas as pd
        
        # Convert query parameters to format expected by query_metrics
        if query:
            metric_types = query.get("metric_types")
            models = query.get("models")
            tags = query.get("tags")
            start_date = query.get("start_date")
            end_date = query.get("end_date")
            limit = query.get("limit")
            
            metrics = self.query_metrics(
                metric_types=metric_types,
                models=models,
                tags=tags,
                start_date=start_date,
                end_date=end_date,
                limit=limit
            )
        else:
            # Get all metrics
            metrics = self.query_metrics()
        
        if not metrics:
            return pd.DataFrame()
        
        return pd.DataFrame(metrics)
    
    def close(self) -> None:
        """Clean up resources when closing the metrics store."""
        self._save_indices()
        self._save_metrics_summary()
        
    def get_metrics_by_filter(self, filter_dict: Dict[str, Any], limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Get metrics that match a filter dictionary.
        
        Args:
            filter_dict: Dictionary containing filter criteria (e.g., {"cycle_id": "cycle_123"})
            limit: Optional maximum number of results
            
        Returns:
            List of metrics matching the filter
        """
        # First get all metrics
        all_metrics = []
        # Collect all metric IDs from type index for efficient retrieval
        for metric_type in self.metrics_indices["by_type"]:
            for metric_id in self.metrics_indices["by_type"][metric_type]:
                metric = self.get_metric(metric_id)
                if metric:
                    all_metrics.append(metric)

        # Sort by timestamp (newest first) before filtering
        all_metrics.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
        
        # Apply filter
        filtered_metrics = []
        for metric in all_metrics:
            match = True
            for key, value in filter_dict.items():
                if key not in metric or metric[key] != value:
                    match = False
                    break
            if match:
                filtered_metrics.append(metric)
                
                # Apply limit if specified
                if limit is not None and len(filtered_metrics) >= limit:
                    break
                    
        return filtered_metrics
    
    def get_recent_metrics(self,
                         metric_types: Optional[List[str]] = None,
                         limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get the most recent metrics, optionally filtered by type.
        
        Args:
            metric_types: Optional list of metric types to filter by
            limit: Maximum number of results to return
            
        Returns:
            List of recent metrics
        """
        # Use the query_metrics method with appropriate parameters
        all_recent = self.query_metrics(
            metric_types=metric_types,
            limit=limit
        )
        
        # Ensure sorting by timestamp (newest first)
        all_recent.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
        
        return all_recent


def get_metrics_store(config: Optional[Dict[str, Any]] = None) -> MetricsStore:
    """
    Get the singleton instance of MetricsStore.
    
    Args:
        config: Optional configuration dictionary
        
    Returns:
        MetricsStore instance
    """
    return MetricsStore.get_instance(config)