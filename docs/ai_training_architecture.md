---
title: "AI Training Layer Architecture"
date: 2025-04-28
---

# AI Training Layer Architecture

```mermaid
flowchart TB
  subgraph Ingestion & Storage
    A[Iris Data Ingestion] --> B[(Raw Data Store)]
    C[Forecast Output\n(PFPA archive)] --> B
    D[Retrodiction Results\n(trust_system)] --> B
  end

  subgraph Preprocessing & Feature Engineering
    B --> E[Preprocessor\n– normalization, blending live/retrodiction]
    E --> F[Feature Store]
  end

  subgraph Training Orchestration
    F --> G[Orchestration Engine\n– schedules experiments & fine-tuning jobs]
    G --> H[Model Manager]
  end

  subgraph Model Management
    H --> I[Model Registry\n(versions, metadata, metrics)]
    I --> J[Deployment & Serving API]
  end

  subgraph Evaluation & Feedback
    I --> K[Evaluation Engine\n– runs benchmarks vs. Pulse outputs]
    F --> K
    K --> L[Metric Store\n(retrodiction error, symbolic alignment, trust delta)]
    L --> G
    L --> M[Rule Generator]
  end

  subgraph Rule Generation & Pruning
    M[Rule Generator\n– GPT & symbolic_system] --> N[Rule Evaluator\n– simulation + retrodiction test]
    N --> O[Rule Repository]
    O --> P[Pruner\n– discard low-performers via thresholds]
    P --> M
  end
```

## 1. Core Modules

- **Iris Data Ingestion**  
  - Plugins for APIs, Kafka, S3, etc. → Raw data store  
  - *Frequency constraint*: Ingest variables at most once per day (weekly time series) unless a new variable is detected.

- **Forecast & Retrodiction Collector**  
  - PFPA logger, `trust_system.retrodiction_engine` → persistence layer

- **Preprocessor & Feature Store**  
  - Blends live forecasts + retrodictions, normalizes overlays, computes derived signals

- **Training Orchestration**  
  - Job scheduler (Airflow/DAG), experiment runner for fine-tuning & RL training

- **Model Manager & Registry**  
  - Version control (MLflow/DVC), metadata, artifact storage

- **Evaluation Engine**  
  - Benchmarks model outputs vs. Pulse simulation via `simulate_forward`  
  - Metrics: MAE retrodiction error, symbolic alignment score, trust/regret delta

- **Rule Generator & Pruner**  
  - GPT-based fingerprint & rule extraction  
  - Symbolic revision planner  
  - Rule mutation engine and evaluation  
  - Pruner applies retention policies based on performance

## 2. End-to-End Data Flow

1. Iris ingestion → raw snapshots & signals  
2. Pulse forecasts → PFPA archive  
3. Retrodiction via `trust_system.retrodiction_engine` → retrodiction memory  
4. Preprocessor merges data, computes features  
5. Orchestrator pipelines features into training jobs (OpenAI fine-tune & open-source)  
6. Evaluation engine scores new models  
7. Metrics feed back into orchestrator and rule generator

## 3. Integration Points

- `forecast_engine.ai_forecaster` & `forecast_output/pfpa_logger`  
- `trust_system.retrodiction_engine` & `simulation_engine.simulator_core`  
- `learning.compute_retrodiction_error` & `learning.retrodiction_curriculum`  
- GPT training hooks in `intelligence/function_router` (“train-gpt”)

## 4. Training & Evaluation Loop

- **APIs**: OpenAI Python SDK, Hugging Face Transformers, Ray RLlib  
- **Metrics**:  
  - Retrodiction MAE (`compute_retrodiction_error`)  
  - Symbolic alignment score (`symbolic_trace_scorer`)  
  - Trust/regret delta  
- **Feedback**: Retraining on drift, rule upgrades, pruning stale rules

## 5. Dynamic Rule Generation & Pruning

1. Propose rules (GPT + symbolic planner)  
2. Batch evaluate in `simulation_engine.rule_mutation_engine`  
3. Store in Rule Repository  
4. Pruner discards rules below impact threshold

## 6. Recommended Frameworks & Tools

- Hugging Face Transformers & Datasets  
- LangChain for LLM orchestration  
- Ray RLlib or Stable-Baselines3 for RL  
- MLflow or DVC for model registry  
- Weights & Biases for experiment tracking  
- OpenAI Python SDK for prototyping  
- Airflow for scheduling

---