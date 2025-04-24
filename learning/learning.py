"""
Learning.py

Pulse Meta-Learning Engine v0.30
Evolves symbolic overlays, variable trust scores, and system memory using simulation lineage,
forecast regret, and symbolic divergence.

Hooks into:
- Trace memory
- Variable performance logs
- Symbolic arc analyzers
- Trust regret and PFPA deltas

Author: Pulse AI Engine
"""

import logging
from typing import Any, Dict, List, Optional, Callable
from datetime import datetime
import json
import pandas as pd
import networkx as nx
import statsmodels.api as sm
from sklearn.feature_selection import mutual_info_regression
from sklearn.preprocessing import StandardScaler

try:
    import shap
except ImportError:
    shap = None  # Optional interpretability

from memory.trace_memory import TraceMemory
from memory.variable_performance_tracker import VariablePerformanceTracker
from core.variable_registry import VariableRegistry
from dev_tools.generate_symbolic_upgrade_plan import generate_symbolic_upgrade_plan
from dev_tools.apply_symbolic_upgrades import apply_symbolic_upgrades
from dev_tools.apply_symbolic_revisions import apply_symbolic_revisions
from dev_tools.pulse_batch_alignment_analyzer import analyze_arc_alignment
from trust_system.pulse_regret_chain import score_symbolic_regret
from simulation_engine.historical_retrodiction_runner import run_retrodiction_test

from core.pulse_learning_log import (
    log_variable_weight_change,
    log_symbolic_upgrade,
    log_revision_trigger,
    log_arc_regret,
    log_learning_summary,
    log_learning_event
)

from simulation_engine.rule_mutation_engine import apply_rule_mutations  # 🔧 Step 1
from memory.variable_cluster_engine import summarize_clusters  # 🔧 Step 1
from memory.rule_cluster_engine import summarize_rule_clusters  # 🔧 Step 1
from operator_interface.rule_cluster_digest_formatter import format_cluster_digest_md  # 🔧 PATCH 1
from operator_interface.variable_cluster_digest_formatter import format_variable_cluster_digest_md  # ✅ PATCH A Step 1
from operator_interface.mutation_digest_exporter import export_full_digest  # ✅ PATCH A Step 1
from symbolic_system.symbolic_contradiction_cluster import cluster_symbolic_conflicts  # ✅ PATCH A Step 1
from operator_interface.symbolic_contradiction_digest import export_contradiction_digest_md  # ✅ PATCH A Step 1
from learning.output_data_reader import OutputDataReader  # Local integration
from learning.learning_profile import LearningProfile
from learning.engines.anomaly_remediation import AnomalyRemediationEngine
from learning.engines.feature_discovery import FeatureDiscoveryEngine
from learning.engines.audit_reporting import AuditReportingEngine
from learning.engines.causal_inference import CausalInferenceEngine
from learning.engines.continuous_learning import ContinuousLearningEngine
from learning.engines.external_integration import ExternalIntegrationEngine
from learning.engines.active_experimentation import ActiveExperimentationEngine
from core.bayesian_trust_tracker import bayesian_trust_tracker
from trust_system.trust_engine import TrustEngine

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)

