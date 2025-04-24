"""
signal_gating.py

Pulse Signal Gating Module — Symbolic Trust Filter

Filters signals coming from `scraper.py` based on symbolic mapping, anomaly status, and trust scoring (STI).
Implements symbolic flood control, STI thresholds, and escalation rules for PulseGrow intake.

Key Features:
- Symbolic domain-based gating table
- STI minimum acceptance threshold per domain
- Anomaly and volatility suppression
- Routing to PulseGrow for rare/escalated signals
- Logging and audit trace of all decisions

Author: Pulse v0.306
"""

import logging
from typing import List, Dict, Any, Tuple
import os
import yaml

try:
    from memory.pulsegrow import PulseGrow
    pulse_grow = PulseGrow()
except Exception:
    pulse_grow = None

logger = logging.getLogger(__name__)

# Load gating rules from YAML config
GATING_RULES_PATH = os.path.join(os.path.dirname(__file__), 'signal_gating_rules.yaml')
def load_gating_rules():
    try:
        with open(GATING_RULES_PATH, 'r', encoding='utf-8') as f:
            rules = yaml.safe_load(f)
            # Convert 'null' key to None for fallback
            if 'null' in rules:
                rules[None] = rules.pop('null')
            return rules
    except Exception as e:
        logging.error(f"Failed to load gating rules: {e}")
        # Fallback to hardcoded defaults if config fails
        return {
            "hope":     {"min_sti": 0.5, "max_anomalies": 2},
            "despair":  {"min_sti": 0.6, "max_anomalies": 1},
            "rage":     {"min_sti": 0.7, "max_anomalies": 1},
            "fatigue":  {"min_sti": 0.4, "max_anomalies": 3},
            None:        {"min_sti": 0.5, "max_anomalies": 2}
        }

GATING_RULES = load_gating_rules()

symbolic_anomaly_counter = {}

def gate_signals(signals: List[Dict[str, Any]]) -> Tuple[List[Dict], List[Dict], List[Dict]]:
    """
    Process and gate a batch of signals.
    Returns (accepted, suppressed, escalated)
    """
    accepted, suppressed, escalated = [], [], []

    for sig in signals:
        name = sig.get("name")
        symbolic = sig.get("symbolic")
        sti = sig.get("sti", 0.0)
        anomaly = sig.get("anomaly", False)

        rules = GATING_RULES.get(symbolic, GATING_RULES[None])

        # Flood control tracker
        if anomaly:
            symbolic_anomaly_counter[symbolic] = symbolic_anomaly_counter.get(symbolic, 0) + 1

        # Determine acceptance
        too_anomalous = symbolic_anomaly_counter.get(symbolic, 0) > rules["max_anomalies"]
        if sti >= rules["min_sti"] and not too_anomalous:
            accepted.append(sig)
            logger.info("[Gate] Accepted signal: %s (STI %.2f, symbolic %s)", name, sti, symbolic)
        elif sti >= 0.4:
            escalated.append(sig)
            logger.warning("[Gate] Escalated signal: %s (STI %.2f, symbolic %s)", name, sti, symbolic)
            if pulse_grow:
                try:
                    pulse_grow.register_variable(name, {
                        "symbolic": symbolic,
                        "reason": "Escalated from signal_gating",
                        "sti": sti
                    })
                except Exception as e:
                    logger.error("[Gate] PulseGrow escalation failed for %s: %s", name, e)
        else:
            suppressed.append(sig)
            logger.info("[Gate] Suppressed signal: %s (STI %.2f, symbolic %s)", name, sti, symbolic)

    return accepted, suppressed, escalated
