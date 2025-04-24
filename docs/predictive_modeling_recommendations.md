# Recommendations to Enhance Predictive Modeling in Pulse

This document maps our top three recommendations to existing modules and outlines expansion vectors for implementation within the current codebase.

## 1. Data & Feature Engineering

**Current Modules & Paths**
- `learning/output_data_reader.py`: data ingestion interfaces  
- `core/path_registry.py`: centralized data path management  
- `simulation_engine/worldstate.py`: state variables  

**Expansion Vectors**
1. Create `core/feature_store.py` to manage raw and engineered features  
2. Extend `learning/output_data_reader.py` to ingest new sources (market, social, ecological)  
3. Add transform plugins in `learning/transforms/`:
   - Rolling windows, lag features  
   - Sentiment scores (integrate NLP pipeline)  
   - Interaction and polynomial features  
4. Register feature pipelines in `core/pulse_config.py` under a new `FEATURE_PIPELINES` section  

## 2. Causal Inference & Counterfactual Reasoning

**Current Modules & Paths**
- `simulation_engine/causal_rules.py`: basic causal rule definitions  
- `learning/history_tracker.py`: trace history  

**Expansion Vectors**
1. Introduce `causal_model/structural_causal_model.py` to represent SCM graphs  
2. Add `causal_model/discovery.py` implementing PC and FCI algorithms  
3. Develop `causal_model/counterfactual_engine.py` for do‐calculus based queries  
4. Integrate causal outputs into forecasts: hook into `forecast_engine/forecast_generator.py`  
5. Include causal explanations in trace logs and the strategos digest  

## 3. Model Optimization, Ensembles & MLOps

**Current Modules & Paths**
- `forecast_engine/forecast_ensemble.py`: existing ensemble skeleton  
- `forecast_engine/forecast_drift_monitor.py`: drift detection  
- `mlflow_tracking_example.py` & `dvc.yaml`: experimental tracking setup  

**Expansion Vectors**
1. Flesh out `forecast_engine/ensemble_manager.py` to support:
   - Weighted averaging, stacking, boosting  
   - Modular registration of models (symbolic, statistical, ML)  
2. Create `forecast_engine/hyperparameter_tuner.py` integrating Optuna or Hyperopt  
3. Automate tuning pipelines via `dvc.yaml` stages and MLflow tracking  
4. Enhance `forecast_engine/forecast_drift_monitor.py` with new detectors (ADWIN, KSWIN)  
5. Develop a model registry interface in `core/path_registry.py` and `core/pulse_config.py`  

## Next Steps
1. Review and align on module locations and naming conventions  
2. Implement feature store and transform extensions  
3. Expand causal model and integrate with forecast engine  
4. Build ensemble manager and tuning workflows  
5. Validate additions via unit tests and benchmarks  

After confirmation, proceed to code implementation in Code mode.