class AdvancedLearningEngine:
    def __init__(self, data_path: str = "data/outputs"):
        self.memory = {}  # Persistent memory trace
        self.plugins = []  # Plugin analytics and hooks
        self.overlay_graph = nx.DiGraph()  # Symbolic influence paths
        self.data_loader = OutputDataReader(data_path)
        self.callbacks = []  # Callbacks for core learning loop

    def integrate_external_data(self, source_df: Optional[pd.DataFrame] = None):
        if source_df is None:
            source_df = self.data_loader.get_all_metadata()
        logging.info("[LearningEngine] Integrating data with %d records", len(source_df))
        # Concept drift detection and semi-supervised blending
        try:
            import pandas as pd
            retdf = pd.read_json("logs/retrodiction_result_log.jsonl", lines=True)
            error_changes = retdf["error_score"].diff().abs()
            if (error_changes > 0.1).any():
                logging.info("[LearningEngine] Concept drift detected: retrodiction error shifts")
            blended = pd.concat([
                source_df.assign(source="live"),
                retdf.assign(source="retrodiction")
            ], ignore_index=True)
            logging.info(f"[LearningEngine] Blended live and retrodicted data: {blended.shape[0]} records")
            source_df = blended
        except Exception as e:
            logging.warning(f"[LearningEngine] Concept drift blending failed: {e}")
        if {'fragility', 'trust_score'}.issubset(source_df.columns):
            self.analyze_trust_patterns(source_df)
        if {'symbolic_overlay', 'forecast_success'}.issubset(source_df.columns):
            self.analyze_symbolic_correlation(source_df)

    def analyze_trust_patterns(self, df: pd.DataFrame):
        try:
            df = df.copy()
            df['fragility_rolling'] = df['fragility'].rolling(window=5).mean()
            model = sm.OLS(df['trust_score'], sm.add_constant(df['fragility_rolling'].fillna(0)))
            result = model.fit()
            logging.info(f"[LearningEngine] Trust-FRAG R²: {result.rsquared:.3f}")
            self.memory['trust_model_summary'] = result.summary().as_text()
        except Exception as e:
            logging.warning("[LearningEngine] Trust regression failed: %s", e)

    def analyze_symbolic_correlation(self, df: pd.DataFrame):
        try:
            df = df.copy()
            df['symbolic_encoded'] = df['symbolic_overlay'].astype('category').cat.codes
            X = df[['symbolic_encoded']]
            y = df['forecast_success']
            score = mutual_info_regression(X, y)[0]
            logging.info(f"[LearningEngine] Symbolic overlay MI score: {score:.4f}")
            overlay_name = df['symbolic_overlay'].mode()[0]
            self.overlay_graph.add_edge(overlay_name, 'forecast_success', weight=score)
        except Exception as e:
            logging.warning("[LearningEngine] Symbolic correlation failed: %s", e)

    def explain_forecast_with_shap(self, model, X: pd.DataFrame):
        if not shap:
            logging.warning("[LearningEngine] SHAP not installed.")
            return None
        try:
            explainer = shap.Explainer(model.predict, X)
            shap_values = explainer(X)
            return shap_values
        except Exception as e:
            logging.error("[LearningEngine] SHAP explanation failed: %s", e)
            return None

    def remember(self, key, value):
        self.memory[key] = value

    def recall(self, key):
        return self.memory.get(key)

    def register_plugin(self, plugin):
        self.plugins.append(plugin)

    def summarize_plugins(self):
        return [str(p) for p in self.plugins]

    def export_analytics_summary(self) -> Dict[str, Any]:
        return {
            "trust_model_summary": self.memory.get("trust_model_summary"),
            "overlay_graph_edges": list(self.overlay_graph.edges(data=True)),
            "plugin_summaries": self.summarize_plugins()
        }

    def register_callback(self, callback: Callable[[Dict[str, Any]], None]):
        self.callbacks.append(callback)

    def trigger_callbacks(self):
        summary = self.export_analytics_summary()
        for cb in self.callbacks:
            cb(summary)

    def sync_memory(self, external_memory: Dict[str, Any]):
        self.memory.update(external_memory)

