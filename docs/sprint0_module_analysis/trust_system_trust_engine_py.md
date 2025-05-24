# Analysis of trust_system/trust_engine.py

**Module Path:** [`trust_system/trust_engine.py`](trust_system/trust_engine.py:496)

**Original Line Number in Inventory:** 496

## 1. Module Intent/Purpose
The `trust_engine.py` module is a core component of the Pulse system, responsible for a wide array of trust-related operations on forecasts. Its primary roles include:
-   **Symbolic Tagging:** Assigning qualitative labels (`arc_label`, `symbolic_tag`) to forecasts based on their \"overlay\" data (e.g., \"Hope Surge\", \"Collapse Risk\").
-   **Confidence Scoring:** Calculating a numerical confidence score for forecasts. This logic is largely similar to `DefaultTrustScoringStrategy` but is also present directly within this module's `score_forecast` static method. The `TrustEngine` class itself now delegates scoring to a `TrustScoringStrategy`.
-   **Risk Assessment:** Computing a `risk_score` based on capital volatility, historical consistency, and a placeholder ML adjustment. This is encapsulated in the `compute_risk_score` function.
-   **Trust Gating:** Classifying forecasts into trust labels (\"🟢 Trusted\", \"🟡 Unstable\", \"🔴 Rejected\") based on confidence, fragility, and risk thresholds.
-   **Contradiction Detection:** Identifying conflicts between forecasts, such as opposing symbolic tags, conflicting arc labels, or divergent capital outcomes.
-   **Lineage Analysis:** Summarizing the relationships and drift between parent and child forecasts in a lineage.
-   **Metadata Enrichment:** Adding various trust-related metadata fields to forecasts (e.g., `trust_label`, `confidence`, `fragility`, `alignment_score`, `attention_score`, `retrodiction_error`, `license_status`). It uses a plugin system (`TRUST_ENRICHMENT_PLUGINS`) and dedicated enrichment functions for this.
-   **Batch Processing:** Applying these trust operations to lists of forecasts.
-   **Drift Management:** Flagging forecasts associated with unstable rules or overlays based on a drift report.
-   **Retrodiction Integration:** Optionally incorporating retrodiction scores into the trust assessment.

The `TrustEngine` class acts as the main interface, orchestrating these functionalities. It has been refactored to use a `TrustEnrichmentService` and a `TrustScoringStrategy`.

## 2. Operational Status/Completeness
-   The module appears largely operational and quite comprehensive in its scope.
-   Many functions seem complete and handle various edge cases (e.g., missing data, empty memory).
-   The plugin system for trust enrichment is defined.
-   The delegation to `TrustEnrichmentService` and `TrustScoringStrategy` in the `TrustEngine` class indicates a move towards better separation of concerns.
-   There are placeholders, such as the `ml_adjustment` in `compute_risk_score` ([`trust_system/trust_engine.py:171`](trust_system/trust_engine.py:171)), suggesting areas for future ML integration.
-   Extensive logging is present, which is good for operational monitoring.
-   The `score_forecast` static method within `TrustEngine` is very similar to the `DefaultTrustScoringStrategy.score` method. This suggests some redundancy or a transition phase.

## 3. Implementation Gaps / Unfinished Next Steps
-   **Signs of intended extension:**
    -   The `TRUST_ENRICHMENT_PLUGINS` system ([`trust_system/trust_engine.py:20`](trust_system/trust_engine.py:20)) is explicitly designed for adding custom enrichment logic.
    -   The use of `TrustScoringStrategy` implies other scoring strategies could be developed.
    -   The `ml_adjustment` ([`trust_system/trust_engine.py:171`](trust_system/trust_engine.py:171)) in `compute_risk_score` is a clear placeholder for a more sophisticated machine learning model.
    -   The `license_enforcer` and `license_explainer` parameters ([`trust_system/trust_engine.py:585-586`](trust_system/trust_engine.py:585-586)) suggest a planned or existing licensing/compliance check system.
-   **Implied but missing features/modules:**
    -   Actual plugin implementations for `TRUST_ENRICHMENT_PLUGINS` are not defined within this file.
    -   The `TrustEnrichmentService` itself is imported but its detailed implementation is in another file ([`trust_system/services/trust_enrichment_service.py`](trust_system/services/trust_enrichment_service.py)).
    -   More sophisticated methods for `symbolic_tag_conflicts` and `arc_conflicts` could be developed beyond simple keyword matching.
-   **Indications of deviated/stopped development:**
    -   The duplication of scoring logic between `TrustEngine.score_forecast` and `DefaultTrustScoringStrategy.score` might indicate a refactoring that is either ongoing or was partially completed. The `TrustEngine` class's `__init__` correctly uses the strategy pattern, but the static `score_forecast` method retains the older, direct implementation.
    -   Some default values in scoring/risk functions (e.g., `historical_component = 0.4` for empty symbolic change in `compute_risk_score` ([`trust_system/trust_engine.py:132`](trust_system/trust_engine.py:132))) seem somewhat arbitrary and might benefit from more empirical tuning or configuration.

## 4. Connections & Dependencies
-   **Direct imports from other project modules:**
    -   `symbolic_system.symbolic_utils.compute_symbolic_drift_penalty` ([`trust_system/trust_engine.py:13`](trust_system/trust_engine.py:13))
    -   `core.pulse_config.CONFIDENCE_THRESHOLD`, `core.pulse_config.USE_SYMBOLIC_OVERLAYS` ([`trust_system/trust_engine.py:14`](trust_system/trust_engine.py:14))
    -   `trust_system.retrodiction_engine.run_retrodiction_simulation` ([`trust_system/trust_engine.py:15`](trust_system/trust_engine.py:15), [`trust_system/trust_engine.py:677`](trust_system/trust_engine.py:677))
    -   `simulation_engine.worldstate.WorldState` ([`trust_system/trust_engine.py:16`](trust_system/trust_engine.py:16), [`trust_system/trust_engine.py:678`](trust_system/trust_engine.py:678))
    -   `trust_system.services.trust_enrichment_service.TrustEnrichmentService` ([`trust_system/trust_engine.py:214`](trust_system/trust_engine.py:214))
    -   `trust_system.services.trust_scoring_strategy.TrustScoringStrategy`, `DefaultTrustScoringStrategy` ([`trust_system/trust_engine.py:215`](trust_system/trust_engine.py:215))
    -   Local (within-function) imports for enrichment:
        -   `trust_system.fragility_detector.compute_fragility` ([`trust_system/trust_engine.py:771`](trust_system/trust_engine.py:771)) (used in `_enrich_fragility`)
        -   `trust_system.alignment_index.compute_alignment_index` ([`trust_system/trust_engine.py:796`](trust_system/trust_engine.py:796)) (used in `_enrich_alignment`)
-   **External library dependencies:**
    -   `logging` ([`trust_system/trust_engine.py:9`](trust_system/trust_engine.py:9))
    -   `math` ([`trust_system/trust_engine.py:10`](trust_system/trust_engine.py:10)) (not explicitly used, but `sum()`, `abs()`, `min()`, `max()`, `round()` are built-in; `math.sqrt` could be implied by `**0.5`)
    -   `typing.Dict`, `List`, `Tuple`, `NamedTuple`, `Optional` ([`trust_system/trust_engine.py:11`](trust_system/trust_engine.py:11))
    -   `collections.defaultdict` ([`trust_system/trust_engine.py:12`](trust_system/trust_engine.py:12))
-   **Interaction with other modules:**
    -   Deeply interconnected with various parts of the `trust_system`, `symbolic_system`, `simulation_engine`, and `core`.
    -   Consumes forecast data structures, memory of past forecasts, current world state, drift reports, and regret logs.
    -   Produces enriched forecasts with extensive trust metadata.
-   **Input/output files:**
    -   Does not directly read from or write to files. Operates on in-memory Python objects and relies on logging for output.

## 5. Function and Class Example Usages
-   **`TrustEngine` class:**
    ```python
    # from trust_system.trust_engine import TrustEngine, TrustResult
    # from trust_system.services.trust_enrichment_service import TrustEnrichmentService # Assuming this exists
    # from trust_system.services.trust_scoring_strategy import DefaultTrustScoringStrategy # Assuming this exists

    # engine = TrustEngine(enrichment_service=TrustEnrichmentService(), scoring_strategy=DefaultTrustScoringStrategy())
    # sample_forecast = {
    #     "trace_id": "forecast_123",
    #     "forecast": {
    #         "start_capital": {"nvda": 100, "spy": 200},
    #         "end_capital": {"nvda": 110, "spy": 190},
    #         "symbolic_change": {"trend": 0.5}
    #     },
    #     "overlays": {"hope": 0.8},
    #     "fragility": 0.1
    # }
    # sample_memory = [{"trace_id": "old_forecast", "forecast": {"symbolic_change": {"trend": 0.4}}, "overlays": {}}]
    #
    # enriched_forecast = engine.enrich_trust_metadata(sample_forecast, memory=sample_memory)
    # print(enriched_forecast.get("trust_label"))
    # print(enriched_forecast.get("confidence"))
    # print(enriched_forecast.get("trust_summary"))

    # batch_forecasts = [sample_forecast, {"trace_id": "forecast_456", ...}]
    # processed_batch = TrustEngine.apply_all(batch_forecasts, memory=sample_memory)
    # for pf in processed_batch:
    #     print(pf.get("pulse_trust_meta"))
    ```
-   **`compute_risk_score(forecast, memory)`:**
    ```python
    # risk = compute_risk_score(sample_forecast, sample_memory)
    # print(f"Risk Score: {risk}")
    ```
-   **`flag_drift_sensitive_forecasts(forecasts, drift_report)`:**
    ```python
    # drift_report_example = {"rule_trigger_delta": {"ruleA": 0.3}, "overlay_drift": {"overlayX": 0.25}}
    # flagged_forecasts = flag_drift_sensitive_forecasts([sample_forecast], drift_report_example)
    # print(flagged_forecasts[0].get("drift_flag"))
    ```
-   The various `_enrich_*` functions are intended to be used by `TrustEnrichmentService` or similar mechanisms, not typically called directly.

## 6. Hardcoding Issues
-   **Asset List:** `["nvda", "msft", "ibit", "spy"]` is hardcoded in `compute_risk_score` ([`trust_system/trust_engine.py:106`](trust_system/trust_engine.py:106)) and `TrustEngine.score_forecast` ([`trust_system/trust_engine.py:321`](trust_system/trust_engine.py:321)).
-   **Normalization Divisors:** `2000.0` in `compute_risk_score` ([`trust_system/trust_engine.py:118`](trust_system/trust_engine.py:118)) and `1000.0` in `TrustEngine.score_forecast` ([`trust_system/trust_engine.py:333`](trust_system/trust_engine.py:333)) for capital movement.
-   **Symbolic Tagging Thresholds:** Thresholds like `0.7` for \"Hope\" in `tag_forecast` ([`trust_system/trust_engine.py:239`](trust_system/trust_engine.py:239)) are hardcoded.
-   **Confidence Gate Thresholds:** Default thresholds in `confidence_gate` (`conf_threshold=0.5`, `fragility_threshold=0.7`, `risk_threshold=0.5`) ([`trust_system/trust_engine.py:259`](trust_system/trust_engine.py:259)).
-   **Scoring Weights & Defaults:** Weights and default/fallback values in `score_forecast` and `compute_risk_score` (e.g., `ml_adjustment = 0.1` ([`trust_system/trust_engine.py:171`](trust_system/trust_engine.py:171)), various similarity defaults, fragility adjustments for empty data).
-   **Memory Lookback:** `memory[-3:]` is used in `compute_risk_score` ([`trust_system/trust_engine.py:137`](trust_system/trust_engine.py:137)) and `score_forecast` ([`trust_system/trust_engine.py:370`](trust_system/trust_engine.py:370), [`trust_system/trust_engine.py:406`](trust_system/trust_engine.py:406)).
-   **Attention Score Divisor:** `delta / 10.0` in `symbolic_attention_score` ([`trust_system/trust_engine.py:61`](trust_system/trust_engine.py:61)) and `compute_symbolic_attention_score` ([`trust_system/trust_engine.py:84`](trust_system/trust_engine.py:84)).
-   **Drift Flagging Thresholds:** `threshold * 10` for rules in `flag_drift_sensitive_forecasts` ([`trust_system/trust_engine.py:195`](trust_system/trust_engine.py:195)).
-   **Capital Conflict Threshold:** `threshold: float = 1000.0` in `capital_conflicts` ([`trust_system/trust_engine.py:491`](trust_system/trust_engine.py:491)).

## 7. Coupling Points
-   **Data Structure Dependency:** Highly dependent on the specific structure and keys within `forecast` dictionaries and `memory` lists. Changes to these structures would require updates here.
-   **Configuration Dependency:** Relies on `CONFIDENCE_THRESHOLD` and `USE_SYMBOLIC_OVERLAYS` from `core.pulse_config`.
-   **Service/Strategy Dependency:** The `TrustEngine` class is coupled to the interfaces of `TrustEnrichmentService` and `TrustScoringStrategy`.
-   **Module Dependencies:** Tightly coupled to `symbolic_utils`, `retrodiction_engine`, `worldstate`, `fragility_detector`, and `alignment_index` through direct imports and usage.
-   **Side Effects:** Many functions (e.g., `tag_forecast`, `score_forecast`, `apply_all`, `enrich_trust_metadata`) modify the input `forecast` dictionaries in place by adding new keys.

## 8. Existing Tests
-   A search for `tests/test_trust_engine.py` yielded no results. Given the complexity and criticality of this module, comprehensive unit and integration tests are essential. The numerous static methods could be tested individually.

## 9. Module Architecture and Flow
-   **Plugin System:** `register_trust_enrichment_plugin` and `run_trust_enrichment_plugins` allow for extensible forecast enrichment.
-   **`TrustEngine` Class:**
    -   `__init__`: Initializes with optional `TrustEnrichmentService` and `TrustScoringStrategy`, defaulting to `DefaultTrustScoringStrategy`.
    -   `tag_forecast` (static): Adds `arc_label` and `symbolic_tag` based on `overlays`.
    -   `confidence_gate` (static): Determines a trust label based on confidence, fragility, and risk.
    -   `score_forecast` (static): Calculates confidence score (similar to `DefaultTrustScoringStrategy`). **This is a point of potential redundancy/refactoring.**
    -   `enrich_trust_metadata`: Orchestrates tagging, scoring (via strategy), and enrichment (via service) for a single forecast.
    -   `enrich_trust_metadata_static` (static): Backward-compatible wrapper.
    -   `apply_all` (static): Batch processes forecasts, including optional retrodiction and drift flagging, then applies tagging, scoring, and gating.
    -   Various static methods for conflict detection (`symbolic_tag_conflicts`, `arc_conflicts`, `capital_conflicts`), lineage scoring (`lineage_arc_summary`), and auditing (`run_trust_audit`, `check_forecast_coherence`).
-   **Helper Functions (module-level):**
    -   `symbolic_attention_score` / `compute_symbolic_attention_score`: Calculates score based on arc volatility.
    -   `compute_risk_score`: Calculates risk based on volatility, history, and ML placeholder.
    -   `flag_drift_sensitive_forecasts`: Flags forecasts based on drift report.
-   **Private Enrichment Functions (`_enrich_*`):** These are likely intended to be registered as plugins or used by `TrustEnrichmentService`. They handle fragility, retrodiction error, alignment, attention, regret, and licensing.

**Key Architectural Points:**
-   The module acts as a facade and orchestrator for many trust-related sub-processes.
-   Recent refactoring introduced the `TrustEnrichmentService` and `TrustScoringStrategy` to the `TrustEngine` class, promoting better design patterns (SRP, Strategy). However, some older static methods with similar functionality persist (e.g., `TrustEngine.score_forecast`).
-   Extensive use of static methods for utility functions and batch processing.
-   Input forecasts are often modified in-place.

## 10. Naming Conventions
-   **Classes:** `TrustResult`, `TrustEngine` (PascalCase) - Standard.
-   **Functions/Methods:** Mostly snake_case (e.g., `compute_risk_score`, `tag_forecast`, `apply_all`). `_enrich_*` for private/internal enrichment helpers.
-   **Constants:** `TRUST_ENRICHMENT_PLUGINS`, `CONFIDENCE_THRESHOLD` (UPPER_SNAKE_CASE) - Standard.
-   **Variables:** Generally snake_case. `fcast` is a common abbreviation.
-   Naming is largely clear and follows Python conventions. The module's scope is very broad, reflected in the diverse function names.