# Pulse

**Version:** v0.2 – Trust Foundations

Pulse is a symbolic-capital foresight simulator that models emotional overlays, strategic fragility, capital exposure forks, and trust-weighted forecast generation.
It's goal is to ingest real-time market, social, political, ecological, etc. data, run monte carlo simulations, state retrodiction, forecast retrodiction, etc. to generate confidence on probabilistic outcomes.

---

## 🔧 Features

- Emotional overlays: Hope, Despair, Rage, Fatigue, Trust
- Capital fork logic: NVDA, MSFT, IBIT, SPY
- Forecast generator with symbolic decay and exposure deltas
- Trust engine scoring confidence from 0.0–1.0
- Fragility index based on symbolic tension and volatility
- Strategos Digest: grouped, sorted, and labeled forecast output
- PFPA forecast memory with confidence, fragility, and trace IDs
- Digest export system (`digest.txt`)
- Modular, fully readable code (Python 3.10+)

---

## 🚀 Quickstart

    cd pulse
    python main.py

- Outputs 5 forecast cycles by default
- Prints Strategos Digest grouped by trust level
- Saves optional `digest.txt` if logging is enabled

---

## 📂 Module Overview

| Folder                  | Purpose |
|-------------------------|---------|
| simulation_engine/      | Worldstate, turn system, symbolic decay engine |
| symbolic_system/        | Overlay logic, symbolic drift, fragility scoring |
| capital_engine/         | Fork logic for capital response to symbolic state |
| forecast_output/        | Generator, formatting, reporting, output generation, tile formatter, logger |
| memory/                 | In-memory forecast history + trace IDs |
| trust_system/           | Confidence scoring, volatility, licensing (v0.2) |
| foresight_architecture/ | Digest-to-file, compression (v0.3+) |
| diagnostics/            | Self-checks, tension audits, PLIA stub |
| operator_interface/     | User-facing. CLI, UI, dashboards |

---

## 🛣 Roadmap

- **v0.3** → Input signal horizon, retrodiction engine
- **v0.4** → Forecast compression, memory decay, strategic prioritization
- **v1.0** → Autonomous simulation intelligence, UI, agent modeling

---

## ⚠️ Status

Pulse v0.2 is functional but experimental.  
All forecasts are scored and labeled, but **licensing, memory pruning, and backtest scoring are still under construction.**

This is an interpretability-first build: every module is readable, auditable, and designed for modular iteration.

---

## Directory Structure

- `simulation_engine/` — Core simulation modules
- `utils/` — Shared utilities (logging, error, file, performance)
- `tests/` — Unit tests and fixtures
- `quarantine/` — Quarantined files and review script
- `docs/` — Documentation, deprecation policy, API reference

---

## Coding Standards

- Use type annotations and docstrings in all new code.
- Shared logic must go in `utils/`.
- Add/maintain tests for each module in `tests/`.
- Use `@profile` from `utils/performance_utils.py` for performance-critical code.

---

## Deprecation & Milestone Policy

See `docs/deprecation_policy.md`.
