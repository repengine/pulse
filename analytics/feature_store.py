"""
Feature store for Pulse.
Manages raw and engineered feature pipelines.
"""

from typing import Callable, Dict, List
import pandas as pd
import importlib
from engine.pulse_config import FEATURE_PIPELINES


class FeatureStore:
    """
    A centralized feature store to register and retrieve raw and transformed features.
    """

    def __init__(self):
        self._raw_loaders: Dict[str, Callable[[], pd.DataFrame]] = {}
        self._transforms: Dict[str, Callable[[pd.DataFrame], pd.Series]] = {}
        self._cache: Dict[str, pd.Series] = {}
        # auto-register pipelines from config
        for feat, spec in FEATURE_PIPELINES.items():
            module_name, fn_name = spec["raw_loader"].rsplit(".", 1)
            raw_fn = getattr(importlib.import_module(module_name), fn_name)
            self.register_raw(feat, raw_fn)
            if "transform" in spec:
                module_name, fn_name = spec["transform"].rsplit(".", 1)
                trans_fn = getattr(importlib.import_module(module_name), fn_name)
                self.register_transform(feat, trans_fn)

    def register_raw(self, name: str, loader: Callable[[], pd.DataFrame]):
        """Register a raw data loader by name."""
        self._raw_loaders[name] = loader

    def register_transform(
        self, name: str, transform: Callable[[pd.DataFrame], pd.Series]
    ):
        """Register a transform function that takes raw DataFrame and returns a Series."""
        self._transforms[name] = transform

    def get(self, name: str) -> pd.Series:
        """
        Retrieve a feature by name, computing it if necessary.
        """
        if name in self._cache:
            return self._cache[name]
        # determine if it's raw or transform
        if name in self._raw_loaders:
            df = self._raw_loaders[name]()
            series = df[name] if name in df else df.iloc[:, 0]
        elif name in self._transforms:
            # apply transform on concatenated raw data
            df = pd.concat(
                {k: loader() for k, loader in self._raw_loaders.items()}, axis=1
            )
            series = self._transforms[name](df)
        else:
            raise KeyError(f"Feature '{name}' not found in store.")
        self._cache[name] = series
        return series

    def list_features(self) -> List[str]:
        """List all registered feature names."""
        return list(set(self._raw_loaders.keys()) | set(self._transforms.keys()))

    def clear_cache(self):
        """
        Clear the cached computed features.
        """
        self._cache.clear()

    def remove_feature(self, name: str):
        """
        Remove a registered feature loader or transform.
        """
        self._raw_loaders.pop(name, None)
        self._transforms.pop(name, None)
        self._cache.pop(name, None)


# instantiate a global feature store
feature_store = FeatureStore()
