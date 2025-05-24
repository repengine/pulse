import pandas as pd
from typing import Dict
from pathlib import Path


class Preprocessor:
    def __init__(self, raw_data_dir: str, feature_store_path: str) -> None:
        self.raw_data_dir = Path(raw_data_dir)
        self.feature_store_path = Path(feature_store_path)
        self.raw_data: Dict[str, pd.DataFrame] = {}
        self.features: pd.DataFrame = pd.DataFrame()

    def load_raw(self) -> None:
        """
        Load raw forecasts, retrodictions, and IRIS data from storage.
        """
        # TODO: implement loading logic for PFPA archive, retrodiction memory, and IRIS snapshots
        pass

    def merge_data(self) -> None:
        """
        Merge live forecast data with retrodiction results.
        """
        # TODO: implement merge logic using self.raw_data
        pass

    def normalize(self) -> None:
        """
        Normalize numeric columns to be suitable for training.
        """
        # TODO: apply scaling/normalization to self.features
        pass

    def compute_features(self) -> None:
        """
        Compute derived features for model training.
        """
        # TODO: implement feature engineering steps
        pass

    def save_features(self) -> str:
        """
        Save computed features to the feature store.
        """
        # TODO: persist self.features to disk (e.g., CSV, Parquet)
        self.feature_store_path.parent.mkdir(parents=True, exist_ok=True)
        self.features.to_parquet(self.feature_store_path)
        return str(self.feature_store_path)
