# Product Context

This file provides a high-level overview of the project and the expected product that will be created. Initially it is based upon projectBrief.md (if provided) and all other available project-related information in the working directory. This file is intended to be updated as the project evolves, and should be used to inform all other modes of the project's goals and context.
2025-04-30 02:02:42 - Log of updates made will be appended as footnotes to the end of this file.

*

## Project Goal

* Pulse is a symbolic-capital foresight simulator designed to ingest real-time data (market, social, political, ecological, etc.), run simulations (Monte Carlo, retrodiction), and generate confidence-weighted probabilistic outcomes. It models emotional overlays, strategic fragility, capital exposure, and trust-weighted forecast generation.

## Key Features

* Modular simulation intelligence engine
* Recursive forecasting and retrodiction
* Capital/narrative strategy synthesis
* Emotional-symbolic overlays modeling
* Trust scoring for forecasts
* Adaptive rule evolution
* Persistent memory and trace scoring/pruning
* CLI and potentially UI interfaces
* Rule fingerprinting & reverse mapping
* Simulation trace viewing & analysis
* Memory audit and coherence checks
* Strategos Digest for forecast summarization
* Prompt logging and management
* DVC and MLflow integration for experiment tracking
* Recursive AI Training with GPT-Symbolic feedback

* OpenAI GPT integration for conversational interface (GPT-4 Turbo, GPT-3.5 Turbo)

## Overall Architecture

* Modular design with distinct engines: Core (config), Simulation Engine, Forecast Engine, Trust Engine, Forecast Output, Memory/Diagnostics, Symbolic System, Capital Engine, Operator Interface (UI/CLI), Utils, Dev Tools, Tests, Recursive Training.
* High-level flow: Input -> Simulation -> WorldState -> Forecast -> Trust -> Output -> Memory/Diagnostics -> UI/CLI.
* Recursive Training flow: Data Ingestion -> Feature Processing -> Model Training -> Rule Generation -> Evaluation -> GPT-Symbolic Feedback -> Rule Enhancement.
* Centralized configuration (`core/path_registry.py`, `core/pulse_config.py`).
* Emphasis on interpretability, auditability, and modular iteration.

2025-05-01 00:36:00 - Added Recursive AI Training capabilities with GPT-Symbolic feedback loop to the system architecture.
2025-05-02 16:47:05 - Added OpenAI GPT integration for the conversational interface.