class LearningEngine:
    """
    The core meta-learning engine for Pulse.
    Handles memory analysis, variable trust updates, symbolic arc scoring,
    overlay mutation planning, and revision triggers.
    Integrates advanced analytics, anomaly detection, feature discovery, audit reporting,
    causal inference, continuous learning, external integration, and experimentation engines.
    """
    def __init__(self) -> None:
        self.trace = TraceMemory()
        self.tracker = VariablePerformanceTracker()
        self.registry = VariableRegistry()
        self.advanced_engine = AdvancedLearningEngine()
        self.worldstate = None
        # --- Integrated Engines ---
        self.anomaly_remediator = AnomalyRemediationEngine()
        self.feature_discoverer = FeatureDiscoveryEngine()
        self.audit_reporter = AuditReportingEngine()
        self.causal_inferencer = CausalInferenceEngine()
        self.continuous_learner = ContinuousLearningEngine()
        self.external_integrator = ExternalIntegrationEngine()
        self.active_experimenter = ActiveExperimentationEngine()
        # Register as plugins for analytics/interpretability
        self.advanced_engine.register_plugin(self.anomaly_remediator)
        self.advanced_engine.register_plugin(self.feature_discoverer)
        self.advanced_engine.register_plugin(self.causal_inferencer)
        self.advanced_engine.register_plugin(self.continuous_learner)
        self.advanced_engine.register_plugin(self.external_integrator)
        self.advanced_engine.register_plugin(self.active_experimenter)

    def attach_worldstate(self, state):
        """
        Attach a WorldState object for direct access.
        """
        self.worldstate = state

    def on_simulation_turn_end(self, state_snapshot):
        """
        Hook to be called after each simulation turn.
        """
        # Example: log trace, update memory, trigger learning, etc.
        # Enrich state_snapshot with trust metadata if overlays/capital present
        enriched = TrustEngine.enrich_trust_metadata(state_snapshot)
        self.trace.log_trace_entry(trace_id="sim_turn", forecast=enriched, input_state=state_snapshot)
        # Optionally trigger learning updates or logging
        if "trust_label" not in enriched or "confidence" not in enriched:
            logging.warning("[TRUST] Warning: trust_label or confidence missing from learning turn output.")

    def consume_simulation_trace(self, trace_path: str):
        """
        Load and analyze a simulation trace file (jsonl).
        """
        df = self.advanced_engine.data_loader.load_trace(trace_path)
        self.advanced_engine.integrate_external_data(df)

    def process_drift_report(self, drift_report: dict):
        """
        Integrate simulation drift analysis into learning.
        """
        self.advanced_engine.memory['last_drift_report'] = drift_report
        # Optionally trigger learning or adaptation

    def update_variable_weights(self, variable_id, outcome):
        """
        Adjusts variable trust weights based on performance statistics.
        """
        try:
            scores: Dict[str, Dict[str, float]] = self.tracker.score_variable_effectiveness()
            logging.info("[Variable Learning] Adjusting weights...")
            for var, stat in scores.items():
                avg_conf = stat.get("avg_confidence")
                avg_frag = stat.get("avg_fragility")
                if avg_conf is None or avg_frag is None:
                    logging.warning(f"Missing stats for variable {var}: {stat}")
                    continue
                current = self.registry.get(var) or {}
                old_weight = current.get("trust_weight", 1.0)
                trust_adj = 1.0 + (avg_conf - avg_frag)
                self.registry.register_variable(var, {
                    **current,
                    "trust_weight": round(trust_adj, 3)
                })
                log_variable_weight_change(var, old_weight, round(trust_adj, 3))
            self.registry._save()
            # Bayesian trust update
            bayesian_trust_tracker.update(variable_id, outcome)
            # Optionally use trust/confidence in weight adjustment
            trust = bayesian_trust_tracker.get_trust(variable_id)
            conf_int = bayesian_trust_tracker.get_confidence_interval(variable_id)
            # Use trust/conf_int in your logic as needed
        except Exception as e:
            logging.error(f"Variable weight update failed: {e}")

    def update_variable_weights_from_profile(self, variable_id, profile_outcome):
        """
        Adjusts variable trust weights based on statistical feedback (e.g., drift, correlation).
        """
        stats = profile_outcome.get("variable_stats", {}).get(variable_id, {})
        if not stats:
            return
        old = self.registry.get(variable_id) or {}
        old_weight = old.get("trust_weight", 1.0)
        new_weight = stats.get("suggested_weight", old_weight)
        if new_weight != old_weight:
            self.registry.register_variable(variable_id, {**old, "trust_weight": new_weight})
            from core.pulse_learning_log import log_variable_weight_change
            log_variable_weight_change(variable_id, old_weight, new_weight)
        bayesian_trust_tracker.update(variable_id, profile_outcome)
        trust = bayesian_trust_tracker.get_trust(variable_id)
        conf_int = bayesian_trust_tracker.get_confidence_interval(variable_id)

    def apply_variable_mutation_pressure(self, variable_id, mutation_success):
        """
        Penalizes high-volatility, low-predictive variables by reducing their trust weights.
        Optionally, this can be extended to remove or reclassify low-trust variables.
        """
        scores = self.tracker.score_variable_effectiveness()
        drift_vars = self.tracker.detect_variable_drift(threshold=0.25)
        print(f"[Variable Learning] Drift-sensitive variables: {drift_vars}")
        for var in drift_vars:
            meta = self.registry.get(var) or {}
            old = meta.get("trust_weight", 1.0)
            new = max(0.1, old * 0.85)
            meta["trust_weight"] = round(new, 3)
            self.registry.register_variable(var, meta)
            log_variable_weight_change(var, old, new)
            bayesian_trust_tracker.update(var, mutation_success)
            trust = bayesian_trust_tracker.get_trust(var)
            conf_int = bayesian_trust_tracker.get_confidence_interval(var)
            print(f"[VariableTrust] {var}: trust={trust:.3f}, CI={conf_int}")

    def apply_rule_mutation_pressure(self, rule_id, mutation_success):
        print("[Rule Learning] Applying pressure to mutate causal rules...")
        apply_rule_mutations()
        bayesian_trust_tracker.update(rule_id, mutation_success)
        trust = bayesian_trust_tracker.get_trust(rule_id)
        conf_int = bayesian_trust_tracker.get_confidence_interval(rule_id)
        print(f"[RuleTrust] {rule_id}: trust={trust:.3f}, CI={conf_int}")

    def audit_cluster_volatility(self):  # 🔧 Step 2
        print("🧠 Variable Cluster Volatility Scan:")
        clusters = summarize_clusters()
        for c in clusters:
            print(f"\n📦 Cluster: {c['cluster']} (size: {c['size']})")
            print(f"Volatility Score: {c['volatility_score']}")
            if c['volatility_score'] > 0.5:
                print("⚠️  High volatility — triggering mutation pressure.")
                for var in c['variables']:
                    current = self.registry.get(var)
                    if not current:
                        continue
                    old = current.get("trust_weight", 1.0)
                    new = max(0.1, old * 0.85)
                    current["trust_weight"] = round(new, 3)
                    self.registry.register_variable(var, current)
                    log_variable_weight_change(var, old, new)
            for v in c["variables"]:
                print(f" - {v}")

    def audit_rule_clusters(self):  # 🔧 Step 2
        print("📊 Rule Cluster Volatility Scan:")
        clusters = summarize_rule_clusters(verbose=False)
        for c in clusters:
            print(f"\n📦 Cluster: {c['cluster']} (size: {c['size']})")
            print(f"Volatility Score: {c['volatility_score']}")
            if c['volatility_score'] > 0.4:
                print(f"⚠️ High-volatility cluster: {c['cluster']} — consider mutation or demotion.")
            for r in c["rules"]:
                print(f" - {r}")

    def audit_symbolic_contradictions(self, forecasts: List[Dict]):
        clusters = cluster_symbolic_conflicts(forecasts)
        if not clusters:
            print("✅ No symbolic contradictions detected.")
            return
        print("⚠️ Symbolic contradiction clusters found:")
        for cluster in clusters:
            log_learning_event("symbolic_contradiction", {
                "origin_turn": cluster["origin_turn"],
                "conflicts": cluster["conflicts"],
                "timestamp": datetime.utcnow().isoformat()
            })
            print(f"🌀 Turn {cluster['origin_turn']} — {len(cluster['conflicts'])} conflict(s)")

    def register_advanced_callback(self, callback):
        """
        Register a callback with the advanced learning engine.
        """
        self.advanced_engine.register_callback(callback)

    def log_learning_summary(self) -> None:
        """
        Logs summary of the learning loop.
        """
        logging.info("✅ Learning loop completed. All metrics updated.")
        log_learning_summary({
            "completed_at": datetime.utcnow().isoformat(),
            "updated_variables": len(self.registry.all()),
            "recent_traces": self.trace.summarize_memory()
        })
        digest = format_cluster_digest_md(limit=5)
        print("\n📘 Rule Cluster Digest:\n")
        print(digest)
        try:
            with open("logs/learning_summary_with_digest.md", "w", encoding="utf-8") as f:
                f.write(digest)
        except Exception as e:
            logging.error(f"Failed to write rule cluster digest: {e}")

        vcluster_digest = format_variable_cluster_digest_md(limit=5)
        print("\n📘 Variable Cluster Digest:\n")
        print(vcluster_digest)

        export_full_digest()
        export_contradiction_digest_md()

