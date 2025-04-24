"""
feature_discovery.py

FeatureDiscoveryEngine: Discovers new symbolic tags, variable groupings, or emergent behaviors using clustering and dimensionality reduction. Logs discoveries to the learning log and provides a CLI entry point.
"""

import pandas as pd
from sklearn.cluster import KMeans, DBSCAN
from sklearn.decomposition import PCA
from sklearn.manifold import TSNE
from core.pulse_learning_log import log_learning_event
from datetime import datetime
from learning.engines.feature_discovery import FeatureDiscoveryEngine
