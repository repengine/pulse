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
from symbolic_system.symbolic_utils import compute_symbolic_drift_penalty
from core.pulse_config import CONFIDENCE_THRESHOLD, USE_SYMBOLIC_OVERLAYS
from trust_system.retrodiction_engine import run_retrodiction_simulation
from simulation_engine.worldstate import WorldState

logger = logging.getLogger("pulse.trust")

TRUST_ENRICHMENT_PLUGINS = []
# Plugins may now supply additional micro scoring metrics for trust evaluation.
def register_trust_enrichment_plugin(plugin_fn):
    """
    Register a plugin function for custom trust enrichment.
    Plugin signature: plugin_fn(forecast: Dict) -> None
    """
    TRUST_ENRICHMENT_PLUGINS.append(plugin_fn)

def run_trust_enrichment_plugins(forecast: Dict):
    """
    Run all registered trust enrichment plugins on the forecast.
    """
    for plugin in TRUST_ENRICHMENT_PLUGINS:
        try:
            plugin(forecast)
        except Exception as e:
            logger.warning(f"[TrustEnrich] Plugin {plugin.__name__} failed: {e}")

class TrustResult(NamedTuple):
    trace_id: str
    confidence: float
    trust_label: str
    arc_label: str
    symbolic_tag: str
    fragility: float

def symbolic_attention_score(forecast: Dict, arc_drift: Dict[str, int]) -> float:
    """
    Score how much attention a forecast deserves based on its arc's volatility.
    Forecasts contributing to unstable arcs receive higher attention scores.

    Args:
        forecast (Dict): A forecast with 'arc_label'
        arc_drift (Dict): Drift delta per arc label

    Returns:
        float: Attention score (0–1+); higher = more volatile/misaligned
    """
    arc = forecast.get("arc_label", "unknown")
    delta = abs(arc_drift.get(arc, 0))
    normalized = min(delta / 10.0, 1.0)  # cap at 1.0
    return round(normalized, 3)

def compute_symbolic_attention_score(forecast: Dict, arc_drift: Dict[str, int]) -> float:
    """
    Return attention score (0–1.0) based on how volatile the forecast's arc is.

    Args:
        forecast (Dict): Single forecast with arc_label
        arc_drift (Dict): Dict of arc label → Δ count

    Returns:
        float: score between 0 (stable) and 1 (volatile arc)
    """
    arc = forecast.get("arc_label", "unknown")
    delta = abs(arc_drift.get(arc, 0))
    return round(min(delta / 10.0, 1.0), 3)

def compute_risk_score(forecast: Dict, memory: Optional[List[Dict]] = None) -> float:
    """
    Compute a risk sub-score based on volatility measures,
    historical forecast consistency, and an ML adjustment placeholder.
    Returns a float between 0 and 1, where higher values indicate higher risk.
    """
    fcast = forecast.get("forecast", {})
    # Volatility measure: assess capital movement volatility
    capital_start = fcast.get("start_capital", {})
    capital_end = fcast.get("end_capital", {})
    risk_volatility = 0.0
    if capital_start and capital_end:
        delta_values = [
            abs(capital_end.get(asset, 0) - capital_start.get(asset, 0))
            for asset in ["nvda", "msft", "ibit", "spy"]
        ]
        risk_volatility = min(sum(delta_values) / 2000.0, 1.0)
    # Historical performance measure: compare recent symbolic_change differences
    historical_component = 0.0
    if memory and len(memory) > 0:
        similarities = []
        current_change = fcast.get("symbolic_change", {})
        for past in memory[-3:]:
            past_change = past.get("forecast", {}).get("symbolic_change", {})
            if current_change and past_change:
                common_keys = set(current_change.keys()).intersection(set(past_change.keys()))
                if common_keys:
                    diff = sum(abs(current_change.get(k, 0) - past_change.get(k, 0)) for k in common_keys)
                    similarity = 1.0 - min(diff / len(common_keys), 1.0)
                else:
                    similarity = 0.5
            else:
                similarity = 0.5
            similarities.append(similarity)
        avg_similarity = sum(similarities) / len(similarities)
        historical_component = 1.0 - avg_similarity  # lower similarity implies higher risk
    else:
        historical_component = 0.0

    # ML model component placeholder (constant adjustment)
    ml_adjustment = 0.1
    risk_score = (risk_volatility * 0.5 + historical_component * 0.4 + ml_adjustment * 0.1)
    return round(min(max(risk_score, 0.0), 1.0), 3)