# --- Retrodiction/Retrospective Analysis Utilities ---
from typing import Dict, List, Optional
import math

# Symbolic/overlay error (from learning/forecast_retrospector.py)
def compute_retrodiction_error(forecast: Dict, current_state: Dict, keys: Optional[List[str]] = None) -> float:
    """
    Compute symbolic/variable delta between forecast's initial assumption
    and what the current_state actually contains now.
    Args:
        forecast (Dict): The forecast being evaluated
        current_state (Dict): Ground truth snapshot
        keys (Optional[List[str]]): Specific overlays or variables to score (default: all)
    Returns:
        float: Normalized mean squared error (0–1+)
    """
    f_init = forecast.get("forecast", {}).get("start_state", {}).get("overlays", {})
    c_now = current_state.get("overlays", {})
    if not isinstance(f_init, dict) or not isinstance(c_now, dict):
        return 0.0
    keys = keys or list(set(f_init.keys()) & set(c_now.keys()))
    if not keys:
        return 0.0
    deltas = []
    for k in keys:
        try:
            a = float(f_init.get(k, 0))
            b = float(c_now.get(k, 0))
            deltas.append((a - b) ** 2)
        except Exception:
            continue
    if not deltas:
        return 0.0
    return round(sum(deltas) / len(deltas), 4)

