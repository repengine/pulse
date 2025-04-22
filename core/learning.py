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
from typing import Any, Dict
from datetime import datetime

from memory.trace_memory import TraceMemory
from memory.variable_performance_tracker import VariablePerformanceTracker
from core.variable_registry import VariableRegistry
from dev_tools.generate_symbolic_upgrade_plan import generate_symbolic_upgrade_plan
from dev_tools.apply_symbolic_upgrades import apply_symbolic_upgrades
from dev_tools.apply_symbolic_revisions import apply_symbolic_revisions
from dev_tools.pulse_batch_alignment_analyzer import analyze_arc_alignment
from trust_system.pulse_regret_chain import score_symbolic_regret

from core.pulse_learning_log import (
    log_variable_weight_change,
    log_symbolic_upgrade,
    log_revision_trigger,
    log_arc_regret,
    log_learning_summary
)

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
        Generates and applies candidate overlay tweaks.
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

# Note: No user input is processed, so no security issues present.

if __name__ == "__main__":
    # Run the learning engine and provide a placeholder for future tests
    engine = LearningEngine()
    engine.run_meta_update()
    # Placeholder: Add unit tests or integration tests here as needed.
