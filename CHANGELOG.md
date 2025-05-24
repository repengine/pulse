# Changelog

All notable changes to the Pulse project will be documented in this file.

## [Unreleased]

### Added
- New `from_dict` static method to `WorldState` class for creating instances from dictionaries

### Fixed
- Fixed `WorldState` class in `simulation_engine/worldstate.py` to properly support the `from_dict` method that was being called in `simulation_replayer.py` but was missing from the class definition
- Resolved import/type errors in `simulation_engine/utils/simulation_replayer.py` related to `WorldState` attributes

### Changed
- Updated documentation for `WorldState` module

## [1.0.0] - 2025-05-01

### Added
- Initial release of Pulse system
- Core simulation engine with WorldState representation
- Symbolic overlay system for emotional state tracking
- Capital exposure tracking across assets
- Variable management with dot notation access
- Event logging and turn management
- Serialization and deserialization capabilities