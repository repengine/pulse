# trust_engine.py
"""
Central trust engine for Pulse.
Combines trust scoring, symbolic tagging, contradiction detection,
regret-driven memory evolution, lineage integrity evaluation,
and metadata enrichment for downstream decision systems.
"""

import logging
import math
from typing import Dict, List, Tuple, NamedTuple, Optional
from collections import defaultdict
from symbolic_system.symbolic_utils import symbolic_fragility_index
from core.pulse_config import CONFIDENCE_THRESHOLD
from trust_system.forecast_retrospector import retrospective_analysis_batch


logger = logging.getLogger("pulse.trust")

class TrustResult(NamedTuple):
    trace_id: str
    confidence: float
    trust_label: str
    arc_label: str
    symbolic_tag: str
    fragility: float

class TrustEngine:
    """
    Main interface for tagging, scoring, gating, and auditing forecasts.
    Produces trust metadata, applies thresholds, and audits symbolic coherence.
    """

    # ---- Symbolic Tagging ----

    @staticmethod
    def tag_forecast(forecast: Dict) -> Dict:
        overlays = forecast.get("overlays", {})
        trace_id = forecast.get("trace_id", "unknown")
        arc_label = "Unknown"
        tag = ""
        if overlays.get("hope", 0) > 0.7:
            arc_label = "Hope Surge"
            tag = "Hope"
        elif overlays.get("despair", 0) > 0.6:
            arc_label = "Collapse Risk"
            tag = "Despair"
        elif overlays.get("rage", 0) > 0.6:
            arc_label = "Rage Arc"
            tag = "Rage"
        elif overlays.get("fatigue", 0) > 0.5:
            arc_label = "Fatigue Loop"
            tag = "Fatigue"
        forecast["arc_label"] = arc_label
        forecast["symbolic_tag"] = tag
        forecast["trace_id"] = trace_id
        return forecast

    # ---- Confidence Classification ----

    @staticmethod
    def confidence_gate(forecast: Dict, conf_threshold=0.5, fragility_threshold=0.7) -> str:
        conf = forecast.get("confidence", 0.0)
        frag = forecast.get("fragility", 0.0)
        if conf >= conf_threshold and frag <= fragility_threshold:
            return "🟢 Trusted"
        elif conf >= conf_threshold:
            return "🟡 Unstable"
        else:
            return "🔴 Rejected"

    # ---- Trust Confidence Scoring ----

    @staticmethod
    def score_forecast(
        forecast: Dict,
        memory: Optional[List[Dict]] = None,
        fragility_weight: float = 0.4,
        delta_weight: float = 0.4,
        novelty_weight: float = 0.2
    ) -> float:
        fcast = forecast.get("forecast", {})
        fragility = forecast.get("fragility", 1.0)
        symbolic_penalty = min(fragility, 1.0)

        capital_start = fcast.get("start_capital", {})
        capital_end = fcast.get("end_capital", {})
        movement_score = 0.0
        if capital_start and capital_end:
            delta_sum = sum(
                abs(capital_end.get(asset, 0) - capital_start.get(asset, 0))
                for asset in ["nvda", "msft", "ibit", "spy"]
            )
            movement_score = min(delta_sum / 1000.0, 1.0) if delta_sum else 0.0

        is_duplicate = False
        if memory:
            for past in memory[-3:]:
                prev = past.get("forecast", {}).get("symbolic_change", {})
                curr = fcast.get("symbolic_change", {})
                if curr == prev:
                    is_duplicate = True
                    break
        novelty_score = 0.0 if is_duplicate else 1.0

        confidence = (
            (1.0 - symbolic_penalty) * fragility_weight +
            movement_score * delta_weight +
            novelty_score * novelty_weight
        )
        return round(min(max(confidence, CONFIDENCE_THRESHOLD), 1.0), 3)

    # ---- Symbolic Conflict / Mirror ----

    @staticmethod
    def check_trust_loop_integrity(forecasts: List[Dict]) -> List[str]:
        issues = []
        for f in forecasts:
            conf = f.get("confidence", 0)
            frag = f.get("fragility", f.get("fragility_score", 0))
            retro = f.get("retrodiction_score", 1.0)
            label = f.get("trust_label", "")
            tid = f.get("trace_id", "unknown")
            if label == "🟢 Trusted" and retro < 0.5:
                issues.append(f"Trusted forecast {tid} has low retrodiction ({retro})")
            if label == "🟢 Trusted" and frag > 0.7:
                issues.append(f"Trusted forecast {tid} is fragile ({frag})")
            if label == "🔴 Fragile" and conf > 0.7:
                issues.append(f"Fragile forecast {tid} has high confidence ({conf})")
        return issues

    @staticmethod
    def check_forecast_coherence(forecast_batch: List[Dict]) -> Tuple[str, List[str]]:
        symbolic_conflicts = TrustEngine.symbolic_tag_conflicts(forecast_batch) + TrustEngine.arc_conflicts(forecast_batch)
        capital_conflicts = TrustEngine.capital_conflicts(forecast_batch)
        issues = [
            f"Symbolic: {x[0]} ⟷ {x[1]} – {x[2]}" for x in symbolic_conflicts
        ] + [
            f"Capital: {x[0]} ⟷ {x[1]} – {x[2]}" for x in capital_conflicts
        ]
        trust_flags = TrustEngine.check_trust_loop_integrity(forecast_batch)
        issues.extend([f"Trust mismatch: {t}" for t in trust_flags])
        return ("fail" if issues else "pass"), issues

    # ---- Symbolic Contradictions ----

    @staticmethod
    def symbolic_tag_conflicts(forecasts: List[Dict]) -> List[Tuple[str, str, str]]:
        conflicts = []
        for i in range(len(forecasts)):
            for j in range(i+1, len(forecasts)):
                tag1 = forecasts[i].get("symbolic_tag", "")
                tag2 = forecasts[j].get("symbolic_tag", "")
                id1 = forecasts[i].get("trace_id", f"fc{i}")
                id2 = forecasts[j].get("trace_id", f"fc{j}")
                if ("Hope" in tag1 and "Despair" in tag2) or ("Despair" in tag1 and "Hope" in tag2):
                    conflicts.append((id1, id2, "Symbolic tag: Hope vs Despair"))
                elif ("Rage" in tag1 and "Fatigue" in tag2) or ("Fatigue" in tag1 and "Rage" in tag2):
                    conflicts.append((id1, id2, "Symbolic tag: Rage vs Fatigue"))
        return conflicts

    @staticmethod
    def arc_conflicts(forecasts: List[Dict]) -> List[Tuple[str, str, str]]:
        conflicts = []
        arc_map = defaultdict(list)
        for f in forecasts:
            arc = f.get("arc_label", "")
            arc_map[arc].append(f)
        for arc1 in arc_map:
            for arc2 in arc_map:
                if arc1 != arc2 and any(x in arc1.lower() for x in ["hope", "recovery"]) and any(x in arc2.lower() for x in ["despair", "collapse"]):
                    for f1 in arc_map[arc1]:
                        for f2 in arc_map[arc2]:
                            conflicts.append((f1["trace_id"], f2["trace_id"], f"Symbolic arc conflict: {arc1} vs {arc2}"))
        return conflicts

    @staticmethod
    def capital_conflicts(forecasts: List[Dict], threshold: float = 1000.0) -> List[Tuple[str, str, str]]:
        conflicts = []
        for i in range(len(forecasts)):
            for j in range(i+1, len(forecasts)):
                id1 = forecasts[i].get("trace_id", f"fc{i}")
                id2 = forecasts[j].get("trace_id", f"fc{j}")
                end1 = forecasts[i].get("forecast", {}).get("end_capital", {})
                end2 = forecasts[j].get("forecast", {}).get("end_capital", {})
                for asset in end1:
                    if asset in end2:
                        delta = end1[asset] - end2[asset]
                        if abs(delta) > threshold and (end1[asset] * end2[asset]) < 0:
                            conflicts.append((id1, id2, f"Capital outcome conflict on {asset}"))
        return conflicts

    # ---- Lineage Arc Scoring ----

    @staticmethod
    def lineage_arc_summary(forecasts: List[Dict]) -> Dict:
        lineage = {f["trace_id"]: f.get("parent_id") for f in forecasts if f.get("trace_id") and f.get("parent_id")}
        by_id = {f["trace_id"]: f for f in forecasts if "trace_id" in f}
        score_map = {k: 0 for k in ["same", "inverted", "rebound", "diverged", "unknown"]}
        score_map["total"] = 0
        score_map["avg_drift"] = 0.0
        drifts = []
        for child_id, parent_id in lineage.items():
            child = by_id.get(child_id)
            parent = by_id.get(parent_id)
            if child and parent:
                rel, drift = TrustEngine._score_arc_integrity(child, parent)
                score_map[rel] += 1
                drifts.append(drift)
                score_map["total"] += 1
        if drifts:
            score_map["avg_drift"] = round(sum(drifts) / len(drifts), 4)
        return score_map

    @staticmethod
    def _score_arc_integrity(child: Dict, parent: Dict) -> Tuple[str, float]:
        arc1 = parent.get("arc_label", "Unknown")
        arc2 = child.get("arc_label", "Unknown")
        relation = "unknown"
        if arc1 == arc2:
            relation = "same"
        elif "Hope" in arc1 and "Despair" in arc2:
            relation = "inverted"
        elif "Despair" in arc1 and "Hope" in arc2:
            relation = "rebound"
        elif arc1 != arc2:
            relation = "diverged"
        o1 = parent.get("overlays", {})
        o2 = child.get("overlays", {})
        keys = set(o1.keys()).intersection(o2.keys())
        diffs = [(o1[k] - o2[k]) ** 2 for k in keys]
        return relation, round(sum(diffs) ** 0.5, 4)

    # ---- Trust Audit ----

    @staticmethod
    def run_trust_audit(forecasts: List[Dict]) -> Dict:
        _, mirror_issues = TrustEngine.check_forecast_coherence(forecasts)
        contradictions = {
            "symbolic_tag_conflicts": TrustEngine.symbolic_tag_conflicts(forecasts),
            "symbolic_arc_conflicts": TrustEngine.arc_conflicts(forecasts),
            "capital_conflicts": TrustEngine.capital_conflicts(forecasts),
            "total_forecasts": len(forecasts)
        }
        lineage = TrustEngine.lineage_arc_summary(forecasts)
        return {
            "mirror": mirror_issues,
            "contradictions": contradictions,
            "lineage_summary": lineage
        }

    # ---- Batch Application ----

    @staticmethod
    def apply_all(
        forecasts: List[Dict],
        memory: Optional[List[Dict]] = None,
        current_state: Optional[Dict] = None,
        retrodiction_threshold: float = 1.5
    ) -> List[Dict]:
        """
        Batch process forecasts: tags, scores, trust labels, and metadata.
        Optionally runs retrodiction analysis if current_state is provided.

        Args:
            forecasts: List of forecast dicts to process.
            memory: Optional list of past forecast dicts for novelty/duplication checks.
            current_state: Optional dict representing the current simulation state for retrodiction.
            retrodiction_threshold: Threshold for retrodiction filtering (default 1.5).
        Returns:
            List of processed forecast dicts with trust metadata.
        """
        # Optional: run retrodiction check before tagging
        if current_state:
            try:
                forecasts = retrospective_analysis_batch(forecasts, current_state, threshold=retrodiction_threshold)
            except Exception as e:
                logger.warning(f"Retrodiction batch analysis failed: {e}")

        for f in forecasts:
            try:
                TrustEngine.tag_forecast(f)
                score = TrustEngine.score_forecast(f, memory)
                label = TrustEngine.confidence_gate(f)
                f["confidence"] = score
                f["trust_label"] = label
                f["pulse_trust_meta"] = TrustResult(
                    trace_id=f.get("trace_id", "unknown"),
                    confidence=score,
                    trust_label=label,
                    arc_label=f.get("arc_label", ""),
                    symbolic_tag=f.get("symbolic_tag", ""),
                    fragility=f.get("fragility", 0.0),
                )._asdict()
            except Exception as e:
                logger.warning(f"Trust pipeline error on forecast {f.get('trace_id', 'unknown')}: {e}")
        return forecasts


# Add this at the end of the file to allow direct import
score_forecast = TrustEngine.score_forecast
