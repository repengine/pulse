"""
RecursiveFeatureProcessor

Responsible for extracting and processing features from raw data for the 
recursive training system. Handles data transformation, normalization,
feature engineering, and preparation for training.
"""

import json
import logging
import os
import hashlib
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Union, Tuple, Set, Iterator, Callable

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


class FeatureTransformer:
    """Base class for feature transformers."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the transformer.
        
        Args:
            config: Optional configuration dictionary
        """
        self.config = config or {}
        self.is_fitted = False
    
    def fit(self, data: Any) -> 'FeatureTransformer':
        """
        Fit the transformer to the data.
        
        Args:
            data: The data to fit to
            
        Returns:
            Self for chaining
        """
        self.is_fitted = True
        return self
    
    def transform(self, data: Any) -> Any:
        """
        Transform the data.
        
        Args:
            data: The data to transform
            
        Returns:
            Transformed data
        """
        if not self.is_fitted:
            raise ValueError("Transformer is not fitted")
        return data
    
    def fit_transform(self, data: Any) -> Any:
        """
        Fit to the data and then transform it.
        
        Args:
            data: The data to fit to and transform
            
        Returns:
            Transformed data
        """
        return self.fit(data).transform(data)


class NumericNormalizer(FeatureTransformer):
    """Normalizes numeric features to a standard range."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the normalizer.
        
        Args:
            config: Optional configuration dictionary
        """
        super().__init__(config)
        self.min_values = {}
        self.max_values = {}
        self.mean_values = {}
        self.std_values = {}
        self.normalize_method = self.config.get("normalize_method", "minmax")
    
    def fit(self, data: Dict[str, List[float]]) -> 'NumericNormalizer':
        """
        Fit the normalizer to the data.
        
        Args:
            data: Dictionary of feature names to numeric values
            
        Returns:
            Self for chaining
        """
        if not NUMPY_AVAILABLE:
            raise ImportError("NumPy is required for NumericNormalizer")
        
        for feature_name, values in data.items():
            if not values:
                continue
                
            # Use numpy safely with explicit import
            if not NUMPY_AVAILABLE:
                raise ImportError("NumPy is required for NumericNormalizer")
                
            import numpy as np
            values_array = np.array(values, dtype=float)
            
            # Handle NaN values
            values_array = values_array[~np.isnan(values_array)]
            
            if len(values_array) == 0:
                continue
                
            # Import numpy locally to ensure it's available
            import numpy as np
            self.min_values[feature_name] = float(np.min(values_array))
            self.max_values[feature_name] = float(np.max(values_array))
            self.mean_values[feature_name] = float(np.mean(values_array))
            self.std_values[feature_name] = float(np.std(values_array))
        
        self.is_fitted = True
        return self
    
    def transform(self, data: Dict[str, List[float]]) -> Dict[str, List[float]]:
        """
        Normalize the data.
        
        Args:
            data: Dictionary of feature names to numeric values
            
        Returns:
            Dictionary of normalized feature values
        """
        if not self.is_fitted:
            raise ValueError("Normalizer is not fitted")
        
        if not NUMPY_AVAILABLE:
            raise ImportError("NumPy is required for NumericNormalizer")
        
        result = {}
        
        for feature_name, values in data.items():
            if not values:
                result[feature_name] = values
                continue
            
            if feature_name not in self.min_values:
                # Skip features that weren't in the training data
                result[feature_name] = values
                continue
            
            # Use numpy safely with explicit import
            if not NUMPY_AVAILABLE:
                raise ImportError("NumPy is required for NumericNormalizer")
                
            import numpy as np
            values_array = np.array(values, dtype=float)
            
            # Handle NaN values
            nan_mask = np.isnan(values_array)
            values_to_transform = values_array[~nan_mask]
            
            if len(values_to_transform) == 0:
                result[feature_name] = values
                continue
            
            if self.normalize_method == "minmax":
                min_val = self.min_values[feature_name]
                max_val = self.max_values[feature_name]
                
                # Avoid division by zero
                if max_val == min_val:
                    import numpy as np
                    transformed = np.zeros_like(values_to_transform)
                else:
                    transformed = (values_to_transform - min_val) / (max_val - min_val)
            elif self.normalize_method == "zscore":
                mean = self.mean_values[feature_name]
                std = self.std_values[feature_name]
                
                # Avoid division by zero
                if std == 0:
                    import numpy as np
                    transformed = np.zeros_like(values_to_transform)
                else:
                    transformed = (values_to_transform - mean) / std
            else:
                transformed = values_to_transform
            
            # Reconstruct original array with NaNs
            # Use numpy safely with explicit import
            import numpy as np
            normalized = np.empty_like(values_array)
            normalized[~nan_mask] = transformed
            normalized[nan_mask] = np.nan
            
            result[feature_name] = normalized.tolist()
        
        return result