def flag_drift_sensitive_forecasts(forecasts: List[Dict], drift_report: Dict, threshold: float = 0.2) -> List[Dict]:
    """
    Flags forecasts if they belong to unstable arcs or drift-prone rule sets.

    Args:
        forecasts (List[Dict])
        drift_report (Dict): Output from run_simulation_drift_analysis()
        threshold (float): Drift cutoff for flagging

    Returns:
        List[Dict]: forecasts updated with 'drift_flag'
    """
    volatile_rules = {r for r, delta in drift_report.get("rule_trigger_delta", {}).items() if abs(delta) > threshold * 10}
    unstable_overlays = {k for k, v in drift_report.get("overlay_drift", {}).items() if v > threshold}

    for fc in forecasts:
        arc = fc.get("arc_label", "unknown")
        rules = fc.get("fired_rules", [])
        overlays = fc.get("forecast", {}).get("symbolic_change", {})

        flagged = False
        if any(r in volatile_rules for r in rules):
            fc["drift_flag"] = "⚠️ Rule Instability"
            flagged = True
        if any(k in unstable_overlays for k in overlays):
            fc["drift_flag"] = "⚠️ Overlay Volatility"
            flagged = True
        if not flagged:
            fc["drift_flag"] = "✅ Stable"
    return forecasts

from trust_system.services.trust_enrichment_service import TrustEnrichmentService
from trust_system.services.trust_scoring_strategy import TrustScoringStrategy, DefaultTrustScoringStrategy

