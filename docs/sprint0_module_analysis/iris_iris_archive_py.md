# Module Analysis: iris/iris_archive.py

## 1. Module Intent/Purpose

The primary role of the [`iris/iris_archive.py`](../../../iris/iris_archive.py:1) module is to provide an append-only storage mechanism for incoming signals. It is designed for long-term historical memory of signals, as stated in its docstring, which also mentions support for "symbolic volatility tracking, and trust retrospection," though these latter features are not implemented within this specific module.

## 2. Operational Status/Completeness

The module appears to be operational for its core functions: appending signals to a file, loading all signals from the file, and counting the number of stored signals. It successfully creates the necessary directory and file. There are no explicit `TODO` comments or obvious placeholders in the implemented code. However, the features mentioned in the docstring (symbolic volatility tracking, trust retrospection) are not present, indicating it's a foundational or initial version.

## 3. Implementation Gaps / Unfinished Next Steps

*   **Missing Advanced Features:** The docstring mentions "symbolic volatility tracking, and trust retrospection" ([`iris/iris_archive.py:5`](../../../iris/iris_archive.py:5)), which are not implemented in this module. These would likely require significant additional logic and potentially new methods or classes.
*   **Scalability of `load_archive()`:** The [`load_archive()`](../../../iris/iris_archive.py:42-56) method loads the entire archive into memory, which is explicitly noted as "memory intensive for very large archives." For a system intended for "long-term historical memory," this is a significant limitation. Future development would require more sophisticated data retrieval methods (e.g., streaming, querying by date/ID, indexing).
*   **Data Management Features:**
    *   No functionality for searching or filtering signals based on criteria (e.g., timestamp, source, symbolic tag).
    *   No mechanism for updating or deleting records (though it's described as "append-only," some administrative functions might be needed).
    *   No archive management features like rotation, splitting, or compression for very large archive files.
*   **Robust Error Handling:** While basic `try-except` blocks exist for file operations, error handling during `json.loads` in [`load_archive()`](../../../iris/iris_archive.py:53) is generic. It doesn't specifically handle malformed lines, which could lead to incomplete data loading or failure if a single line is corrupted.
*   **Configuration:** The archive directory and filename are hardcoded. These should ideally be configurable.

## 4. Connections & Dependencies

*   **Direct Imports from other project modules:** None.
*   **External Library Dependencies:**
    *   `os`: For path manipulation and directory creation ([`os.path.join`](../../../iris/iris_archive.py:19), [`os.makedirs`](../../../iris/iris_archive.py:26), [`os.path.exists`](../../../iris/iris_archive.py:51)).
    *   `json`: For serializing signals to JSON strings and deserializing them ([`json.dumps`](../../../iris/iris_archive.py:37), [`json.loads`](../../../iris/iris_archive.py:53)).
    *   `logging`: For informational and error messages.
    *   `typing.Dict`, `typing.Any`: For type hinting.
*   **Interaction with other modules via shared data:**
    *   The module's primary interaction is through the filesystem, specifically the JSON Lines file located at [`data/iris_archive/signals_archive.jsonl`](../../../iris/iris_archive.py:19). Other modules would use this class (or interact with the file directly, though less ideal) to persist or retrieve signal data.
*   **Input/Output Files:**
    *   **Output:** [`data/iris_archive/signals_archive.jsonl`](../../../iris/iris_archive.py:19) (written by [`append_signal()`](../../../iris/iris_archive.py:28-40)).
    *   **Input:** [`data/iris_archive/signals_archive.jsonl`](../../../iris/iris_archive.py:19) (read by [`load_archive()`](../../../iris/iris_archive.py:42-56) and [`count_signals()`](../../../iris/iris_archive.py:58-71)).
    *   Logs messages using the standard Python `logging` module.

## 5. Function and Class Example Usages

The module defines one class, [`IrisArchive`](../../../iris/iris_archive.py:21-71).

*   **`IrisArchive()` Constructor ([`iris/iris_archive.py:22-26`](../../../iris/iris_archive.py:22-26)):**
    *   Initializes the archive system.
    *   Ensures the archive directory ([`ARCHIVE_DIR`](../../../iris/iris_archive.py:18)) exists, creating it if necessary.
    ```python
    archive = IrisArchive()
    ```

*   **`append_signal(self, signal_record: Dict[str, Any])` ([`iris/iris_archive.py:28-40`](../../../iris/iris_archive.py:28-40)):**
    *   Appends a single signal record (a dictionary) to the archive file. The record is serialized to a JSON string and a newline character is added, making it a JSON Lines format.
    ```python
    test_signal = {
        "name": "hope_resurgence", "value": 0.85, "source": "mock_plugin",
        "timestamp": "2025-04-27T00:00:00Z", "symbolic_tag": "hope",
        "recency_score": 0.99, "anomaly_flag": False, "sti": 0.93
    }
    archive.append_signal(test_signal)
    ```

*   **`load_archive(self) -> list` ([`iris/iris_archive.py:42-56`](../../../iris/iris_archive.py:42-56)):**
    *   Loads all signal records from the archive file. Each line is deserialized from JSON into a dictionary.
    *   Returns a list of dictionaries, where each dictionary is a signal record.
    *   Warns that this can be memory-intensive for large archives.
    ```python
    all_signals = archive.load_archive()
    for signal in all_signals:
        print(signal['name'])
    ```

*   **`count_signals(self) -> int` ([`iris/iris_archive.py:58-71`](../../../iris/iris_archive.py:58-71)):**
    *   Counts the total number of signals stored in the archive by counting the lines in the file.
    *   Returns an integer representing the total count.
    ```python
    total_signals = archive.count_signals()
    print(f"Total signals: {total_signals}")
    ```
The module includes a basic command-line execution block (`if __name__ == "__main__":`) ([`iris/iris_archive.py:74-91`](../../../iris/iris_archive.py:74-91)) that demonstrates these usages.

## 6. Hardcoding Issues

*   **Archive Directory Path:** `ARCHIVE_DIR = "data/iris_archive"` ([`iris/iris_archive.py:18`](../../../iris/iris_archive.py:18)) is hardcoded. This makes the storage location inflexible without code changes.
*   **Archive Filename:** The filename `signals_archive.jsonl` within `ARCHIVE_FILE` ([`iris/iris_archive.py:19`](../../../iris/iris_archive.py:19)) is hardcoded.
*   **Logging Prefixes:** Log messages include a hardcoded prefix like `"[IrisArchive]"` (e.g., [`iris/iris_archive.py:38`](../../../iris/iris_archive.py:38)). While common, this could be made more dynamic if needed.

## 7. Coupling Points

*   **Filesystem Coupling:** The module is tightly coupled to the local filesystem through the hardcoded path [`data/iris_archive/signals_archive.jsonl`](../../../iris/iris_archive.py:19). Changes to storage strategy (e.g., moving to a database, cloud storage) would require significant modification to this module.
*   **Data Format Coupling:** It's coupled to the JSON Lines (`.jsonl`) format for storing signals. Any change in serialization format would impact all methods.
*   **Consuming Modules:** Any module that needs to store or retrieve signals would depend on the `IrisArchive` class and its specific methods, or, less ideally, directly on the `signals_archive.jsonl` file structure.

## 8. Existing Tests

*   **No Dedicated Test File:** Based on the provided file list, there does not appear to be a dedicated test file (e.g., `tests/test_iris_archive.py`).
*   **Inline Example/Test:** The module contains an `if __name__ == "__main__":` block ([`iris/iris_archive.py:74-91`](../../../iris/iris_archive.py:74-91)) which functions as a rudimentary test and usage example. It appends a sample signal and then prints the total count. This is not a substitute for a formal, comprehensive test suite using a testing framework like `pytest`.
*   **Test Coverage Gaps:** Obvious gaps include testing:
    *   File/directory creation edge cases (e.g., permissions issues, pre-existing file instead of directory).
    *   Behavior when the archive file is empty or does not exist for `load_archive` and `count_signals`.
    *   Error handling for I/O exceptions (e.g., disk full, read/write errors).
    *   Handling of malformed JSON data in the archive file during `load_archive`.
    *   Appending various valid and potentially invalid signal structures.

## 9. Module Architecture and Flow

*   **Structure:** The module consists of a single class, [`IrisArchive`](../../../iris/iris_archive.py:21-71), which encapsulates all functionality. It defines constants for the archive directory and file path at the module level.
*   **Key Components:**
    *   [`IrisArchive`](../../../iris/iris_archive.py:21-71) class: Manages signal persistence.
    *   [`ARCHIVE_FILE`](../../../iris/iris_archive.py:19): The JSONL file used as the data store.
*   **Primary Data Flow:**
    1.  Signal data (as a Python dictionary) is passed to [`append_signal()`](../../../iris/iris_archive.py:28-40).
    2.  [`append_signal()`](../../../iris/iris_archive.py:28-40) serializes the dictionary to a JSON string and appends it as a new line to [`ARCHIVE_FILE`](../../../iris/iris_archive.py:19).
    3.  [`load_archive()`](../../../iris/iris_archive.py:42-56) reads each line from [`ARCHIVE_FILE`](../../../iris/iris_archive.py:19), deserializes it from JSON into a dictionary, and aggregates these into a list.
    4.  [`count_signals()`](../../../iris/iris_archive.py:58-71) reads [`ARCHIVE_FILE`](../../../iris/iris_archive.py:19) line by line to determine the count.
*   **Control Flow:**
    *   The constructor [`__init__()`](../../../iris/iris_archive.py:22-26) ensures the archive directory exists.
    *   Methods perform specific file I/O operations (append, read all, count lines).
    *   Basic error handling is implemented using `try-except Exception` blocks, which log errors but may not always recover gracefully or provide specific feedback.

## 10. Naming Conventions

*   **Module Name:** `iris_archive.py` follows snake_case, which is standard for Python modules.
*   **Class Name:** [`IrisArchive`](../../../iris/iris_archive.py:21-71) uses PascalCase, adhering to PEP 8.
*   **Method Names:** [`append_signal`](../../../iris/iris_archive.py:28-40), [`load_archive`](../../../iris/iris_archive.py:42-56), [`count_signals`](../../../iris/iris_archive.py:58-71) use snake_case, adhering to PEP 8.
*   **Constant Names:** [`ARCHIVE_DIR`](../../../iris/iris_archive.py:18), [`ARCHIVE_FILE`](../../../iris/iris_archive.py:19) use UPPER_SNAKE_CASE, which is conventional for module-level constants.
*   **Variable Names:** `signal_record`, `logger`, `f`, `signals`, `line`, `total` generally follow snake_case.
*   **Overall Consistency:** Naming conventions are generally consistent and follow PEP 8 guidelines. No obvious AI assumption errors or significant deviations were noted.