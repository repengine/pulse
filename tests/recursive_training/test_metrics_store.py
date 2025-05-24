"""
Tests for MetricsStore

This module contains unit tests for the MetricsStore class,
focusing on metrics storage, retrieval, and querying.
"""

import pytest
import json
from unittest.mock import patch, MagicMock, mock_open
from datetime import datetime, timezone
from pathlib import Path

from recursive_training.metrics.metrics_store import MetricsStore, get_metrics_store


@pytest.fixture
def mock_config():
    """Fixture for mock configuration."""
    return {
        "metrics_path": "./data/recursive_training/metrics",
        "use_compression": True,
        "compression_level": 6,
        "enable_caching": True,
        "max_cache_size": 100,
        "warning_cost_threshold": 5.0,
        "critical_cost_threshold": 25.0,
        "shutdown_cost_threshold": 50.0,
    }


@pytest.fixture
def sample_metric():
    """Fixture for sample metric data."""
    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "metric_type": "training_iteration",
        "iteration": 1,
        "model": "test_model",
        "metrics": {"mse": 0.05, "mae": 0.02, "rmse": 0.22, "accuracy": 0.95},
        "tags": ["test", "iteration1"],
    }


@pytest.fixture
def metrics_store(mock_config):
    """Fixture for metrics store with mocked paths."""
    with patch("os.path.exists", return_value=False):
        with patch(
            "recursive_training.metrics.metrics_store.Path.mkdir", return_value=None
        ):
            with patch("builtins.open", mock_open()):
                store = MetricsStore(mock_config)

                # Mock internal state
                store.metrics_indices = {
                    "by_type": {},
                    "by_model": {},
                    "by_date": {},
                    "by_tag": {},
                }

                store.metrics_summary = {
                    "total_metrics": 0,
                    "metrics_by_type": {},
                    "time_range": {"start": None, "end": None},
                    "models": set(),
                    "tags": set(),
                    "cost_tracking": {
                        "total_cost": 0.0,
                        "api_calls": 0,
                        "token_usage": 0,
                    },
                }

                store.metrics_cache = {}

                return store


