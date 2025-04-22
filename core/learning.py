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
from typing import Any, Dict, List
from datetime import datetime
import json

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

from dev_tools.rule_mutation_engine import apply_rule_mutations  # 🔧 Step 1
from core.variable_cluster_engine import summarize_clusters  # 🔧 Step 1
from memory.rule_cluster_engine import summarize_rule_clusters  # 🔧 Step 1
from operator_interface.rule_cluster_digest_formatter import format_cluster_digest_md  # 🔧 PATCH 1
from operator_interface.variable_cluster_digest_formatter import format_variable_cluster_digest_md  # ✅ PATCH A Step 1
from operator_interface.mutation_digest_exporter import export_full_digest  # ✅ PATCH A Step 1
from symbolic_system.symbolic_contradiction_cluster import cluster_symbolic_conflicts  # ✅ PATCH A Step 1
from operator_interface.symbolic_contradiction_digest import export_contradiction_digest_md  # ✅ PATCH A Step 1

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)

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
            # Run retrodiction learning before logging summary
            self.run_retrodiction_learning(start_date="2020-01-01", days=14)
            self.apply_retrodiction_pressure()
            self.apply_variable_mutation_pressure()
            self.apply_rule_mutation_pressure()
            self.audit_cluster_volatility()  # 🔧 Step 3
            self.audit_rule_clusters()       # 🔧 Step 3

            # --- PATCH A Step 3: Audit symbolic contradictions after retrodiction ---
            # If you have forecasts available, pass them here. Example:
            # forecasts = self.trace.get_recent_forecasts()  # <-- Replace with actual method if available
            # self.audit_symbolic_contradictions(forecasts)
            # For now, this is a placeholder:
            forecasts = []  # TODO: Replace with actual forecast retrieval
            self.audit_symbolic_contradictions(forecasts)
            # --- end PATCH ---

            self.log_learning_summary()
        except Exception as e:
            logging.exception(f"Meta update failed: {e}")

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
                # Validate stat keys
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
        # Trigger symbolic mutation
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
        # Optionally: remove or reclassify variables with very low trust_weight here

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

    # ✅ PATCH A Step 2: Add contradiction audit method
    def audit_symbolic_contradictions(self, forecasts: List[Dict]):
        clusters = cluster_symbolic_conflicts(forecasts)
        if not clusters:
            print("✅ No symbolic contradictions detected.")
            return
        print("⚠️ Symbolic contradiction clusters found:")
        for cluster in clusters:
            log_learning_event("symbolic_contradiction_cluster", {
                "origin_turn": cluster["origin_turn"],
                "conflicts": cluster["conflicts"]
            })
            print(f"🌀 Turn {cluster['origin_turn']} — {len(cluster['conflicts'])} conflict(s)")

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
        # --- PATCH: Print and save Rule Cluster Digest ---
        digest = format_cluster_digest_md(limit=5)
        print("\n📘 Rule Cluster Digest:\n")
        print(digest)
        try:
            with open("logs/learning_summary_with_digest.md", "w", encoding="utf-8") as f:
                f.write(digest)
        except Exception as e:
            logging.error(f"Failed to write rule cluster digest: {e}")

        # ✅ PATCH A Step 2: Print Variable Cluster Digest
        vcluster_digest = format_variable_cluster_digest_md(limit=5)
        print("\n📘 Variable Cluster Digest:\n")
        print(vcluster_digest)

        # ✅ PATCH A: Auto-export full mutation digest
        export_full_digest()

        # ✅ PATCH A Step 2: Export symbolic contradiction digest
        export_contradiction_digest_md()

# Note: No user input is processed, so no security issues present.

if __name__ == "__main__":
    # Run the learning engine and provide a placeholder for future tests
    engine = LearningEngine()
    engine.run_meta_update()
    # Placeholder: Add unit tests or integration tests here as needed.
