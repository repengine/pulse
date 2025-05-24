# Module Analysis: `data/manual_ingestion.py`

## 1. Module Intent/Purpose

The primary purpose of the [`data/manual_ingestion.py`](data/manual_ingestion.py:1) script is to process and ingest data from a predefined list of local ZIP files, each expected to contain a single CSV file. It extracts the CSV, performs several data cleaning and optimization steps (like type conversion and downcasting), and then stores the processed data using the [`StreamingDataStore`](recursive_training/data/streaming_data_store.py:1) (which potentially includes uploading to S3).

Its role within the `data/` directory is to provide a batch ingestion mechanism for datasets that are manually acquired and stored locally as ZIP archives. This is likely used for bulk loading historical data or datasets from sources not covered by automated ingestion pipelines.

## 2. Key Functionalities

*   **Logging Configuration**: Sets up basic logging to an INFO level.
*   **ZIP File Processing ([`process_zip_file(zip_filepath, data_store)`](data/manual_ingestion.py:13))**:
    *   Checks if the ZIP file exists.
    *   Extracts the first (assumed to be only) CSV file from the ZIP archive.
    *   Reads the CSV into a pandas DataFrame using `low_memory=False`.
    *   **Data Processing and Optimization**:
        *   Converts column names to lowercase.
        *   Attempts to convert a 'date', 'Date', or 'DATE' column to `datetime` objects, coercing errors.
        *   Converts numeric columns to appropriate `pd.to_numeric` types, coercing errors and attempting to downcast to `integer` and `float` to save memory.
        *   Converts object-type columns with low cardinality (less than 50% unique values) to the `category` dtype.
        *   Includes a placeholder example for vectorized operations (calculating a rolling mean on the first numeric column).
    *   **Data Storage**:
        *   Uses the ZIP file's stem (name without extension) as the `dataset_name`.
        *   Converts the processed DataFrame to a list of dictionaries, replacing `pd.NaT` and `np.nan` with `None` for JSON compatibility.
        *   Calls [`data_store.store_dataset_optimized(dataset_name, data_items)`](data/manual_ingestion.py:106) to save the data.
    *   **Error Handling**: Includes `try-except` blocks for `zipfile.BadZipFile`, `IndexError` (empty zip), and general exceptions during processing.
*   **Main Execution Block (`if __name__ == "__main__":`)**:
    *   Defines a hardcoded list of `zip_files_to_process` located in [`data/manual_bulk_data/`](data/manual_ingestion.py:122-137).
    *   Gets an instance of [`StreamingDataStore`](recursive_training/data/streaming_data_store.py:1) using [`StreamingDataStore.get_instance()`](data/manual_ingestion.py:140).
    *   Iterates through the list of ZIP files, calling [`process_zip_file()`](data/manual_ingestion.py:13) for each.
    *   Logs completion and closes the `data_store`.

## 3. Dependencies

### External Libraries:
*   `zipfile`: For reading and extracting from ZIP archives.
*   `pandas` (as `pd`): For data manipulation (DataFrame, CSV reading, type conversions).
*   `os`: Used implicitly by `pathlib.Path`.
*   `logging`: For application-level logging.
*   `numpy` (as `np`): Used for `np.number` in dtype selection and `np.nan` for missing value replacement.
*   `pathlib.Path`: For object-oriented path manipulation.

### Internal Pulse Modules:
*   [`recursive_training.data.streaming_data_store.StreamingDataStore`](recursive_training/data/streaming_data_store.py:1): This is a critical dependency used for storing the processed data. The script assumes this class handles optimized storage and potential S3 uploads.

## 4. SPARC Principles Assessment

### Operational Status/Completeness
*   The script is operational for its defined task: processing a hardcoded list of local ZIP/CSV files and ingesting them via [`StreamingDataStore`](recursive_training/data/streaming_data_store.py:1).
*   It is complete in the sense that it performs all steps from file reading to data storage for the predefined files.
*   Its completeness for general manual ingestion is limited by the hardcoded file list and specific data processing assumptions.

### Implementation Gaps / Unfinished Next Steps
*   **Dynamic File Discovery**: The list of files to process is hardcoded ([`zip_files_to_process`](data/manual_ingestion.py:121-137)). A more flexible solution might scan a directory or accept file paths as arguments.
*   **Schema/Configuration per Dataset**: Data processing steps (like identifying the date column, specific transformations) are somewhat generic. For diverse datasets, a configuration mechanism per dataset might be needed. The rolling mean calculation ([`process_zip_file()`](data/manual_ingestion.py:89)) is a generic example and might not be suitable for all datasets.
*   **Robust Date Parsing**: Relies on a few common names for the date column. More robust detection or configuration would be better.
*   **Error Reporting for Data Issues**: While it logs warnings for conversion issues, it generally continues processing. Depending on requirements, stricter error handling or a summary report of data quality issues might be needed.
*   **Assumption of Single CSV in ZIP**: The code assumes `zip_ref.namelist()[0]` ([`process_zip_file()`](data/manual_ingestion.py:31)) is the correct and only CSV. This could fail if ZIPs have multiple files or non-CSV files.

