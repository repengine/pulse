"""
Tests for RecursiveFeatureProcessor

This module contains unit tests for the RecursiveFeatureProcessor class,
focusing on feature extraction, transformation, and processing.
"""

import pytest
import json
import hashlib
from unittest.mock import patch, MagicMock
from datetime import datetime
from collections import Counter

from recursive_training.data.feature_processor import (
    RecursiveFeatureProcessor,
    FeatureTransformer,
    NumericNormalizer,
    TextVectorizer,
    CategoryEncoder,
    FeatureCache,
    get_feature_processor
)


@pytest.fixture
def numpy_mock():
    """Mock numpy for tests."""
    numpy_mock = MagicMock()
    numpy_mock.array.return_value = MagicMock()
    numpy_mock.min.return_value = 0.0
    numpy_mock.max.return_value = 10.0
    numpy_mock.mean.return_value = 5.0
    numpy_mock.std.return_value = 2.0
    numpy_mock.isnan.return_value = MagicMock()
    numpy_mock.zeros_like.return_value = MagicMock()
    numpy_mock.empty_like.return_value = MagicMock()
    numpy_mock.nan = float('nan')
    return numpy_mock


@pytest.fixture
def mock_config():
    """Fixture for mock configuration."""
    return {
        "normalize_method": "minmax",
        "vectorize_method": "tfidf",
        "max_features": 50,
        "encode_method": "onehot",
        "unknown_value": -1,
        "feature_cache_size": 100,
        "feature_extraction_methods": ["basic", "dict_rules"],
        "embedding_dimensions": 300
    }


@pytest.fixture
def sample_numeric_data():
    """Sample numeric data for testing."""
    return {
        "feature1": [1.0, 2.0, 3.0, 4.0, 5.0],
        "feature2": [10.0, 20.0, 30.0, 40.0, 50.0]
    }


@pytest.fixture
def sample_text_data():
    """Sample text data for testing."""
    return {
        "text1": ["This is a test document", "Another test document here", "Third document with more words"],
        "text2": ["Different content altogether", "Completely unrelated text", "More random words"]
    }


@pytest.fixture
def sample_categorical_data():
    """Sample categorical data for testing."""
    return {
        "category1": ["red", "green", "blue", "red", "green"],
        "category2": ["small", "medium", "large", "medium", "small"]
    }


@pytest.fixture
def sample_data_items():
    """Sample data items for feature extraction."""
    return [
        {
            "id": "item1",
            "numeric_value": 42.0,
            "text_field": "This is a sample text with several words",
            "category": "cat_a"
        },
        {
            "id": "item2",
            "numeric_value": 73.5,
            "text_field": "Another example of text content here",
            "category": "cat_b"
        },
        {
            "id": "item3",
            "numeric_value": 12.3,
            "text_field": "Third sample with different words",
            "category": "cat_a"
        }
    ]


@pytest.fixture
def sample_rule_items():
    """Sample rule items for feature extraction."""
    return [
        {
            "id": "rule1",
            "rule_definition": {
                "conditions": [
                    {"variable": "price", "operator": ">", "value": 100},
                    {"variable": "category", "operator": "==", "value": "electronics"}
                ],
                "actions": [
                    {"variable": "discount", "value": 0.1},
                    {"variable": "message", "value": "10% off electronics!"}
                ]
            }
        },
        {
            "id": "rule2",
            "rule_definition": {
                "conditions": [
                    {"variable": "quantity", "operator": ">", "value": 5}
                ],
                "actions": [
                    {"variable": "shipping", "value": "free"}
                ]
            }
        }
    ]


@pytest.fixture
def feature_processor(mock_config):
    """Fixture for feature processor."""
    with patch('recursive_training.data.feature_processor.NUMPY_AVAILABLE', True):
        with patch('recursive_training.data.feature_processor.PANDAS_AVAILABLE', True):
            processor = RecursiveFeatureProcessor(mock_config)
            return processor


