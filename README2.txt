# 🧬 Pulse Roadmap: Micro-Granular Build Plan

---




---

## PHASE I: FOUNDATIONS (Weeks 1–2)

**Goal:** Fully modular, togglable pipeline with real/mocked data, "data-only" rules, and overlays as add-ons

### 1. Data Layer (pulse/data.py)
- **Task 1.1:** Design a `DataConnector` base class supporting batch and streaming modes.
    - Subclass for at least two domains: `MarketDataConnector`, `NewsDataConnector` (can be mocked first).
    - Design ingestion signatures: `fetch_latest()`, `inject_external(data_batch)`, `reset()`.
    - Acceptance: Unit test shows state injection from CSV, REST API, or random generator.
- **Task 1.2:** Implement data preprocessing for signal normalization, mapping to simulation's internal schema.
    - Map market “price” or “volatility” fields; news feeds to sentiment signals.
- **Task 1.3:** Enable “mock mode”, `real_mode` flags in config; swaps between true/synthetic data sources.

### 2. State Representation (pulse/state.py)
- **Task 2.1:** Define the canonical `State` class containing:
    - Environment signals (all relevant real/mocked fields)
    - List of agent references
    - Timestamp/step id
- **Task 2.2:** Method to “advance” (generate next state) with/without overlays.

### 3. Agent System (pulse/agent.py)
- **Task 3.1:** Define `Agent` base class:
    - Properties: unique_id, capital, strategy_type, trust_score, overlay_buckets (dict for emotional/symbolic overlays)
- **Task 3.2:** API for agents to receive state updates and return “actions” (e.g., buy/sell/hold, broadcast sentiment).
- **Task 3.3:** Interface for overlays to modify agent state (inject/withdraw overlay, multiplicative/threshold effects).

### 4. Rules Engine (pulse/rule.py)
- **Task 4.1:** Implement base `Rule` class with `apply(state, agent=None, overlays=None)` method.
    - **Hard-data Rules:** Add rules mapping price/signal/agent state+action → new state.
    - Include togglable overlay hooks (`include_overlays=True/False`).
    - Acceptance: Unit test shows core sim logic operates with overlays off.

### 5. Simulation Core (pulse/simulate.py)
- **Task 5.1:** Orchestrate simulation steps:
    - Initialize: Ingest data, create agents, create initial state.
    - Main loop (`run(n_steps, overlay_mode)`):
        1. For each agent: process overlays [if enabled], generate action(s)
        2. Apply rules: calculate new state from actions, rules, overlays/none
        3. Score and log outcomes
    - Acceptance: Can run with overlays OFF (baseline) and ON (optional).

### 6. Overlays & Toggling (pulse/overlay.py, simulate.py)
- **Task 6.1:** Create abstract `Overlay` class. Examples: `EmotionOverlay`, `TrustOverlay`, `ReputationOverlay`.
    - Implements `modify(agent, state)` and/or `activate`, `deactivate`
- **Task 6.2:** API to pass overlay objects (list) to simulation at runtime; overlays attached/detached from agents as needed.
- **Task 6.3:** "Ablation": Command-line/config switch to enable/disable all overlays for any simulation run.

### 7. Score & Memory Initialization (pulse/score.py, memories.py)
- **Task 7.1:** Implement basic scoring function: confidence, reward, risk (based on capital, branch outcomes, agent trust).
- **Task 7.2:** Log every state, agent action, score step to persistent memory (pickle/JSON/db for later validation).
- **Task 7.3:** `MemoryTrace` objects track each timeline/sim path.
- **Task 7.4:** Acceptance: Print and validate memory of a full sim run with all agent actions and overlays annotated.

---

## PHASE II: MODULAR EXPERIMENTS & BASELINE COMPARISON (Weeks 3–5)

**Goal:** Empirically compare the effect of symbolic overlays (vs. “data only”). Score and log memory. Fork agent/capital scenarios.

### 1. A/B Testing Infrastructure (test/ & simulate.py)
- **Task 8.1:** Frontend CLI/param toggles:  
    - batch mode running N sims "overlay ON" vs "OVERLAY OFF".
    - Reports aggregate deltas in key metrics (accuracy, fragility, capital, trust).
- **Task 8.2:** Result logging utility: Separate output/CSV for each run grouped by overlay config.

### 2. Overlay Impact Logging (overlay.py, score.py)
- **Task 9.1:** For every overlay-induced action/state change, log `OverlayImpact` record to memory.
- **Task 9.2:** Post-sim, automatically extract summaries:
    - How many decisions per timeline were overlay modified?
    - Was prediction error/fragility higher or lower?
    - Simple correlation coefficient overlay → score/fragility/trust.

### 3. Strategic Fragility & Capital Forks (agent.py, state.py, simulate.py)
- **Task 10.1:** Expand Agent and State to support:
    - Capital “exposure” (per agent, per timeline fork)
    - Branch/fork model: at key events (market crash, news shock), duplicate timeline (sim “fork”), track diverging paths in parallel
- **Task 10.2:** For each agent per state:
    - Calculate/record fragility index (delta trust/capital on shock)
    - Expose this in scoring/memory.