### Connections & Dependencies
*   Tightly coupled to the [`StreamingDataStore`](recursive_training/data/streaming_data_store.py:1) implementation, particularly the [`store_dataset_optimized()`](data/manual_ingestion.py:106) method.
*   Dependent on the local file system structure, specifically the paths in `zip_files_to_process`.
*   Relies on pandas for CSV parsing and data manipulation.

### Function and Class Example Usages
This script is designed to be run directly.
```bash
python data/manual_ingestion.py
```
This will:
1.  Iterate through the hardcoded list of ZIP files in [`data/manual_bulk_data/`](data/manual_ingestion.py:122-137).
2.  For each ZIP:
    *   Extract the (assumed single) CSV.
    *   Perform data type conversions and optimizations on the DataFrame.
    *   Store the data using [`StreamingDataStore.store_dataset_optimized()`](data/manual_ingestion.py:106).
3.  Log progress and errors.
4.  Close the [`StreamingDataStore`](recursive_training/data/streaming_data_store.py:1) connection.

### Hardcoding Issues
*   **List of ZIP files**: The `zip_files_to_process` list ([`__main__`](data/manual_ingestion.py:121-137)) is entirely hardcoded. This is the most significant hardcoding.
*   **Date Column Names**: The list `['date', 'Date', 'DATE']` ([`process_zip_file()`](data/manual_ingestion.py:47)) for identifying the date column.
*   **Cardinality Threshold**: The `0.5` threshold for converting object columns to category type ([`process_zip_file()`](data/manual_ingestion.py:75)).
*   **Rolling Mean Window**: The window size `5` for the example rolling mean calculation ([`process_zip_file()`](data/manual_ingestion.py:89)).

### Coupling Points
*   **[`StreamingDataStore`](recursive_training/data/streaming_data_store.py:1)**: The script is tightly coupled to this specific class for data storage.
*   **Input File Paths**: Directly coupled to the hardcoded paths of the ZIP files.
*   **CSV Format**: Assumes input is CSV within a ZIP.

### Existing Tests
*   No automated tests are provided within this module. Testing would involve:
    *   Creating sample ZIP/CSV files.
    *   Mocking the [`StreamingDataStore`](recursive_training/data/streaming_data_store.py:1).
    *   Verifying that data is processed as expected (correct types, NaN/NaT handling).
    *   Checking logs for correct messages and errors.

### Module Architecture and Flow
*   **Procedural Script**: The script is primarily procedural.
*   **Main Processing Function**: [`process_zip_file()`](data/manual_ingestion.py:13) encapsulates the logic for a single ZIP file.
*   **Main Guard**: The `if __name__ == "__main__":` block orchestrates the processing of all predefined files.
*   **Setup**: Logging is configured at the beginning. An instance of [`StreamingDataStore`](recursive_training/data/streaming_data_store.py:1) is obtained.
*   **Iteration**: The script iterates through the hardcoded list, calling the processing function.
*   **Cleanup**: The data store is closed at the end.

### Naming Conventions
*   Functions and variables generally use snake_case (e.g., [`process_zip_file`](data/manual_ingestion.py:13), `data_store`).
*   `logger` is a common and clear name for the logging instance.
*   `Path` objects are used appropriately.
*   Type hints are present, improving readability.

## 5. Overall Assessment

### Completeness
The script is complete for its narrow, hardcoded task of ingesting a specific list of ZIP files. It handles extraction, basic data processing/optimization, and storage via [`StreamingDataStore`](recursive_training/data/streaming_data_store.py:1). It is not a general-purpose manual ingestion tool due to the hardcoded file list.

### Quality
*   **Clarity**: The code is reasonably clear, with logging statements helping to trace execution. The [`process_zip_file()`](data/manual_ingestion.py:13) function is well-defined.
*   **Simplicity**: The data processing steps are relatively simple and common for pandas workflows.
*   **Maintainability**:
    *   Low, primarily due to the hardcoded list of `zip_files_to_process`. Adding or removing files requires direct code modification.
    *   If the structure of CSVs within the ZIPs varies significantly, the generic processing steps might become insufficient, requiring more complex, conditional logic within [`process_zip_file()`](data/manual_ingestion.py:13).
*   **Robustness**:
    *   Basic error handling for file operations (zip, CSV reading) is present.
    *   Conversion errors for data types are logged as warnings but don't stop the processing of a file or other columns, which might be desired or not depending on the use case.
    *   The assumption of a single CSV per ZIP could be a point of failure if violated.
*   **Extensibility**: Limited. To support new datasets or different processing logic without code changes, a more configurable design (e.g., configuration files for datasets, command-line arguments for paths) would be needed.

The script serves its purpose as a one-off or infrequent batch ingestion tool for a known set of files. For more dynamic or varied manual ingestion tasks, it would require significant refactoring to improve flexibility and maintainability. The data type conversions and downcasting are good practices for memory optimization.