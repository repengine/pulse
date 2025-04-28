"""
FeatureDiscoveryEngine

Discovers new symbolic tags, variable groupings, or emergent behaviors using clustering and dimensionality reduction.
Logs discoveries to the learning log and provides a CLI entry point.
"""

import pandas as pd
from sklearn.cluster import KMeans, DBSCAN
from sklearn.decomposition import PCA
from sklearn.manifold import TSNE
from sklearn.feature_selection import SelectKBest, mutual_info_regression
from pydantic import BaseModel, ValidationError
from core.pulse_learning_log import log_learning_event
from datetime import datetime
from typing import Dict, Any, Optional

class FeatureDiscoveryInput(BaseModel):
    data: Any  # Accepts DataFrame or dict

class FeatureDiscoveryResult(BaseModel):
    status: str
    features: list
    clusters: dict = {}
    top_variables: list = []
    error: Optional[str] = None

class FeatureDiscoveryEngine:
    """
    Engine for discovering new features, tags, or clusters in data.
    """
    def discover_features(self, df: pd.DataFrame) -> dict:
        """
        Discover features using feature selection and clustering.
        Args:
            df (pd.DataFrame): Input data.
        Returns:
            dict: Discovery results.
        """
        try:
            # Validate input schema
            FeatureDiscoveryInput(data=df)
            result = {"status": "success", "features": [], "clusters": {}, "top_variables": []}
            # Feature selection (SelectKBest)
            if 'target' in df.columns:
                X = df.drop(columns=['target'])
                y = df['target']
                selector = SelectKBest(mutual_info_regression, k=min(5, X.shape[1]))
                selector.fit(X, y)
                top_vars = list(X.columns[selector.get_support()])
                result["top_variables"] = top_vars
            else:
                top_vars = list(df.columns)
            # Clustering (KMeans)
            if len(top_vars) >= 2:
                kmeans = KMeans(n_clusters=min(3, len(df)), n_init=10)
                clusters = kmeans.fit_predict(df[top_vars])
                result["clusters"] = {"labels": clusters.tolist()}
            # DBSCAN (optional)
            dbscan = DBSCAN(eps=0.5, min_samples=2)
            db_labels = dbscan.fit_predict(df[top_vars])
            result["clusters"]["dbscan_labels"] = db_labels.tolist()
            # Log event
            log_learning_event("feature_discovery", {
                "timestamp": datetime.utcnow().isoformat(),
                "top_variables": result["top_variables"],
                "clusters": result["clusters"]
            })
            # Validate output schema
            FeatureDiscoveryResult(**result)
            return result
        except ValidationError as ve:
            return {"status": "error", "error": str(ve)}
        except Exception as e:
            return {"status": "error", "error": str(e)}

if __name__ == "__main__":
    engine = FeatureDiscoveryEngine()
    import pandas as pd
    df = pd.DataFrame({"a": [1,2,3], "b": [4,5,6]})
    print(engine.discover_features(df))