class TextVectorizer(FeatureTransformer):
    """Converts text features into numerical representations."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the vectorizer.
        
        Args:
            config: Optional configuration dictionary
        """
        super().__init__(config)
        self.vocab = {}
        self.idf = {}
        self.method = self.config.get("vectorize_method", "tfidf")
        self.max_features = self.config.get("max_features", 1000)
    
    def fit(self, data: Dict[str, List[str]]) -> 'TextVectorizer':
        """
        Fit the vectorizer to the data.
        
        Args:
            data: Dictionary of feature names to text values
            
        Returns:
            Self for chaining
        """
        if not NUMPY_AVAILABLE:
            raise ImportError("NumPy is required for TextVectorizer")
        
        # Build vocabulary and document frequency
        all_docs = []
        for feature_name, texts in data.items():
            all_docs.extend([text for text in texts if text])
        
        # Tokenize
        doc_tokens = [self._tokenize(doc) for doc in all_docs if doc]
        
        # Build vocabulary with document frequency
        vocab_counter = Counter()
        doc_freq = Counter()
        
        for tokens in doc_tokens:
            # Count each token once per document for IDF
            unique_tokens = set(tokens)
            for token in unique_tokens:
                doc_freq[token] += 1
            
            # Count all token occurrences for vocabulary
            for token in tokens:
                vocab_counter[token] += 1
        
        # Get most common tokens for vocabulary
        self.vocab = {token: idx for idx, (token, _) in enumerate(vocab_counter.most_common(self.max_features))}
        
        # Calculate IDF
        num_docs = len(doc_tokens)
        # Use numpy safely with explicit import
        if not NUMPY_AVAILABLE:
            raise ImportError("NumPy is required for TextVectorizer")
            
        import numpy as np
        self.idf = {token: np.log(num_docs / (1 + df)) for token, df in doc_freq.items() if token in self.vocab}
        
        self.is_fitted = True
        return self
    
    def transform(self, data: Dict[str, List[str]]) -> Dict[str, List[List[float]]]:
        """
        Transform text data into vector representations.
        
        Args:
            data: Dictionary of feature names to text values
            
        Returns:
            Dictionary of feature names to vector representations
        """
        if not self.is_fitted:
            raise ValueError("Vectorizer is not fitted")
        
        if not NUMPY_AVAILABLE:
            raise ImportError("NumPy is required for TextVectorizer")
        
        result = {}
        
        for feature_name, texts in data.items():
            vectors = []
            
            for text in texts:
                if not text:
                    vectors.append([0.0] * len(self.vocab))
                    continue
                
                tokens = self._tokenize(text)
                
                if self.method == "tfidf":
                    vector = self._compute_tfidf(tokens)
                elif self.method == "count":
                    vector = self._compute_count(tokens)
                elif self.method == "binary":
                    vector = self._compute_binary(tokens)
                else:
                    vector = [0.0] * len(self.vocab)
                
                vectors.append(vector)
            
            result[feature_name] = vectors
        
        return result
    
    def _tokenize(self, text: str) -> List[str]:
        """
        Tokenize text into words.
        
        Args:
            text: Text to tokenize
            
        Returns:
            List of tokens
        """
        return text.lower().split()
    
    def _compute_tfidf(self, tokens: List[str]) -> List[float]:
        """
        Compute TF-IDF representation.
        
        Args:
            tokens: List of tokens
            
        Returns:
            TF-IDF vector
        """
        vector = [0.0] * len(self.vocab)
        token_counts = Counter(tokens)
        
        for token, count in token_counts.items():
            if token in self.vocab:
                idx = self.vocab[token]
                tf = count / len(tokens)
                idf = self.idf.get(token, 0.0)
                vector[idx] = tf * idf
        
        return vector
    
    def _compute_count(self, tokens: List[str]) -> List[float]:
        """
        Compute count representation.
        
        Args:
            tokens: List of tokens
            
        Returns:
            Count vector
        """
        vector = [0.0] * len(self.vocab)
        token_counts = Counter(tokens)
        
        for token, count in token_counts.items():
            if token in self.vocab:
                idx = self.vocab[token]
                vector[idx] = count
        
        return vector
    
    def _compute_binary(self, tokens: List[str]) -> List[float]:
        """
        Compute binary representation.
        
        Args:
            tokens: List of tokens
            
        Returns:
            Binary vector
        """
        vector = [0.0] * len(self.vocab)
        unique_tokens = set(tokens)
        
        for token in unique_tokens:
            if token in self.vocab:
                idx = self.vocab[token]
                vector[idx] = 1.0
        
        return vector