class TrustEngine:
    """
    Main interface for tagging, scoring, gating, and auditing forecasts.
    Produces trust metadata, applies thresholds, and audits symbolic coherence.
    Now delegates enrichment and scoring to dedicated services (SRP, Strategy Pattern).
    """
    def __init__(
        self,
        enrichment_service: Optional[TrustEnrichmentService] = None,
        scoring_strategy: Optional[TrustScoringStrategy] = None
    ):
        self.enrichment_service = enrichment_service or TrustEnrichmentService()
        self.scoring_strategy = scoring_strategy or DefaultTrustScoringStrategy()

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
    def confidence_gate(forecast: Dict, conf_threshold=0.5, fragility_threshold=0.7, risk_threshold=0.5) -> str:
        conf = forecast.get("confidence", 0.0)
        frag = forecast.get("fragility", 0.0)
        risk = forecast.get("risk_score", 0.0)
        if conf >= conf_threshold and frag <= fragility_threshold and risk <= risk_threshold:
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
        baseline_weight: float = 0.4,
        risk_weight: float = 0.3,
        historical_weight: float = 0.2,
        novelty_weight: float = 0.1
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
        # Baseline confidence: average of capital movement and inverse fragility
        baseline_confidence = ((1.0 - symbolic_penalty) + movement_score) / 2.0

        risk_score = compute_risk_score(forecast, memory)
        forecast["risk_score"] = risk_score

        if memory:
            similarities = []
            for past in memory[-3:]:
                curr_change = fcast.get("symbolic_change", {})
                past_change = past.get("forecast", {}).get("symbolic_change", {})
                if curr_change and past_change:
                    common = set(curr_change.keys()).intersection(set(past_change.keys()))
                    if common:
                        diff = sum(abs(curr_change[k] - past_change[k]) for k in common)
                        sim = 1.0 - min(diff / len(common), 1.0)
                    else:
                        sim = 0.5
                else:
                    sim = 0.5
                similarities.append(sim)
            historical_consistency = sum(similarities) / len(similarities)
        else:
            historical_consistency = 1.0
        forecast["historical_consistency"] = historical_consistency

        is_duplicate = False
        if memory:
            for past in memory[-3:]:
                prev = past.get("forecast", {}).get("symbolic_change", {})
                curr = fcast.get("symbolic_change", {})
                if curr == prev:
                    is_duplicate = True
                    break
        novelty_score = 0.0 if is_duplicate else 1.0

        final_confidence = (
            baseline_weight * baseline_confidence +
            risk_weight * (1 - risk_score) +
            historical_weight * historical_consistency +
            novelty_weight * novelty_score
        )
        if USE_SYMBOLIC_OVERLAYS:
            final_confidence -= compute_symbolic_drift_penalty(forecast)
        final_confidence = round(min(max(final_confidence, CONFIDENCE_THRESHOLD), 1.0), 3)
        logger.info(f"[TrustEngine] Scores for trace_id {forecast.get('trace_id', 'unknown')}: baseline={baseline_confidence}, risk={risk_score}, historical={historical_consistency}, novelty={novelty_score}, final_confidence={final_confidence}")
        return final_confidence

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
        # Build lineage and lookup maps
        lineage = {f["trace_id"]: f.get("parent_id") for f in forecasts if f.get("trace_id") and f.get("parent_id")}
        by_id = {f["trace_id"]: f for f in forecasts if "trace_id" in f}
        score_map = {
            "same": 0,
            "inverted": 0,
            "rebound": 0,
            "diverged": 0,
            "unknown": 0,
            "total": 0,
            "avg_drift": 0.0  # avg_drift is always a float
        }
        drifts = []
        for child_id, parent_id in lineage.items():
            child = by_id.get(child_id)
            parent = by_id.get(parent_id)
            if child and parent:
                rel, drift = TrustEngine._score_arc_integrity(child, parent)
                # Safeguard: increment only if rel is a known key
                if rel in score_map:
                    score_map[rel] += 1
                else:
                    score_map["unknown"] += 1
                drifts.append(drift)
                score_map["total"] += 1
        if drifts:
            score_map["avg_drift"] = float(round(sum(drifts) / len(drifts), 4))
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

    # ---- Trust Metadata Enrichment ----

    def enrich_trust_metadata(
        self,
        forecast: Dict,
        current_state: Optional[Dict] = None,
        memory: Optional[List[Dict]] = None,
        arc_drift: Optional[Dict[str, int]] = None,
        regret_log: Optional[List[Dict]] = None,
        license_enforcer=None,
        license_explainer=None
    ):
        """
        Delegates trust enrichment to the configured service.
        """
        forecast = self.tag_forecast(forecast)
        forecast["confidence"] = self.score_forecast(forecast, memory)
        self.enrichment_service.enrich(
            forecast,
            current_state=current_state,
            memory=memory,
            arc_drift=arc_drift,
            regret_log=regret_log,
            license_enforcer=license_enforcer,
            license_explainer=license_explainer
        )
        # Add summary/explanation for operator interpretability
        explanations = []
        if forecast.get("trust_label") != "🟢 Trusted":
            explanations.append(f"Trust label: {forecast.get('trust_label')}")
        if forecast.get("confidence", 1.0) < 0.6:
            explanations.append(f"Low confidence: {forecast.get('confidence')}")
        if forecast.get("alignment_score", 100) < 70:
            explanations.append(f"Low alignment: {forecast.get('alignment_score')}")
        if forecast.get("fragility", 0.0) > 0.6:
            explanations.append(f"High fragility: {forecast.get('fragility')}")
        if forecast.get("license_status") and forecast.get("license_status") != "✅ Approved":
            explanations.append(f"License: {forecast.get('license_status')}")
        forecast["trust_summary"] = (
            f"Trust: {forecast.get('trust_label', 'N/A')}, "
            f"Conf: {forecast.get('confidence', 'N/A')}, "
            f"Align: {forecast.get('alignment_score', 'N/A')}, "
            f"Fragility: {forecast.get('fragility', 'N/A')}, "
            f"License: {forecast.get('license_status', 'N/A')}"
            + (f"\nExplanation(s): {'; '.join(explanations)}" if explanations else "")
        )
        return forecast

    @staticmethod
    def enrich_trust_metadata_static(
        forecast: Dict,
        current_state: Optional[Dict] = None,
        memory: Optional[List[Dict]] = None,
        arc_drift: Optional[Dict[str, int]] = None,
        regret_log: Optional[List[Dict]] = None,
        license_enforcer=None,
        license_explainer=None
    ):
        """
        Backward-compatible static method for trust enrichment.
        Uses a default TrustEngine instance.
        """
        engine = TrustEngine()
        return engine.enrich_trust_metadata(
            forecast,
            current_state=current_state,
            memory=memory,
            arc_drift=arc_drift,
            regret_log=regret_log,
            license_enforcer=license_enforcer,
            license_explainer=license_explainer
        )

    # ---- Batch Application ----

    @staticmethod
    def apply_all(
        forecasts: List[Dict],
        memory: Optional[List[Dict]] = None,
        current_state: Optional[Dict] = None,
        retrodiction_threshold: float = 1.5,
        arc_drift: Optional[Dict[str, int]] = None,
        drift_report: Optional[Dict] = None
    ) -> List[Dict]:
        """
        Batch process forecasts: tags, scores, trust labels, and metadata.
        Optionally runs retrodiction analysis if current_state is provided.

        Args:
            forecasts: List of forecast dicts to process.
            memory: Optional list of past forecast dicts for novelty/duplication checks.
            current_state: Optional dict representing the current simulation state for retrodiction.
            retrodiction_threshold: Threshold for retrodiction filtering (default 1.5).
            arc_drift: Optional dict of arc drift deltas for attention scoring.
            drift_report: Optional simulation drift report for drift flagging.
        Returns:
            List of processed forecast dicts with trust metadata.
        """
        from trust_system.retrodiction_engine import run_retrodiction_simulation
        from simulation_engine.worldstate import WorldState

        # Optional: run retrodiction check before tagging
        if current_state:
            try:
                # Convert current_state dict to WorldState if needed
                if not isinstance(current_state, WorldState):
                    ws = WorldState()
                    for k, v in current_state.items():
                        setattr(ws, k, v)
                    current_state_obj = ws
                else:
                    current_state_obj = current_state

                # Run retrodiction simulation using unified function
                retrodiction_results = run_retrodiction_simulation(
                    initial_state=current_state_obj,
                    turns=1,  # or appropriate number of turns
                    retrodiction_loader=None  # Could be passed as parameter if available
                )
                # Map retrodiction scores back to forecasts by trace_id
                score_map = {r.get("trace_id"): r.get("confidence", 0.0) for r in retrodiction_results}
                for f in forecasts:
                    tid = f.get("trace_id")
                    if tid in score_map:
                        f["retrodiction_score"] = score_map[tid]
                    else:
                        f["retrodiction_score"] = None
            except Exception as e:
                logger.warning(f"Retrodiction batch analysis failed: {e}")

        # Flag drift-sensitive forecasts if drift_report is provided
        if drift_report:
            forecasts = flag_drift_sensitive_forecasts(forecasts, drift_report)

        for f in forecasts:
            try:
                TrustEngine.tag_forecast(f)
                score = TrustEngine.score_forecast(f, memory)
                # Drift gating: hard-cap drifted outputs
                if f.get("drift_flag") in {"⚠️ Rule Instability", "⚠️ Overlay Volatility"}:
                    label = "🔴 Drift-Prone"
                else:
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
                if arc_drift:
                    f["attention_score"] = symbolic_attention_score(f, arc_drift)
            except Exception as e:
                logger.warning(f"Trust pipeline error on forecast {f.get('trace_id', 'unknown')}: {e}")
        return forecasts