class TestFeatureTransformers:
    """Tests for the feature transformer classes."""

    def test_base_transformer(self):
        """Test the base FeatureTransformer class."""
        transformer = FeatureTransformer()
        assert not transformer.is_fitted
        
        # Test fit
        transformer.fit("test_data")
        assert transformer.is_fitted
        
        # Test transform
        result = transformer.transform("test_data")
        assert result == "test_data"
        
        # Test fit_transform
        new_transformer = FeatureTransformer()
        result = new_transformer.fit_transform("test_data")
        assert result == "test_data"
        assert new_transformer.is_fitted

    def test_numeric_normalizer(self, sample_numeric_data, numpy_mock):
        """Test NumericNormalizer with mocked numpy."""
        with patch('recursive_training.data.feature_processor.np', numpy_mock):
            with patch('recursive_training.data.feature_processor.NUMPY_AVAILABLE', True):
                # Test initialization
                normalizer = NumericNormalizer({"normalize_method": "minmax"})
                assert normalizer.normalize_method == "minmax"
                
                # Test fitting
                normalizer.fit(sample_numeric_data)
                assert normalizer.is_fitted
                
                # Verify min/max values were captured
                assert "feature1" in normalizer.min_values
                assert "feature1" in normalizer.max_values
                assert normalizer.min_values["feature1"] == 0.0
                assert normalizer.max_values["feature1"] == 10.0
                
                # Test transformation
                transformed = normalizer.transform(sample_numeric_data)
                assert "feature1" in transformed
                assert "feature2" in transformed

    def test_text_vectorizer(self, sample_text_data, numpy_mock):
        """Test TextVectorizer with mocked numpy."""
        with patch('recursive_training.data.feature_processor.np', numpy_mock):
            with patch('recursive_training.data.feature_processor.NUMPY_AVAILABLE', True):
                # Test initialization
                vectorizer = TextVectorizer({"vectorize_method": "tfidf", "max_features": 10})
                assert vectorizer.method == "tfidf"
                assert vectorizer.max_features == 10
                
                # Mock tokenize to simplify testing
                vectorizer._tokenize = MagicMock(return_value=["word1", "word2", "word3"])
                
                # Test fitting
                vectorizer.fit(sample_text_data)
                assert vectorizer.is_fitted
                
                # Verify vocabulary was built
                assert isinstance(vectorizer.vocab, dict)
                
                # Mock compute methods
                vectorizer._compute_tfidf = MagicMock(return_value=[0.1, 0.2, 0.0])
                vectorizer._compute_count = MagicMock(return_value=[1, 2, 0])
                vectorizer._compute_binary = MagicMock(return_value=[1.0, 1.0, 0.0])
                
                # Test transform with tfidf
                transformed = vectorizer.transform(sample_text_data)
                assert "text1" in transformed
                assert "text2" in transformed
                vectorizer._compute_tfidf.assert_called()
                
                # Test with different methods
                vectorizer.method = "count"
                vectorizer.transform(sample_text_data)
                vectorizer._compute_count.assert_called()
                
                vectorizer.method = "binary"
                vectorizer.transform(sample_text_data)
                vectorizer._compute_binary.assert_called()

    def test_category_encoder(self, sample_categorical_data):
        """Test CategoryEncoder."""
        # Test initialization
        encoder = CategoryEncoder({"encode_method": "onehot", "unknown_value": -1})
        assert encoder.method == "onehot"
        assert encoder.unknown_value == -1
        
        # Test fitting
        encoder.fit(sample_categorical_data)
        assert encoder.is_fitted
        
        # Verify categories were captured
        assert "category1" in encoder.categories
        assert "category2" in encoder.categories
        assert "red" in encoder.categories["category1"]
        assert "green" in encoder.categories["category1"]
        assert "blue" in encoder.categories["category1"]
        
        # Test transform with onehot encoding
        transformed = encoder.transform(sample_categorical_data)
        assert "category1" in transformed
        assert "category2" in transformed
        
        # Check that the first item in category1 is a one-hot vector
        # In this case, "red" should be encoded as [1,0,0] if it's the first category
        assert isinstance(transformed["category1"][0], list)
        
        # Test with ordinal encoding
        encoder.method = "ordinal"
        transformed = encoder.transform(sample_categorical_data)
        assert isinstance(transformed["category1"][0], int)


class TestFeatureCache:
    """Tests for the FeatureCache class."""

    def test_cache_operations(self):
        """Test cache put, get, and eviction."""
        cache = FeatureCache(max_size=2)
        
        # Test put and get
        cache.put("key1", "value1")
        assert cache.get("key1") == "value1"
        
        # Test missing key
        assert cache.get("nonexistent") is None
        
        # Test eviction when full
        cache.put("key2", "value2")
        cache.put("key3", "value3")  # This should evict key1
        
        assert cache.get("key1") is None
        assert cache.get("key2") == "value2"
        assert cache.get("key3") == "value3"
        
        # Test clear
        cache.clear()
        assert cache.get("key2") is None
        assert cache.get("key3") is None


