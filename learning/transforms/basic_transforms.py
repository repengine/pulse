"""
Basic feature transforms for Pulse.
Provides common transformations for time series and text data.
"""
import pandas as pd
import numpy as np
from typing import Optional, Union, List

def rolling_window(df: pd.DataFrame, window: int = 5, features: Optional[List[str]] = None) -> pd.Series:
    """
    Apply rolling window aggregation to selected features.
    
    Args:
        df: Input DataFrame
        window: Window size for rolling operation
        features: List of feature names to transform (if None, uses all numeric columns)
    
    Returns:
        Series with rolling window averages
    """
    if features is None:
        features = df.select_dtypes(include=['number']).columns.tolist()
    
    result = df[features].rolling(window=window).mean()
    # Fill NaN values that occur at the beginning of the window
    result = result.fillna(method='bfill')
    
    # Return the first column if multiple, or the series if single column
    if len(features) == 1:
        return result[features[0]]
    else:
        return result.mean(axis=1)  # Average across features

def lag_features(df: pd.DataFrame, lags: List[int] = [1, 3, 7], features: Optional[List[str]] = None) -> pd.Series:
    """
    Create lagged features for time series forecasting.
    
    Args:
        df: Input DataFrame
        lags: List of lag periods to create
        features: List of feature names to transform (if None, uses all numeric columns)
    
    Returns:
        Series with lagged features
    """
    if features is None:
        features = df.select_dtypes(include=['number']).columns.tolist()
    
    result = pd.DataFrame(index=df.index)
    
    for feature in features:
        for lag in lags:
            result[f"{feature}_lag_{lag}"] = df[feature].shift(lag)
    
    # Fill NaN values that occur at the beginning due to shifting
    result = result.fillna(method='bfill')
    
    # Return the mean across all lagged features
    return result.mean(axis=1)

def sentiment_score(df: pd.DataFrame, text_col: str = 'text') -> pd.Series:
    """
    Calculate a simple sentiment score for text data.
    This is a placeholder for a more sophisticated NLP pipeline.
    
    Args:
        df: Input DataFrame
        text_col: Column name containing text data
    
    Returns:
        Series with sentiment scores (-1 to 1)
    """
    # This is a very simplistic implementation
    # In a real system, you would use a proper NLP library
    
    # Positive and negative word lists (very minimal example)
    positive_words = ['good', 'great', 'excellent', 'positive', 'success', 'happy', 'gain']
    negative_words = ['bad', 'poor', 'negative', 'failure', 'sad', 'loss', 'problem']
    
    if text_col not in df.columns:
        # Return zeros if text column doesn't exist
        return pd.Series(0, index=df.index)
    
    scores = []
    
    for text in df[text_col]:
        if not isinstance(text, str):
            scores.append(0)
            continue
            
        text = text.lower()
        pos_count = sum(1 for word in positive_words if word in text)
        neg_count = sum(1 for word in negative_words if word in text)
        
        total = pos_count + neg_count
        if total == 0:
            scores.append(0)
        else:
            scores.append((pos_count - neg_count) / total)
    
    return pd.Series(scores, index=df.index)

def interaction_features(df: pd.DataFrame, features: List[str]) -> pd.Series:
    """
    Create interaction features (products) between specified features.
    
    Args:
        df: Input DataFrame
        features: List of feature names to create interactions for
    
    Returns:
        Series with interaction features
    """
    if len(features) < 2:
        raise ValueError("Need at least 2 features to create interactions")
    
    result = pd.Series(1.0, index=df.index)
    for feature in features:
        if feature in df.columns:
            result *= df[feature]
    
    return result

def polynomial_features(df: pd.DataFrame, feature: str, degree: int = 2) -> pd.Series:
    """
    Create polynomial features for a given column.
    
    Args:
        df: Input DataFrame
        feature: Feature name to transform
        degree: Polynomial degree
    
    Returns:
        Series with polynomial features
    """
    if feature not in df.columns:
        raise ValueError(f"Feature {feature} not found in DataFrame")
    
    base = df[feature]
    return base ** degree