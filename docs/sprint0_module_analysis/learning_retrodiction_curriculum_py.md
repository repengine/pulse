# Module Analysis: `learning/retrodiction_curriculum.py`

## 1. Module Intent/Purpose

The primary role of the [`learning/retrodiction_curriculum.py`](learning/retrodiction_curriculum.py:1) module is to manage and orchestrate structured historical simulation batches for learning purposes. It is designed to harvest divergence outcomes from these simulations and prepare these outcomes in a format suitable for analysis by a "PulseMind" component. The module aims to leverage existing Pulse retrodiction modules.

## 2. Operational Status/Completeness

The module appears to be in an early stage of development or a foundational state.
- It contains placeholder imports (lines 17-20) for key functionalities like [`run_historical_retrodiction`](simulation_engine/historical_retrodiction_runner.py:0), [`evaluate_retrodiction_batch`](trust_system/retrodiction_engine.py:0), and [`replay_simulation`](simulation_engine/utils/simulation_replayer.py:0).
- Core logic, such as the actual execution of retrodiction runs, is mocked (e.g., [`mock_run_historical_retrodiction()`](learning/retrodiction_curriculum.py:112)).
- There are no explicit TODO comments, but the presence of mock functions and placeholder imports indicates incompleteness.

## 3. Implementation Gaps / Unfinished Next Steps

*   **Core Functionality Missing:** The actual retrodiction process is mocked. Integration with [`simulation_engine.historical_retrodiction_runner`](simulation_engine/historical_retrodiction_runner.py:0) and [`trust_system.retrodiction_engine`](trust_system/retrodiction_engine.py:0) is a clear next step.
*   **PulseMind Integration:** The module prepares a feed for "PulseMind" ([`prepare_pulsemind_feed()`](learning/retrodiction_curriculum.py:95)), but the actual interaction or data schema for PulseMind is not defined within this module.
*   **Error Handling and Logging:** Beyond a simple print statement in [`harvest_divergence_logs()`](learning/retrodiction_curriculum.py:67) if a file is not found, robust error handling and logging mechanisms are absent.
*   **Configuration:** The `retrodiction_log_dir` is configurable, but other aspects like scoring weights or batching strategies are hardcoded or very simple.
*   **Advanced Curriculum Logic:** The current scoring ([`score_batch_learning_value()`](learning/retrodiction_curriculum.py:77)) is basic. More sophisticated logic for selecting or prioritizing retrodiction batches based on learning value could be an intended extension.

## 4. Connections & Dependencies

*   **Direct Project Imports (Placeholders):**
    *   `simulation_engine.historical_retrodiction_runner.run_historical_retrodiction` (commented out)
    *   `trust_system.retrodiction_engine.evaluate_retrodiction_batch` (commented out)
    *   `simulation_engine.utils.simulation_replayer.replay_simulation` (commented out)
*   **External Library Dependencies:**
    *   `os` (standard library)
    *   `json` (standard library)
    *   `typing` (standard library: `List`, `Dict`, `Any`)
*   **Interaction via Shared Data:**
    *   **Input:** Expects `worldstate_snapshots` (List of Dictionaries) as input for batch runs.
    *   **Output/Input Files:** Reads and writes JSON files in the `retrodiction_log_dir` (default: `"data/retrodiction_batches"`) to store and retrieve batch results and divergence logs. Example: `f"{batch_tag}_batch_results.json"`.
*   **Input/Output Files:**
    *   Log files for batch results (JSON format) are created in the directory specified by `retrodiction_log_dir`.

## 5. Function and Class Example Usages

The module defines one class, [`RetrodictionCurriculumManager`](learning/retrodiction_curriculum.py:22).

**Class: `RetrodictionCurriculumManager`**

*   **Initialization:**
    ```python
    curriculum = RetrodictionCurriculumManager(retrodiction_log_dir="data/custom_retro_logs")
    ```
*   **Running a Batch Retrodiction:**
    ```python
    snapshots = [{"id": "snap1", "data": ...}, {"id": "snap2", "data": ...}]
    batch_tag = "initial_learning_run"
    results_path = curriculum.batch_retrodiction_run(snapshots, batch_tag)
    # results_path will be e.g., "data/custom_retro_logs/initial_learning_run_batch_results.json"
    ```
*   **Harvesting Divergence Logs:**
    ```python
    divergences = curriculum.harvest_divergence_logs(results_path)
    # divergences will be a list of dicts, e.g., [{"divergence_type": "symbolic_drift", ...}]
    ```
*   **Scoring Learning Value:**
    ```python
    score = curriculum.score_batch_learning_value(divergences)
    # score will be a float
    ```
*   **Preparing PulseMind Feed:**
    ```python
    pulsemind_input = curriculum.prepare_pulsemind_feed(divergences)
    # pulsemind_input will be a dict summarizing divergence types, e.g., {"symbolic_drift": 5}
    ```
