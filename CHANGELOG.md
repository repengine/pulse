# Changelog

All notable changes to the Pulse project will be documented in this file.

## [Unreleased]

### Added
- New `from_dict` static method to `WorldState` class for creating instances from dictionaries
- New Pydantic model `PulseConfig` in `engine/pulse_config.py`.
- **Task 6 (Project Re-layout)**: Completed comprehensive project restructuring from flat module layout to hierarchical domain-based architecture
  - Created new top-level directories: `engine/`, `rules/`, `ingestion/`, `analytics/`, `adapters/`, `api/`, `cli/`
  - Moved 186 modules from flat structure to appropriate domain directories
  - Updated all import statements across the codebase (176 legacy import patterns updated)
  - Generated comprehensive module dependency map with visualization
  - Updated project documentation to reflect new structure
- **Task 7 (Config Cleanup)**: Implemented centralized, type-safe configuration management system
  - Created new `pulse.core.app_settings` module with Pydantic BaseSettings for configuration management
  - Consolidated scattered configuration constants into hierarchical, validated settings structure
  - Added environment variable integration with `PULSE_` prefix mapping to nested configuration
  - Implemented backward compatibility layer via `pulse.config.loader` for existing code
  - Added comprehensive configuration validation, type conversion, and error handling
  - Migrated from deprecated Pydantic V1 validators to V2 field_validator decorators
  - Created extensive module documentation and updated project inventory
- **Task 9 (Testing & Guardrails)**: Implemented comprehensive testing strategy with critical path protection
  - Created integration tests for FastAPI + Celery workflows in `tests/integration/test_api_celery_integration.py`
  - Implemented end-to-end tests for retrodiction analysis workflow in `tests/e2e/test_retrodiction_e2e.py`
  - Developed guardrail tests for critical system components in `tests/guardrails/test_critical_path_guardrails.py`
  - Added comprehensive testing strategy documentation in `docs/testing_strategy.md`
  - Implemented test categorization with pytest marks (@pytest.mark.integration, @pytest.mark.e2e, @pytest.mark.guardrail)
  - Created safety net tests for simulation engine, rules engine, API endpoints, data ingestion, and autopilot functionality
  - Enhanced test coverage and CI pipeline reliability with layered testing approach

### Fixed
- Fixed `WorldState` class in `simulation_engine/worldstate.py` to properly support the `from_dict` method that was being called in `simulation_replayer.py` but was missing from the class definition
- Resolved import/type errors in `simulation_engine/utils/simulation_replayer.py` related to `WorldState` attributes
- Resolved various `pytest` failures and `mypy` errors across multiple modules.
- Resolved remaining import errors and type mismatches across various modules, including corrections to patch targets in test files and adding type hints to `pulse/logs/api.py` functions.

### Changed
- Updated documentation for `WorldState` module
- Refactored `PulseConfig` to be the Pydantic model in `engine/pulse_config.py`.
- Updated `recursive_training.metrics.metrics_store`, `recursive_training.integration.pulse_adapter`, and `recursive_training.data.data_store` to import and use the new `PulseConfig` from `engine.pulse_config`.
- Removed fallback `PulseConfig` class definitions and associated conditional import logic from `recursive_training` modules.
- Applied extensive type hinting to `engine/pulse_config.py`, `recursive_training/metrics/metrics_store.py`, `recursive_training/integration/pulse_adapter.py`, `recursive_training/data/data_store.py`, `engine/event_bus.py`, `tests/test_pulse_config.py`, and `tests/test_ai_forecaster.py` to achieve `mypy --strict` compliance for these files.
- Updated import paths for `PulseConfig` in `tests/test_pulse_config.py` and `tests/test_ai_forecaster.py`.
- Updated `PulseEventSystem` usage in `recursive_training/integration/pulse_adapter.py` to correctly use the `event_bus` instance from `engine.event_bus`.
- Adapted `recursive_training/integration/pulse_adapter.py` to the functional nature of `SymbolicExecutor` from `symbolic_system/symbolic_executor.py`.

## [1.0.0] - 2025-05-01

### Added
- Initial release of Pulse system
- Core simulation engine with WorldState representation
- Symbolic overlay system for emotional state tracking
- Capital exposure tracking across assets
- Variable management with dot notation access
- Event logging and turn management
- Serialization and deserialization capabilities