def _enrich_fragility(forecast):
    try:
        from trust_system.fragility_detector import compute_fragility
        overlays = forecast.get("overlays", {})
        symbolic_change = forecast.get("symbolic_change", {})
        forecast["fragility"] = compute_fragility(overlays, symbolic_change)
    except Exception as e:
        logger.warning(f"[TrustEnrich] Fragility enrichment failed: {e}")

def _enrich_retrodiction(forecast, current_state):
    """
    Enrich forecast with retrodiction error score using unified retrodiction simulation results.
    """
    if current_state:
        try:
            # Assuming retrodiction_score is already set in forecast by batch retrodiction
            if "retrodiction_score" not in forecast or forecast["retrodiction_score"] is None:
                forecast["retrodiction_error"] = None
            else:
                # Use retrodiction_score as retrodiction_error for now
                forecast["retrodiction_error"] = 1.0 - forecast["retrodiction_score"]
        except Exception as e:
            logger.warning(f"[TrustEnrich] Retrodiction enrichment failed: {e}")
            forecast["retrodiction_error"] = None

def _enrich_alignment(forecast, current_state, memory):
    try:
        from trust_system.alignment_index import compute_alignment_index
        alignment = compute_alignment_index(forecast, current_state=current_state, memory=memory)
        forecast["alignment_score"] = alignment.get("alignment_score", 0)
        forecast["alignment_components"] = alignment.get("components", {})
    except Exception as e:
        logger.warning(f"[TrustEnrich] Alignment enrichment failed: {e}")
        forecast["alignment_score"] = 0

def _enrich_attention(forecast, arc_drift):
    if arc_drift:
        forecast["attention_score"] = compute_symbolic_attention_score(forecast, arc_drift)

def _enrich_regret(forecast, regret_log):
    if regret_log:
        forecast["repeat_regret"] = forecast.get("trace_id") in {r.get("trace_id") for r in regret_log}

def _enrich_license(forecast, license_enforcer, license_explainer):
    if license_enforcer and license_explainer:
        forecast["license_status"] = license_enforcer(forecast)
        forecast["license_explanation"] = license_explainer(forecast)