The module includes an `if __name__ == "__main__":` block (lines 133-144) demonstrating a basic CLI usage pattern for testing its methods.

## 6. Hardcoding Issues

*   **Default Log Directory:** The default `retrodiction_log_dir` is hardcoded to `"data/retrodiction_batches"` in the [`__init__`](learning/retrodiction_curriculum.py:23) method's signature.
*   **Scoring Logic:** The weights in [`score_batch_learning_value()`](learning/retrodiction_curriculum.py:92) (`score = unique_types + 0.1 * total_count`) are hardcoded.
*   **Mock Data:** The [`mock_run_historical_retrodiction()`](learning/retrodiction_curriculum.py:112) function contains hardcoded mock divergence data (lines 122-125).
*   **String Literals:** "unknown" is used as a default for `divergence_type` and `worldstate_id` in a few places.

## 7. Coupling Points

*   **Simulation Engine:** Tightly coupled with the (currently placeholder) `simulation_engine` for running retrodictions. Changes in the simulation output format would directly impact this module.
*   **Trust System:** Dependency on a (currently placeholder) `trust_system.retrodiction_engine` for evaluation.
*   **PulseMind:** The module is designed to produce input for an external "PulseMind" system. The structure of this output ([`prepare_pulsemind_feed()`](learning/retrodiction_curriculum.py:95)) creates a coupling point.
*   **File System:** Relies on the file system for storing and retrieving batch results. The path structure and JSON format are coupling points.

## 8. Existing Tests

*   A test file exists at [`tests/recursive_training/advanced_metrics/test_retrodiction_curriculum.py`](tests/recursive_training/advanced_metrics/test_retrodiction_curriculum.py:1).
*   However, this test file appears to be for a different class, [`EnhancedRetrodictionCurriculum`](tests/recursive_training/advanced_metrics/test_retrodiction_curriculum.py:12), located in `recursive_training.advanced_metrics.retrodiction_curriculum`.
*   There are no apparent dedicated tests for the [`RetrodictionCurriculumManager`](learning/retrodiction_curriculum.py:22) class within the provided file structure.
*   The module itself contains a basic `if __name__ == "__main__":` block (lines 133-144) which serves as a rudimentary test or example usage script. This script covers the main methods of the [`RetrodictionCurriculumManager`](learning/retrodiction_curriculum.py:22) class using mock data.

## 9. Module Architecture and Flow

1.  **Initialization:** The [`RetrodictionCurriculumManager`](learning/retrodiction_curriculum.py:22) is initialized, setting up the directory for storing batch results.
2.  **Batch Execution:** The [`batch_retrodiction_run()`](learning/retrodiction_curriculum.py:33) method takes a list of worldstate snapshots.
    *   It iterates through these snapshots.
    *   For each snapshot, it (currently) calls a mock function ([`mock_run_historical_retrodiction()`](learning/retrodiction_curriculum.py:112)) to simulate a retrodiction run.
    *   The results (including mock divergence logs) are collected.
    *   These results are saved to a JSON file in the `retrodiction_log_dir`.
3.  **Harvesting Results:** The [`harvest_divergence_logs()`](learning/retrodiction_curriculum.py:56) method loads the JSON batch result file and extracts all divergence log entries.
4.  **Scoring:** The [`score_batch_learning_value()`](learning/retrodiction_curriculum.py:77) method calculates a simple score based on the variety and count of divergence types.
5.  **Preparing Feed:** The [`prepare_pulsemind_feed()`](learning/retrodiction_curriculum.py:95) method transforms the list of divergences into a summary dictionary, counting occurrences of each divergence type, intended for "PulseMind".

The primary data flow involves:
`worldstate_snapshots` -> `batch_retrodiction_run` -> `batch_results.json` file -> `harvest_divergence_logs` -> `divergences list` -> (`score_batch_learning_value` AND `prepare_pulsemind_feed`).

## 10. Naming Conventions

*   **Class Name:** [`RetrodictionCurriculumManager`](learning/retrodiction_curriculum.py:22) is descriptive and follows PascalCase.
*   **Method Names:** Generally follow snake_case (e.g., [`batch_retrodiction_run()`](learning/retrodiction_curriculum.py:33), [`harvest_divergence_logs()`](learning/retrodiction_curriculum.py:56)).
*   **Variable Names:** Mostly snake_case (e.g., `retrodiction_log_dir`, `worldstate_snapshots`, `batch_tag`).
*   **Constants/Configuration:** No explicit constants are defined, but string literals like `"data/retrodiction_batches"` are used.
*   **PEP 8:** The module generally adheres to PEP 8 styling for naming and formatting.
*   **Clarity:** Names are generally clear and indicate their purpose.
*   No obvious AI assumption errors or significant deviations from standard Python conventions were noted.