class CategoryEncoder(FeatureTransformer):
    """Encodes categorical features."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the encoder.
        
        Args:
            config: Optional configuration dictionary
        """
        super().__init__(config)
        self.categories = {}
        self.method = self.config.get("encode_method", "onehot")
        self.unknown_value = self.config.get("unknown_value", -1)
    
    def fit(self, data: Dict[str, List[str]]) -> 'CategoryEncoder':
        """
        Fit the encoder to the data.
        
        Args:
            data: Dictionary of feature names to categorical values
            
        Returns:
            Self for chaining
        """
        for feature_name, values in data.items():
            # Get unique categories
            unique_values = list(set([str(val) for val in values if val is not None]))
            
            # Store mapping from category to index
            self.categories[feature_name] = {cat: idx for idx, cat in enumerate(unique_values)}
        
        self.is_fitted = True
        return self
    
    def transform(self, data: Dict[str, List[str]]) -> Dict[str, Union[List[int], List[List[float]]]]:
        """
        Encode categorical data.
        
        Args:
            data: Dictionary of feature names to categorical values
            
        Returns:
            Dictionary of encoded feature values
        """
        if not self.is_fitted:
            raise ValueError("Encoder is not fitted")
        
        result = {}
        
        for feature_name, values in data.items():
            if feature_name not in self.categories:
                # Skip features that weren't in the training data
                result[feature_name] = values
                continue
            
            if self.method == "ordinal":
                encoded = []
                for val in values:
                    if val is None:
                        encoded.append(self.unknown_value)
                    else:
                        val_str = str(val)
                        encoded.append(self.categories[feature_name].get(val_str, self.unknown_value))
                
                result[feature_name] = encoded
            elif self.method == "onehot":
                num_categories = len(self.categories[feature_name])
                encoded = []
                
                for val in values:
                    if val is None:
                        # Use all zeros for None
                        encoded.append([0.0] * num_categories)
                    else:
                        val_str = str(val)
                        idx = self.categories[feature_name].get(val_str, -1)
                        
                        if idx == -1:
                            # Unknown category, use all zeros
                            encoded.append([0.0] * num_categories)
                        else:
                            # One-hot encoding
                            vec = [0.0] * num_categories
                            vec[idx] = 1.0
                            encoded.append(vec)
                
                result[feature_name] = encoded
            else:
                # Fallback to keeping original values
                result[feature_name] = values
        
        return result


class FeatureCache:
    """Cache for processed features to avoid redundant processing."""
    
    def __init__(self, max_size: int = 1000):
        """
        Initialize the cache.
        
        Args:
            max_size: Maximum number of cached items
        """
        self.cache = {}
        self.max_size = max_size
        self.access_count = {}
    
    def get(self, key: str) -> Optional[Any]:
        """
        Get a cached item.
        
        Args:
            key: Cache key
            
        Returns:
            Cached item or None if not found
        """
        if key in self.cache:
            self.access_count[key] = self.access_count.get(key, 0) + 1
            return self.cache[key]
        return None
    
    def put(self, key: str, value: Any) -> None:
        """
        Store an item in the cache.
        
        Args:
            key: Cache key
            value: Item to cache
        """
        # Evict least recently used items if cache is full
        if len(self.cache) >= self.max_size:
            # Find the key with the lowest access count
            min_key = min(self.access_count.items(), key=lambda x: x[1])[0]
            del self.cache[min_key]
            del self.access_count[min_key]
        
        self.cache[key] = value
        self.access_count[key] = 1
    
    def clear(self) -> None:
        """Clear the cache."""
        self.cache.clear()
        self.access_count.clear()


