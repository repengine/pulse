"""
Data preprocessing and feature engineering transforms.
"""

import pandas as pd
import numpy as np

def impute_missing(df: pd.DataFrame) -> pd.DataFrame:
    """Fill missing values with column median."""
    return df.fillna(df.median())

def normalize(df: pd.DataFrame) -> pd.DataFrame:
    """Scale features to zero mean and unit variance."""
    return (df - df.mean()) / df.std()

def select_top_k(df: pd.DataFrame, k: int = 5) -> pd.DataFrame:
    """Select top K features by variance."""
    variances = df.var().sort_values(ascending=False)
    top_cols = variances.index[:k]
    return df[top_cols]

# Example composite pipeline
def preprocess_pipeline(df: pd.DataFrame) -> pd.DataFrame:
    df_imputed = impute_missing(df)
    df_norm = normalize(df_imputed)
    return select_top_k(df_norm)