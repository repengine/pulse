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
    """
    def __init__(self) -> None:
        self.trace = TraceMemory()
        self.tracker = VariablePerformanceTracker()
        self.registry = VariableRegistry()
        self.advanced_engine = AdvancedLearningEngine()
        self.worldstate = None

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
        self.trace.log_trace_entry(trace_id="sim_turn", forecast={}, input_state=state_snapshot)
        # Optionally trigger learning updates or logging

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

    def adjust_rule_weights_from_learning_profile(self, learning_profile: Dict[str, Any]) -> None:
        """
        Adjusts arc/tag trust weights based on learning profile statistics.
        Logs all changes. Extend to persist to rule/tag registry as needed.
        """
        arc_perf = learning_profile.get("arc_performance", {})
        tag_perf = learning_profile.get("tag_performance", {})
        for arc, stats in arc_perf.items():
            win_rate = stats.get("rate", 0)
            old_weight = stats.get("weight", 1.0)
            if win_rate < 0.3:
                new_weight = max(0.0, old_weight - 0.1)
                log_variable_weight_change(arc, old_weight, new_weight)
                # TODO: persist new_weight to arc registry
            elif win_rate > 0.8:
                new_weight = min(1.0, old_weight + 0.1)
                log_variable_weight_change(arc, old_weight, new_weight)
                # TODO: persist new_weight to arc registry
        for tag, stats in tag_perf.items():
            win_rate = stats.get("rate", 0)
            old_weight = stats.get("weight", 1.0)
            if win_rate < 0.3:
                new_weight = max(0.0, old_weight - 0.1)
                log_variable_weight_change(tag, old_weight, new_weight)
                # TODO: persist new_weight to tag registry
            elif win_rate > 0.8:
                new_weight = min(1.0, old_weight + 0.1)
                log_variable_weight_change(tag, old_weight, new_weight)
                # TODO: persist new_weight to tag registry

    def auto_tune_thresholds(self, learning_profile: Dict[str, Any]) -> None:
        """
        Adjusts confidence/fragility thresholds based on learning loop outputs.
        """
        from core.pulse_config import update_threshold
        avg_regret = learning_profile.get("avg_regret", None)
        if avg_regret is not None:
            if avg_regret > 0.5:
                update_threshold("CONFIDENCE_THRESHOLD", 0.5)
            elif avg_regret < 0.2:
                update_threshold("CONFIDENCE_THRESHOLD", 0.7)
        # Extend with more logic as needed

    def process_learning_profile(self, learning_profile: Dict[str, Any]) -> None:
        """
        Automates trust/weight feedback and threshold tuning from a learning profile.
        Ensures symbolic elements are not hardcoded to influence system learning; system can differentiate symbolic/statistical/causal sources.
        """
        # Only adjust symbolic elements if profile explicitly marks them as symbolic
        if learning_profile.get("type") == "symbolic":
            self.adjust_rule_weights_from_learning_profile(learning_profile)
        # Always allow threshold tuning, but can be extended to check source
        self.auto_tune_thresholds(learning_profile)
        # Optionally log a summary event
        from core.pulse_learning_log import log_learning_event
        log_learning_event("learning_profile_processed", {
            "profile_type": learning_profile.get("type"),
            "profile_keys": list(learning_profile.keys()),
            "timestamp": datetime.utcnow().isoformat()
        })

    def update_variable_weights_from_profile(self, learning_profile: Dict[str, Any]) -> None:
        """
        Adjusts variable trust weights based on statistical feedback (e.g., drift, correlation).
        """
        stats = learning_profile.get("variable_stats", {})
        for var, stat in stats.items():
            old = self.registry.get(var) or {}
            old_weight = old.get("trust_weight", 1.0)
            new_weight = stat.get("suggested_weight", old_weight)
            if new_weight != old_weight:
                self.registry.register_variable(var, {**old, "trust_weight": new_weight})
                from core.pulse_learning_log import log_variable_weight_change
                log_variable_weight_change(var, old_weight, new_weight)
        self.registry._save()

    def update_causal_links_from_profile(self, learning_profile: Dict[str, Any]) -> None:
        """
        Integrates causal feedback (e.g., inferred relationships, causal path analysis).
        """
        # Example: log or persist causal links
        causal_links = learning_profile.get("causal_links", {})
        if causal_links:
            from core.pulse_learning_log import log_learning_event
            log_learning_event("causal_links_update", {
                "links": causal_links,
                "timestamp": datetime.utcnow().isoformat()
            })
        # TODO: Integrate with rule/arc/variable registries as needed

    def process_learning_feedback(self, learning_profile: Dict[str, Any]) -> None:
        """
        Central entry point for all learning feedback.
        Routes feedback to symbolic, statistical, or causal handlers as appropriate.
        Accepts either a dict or a LearningProfile dataclass.
        """
        if isinstance(learning_profile, dict):
            profile = LearningProfile.from_dict(learning_profile)
        else:
            profile = learning_profile
        profile_type = profile.type
        if profile_type == "symbolic":
            self.adjust_rule_weights_from_learning_profile(profile.__dict__)
        elif profile_type == "statistical":
            self.update_variable_weights_from_profile(profile.__dict__)
        elif profile_type == "causal":
            self.update_causal_links_from_profile(profile.__dict__)
        # Always allow threshold tuning
        self.auto_tune_thresholds(profile.__dict__)
        from core.pulse_learning_log import log_learning_event
        log_learning_event("learning_feedback_processed", {
            "profile_type": profile_type,
            "profile_keys": list(profile.__dict__.keys()),
            "timestamp": datetime.utcnow().isoformat()
        })

    def run_meta_update(self) -> None:
        """
        Runs the full meta-learning update loop.
        """
        logging.info("🧠 Running Pulse Learning Loop...")
        try:
            self.analyze_trace_memory()
            self.update_variable_weights()
            self.score_symbolic_arcs()
            self.plan_overlay_mutations()
            self.trigger_revisions_if_needed()
            self.run_retrodiction_learning(start_date="2020-01-01", days=14)
            self.apply_retrodiction_pressure()
            self.apply_variable_mutation_pressure()
            self.apply_rule_mutation_pressure()
            self.audit_cluster_volatility()
            self.audit_rule_clusters()
            forecasts = []  # TODO: Replace with actual forecast retrieval
            self.audit_symbolic_contradictions(forecasts)
        except Exception as e:
            logging.exception(f"Meta update failed: {e}")
        try:
            self.advanced_engine.sync_memory(self.trace.summarize_memory())
            self.advanced_engine.integrate_external_data()
            analytics = self.advanced_engine.export_analytics_summary()
            log_learning_event("advanced_analytics_summary", analytics)
            self.run_retrodiction_learning(start_date="2020-01-01", days=14)
            self.log_learning_summary()
        except Exception as e:
            logging.exception(f"Meta update failed: {e}")

        # --- Symbolic Feedback Integration (Batch 2) ---
        try:
            from symbolic_system.pulse_symbolic_learning_loop import generate_learning_profile, learn_from_tuning_log
            from forecast_output.forecast_memory import ForecastMemory as OutputForecastMemory
            import os
            # Use revision candidates from forecast_output memory as symbolic input
            output_mem = OutputForecastMemory()
            revision_candidates = output_mem.isolate_revision_candidates()
            if revision_candidates:
                symbolic_profile = generate_learning_profile(revision_candidates)
                symbolic_profile["type"] = "symbolic"
                self.process_learning_feedback(symbolic_profile)
            # Fallback: tuning log
            tuning_log_path = os.path.join("logs", "symbolic_learning_log.jsonl")
            if os.path.exists(tuning_log_path):
                results = learn_from_tuning_log(tuning_log_path)
                symbolic_profile = generate_learning_profile(results)
                symbolic_profile["type"] = "symbolic"
                self.process_learning_feedback(symbolic_profile)
        except Exception as e:
            logging.warning(f"Symbolic feedback integration failed: {e}")

        # --- Statistical Feedback Integration (Batch 3) ---
        try:
            from memory.forecast_memory import ForecastMemory
            from memory.variable_performance_tracker import VariablePerformanceTracker
            forecast_mem = ForecastMemory()
            tracker = VariablePerformanceTracker()
            tracker.aggregate_from_memory(forecast_mem)
            stats = tracker.score_variable_effectiveness()
            drift = tracker.detect_variable_drift()
            variable_stats = {}
            for var, stat in stats.items():
                avg_conf = stat.get("avg_confidence")
                avg_frag = stat.get("avg_fragility")
                mi = stat.get("mutual_info")
                if avg_conf is not None and avg_frag is not None:
                    trust_adj = 1.0 + (avg_conf - avg_frag)
                    variable_stats[var] = {"suggested_weight": round(trust_adj, 3)}
                    if mi is not None:
                        variable_stats[var]["mutual_info"] = mi
            for var in drift:
                if var in variable_stats:
                    variable_stats[var]["drift_flagged"] = True
            if variable_stats:
                stat_profile = {"type": "statistical", "variable_stats": variable_stats}
                self.process_learning_feedback(stat_profile)
        except Exception as e:
            logging.warning(f"Statistical feedback integration failed: {e}")

        # --- Causal Feedback Integration (Batch 1 & 4) ---
        try:
            from memory.forecast_memory import ForecastMemory
            from forecast_engine.forecast_integrity_engine import infer_causal_links
            from simulation_engine.rules.reverse_rule_engine import trace_causal_paths
            forecast_mem = ForecastMemory()
            recent_forecasts = forecast_mem.get_recent(100)
            # Direct causal links
            causal_links = infer_causal_links(recent_forecasts)
            # Causal paths (multi-step)
            causal_paths = trace_causal_paths(recent_forecasts)
            if causal_links or causal_paths:
                causal_profile = {"type": "causal", "causal_links": causal_links, "causal_paths": causal_paths}
                self.process_learning_feedback(causal_profile)
        except Exception as e:
            logging.warning(f"Causal feedback integration failed: {e}")

        # --- Logging, Auditing, and Profile Schema (Batch 5) ---
        # All feedback is logged via process_learning_feedback; schema is enforced by profile dict structure.
        # For future: consider using a dataclass or pydantic model for learning profiles.

    def analyze_trace_memory(self) -> None:
        """
        Summarizes trace memory for interpretability.
        """
        try:
            summary = self.trace.summarize_memory()
            logging.info(f"[Trace Summary] {summary}")
        except Exception as e:
            logging.error(f"Trace memory analysis failed: {e}")

    def update_variable_weights(self) -> None:
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
        except Exception as e:
            logging.error(f"Variable weight update failed: {e}")

    def score_symbolic_arcs(self) -> None:
        """
        Scores symbolic arcs for regret/drift.
        """
        logging.info("[Arc Drift] Scoring symbolic arc regret...")
        try:
            result = score_symbolic_regret()
            for arc, score in result.get("regret_scores", {}).items():
                logging.info(f" - Arc: {arc}  Regret Score: {score:.2f}")
            log_arc_regret(result.get("regret_scores", {}))
        except Exception as e:
            logging.error(f"Symbolic arc scoring failed: {e}")

    def plan_overlay_mutations(self) -> None:
        """
        Generates and applies candidate overlay tweaks (symbolic rule mutation).
        Uses generate_symbolic_upgrade_plan and apply_symbolic_upgrades.
        """
        logging.info("[Symbolic Upgrade Plan] Generating candidate overlay tweaks...")
        try:
            plan = generate_symbolic_upgrade_plan()
            if plan:
                logging.info(f" - Proposed changes: {len(plan)}")
                apply_symbolic_upgrades(plan)
                log_symbolic_upgrade(plan)
            else:
                logging.info(" - No overlay tweaks proposed.")
        except Exception as e:
            logging.error(f"Overlay mutation planning failed: {e}")

    def trigger_revisions_if_needed(self) -> None:
        """
        Checks for batch drift and applies symbolic revisions if needed.
        """
        logging.info("[Arc Realignment] Checking batch drift...")
        try:
            drift_detected = analyze_arc_alignment(min_fragility=0.4)
            if drift_detected:
                logging.info(" - Drift detected. Applying symbolic revisions.")
                log_revision_trigger("batch drift or symbolic fragmentation detected")
                apply_symbolic_revisions()
            else:
                logging.info(" - No drift detected.")
        except Exception as e:
            logging.error(f"Arc realignment failed: {e}")

    def run_retrodiction_learning(self, start_date: str = "2020-01-01", days: int = 30):
        print(f"[Retrodiction] Running from {start_date} for {days} days...")
        run_retrodiction_test(start_date, days=days)

    def parse_retrodiction_log(self, path: str = "logs/retrodiction_result_log.jsonl", top_n: int = 5):
        try:
            with open(path, "r", encoding="utf-8") as f:
                entries = [json.loads(line) for line in f]
            sorted_errors = sorted(entries, key=lambda x: x.get("error_score", 0), reverse=True)
            return sorted_errors[:top_n]
        except Exception as e:
            print(f"[Learning] Failed to read retrodiction log: {e}")
            return []

    def apply_retrodiction_pressure(self):
        top_drift = self.parse_retrodiction_log()
        if not top_drift:
            return
        print("[Learning] Retrodiction pressure triggered. Top error days:")
        for entry in top_drift:
            print(f" - {entry['sim_date']}: error={entry['error_score']}")
        plan = generate_symbolic_upgrade_plan()
        if plan:
            print(" - Applying symbolic upgrades due to retrodiction divergence.")
            apply_symbolic_upgrades(plan)

    def apply_variable_mutation_pressure(self):
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

    def apply_rule_mutation_pressure(self):  # 🔧 Step 2
        print("[Rule Learning] Applying pressure to mutate causal rules...")
        apply_rule_mutations()

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

if __name__ == "__main__":
    engine = LearningEngine()
    engine.run_meta_update()