class RecursiveFeatureProcessor:
    """
    Processor for extracting and transforming features from data for recursive training.
    
    Features:
    - Numeric feature normalization
    - Text vectorization
    - Categorical encoding
    - Feature selection and engineering
    - Caching for efficient processing
    - Dictionary-based rule feature extraction
    - Object-based rule feature extraction
    
    Designed to work with RecursiveDataIngestionManager and RecursiveDataStore.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the feature processor.
        
        Args:
            config: Optional configuration dictionary
        """
        self.logger = logging.getLogger("RecursiveFeatureProcessor")
        self.config = config or {}
        
        # Initialize transformers
        self.numeric_normalizer = NumericNormalizer(self.config)
        self.text_vectorizer = TextVectorizer(self.config)
        self.category_encoder = CategoryEncoder(self.config)
        
        # Initialize feature cache
        cache_size = self.config.get("feature_cache_size", 1000)
        self.cache = FeatureCache(max_size=cache_size)
        
        # Track fitted state
        self.is_fitted = False
        
        # Feature selection settings
        self.selected_features = set()
        self.feature_importance = {}
        
        # Configure feature extraction
        self.feature_extraction_methods = self.config.get(
            "feature_extraction_methods", 
            ["basic", "dict_rules", "object_rules"]
        )
    
    def _generate_cache_key(self, data: Any, feature_type: str) -> str:
        """
        Generate a cache key for the data.
        
        Args:
            data: The data to generate a key for
            feature_type: Type of feature processing
            
        Returns:
            Cache key string
        """
        # Create a string representation of the data
        if isinstance(data, dict):
            data_str = json.dumps(data, sort_keys=True)
        else:
            data_str = str(data)
        
        # Hash the string
        hash_obj = hashlib.md5(data_str.encode())
        return f"{feature_type}_{hash_obj.hexdigest()}"
    
    def extract_features(self, data_items: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Extract features from raw data items.
        
        Args:
            data_items: List of data items
            
        Returns:
            Dictionary of extracted features
        """
        cache_key = self._generate_cache_key(data_items, "extract")
        cached = self.cache.get(cache_key)
        if cached is not None:
            return cached
        
        features = {}
        
        # Extract basic features
        if "basic" in self.feature_extraction_methods:
            basic_features = self._extract_basic_features(data_items)
            features.update(basic_features)
        
        # Extract dictionary-based rule features
        if "dict_rules" in self.feature_extraction_methods:
            dict_rule_features = self._extract_dict_rule_features(data_items)
            features.update(dict_rule_features)
        
        # Extract object-based rule features
        if "object_rules" in self.feature_extraction_methods:
            object_rule_features = self._extract_object_rule_features(data_items)
            features.update(object_rule_features)
        
        # Cache the result
        self.cache.put(cache_key, features)
        
        return features
    
    def _extract_basic_features(self, data_items: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Extract basic features from data items.
        
        Args:
            data_items: List of data items
            
        Returns:
            Dictionary of basic features
        """
        # Categorize features by data type
        numeric_features = {}
        text_features = {}
        categorical_features = {}
        
        for item in data_items:
            for key, value in item.items():
                if key not in numeric_features:
                    numeric_features[key] = []
                if key not in text_features:
                    text_features[key] = []
                if key not in categorical_features:
                    categorical_features[key] = []
                
                # Determine data type and add to appropriate collection
                if isinstance(value, (int, float)) or (isinstance(value, str) and value.isdigit()):
                    try:
                        numeric_features[key].append(float(value))
                    except (ValueError, TypeError):
                        numeric_features[key].append(float('nan'))
                elif isinstance(value, str) and len(value.split()) > 1:
                    text_features[key].append(value)
                else:
                    categorical_features[key].append(str(value) if value is not None else None)
        
        return {
            "numeric": numeric_features,
            "text": text_features,
            "categorical": categorical_features
        }
    
    def _extract_dict_rule_features(self, data_items: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Extract features from dictionary-based rules.
        
        Args:
            data_items: List of data items
            
        Returns:
            Dictionary of rule features
        """
        rule_features = {}
        
        # Extract rule-specific features
        for item in data_items:
            rule_def = item.get("rule_definition", {})
            
            if not isinstance(rule_def, dict):
                continue
            
            # Extract conditions and actions
            conditions = rule_def.get("conditions", [])
            actions = rule_def.get("actions", [])
            
            # Process conditions
            condition_count = len(conditions)
            condition_vars = set()
            
            for condition in conditions:
                if isinstance(condition, dict):
                    var_name = condition.get("variable")
                    if var_name:
                        condition_vars.add(var_name)
            
            # Process actions
            action_count = len(actions)
            action_vars = set()
            
            for action in actions:
                if isinstance(action, dict):
                    var_name = action.get("variable")
                    if var_name:
                        action_vars.add(var_name)
            
            # Store rule features
            if "condition_count" not in rule_features:
                rule_features["condition_count"] = []
            rule_features["condition_count"].append(condition_count)
            
            if "action_count" not in rule_features:
                rule_features["action_count"] = []
            rule_features["action_count"].append(action_count)
            
            if "condition_var_count" not in rule_features:
                rule_features["condition_var_count"] = []
            rule_features["condition_var_count"].append(len(condition_vars))
            
            if "action_var_count" not in rule_features:
                rule_features["action_var_count"] = []
            rule_features["action_var_count"].append(len(action_vars))
            
            if "rule_complexity" not in rule_features:
                rule_features["rule_complexity"] = []
            rule_features["rule_complexity"].append(condition_count * action_count)
        
        return {"rule": rule_features}
    
    def _extract_object_rule_features(self, data_items: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Extract features from object-based rules.
        
        Args:
            data_items: List of data items
            
        Returns:
            Dictionary of object rule features
        """
        # This is a placeholder for object-based rule feature extraction
        # It will be implemented as part of the hybrid rules approach
        return {}
    
    def fit(self, data_items: List[Dict[str, Any]]) -> 'RecursiveFeatureProcessor':
        """
        Fit the feature processor to the data.
        
        Args:
            data_items: List of data items
            
        Returns:
            Self for chaining
        """
        # Extract features
        features = self.extract_features(data_items)
        
        # Fit transformers
        if "numeric" in features:
            self.numeric_normalizer.fit(features["numeric"])
        
        if "text" in features:
            self.text_vectorizer.fit(features["text"])
        
        if "categorical" in features:
            self.category_encoder.fit(features["categorical"])
        
        # Perform feature selection
        self._select_features(features)
        
        self.is_fitted = True
        return self
    
    def _select_features(self, features: Dict[str, Any]) -> None:
        """
        Select important features.
        
        Args:
            features: Dictionary of extracted features
        """
        # Simple feature selection based on non-empty features
        for feature_type, type_features in features.items():
            for feature_name, values in type_features.items():
                if not values:
                    continue
                
                # Add to selected features
                self.selected_features.add(f"{feature_type}:{feature_name}")
                
                # Simple importance calculation based on non-null value count
                non_null_count = sum(1 for val in values if val is not None)
                if non_null_count > 0:
                    self.feature_importance[f"{feature_type}:{feature_name}"] = non_null_count / len(values)
    
    def transform(self, data_items: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Transform the data into features for training.
        
        Args:
            data_items: List of data items
            
        Returns:
            Dictionary of transformed features
        """
        if not self.is_fitted:
            raise ValueError("Feature processor is not fitted")
        
        cache_key = self._generate_cache_key(data_items, "transform")
        cached = self.cache.get(cache_key)
        if cached is not None:
            return cached
        
        # Extract features
        features = self.extract_features(data_items)
        
        # Transform features
        transformed = {}
        
        if "numeric" in features:
            transformed["numeric"] = self.numeric_normalizer.transform(features["numeric"])
        
        if "text" in features:
            transformed["text"] = self.text_vectorizer.transform(features["text"])
        
        if "categorical" in features:
            transformed["categorical"] = self.category_encoder.transform(features["categorical"])
        
        # Keep rule features as they are
        if "rule" in features:
            transformed["rule"] = features["rule"]
        
        # Cache the result
        self.cache.put(cache_key, transformed)
        
        return transformed
    
    def fit_transform(self, data_items: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Fit to the data and then transform it.
        
        Args:
            data_items: List of data items
            
        Returns:
            Dictionary of transformed features
        """
        return self.fit(data_items).transform(data_items)
    
    def get_feature_names(self) -> List[str]:
        """
        Get the names of all features.
        
        Returns:
            List of feature names
        """
        return list(self.selected_features)
    
    def get_feature_importance(self) -> Dict[str, float]:
        """
        Get feature importance scores.
        
        Returns:
            Dictionary mapping feature names to importance scores
        """
        return self.feature_importance
    
    def prepare_training_data(self, 
                             features: Dict[str, Any], 
                             target_name: str) -> Tuple[List[List[float]], List[float]]:
        """
        Prepare features and target for model training.
        
        Args:
            features: Dictionary of transformed features
            target_name: Name of the target feature
            
        Returns:
            Tuple of (X_features, y_target)
        """
        if not self.is_fitted:
            raise ValueError("Feature processor is not fitted")
        
        if not NUMPY_AVAILABLE:
            raise ImportError("NumPy is required for preparing training data")
        
        # Initialize target list
        target = []
        feature_parts = target_name.split(":")
        
        if len(feature_parts) != 2:
            raise ValueError(f"Invalid target feature name: {target_name}")
        
        feature_type, feature_name = feature_parts
        
        if feature_type not in features or feature_name not in features[feature_type]:
            raise ValueError(f"Target feature not found: {target_name}")
        
        target_values = features[feature_type][feature_name]
        
        # Extract and flatten features
        feature_matrix = []
        
        # Process all data items
        num_items = len(target_values)
        
        for i in range(num_items):
            item_features = []
            
            # Add features in a consistent order
            for feature_type in sorted(features.keys()):
                for feature_name in sorted(features[feature_type].keys()):
                    full_name = f"{feature_type}:{feature_name}"
                    
                    # Skip the target feature
                    if full_name == target_name:
                        target.append(target_values[i])
                        continue
                    
                    # Skip features that weren't selected
                    if full_name not in self.selected_features:
                        continue
                    
                    feature_values = features[feature_type][feature_name]
                    
                    if i >= len(feature_values):
                        # Handle missing values
                        if feature_type == "numeric":
                            item_features.append(0.0)
                        elif feature_type == "text":
                            item_features.extend([0.0] * self.text_vectorizer.max_features)
                        elif feature_type == "categorical":
                            if self.category_encoder.method == "ordinal":
                                item_features.append(self.category_encoder.unknown_value)
                            else:
                                cat_count = len(self.category_encoder.categories.get(feature_name, {}))
                                item_features.extend([0.0] * cat_count)
                        continue
                    
                    value = feature_values[i]
                    
                    if feature_type == "numeric":
                        # Add numeric value directly
                        item_features.append(value)
                    elif feature_type == "text":
                        # Add vectorized text features
                        item_features.extend(value)
                    elif feature_type == "categorical":
                        # Add encoded categorical features
                        if self.category_encoder.method == "ordinal":
                            item_features.append(value)
                        else:
                            item_features.extend(value)
                    elif feature_type == "rule":
                        # Add rule feature directly
                        item_features.append(value)
            
            feature_matrix.append(item_features)
        
        return feature_matrix, target
    
    def to_pandas_dataframe(self, features: Dict[str, Any]) -> Optional[Any]:
        """
        Convert features to a pandas DataFrame.
        
        Args:
            features: Dictionary of transformed features
            
        Returns:
            DataFrame or None if pandas is not available
        """
        if not PANDAS_AVAILABLE:
            self.logger.warning("pandas is not available, cannot convert to DataFrame")
            return None
        
        if not self.is_fitted:
            raise ValueError("Feature processor is not fitted")
        
        # Create a list to hold all data
        rows = []
        
        # Determine number of data points
        num_items = 0
        for feature_type in features:
            for feature_name in features[feature_type]:
                num_items = max(num_items, len(features[feature_type][feature_name]))
                break
            if num_items > 0:
                break
        
        # Process all data items
        for i in range(num_items):
            row = {}
            
            for feature_type in features:
                for feature_name in features[feature_type]:
                    full_name = f"{feature_type}:{feature_name}"
                    
                    # Skip features that weren't selected
                    if full_name not in self.selected_features:
                        continue
                    
                    feature_values = features[feature_type][feature_name]
                    
                    if i >= len(feature_values):
                        # Handle missing values
                        row[full_name] = None
                        continue
                    
                    value = feature_values[i]
                    
                    if feature_type == "text":
                        # Skip vectorized text features as they're too large for DataFrame display
                        continue
                    elif feature_type == "categorical" and self.category_encoder.method == "onehot":
                        # Handle one-hot encoded features
                        categories = self.category_encoder.categories.get(feature_name, {})
                        for cat, idx in categories.items():
                            if idx < len(value):
                                row[f"{full_name}_{cat}"] = value[idx]
                    else:
                        # Add other features directly
                        row[full_name] = value
            
            rows.append(row)
        
        # Import pandas locally to ensure it's available
        import pandas as pd
        return pd.DataFrame(rows)


# Singleton instance
_instance = None

def get_feature_processor(config: Optional[Dict[str, Any]] = None) -> RecursiveFeatureProcessor:
    """
    Get the singleton instance of RecursiveFeatureProcessor.
    
    Args:
        config: Optional configuration dictionary
        
    Returns:
        RecursiveFeatureProcessor instance
    """
    global _instance
    if _instance is None:
        _instance = RecursiveFeatureProcessor(config)
    return _instance