class TestRecursiveFeatureProcessor:
    """Tests for the RecursiveFeatureProcessor class."""

    def test_initialization(self, mock_config):
        """Test correct initialization of the processor."""
        with patch('recursive_training.data.feature_processor.NUMPY_AVAILABLE', True):
            processor = RecursiveFeatureProcessor(mock_config)
            
            assert isinstance(processor.numeric_normalizer, NumericNormalizer)
            assert isinstance(processor.text_vectorizer, TextVectorizer)
            assert isinstance(processor.category_encoder, CategoryEncoder)
            assert isinstance(processor.cache, FeatureCache)
            assert not processor.is_fitted
            assert processor.feature_extraction_methods == mock_config["feature_extraction_methods"]

    def test_generate_cache_key(self, feature_processor, sample_data_items):
        """Test cache key generation."""
        key1 = feature_processor._generate_cache_key(sample_data_items, "test")
        key2 = feature_processor._generate_cache_key(sample_data_items, "test")
        
        # Same data should generate same key
        assert key1 == key2
        
        # Different feature type should generate different key
        key3 = feature_processor._generate_cache_key(sample_data_items, "different")
        assert key1 != key3
        
        # Different data should generate different key
        modified_items = sample_data_items.copy()
        modified_items.append({"id": "new_item", "value": 99})
        key4 = feature_processor._generate_cache_key(modified_items, "test")
        assert key1 != key4

    def test_extract_basic_features(self, feature_processor, sample_data_items):
        """Test basic feature extraction."""
        features = feature_processor._extract_basic_features(sample_data_items)
        
        # Verify structure
        assert "numeric" in features
        assert "text" in features
        assert "categorical" in features
        
        # Verify numeric features
        assert "numeric_value" in features["numeric"]
        assert len(features["numeric"]["numeric_value"]) == len(sample_data_items)
        
        # Verify text features
        assert "text_field" in features["text"]
        assert len(features["text"]["text_field"]) == len(sample_data_items)
        
        # Verify categorical features
        assert "category" in features["categorical"]
        assert len(features["categorical"]["category"]) == len(sample_data_items)

    def test_extract_dict_rule_features(self, feature_processor, sample_rule_items):
        """Test dictionary-based rule feature extraction."""
        features = feature_processor._extract_dict_rule_features(sample_rule_items)
        
        # Verify structure
        assert "rule" in features
        
        # Verify rule features
        assert "condition_count" in features["rule"]
        assert "action_count" in features["rule"]
        assert "condition_var_count" in features["rule"]
        assert "action_var_count" in features["rule"]
        assert "rule_complexity" in features["rule"]
        
        # Verify values
        assert features["rule"]["condition_count"][0] == 2  # rule1 has 2 conditions
        assert features["rule"]["action_count"][0] == 2     # rule1 has 2 actions
        assert features["rule"]["condition_count"][1] == 1  # rule2 has 1 condition
        assert features["rule"]["action_count"][1] == 1     # rule2 has 1 action

    def test_fit_and_transform(self, feature_processor, sample_data_items):
        """Test fitting and transforming data."""
        # Mock the transformers to simplify testing
        feature_processor.numeric_normalizer.fit = MagicMock(return_value=feature_processor.numeric_normalizer)
        feature_processor.numeric_normalizer.transform = MagicMock(return_value={"numeric_value": [0.1, 0.2, 0.3]})
        
        feature_processor.text_vectorizer.fit = MagicMock(return_value=feature_processor.text_vectorizer)
        feature_processor.text_vectorizer.transform = MagicMock(return_value={"text_field": [[0.1, 0.2], [0.3, 0.4], [0.5, 0.6]]})
        
        feature_processor.category_encoder.fit = MagicMock(return_value=feature_processor.category_encoder)
        feature_processor.category_encoder.transform = MagicMock(return_value={"category": [[1, 0], [0, 1], [1, 0]]})
        
        # Mock extract_features to return predetermined structure
        feature_processor.extract_features = MagicMock(return_value={
            "numeric": {"numeric_value": [42.0, 73.5, 12.3]},
            "text": {"text_field": ["text1", "text2", "text3"]},
            "categorical": {"category": ["cat_a", "cat_b", "cat_a"]}
        })
        
        # Test fit
        feature_processor.fit(sample_data_items)
        assert feature_processor.is_fitted
        feature_processor.numeric_normalizer.fit.assert_called_once()
        feature_processor.text_vectorizer.fit.assert_called_once()
        feature_processor.category_encoder.fit.assert_called_once()
        
        # Test transform
        transformed = feature_processor.transform(sample_data_items)
        assert "numeric" in transformed
        assert "text" in transformed
        assert "categorical" in transformed
        feature_processor.numeric_normalizer.transform.assert_called_once()
        feature_processor.text_vectorizer.transform.assert_called_once()
        feature_processor.category_encoder.transform.assert_called_once()
        
        # Test fit_transform
        feature_processor.is_fitted = False
        feature_processor.fit = MagicMock(return_value=feature_processor)
        feature_processor.transform = MagicMock(return_value={"transformed": "data"})
        
        result = feature_processor.fit_transform(sample_data_items)
        feature_processor.fit.assert_called_once_with(sample_data_items)
        feature_processor.transform.assert_called_once_with(sample_data_items)
        assert result == {"transformed": "data"}

    def test_singleton_pattern(self):
        """Test the singleton pattern implementation."""
        with patch('recursive_training.data.feature_processor.RecursiveFeatureProcessor') as mock_class:
            mock_instance = MagicMock()
            mock_class.return_value = mock_instance
            
            # First call should create a new instance
            get_feature_processor()
            mock_class.assert_called_once()
            
            # Reset mock to check second call
            mock_class.reset_mock()
            
            # Second call should reuse existing instance
            get_feature_processor()
            mock_class.assert_not_called()


if __name__ == "__main__":
    pytest.main()