class TestMetricsStore:
    """Tests for the MetricsStore class."""

    def test_initialization(self, mock_config):
        """Test correct initialization of the metrics store."""
        with patch("os.path.exists", return_value=False):
            with patch(
                "recursive_training.metrics.metrics_store.Path.mkdir", return_value=None
            ):
                with patch("builtins.open", mock_open()):
                    store = MetricsStore(mock_config)

                    assert isinstance(store.logger, object)
                    assert isinstance(store.base_path, Path)
                    assert isinstance(store.metrics_path, Path)
                    assert isinstance(store.index_path, Path)
                    assert isinstance(store.meta_path, Path)
                    assert isinstance(store.metrics_indices, dict)
                    assert isinstance(store.metrics_cache, dict)
                    assert store.use_compression == mock_config["use_compression"]
                    assert store.compression_level == mock_config["compression_level"]
                    assert store.enable_caching == mock_config["enable_caching"]
                    assert store.max_cache_size == mock_config["max_cache_size"]
                    assert "warning_threshold" in store.cost_thresholds
                    assert "critical_threshold" in store.cost_thresholds
                    assert "shutdown_threshold" in store.cost_thresholds

    def test_singleton_pattern(self):
        """Test the singleton pattern implementation."""
        # Ensure a clean state for the singleton instance for this test
        MetricsStore._instance = None

        with patch(
            "recursive_training.metrics.metrics_store.MetricsStore.__init__",
            return_value=None,
        ) as mock_init:
            # First call should initialize a new instance
            instance1 = MetricsStore.get_instance()
            mock_init.assert_called_once()

            # Reset mock to check second call
            mock_init.reset_mock()

            # Second call should not initialize again but return the same instance
            instance2 = MetricsStore.get_instance()
            mock_init.assert_not_called()
            assert instance1 is instance2, (
                "get_instance should return the same instance"
            )

            # get_metrics_store should call get_instance
            # Reset _instance again to test get_metrics_store properly if it also initializes
            MetricsStore._instance = None
            mock_init.reset_mock()  # Reset mock for get_metrics_store call

            # Patch get_instance to verify get_metrics_store calls it,
            # and also patch __init__ for the get_metrics_store scenario
            with (
                patch(
                    "recursive_training.metrics.metrics_store.MetricsStore.get_instance",
                    side_effect=MetricsStore.get_instance,
                ) as mock_get_instance_method,
                patch(
                    "recursive_training.metrics.metrics_store.MetricsStore.__init__",
                    return_value=None,
                ) as mock_init_for_get_metrics_store,
            ):
                store_from_getter = get_metrics_store()
                mock_get_instance_method.assert_called_once()
                mock_init_for_get_metrics_store.assert_called_once()  # __init__ should be called by get_instance via get_metrics_store

                # Verify it's the same instance logic
                mock_init_for_get_metrics_store.reset_mock()
                store_from_getter_again = get_metrics_store()
                mock_init_for_get_metrics_store.assert_not_called()
                assert store_from_getter is store_from_getter_again

    def test_generate_metric_id(self, metrics_store):
        """Test generating a unique ID for a metric."""
        metric_data = {
            "timestamp": "2025-04-30T12:00:00Z",
            "metric_type": "training_iteration",
            "model": "test_model",
        }

        metric_id = metrics_store._generate_metric_id(metric_data)

        # Verify ID is a valid MD5 hash string
        assert isinstance(metric_id, str)
        assert len(metric_id) == 32

        # Verify same data gives same ID
        second_id = metrics_store._generate_metric_id(metric_data)
        assert metric_id == second_id

        # Verify different data gives different ID
        modified_data = metric_data.copy()
        modified_data["model"] = "different_model"
        different_id = metrics_store._generate_metric_id(modified_data)
        assert metric_id != different_id

    def test_store_metric(self, metrics_store, sample_metric):
        """Test storing a metric."""
        # Mock internal methods
        metrics_store._get_metric_path = MagicMock(return_value=Path("./fake_path"))
        metrics_store._update_indices = MagicMock()
        metrics_store._update_summary = MagicMock()
        metrics_store._generate_metric_id = MagicMock(return_value="test_metric_id")

        with patch("builtins.open", mock_open()):
            # Store the metric
            metric_id = metrics_store.store_metric(sample_metric)

            # Verify methods were called
            assert metric_id == "test_metric_id"
            metrics_store._update_indices.assert_called_once_with(
                "test_metric_id", sample_metric
            )
            metrics_store._update_summary.assert_called_once_with(sample_metric)

            # Verify metric was cached
            assert "test_metric_id" in metrics_store.metrics_cache
            assert metrics_store.metrics_cache["test_metric_id"] == sample_metric

    def test_get_metric(self, metrics_store):
        """Test retrieving a metric."""
        # Setup cached metric
        cached_metric = {"id": "cached_id", "value": 42}
        metrics_store.metrics_cache["cached_id"] = cached_metric

        # Test retrieving from cache
        result = metrics_store.get_metric("cached_id")
        assert result == cached_metric

        # Test retrieving from disk
        metrics_store._get_metric_path = MagicMock(return_value=Path("./fake_path"))

        with patch("os.path.exists", return_value=True):
            with patch(
                "builtins.open",
                mock_open(read_data=json.dumps({"id": "disk_id", "value": 73})),
            ):
                result = metrics_store.get_metric("disk_id")
                assert result["id"] == "disk_id"
                assert result["value"] == 73

                # Verify metric was cached
                assert "disk_id" in metrics_store.metrics_cache

        # Test retrieving non-existent metric
        with patch("os.path.exists", return_value=False):
            result = metrics_store.get_metric("nonexistent_id")
            assert result is None

    def test_update_indices(self, metrics_store, sample_metric):
        """Test updating indices with a new metric."""
        metrics_store._save_indices = MagicMock()

        # Update indices
        metrics_store._update_indices("test_metric_id", sample_metric)

        # Verify indices were updated correctly
        assert "test_metric_id" in metrics_store.metrics_indices["by_type"].get(
            "training_iteration", []
        )
        assert "test_metric_id" in metrics_store.metrics_indices["by_model"].get(
            "test_model", []
        )

        # Verify date indexing
        date_part = sample_metric["timestamp"].split("T")[0]
        assert "test_metric_id" in metrics_store.metrics_indices["by_date"].get(
            date_part, []
        )

        # Verify tag indexing
        for tag in sample_metric["tags"]:
            assert "test_metric_id" in metrics_store.metrics_indices["by_tag"].get(
                tag, []
            )

        # Verify _save_indices was called
        metrics_store._save_indices.assert_called_once()

    def test_update_summary(self, metrics_store, sample_metric):
        """Test updating metrics summary with a new metric."""
        metrics_store._save_metrics_summary = MagicMock()

        # Initial state
        assert metrics_store.metrics_summary["total_metrics"] == 0
        assert len(metrics_store.metrics_summary["models"]) == 0
        assert len(metrics_store.metrics_summary["tags"]) == 0

        # Update summary
        metrics_store._update_summary(sample_metric)

        # Verify summary was updated
        assert metrics_store.metrics_summary["total_metrics"] == 1
        assert "training_iteration" in metrics_store.metrics_summary["metrics_by_type"]
        assert "test_model" in metrics_store.metrics_summary["models"]
        assert "test" in metrics_store.metrics_summary["tags"]
        assert "iteration1" in metrics_store.metrics_summary["tags"]

        # Verify time range was updated
        assert (
            metrics_store.metrics_summary["time_range"]["start"]
            == sample_metric["timestamp"]
        )
        assert (
            metrics_store.metrics_summary["time_range"]["end"]
            == sample_metric["timestamp"]
        )

        # Verify _save_metrics_summary was called
        metrics_store._save_metrics_summary.assert_called_once()

        # Test with cost metrics
        cost_metric = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "metric_type": "cost",
            "cost": 1.5,
            "api_calls": 10,
            "token_usage": 1000,
        }

        metrics_store._save_metrics_summary.reset_mock()
        metrics_store._update_summary(cost_metric)

        # Verify cost tracking was updated
        assert metrics_store.metrics_summary["cost_tracking"]["total_cost"] == 1.5
        assert metrics_store.metrics_summary["cost_tracking"]["api_calls"] == 10
        assert metrics_store.metrics_summary["cost_tracking"]["token_usage"] == 1000

        # Verify _save_metrics_summary was called again
        metrics_store._save_metrics_summary.assert_called_once()

    def test_query_metrics(self, metrics_store):
        """Test querying metrics by criteria."""
        # Setup test indices
        metrics_store.metrics_indices = {
            "by_type": {
                "training_iteration": ["metric1", "metric2", "metric3"],
                "validation": ["metric4", "metric5"],
            },
            "by_model": {
                "model_a": ["metric1", "metric3", "metric4"],
                "model_b": ["metric2", "metric5"],
            },
            "by_date": {
                "2025-04-29": ["metric1", "metric2"],
                "2025-04-30": ["metric3", "metric4", "metric5"],
            },
            "by_tag": {
                "tag1": ["metric1", "metric2", "metric3"],
                "tag2": ["metric2", "metric4"],
                "tag3": ["metric5"],
            },
        }

        # Mock get_metric to return test data
        def mock_get_metric(metric_id):
            return {
                "id": metric_id,
                "timestamp": f"2025-04-{30 if 'metric3' in metric_id or 'metric4' in metric_id or 'metric5' in metric_id else 29}",
                "metric_type": "training_iteration"
                if "metric1" in metric_id
                or "metric2" in metric_id
                or "metric3" in metric_id
                else "validation",
                "model": "model_a"
                if "metric1" in metric_id
                or "metric3" in metric_id
                or "metric4" in metric_id
                else "model_b",
            }

        metrics_store.get_metric = MagicMock(side_effect=mock_get_metric)

        # Test query by metric type
        results = metrics_store.query_metrics(metric_types=["training_iteration"])
        assert len(results) == 3
        assert any(r["id"] == "metric1" for r in results)
        assert any(r["id"] == "metric2" for r in results)
        assert any(r["id"] == "metric3" for r in results)

        # Test query by model and tag (should intersect)
        results = metrics_store.query_metrics(models=["model_a"], tags=["tag1"])
        assert len(results) == 2
        assert any(r["id"] == "metric1" for r in results)
        assert any(r["id"] == "metric3" for r in results)

        # Test query by date range
        results = metrics_store.query_metrics(
            start_date="2025-04-30", end_date="2025-04-30"
        )
        assert len(results) == 3
        assert all("metric1" not in r["id"] for r in results)
        assert all("metric2" not in r["id"] for r in results)

        # Test query with limit
        results = metrics_store.query_metrics(tags=["tag1"], limit=2)
        assert len(results) == 2

    def test_track_cost(self, metrics_store):
        """Test tracking API and token usage costs."""

        # Mock store_metric and simulate its effect on cost_tracking in metrics_summary
        def mock_store_metric_side_effect(metric_data):
            if metric_data.get("metric_type") == "cost":
                metrics_store.metrics_summary["cost_tracking"]["total_cost"] += (
                    metric_data.get("cost", 0.0)
                )
                metrics_store.metrics_summary["cost_tracking"]["api_calls"] += (
                    metric_data.get("api_calls", 0)
                )
                metrics_store.metrics_summary["cost_tracking"]["token_usage"] += (
                    metric_data.get("token_usage", 0)
                )
            return "cost_metric_id"

        # Initial state (ensure it's clean before the call)
        metrics_store.metrics_summary["cost_tracking"]["total_cost"] = 0.0
        metrics_store.metrics_summary["cost_tracking"]["api_calls"] = 0
        metrics_store.metrics_summary["cost_tracking"]["token_usage"] = 0

        with patch.object(
            metrics_store, "store_metric", side_effect=mock_store_metric_side_effect
        ) as mocked_store_metric_method:
            # Track cost
            result = metrics_store.track_cost(cost=2.5, api_calls=20, token_usage=2000)

            # Verify cost tracking was updated via the mock's side effect
            assert metrics_store.metrics_summary["cost_tracking"]["total_cost"] == 2.5
            assert metrics_store.metrics_summary["cost_tracking"]["api_calls"] == 20
            assert metrics_store.metrics_summary["cost_tracking"]["token_usage"] == 2000

            # Verify metric was stored (mock was called)
            mocked_store_metric_method.assert_called_once()
            assert mocked_store_metric_method.call_args[0][0]["metric_type"] == "cost"
            assert mocked_store_metric_method.call_args[0][0]["api_calls"] == 20
            assert mocked_store_metric_method.call_args[0][0]["token_usage"] == 2000
            assert mocked_store_metric_method.call_args[0][0]["cost"] == 2.5

            # Verify cost thresholds check
            assert result["total_cost"] == 2.5
            assert result["status"] == "ok"

            # Test warning threshold
            # Reset mock and relevant summary parts for the next call within the same test
            mocked_store_metric_method.reset_mock()
            metrics_store.metrics_summary["cost_tracking"]["total_cost"] = 0.0
            metrics_store.metrics_summary["cost_tracking"]["api_calls"] = 0
            metrics_store.metrics_summary["cost_tracking"]["token_usage"] = 0
            metrics_store.cost_thresholds["warning_threshold"] = 2.0

            result = metrics_store.track_cost(cost=2.5)
            assert result["status"] == "warning"
            mocked_store_metric_method.assert_called_once()  # Check it was called again for this scenario
            assert (
                metrics_store.metrics_summary["cost_tracking"]["total_cost"] == 2.5
            )  # Check side effect for this call

            # Test critical threshold
            mocked_store_metric_method.reset_mock()
            metrics_store.metrics_summary["cost_tracking"]["total_cost"] = 0.0
            metrics_store.metrics_summary["cost_tracking"]["api_calls"] = 0
            metrics_store.metrics_summary["cost_tracking"]["token_usage"] = 0
            metrics_store.cost_thresholds["critical_threshold"] = 2.0

            result = metrics_store.track_cost(cost=2.5)
            assert result["status"] == "critical"
            mocked_store_metric_method.assert_called_once()
            assert metrics_store.metrics_summary["cost_tracking"]["total_cost"] == 2.5

            # Test shutdown threshold
            mocked_store_metric_method.reset_mock()
            metrics_store.metrics_summary["cost_tracking"]["total_cost"] = 0.0
            metrics_store.metrics_summary["cost_tracking"]["api_calls"] = 0
            metrics_store.metrics_summary["cost_tracking"]["token_usage"] = 0
            metrics_store.cost_thresholds["shutdown_threshold"] = 2.0

            result = metrics_store.track_cost(cost=2.5)
            assert result["status"] == "shutdown"
            mocked_store_metric_method.assert_called_once()
            assert metrics_store.metrics_summary["cost_tracking"]["total_cost"] == 2.5

    def test_get_metrics_summary(self, metrics_store):
        """Test getting metrics summary."""
        # Setup test data
        metrics_store.metrics_summary = {
            "total_metrics": 10,
            "metrics_by_type": {"training": 5, "validation": 5},
            "time_range": {"start": "2025-04-01", "end": "2025-04-30"},
            "models": {"model1", "model2"},
            "tags": {"tag1", "tag2", "tag3"},
            "cost_tracking": {
                "total_cost": 10.5,
                "api_calls": 100,
                "token_usage": 10000,
            },
        }

        # Get summary
        summary = metrics_store.get_metrics_summary()

        # Verify summary contains expected data
        assert summary["total_metrics"] == 10
        assert summary["metrics_by_type"] == {"training": 5, "validation": 5}
        assert summary["time_range"] == {"start": "2025-04-01", "end": "2025-04-30"}
        assert set(summary["models"]) == {"model1", "model2"}
        assert set(summary["tags"]) == {"tag1", "tag2", "tag3"}
        assert summary["cost_tracking"]["total_cost"] == 10.5
        assert summary["cost_tracking"]["api_calls"] == 100
        assert summary["cost_tracking"]["token_usage"] == 10000

    def test_export_to_dataframe(self, metrics_store):
        """Test exporting metrics to a DataFrame."""
        # Mock pandas
        mock_df = MagicMock()
        mock_df_constructor = MagicMock(return_value=mock_df)

        with patch("recursive_training.metrics.metrics_store.PANDAS_AVAILABLE", True):
            with patch("recursive_training.metrics.metrics_store.pd") as mock_pd:
                mock_pd.DataFrame = mock_df_constructor

                # Mock query_metrics to return test data
                test_metrics = [{"id": "metric1"}, {"id": "metric2"}]
                metrics_store.query_metrics = MagicMock(return_value=test_metrics)

                # Test with query
                result = metrics_store.export_to_dataframe({"metric_types": ["test"]})

                # Verify methods were called correctly
                metrics_store.query_metrics.assert_called_once_with(
                    metric_types=["test"],
                    models=None,
                    tags=None,
                    start_date=None,
                    end_date=None,
                    limit=None,
                )
                mock_pd.DataFrame.assert_called_once_with(test_metrics)
                assert result == mock_df

                # Test with no results
                metrics_store.query_metrics.reset_mock()
                mock_pd.DataFrame.reset_mock()

                metrics_store.query_metrics.return_value = []
                mock_empty_df = MagicMock()
                mock_pd.DataFrame.return_value = mock_empty_df

                result = metrics_store.export_to_dataframe()

                metrics_store.query_metrics.assert_called_once()
                mock_pd.DataFrame.assert_called_once_with()
                assert result == mock_empty_df


if __name__ == "__main__":
    pytest.main()