### 4. Trust-Weighted Forecasting (forecast.py, agent.py, score.py)
- **Task 11.1:** Forecast generator outputs:
    - Both forecasted states *and* confidence/trust intervals per agent and collective.
- **Task 11.2:** Predict with/without overlays and log impact on confidence distributions.

### 5. Persistent, Empirical Memory/Log Upgrade (memories.py)
- **Task 12.1:** Memory log supports:
    - Multiple “timelines”/forks
    - All scores, overlay impacts, trust/confidence metrics
    - Export tools for data analysis.

---

## PHASE III: RECURSIVE/EVOLUTIONARY RETRODICTION & LEARNING (Weeks 6–8+)

**Goal:** Persistence, recursive improvement, adaptive rule/overlay learning, and optimal scenario generation.

### 1. Recursive Simulation (forecast.py, simulate.py, memories.py)
- **Task 13.1:** Run multiple, branching sims recursively:
    - Each outcome stored as “scenario”; best (or most resilient/diverse) scenarios selected for further mutation/evolution.
- **Task 13.2:** Maintain lineage (“which memories/agents/rules/overlays spawned each successful scenario”).
- **Task 13.3:** Implement bootstrapped retrodiction: can your system recover past scenarios, then forecast forward accurately?

### 2. Rule/Overlay Adaptation (rule.py, overlay.py)
- **Task 14.1:** Add hooks for rules/overlays to:
    - Update parameters using memory/score feedback (grid search, RL-lite, or simple heuristics).
    - E.g., overlay strength, rule threshold, agent trust decay/increase.
- **Task 14.2:** Track and log which *meta-parameters* are most adaptive/resilient over time and scenario forks.

### 3. Automated Pruning & Optimal Path Selection (score.py, memories.py)
- **Task 15.1:** Pruning logic in memory: scenarios below a pre-set score/confidence threshold are culled each round.
- **Task 15.2:** Store “optimal” scenarios and surface them for user inspection.

### 4. Explainability & Trace Visualization (utils.py, external tools)
- **Task 16.1:** Develop simple dashboard or Jupyter notebook tool to:
    - Visualize timeline forks, overlay impacts, agent trust/capital evolution
    - Enable user-driven exploration of alternate scenarios

---

## PHASE IV: REAL-TIME PIPELINES & EXTERNALIZATION (Months 3+)

- Continuous, streaming data connectors
- User/event-driven “interactive” scenario launches
- Collaboration hooks (API endpoints for external tools, possible integration)
- Advanced learning: online adaptation, multi-agent evolutionary runs, adversarial overlay testing

---

## Micro-Task Sample: Week 1 Checklist

| Day | Task                                                                    | Acceptance                                           |
|-----|-------------------------------------------------------------------------|------------------------------------------------------|
| 1   | Implement DataConnector, Market/News mock, basic fetch                   | fetch_latest returns mock data, injected to State    |
| 2   | Build State class, integrates all data channels, references all agents   | State constructed in simulate, validated in test     |
| 2-3 | Create basic Agent class, agent creation, minimal properties             | Agents instantiate, listed in State                  |
| 3   | Implement Rule base: hard-coded rule can transform state from data/agent | Rule.apply moves state, nod overlay impact support   |
| 4   | Connect simple simulate loop “wiring”: Run 10 steps “data only”          | Print timeline, capital evolution, scoring baseline  |
| 5   | Overlay base class, logic for attaching/detaching overlays per agent     | Overlays can be toggled/assigned, no other impact    |
| 6   | Toggle overlays in simulate/main, baseline/overlay-off experiment        | Two runs print different traces, all logs persist    |
| 7   | MemoryTrace logs all runs, actions, scores, overlays                     | Export run logs and validate completeness            |
| 7   | Draft test suite for all above                                           | All new modules >80% coverage, pass basic tests      |

---

## Acceptance Criteria Reference

**Across all phases:**
- Every simulation run, state, agent action, overlay interaction, and scoring output is logged/persisted stepwise.
- CLI/script toggles overlays, agent abstractions, rule sets, data modes.
- Diffs between “data only” and “with overlays” are empirically, not anecdotally, surfaced—available for review.
- Each module is unit-tested, and system “integration” runs can be validated reproducibly.
- Documentation grows along with modules, especially around toggling, scenario forking, and trust/confidence scoring.

---

## Artifacts At Project Milestones

- Architecture & API map (in code and docs)
- Config-driven simulation runner with overlays/data sources/rules selectable
- Memory store (object, log, database, or file) capturing all traces, forks, overlays, agent stats, scoring
- Test suite (unit + integration)
- A/B baseline vs overlays output report
- Interactive output/report for stakeholder review

---

## Summary Table: From Here to There

| Phase       | Time       | Key Deliverables & Acceptance                                                      |
|-------------|------------|----------------------------------------------------------------------------------|
| Foundations | Weeks 1–2  | Data, state, agents, overlays, rules, scoring, baseline simulation, logging      |
| Experiments | Weeks 3–5  | Overlay toggle/deltalogs, A/B testing infra, fragility/capital forks             |
| Recursion   | Weeks 6–8  | Recursive/multi-fork sim, adaptive overlays/rules, pruning, optimal path memory  |
| Real-time   | Months 3+  | Streaming, dashboard/API, advanced learning, external collaboration              |

---