# Past state reconstruction (from trust_system/forecast_retrospector.py)
def reconstruct_past_state(forecast: Dict) -> Dict:
    """
    Generate a synthetic approximation of the past state implied by a given forecast.
    Uses symbolic overlays and capital snapshot to infer the forecast's assumptions.
    """
    overlays = forecast.get("overlays", {})
    capital = forecast.get("forecast", {}).get("start_capital", {})
    return {
        "hope": overlays.get("hope", 0.5),
        "despair": overlays.get("despair", 0.5),
        "fatigue": overlays.get("fatigue", 0.5),
        "rage": overlays.get("rage", 0.5),
        "capital_snapshot": capital,
    }

# Symbolic + capital error (from trust_system/forecast_retrospector.py)
def retrodict_error_score(past_state: Dict, current_state: Dict, symbolic_weight: float = 1.0, capital_weight: float = 1.0) -> float:
    """
    Compute an error score between a reconstructed past and the current believed state.
    Combines symbolic and capital deviations into a single metric.
    """
    symbolic_keys = ["hope", "despair", "rage", "fatigue"]
    error_sum = 0.0
    for k in symbolic_keys:
        error_sum += symbolic_weight * (past_state.get(k, 0.5) - current_state.get(k, 0.5)) ** 2
    capital_keys = set(past_state.get("capital_snapshot", {}).keys()) | set(current_state.get("capital_snapshot", {}).keys())
    for k in capital_keys:
        p_val = past_state.get("capital_snapshot", {}).get(k, 0)
        c_val = current_state.get("capital_snapshot", {}).get(k, 0)
        error_sum += capital_weight * ((p_val - c_val) / 1000.0) ** 2
    return round(math.sqrt(error_sum), 4)

# Batch analysis (from trust_system/forecast_retrospector.py)
def retrospective_analysis_batch(forecasts: List[Dict], current_state: Dict, threshold: float = 1.5) -> List[Dict]:
    """
    Perform retrodiction error scoring across a batch of forecasts.
    Appends 'retrodiction_error' and optional trust flag if above threshold.
    """
    for f in forecasts:
        past_state = reconstruct_past_state(f)
        score = retrodict_error_score(past_state, current_state)
        f["retrodiction_error"] = score
        if score > threshold:
            f["retrodiction_flag"] = "⚠️ Symbolic misalignment"
    return forecasts

# --- End Retrodiction/Retrospective Analysis Utilities ---

if __name__ == "__main__":
    engine = LearningEngine()
    engine.run_meta_update()
