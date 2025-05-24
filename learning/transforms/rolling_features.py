"""
rolling_features.py

Provides rolling window feature engineering for Pulse.
"""

import pandas as pd


def rolling_mean_feature(
    df: pd.DataFrame, window: int = 3, column: str = None
) -> pd.Series:
    """
    Compute rolling mean for a specified column in the DataFrame.
    If column is None, use the first column.
    """
    if column is None:
        column = df.columns[0]
    return (
        df[column]
        .rolling(window=window, min_periods=1)
        .mean()
        .rename(f"{column}_rolling_mean_{window}")
    )
