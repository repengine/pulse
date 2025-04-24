"""
output_data_reader.py

Pulse Output Reader — unified interface for historical forecast, symbolic, trust, and capital data.

This module parses Pulse-generated output files and memory logs into structured DataFrames
so that meta-analysis modules (e.g., LearningEngine) can perform scoring, mutation, or regression.

Supports:
- Forecast outcome loading
- Symbolic overlay mapping
- Capital performance parsing
- Trust metadata extraction
- Strategos Digest tag access

Author: Pulse v0.299
"""

import os
import json
import pandas as pd
from typing import List, Dict, Optional
from core.schemas import ForecastRecord, OverlayLog, TrustScoreLog, CapitalOutcome, DigestTag
from pydantic import ValidationError

class OutputDataReader:
    def __init__(self, base_path: str):
        """
        Args:
            base_path (str): Directory root where Pulse outputs and logs are stored
        """
        self.base_path = base_path

    def load_forecast_outputs(self) -> pd.DataFrame:
        """Load all forecast output records into a unified DataFrame."""
        records = []
        forecasts_path = os.path.join(self.base_path, "forecast_output")
        for fname in os.listdir(forecasts_path):
            if fname.endswith(".json"):
                with open(os.path.join(forecasts_path, fname)) as f:
                    data = json.load(f)
                    if isinstance(data, list):
                        records.extend(data)
                    elif isinstance(data, dict):
                        records.append(data)
        valid_records = []
        for rec in records:
            try:
                ForecastRecord(**rec)
                valid_records.append(rec)
            except ValidationError as ve:
                print(f"[OutputDataReader] Invalid forecast record: {ve}")
        return pd.DataFrame(valid_records)

    def load_symbolic_overlays(self) -> pd.DataFrame:
        """Extract symbolic overlays with success/failure attribution."""
        overlay_path = os.path.join(self.base_path, "symbolic_logs")
        data = []
        for fname in os.listdir(overlay_path):
            if fname.endswith(".json"):
                with open(os.path.join(overlay_path, fname)) as f:
                    data.extend(json.load(f))
        valid_data = []
        for rec in data:
            try:
                OverlayLog(**rec)
                valid_data.append(rec)
            except ValidationError as ve:
                print(f"[OutputDataReader] Invalid overlay log: {ve}")
        return pd.DataFrame(valid_data)

    def load_trust_scores(self) -> pd.DataFrame:
        """Load trust scoring metadata per forecast."""
        trust_path = os.path.join(self.base_path, "trust_logs")
        results = []
        for fname in os.listdir(trust_path):
            if fname.endswith(".json"):
                with open(os.path.join(trust_path, fname)) as f:
                    results.extend(json.load(f))
        valid_results = []
        for rec in results:
            try:
                TrustScoreLog(**rec)
                valid_results.append(rec)
            except ValidationError as ve:
                print(f"[OutputDataReader] Invalid trust score log: {ve}")
        return pd.DataFrame(valid_results)

    def load_capital_outcomes(self) -> pd.DataFrame:
        """Aggregate capital simulation results per scenario."""
        capital_path = os.path.join(self.base_path, "capital_output")
        outputs = []
        for fname in os.listdir(capital_path):
            if fname.endswith(".json"):
                with open(os.path.join(capital_path, fname)) as f:
                    outputs.extend(json.load(f))
        valid_outputs = []
        for rec in outputs:
            try:
                CapitalOutcome(**rec)
                valid_outputs.append(rec)
            except ValidationError as ve:
                print(f"[OutputDataReader] Invalid capital outcome: {ve}")
        return pd.DataFrame(valid_outputs)

    def load_digest_tags(self) -> pd.DataFrame:
        """Pull Strategos Digest tags or narrative summaries."""
        tag_path = os.path.join(self.base_path, "digest_logs")
        tags = []
        for fname in os.listdir(tag_path):
            if fname.endswith(".json"):
                with open(os.path.join(tag_path, fname)) as f:
                    tags.extend(json.load(f))
        valid_tags = []
        for rec in tags:
            try:
                DigestTag(**rec)
                valid_tags.append(rec)
            except ValidationError as ve:
                print(f"[OutputDataReader] Invalid digest tag: {ve}")
        return pd.DataFrame(valid_tags)

    def get_all_metadata(self) -> pd.DataFrame:
        """
        Merge all subsystems' data on scenario ID or timestamp if present.
        Returns a master DataFrame for learning engines to analyze.
        """
        try:
            df_f = self.load_forecast_outputs()
            df_s = self.load_symbolic_overlays()
            df_t = self.load_trust_scores()
            df_c = self.load_capital_outcomes()
            df_d = self.load_digest_tags()
            df = df_f.merge(df_s, how="left", on="scenario_id")\
                      .merge(df_t, how="left", on="scenario_id")\
                      .merge(df_c, how="left", on="scenario_id")\
                      .merge(df_d, how="left", on="scenario_id")
            return df
        except Exception as e:
            print(f"[OutputDataReader] Metadata merge failed: {e}")
            return pd.DataFrame()

# Market, social, ecological data loaders for feature engineering
def load_market_data() -> pd.DataFrame:
    """
    Load market data for feature engineering.
    Reads CSV files from irldata/market_data directory.
    """
    base_dir = os.path.dirname(os.path.dirname(__file__))
    data_dir = os.path.join(base_dir, "irldata", "market_data")
    dfs = []
    if os.path.isdir(data_dir):
        for fname in os.listdir(data_dir):
            if fname.endswith(".csv"):
                try:
                    df = pd.read_csv(os.path.join(data_dir, fname))
                    dfs.append(df)
                except Exception as e:
                    print(f"[OutputDataReader] Error reading market data file {fname}: {e}")
    if dfs:
        return pd.concat(dfs, ignore_index=True)
    return pd.DataFrame()

def load_social_data() -> pd.DataFrame:
    """
    Load social data (e.g., sentiment, engagement) for feature engineering.
    Reads CSV files from irldata/social_data directory.
    """
    base_dir = os.path.dirname(os.path.dirname(__file__))
    data_dir = os.path.join(base_dir, "irldata", "social_data")
    dfs = []
    if os.path.isdir(data_dir):
        for fname in os.listdir(data_dir):
            if fname.endswith(".csv"):
                try:
                    df = pd.read_csv(os.path.join(data_dir, fname))
                    dfs.append(df)
                except Exception as e:
                    print(f"[OutputDataReader] Error reading social data file {fname}: {e}")
    if dfs:
        return pd.concat(dfs, ignore_index=True)
    return pd.DataFrame()

def load_ecological_data() -> pd.DataFrame:
    """
    Load ecological data (e.g., environmental indicators) for feature engineering.
    Reads CSV files from irldata/ecological_data directory.
    """
    base_dir = os.path.dirname(os.path.dirname(__file__))
    data_dir = os.path.join(base_dir, "irldata", "ecological_data")
    dfs = []
    if os.path.isdir(data_dir):
        for fname in os.listdir(data_dir):
            if fname.endswith(".csv"):
                try:
                    df = pd.read_csv(os.path.join(data_dir, fname))
                    dfs.append(df)
                except Exception as e:
                    print(f"[OutputDataReader] Error reading ecological data file {fname}: {e}")
    if dfs:
        return pd.concat(dfs, ignore_index=True)
    return pd.DataFrame()
