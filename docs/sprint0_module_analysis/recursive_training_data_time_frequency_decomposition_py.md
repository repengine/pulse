# Module Analysis: `recursive_training.data.time_frequency_decomposition`

## 1. Module Intent/Purpose

The primary role of the [`recursive_training/data/time_frequency_decomposition.py`](../../recursive_training/data/time_frequency_decomposition.py:1) module is to provide advanced time-frequency decomposition capabilities for time series data. It supports methods like Short-Time Fourier Transform (STFT), Continuous Wavelet Transform (CWT), and Discrete Wavelet Transform (DWT). Beyond decomposition, it aims to extract meaningful features from the transformed data and includes functionality to detect potential regime shifts within the time series based on changes in their spectral characteristics.

## 2. Operational Status/Completeness

The module appears to be largely complete and operational for its defined scope.
- It gracefully handles the absence of optional dependencies like `scipy` and `pywavelets`, typically by falling back to STFT if a chosen wavelet method is unavailable or by logging an error if STFT itself cannot be performed.
- NaN values in input time series are handled through linear interpolation (if `scipy` is available) or by replacing them with zeros.
- Basic error handling (try-except blocks) is implemented for core operations, with issues logged.
- A DWT reconstruction feature ([`recursive_training/data/time_frequency_decomposition.py:246`](../../recursive_training/data/time_frequency_decomposition.py:246)) is commented out, suggesting it was likely used for verification during development rather than being an intended primary output.
- No explicit "TODO" or "FIXME" comments are present, indicating that the developer might consider the current feature set as implemented.

## 3. Implementation Gaps / Unfinished Next Steps

While functional, several areas could be expanded or refined:

*   **Sophistication of Regime Shift Detection:** The current regime shift detection methods ([`_detect_regime_shifts`](../../recursive_training/data/time_frequency_decomposition.py:407) and [`_detect_regime_shifts_wavelet`](../../recursive_training/data/time_frequency_decomposition.py:474)) rely on changes in the power spectrum's total power relative to a rolling mean and standard deviation. More advanced statistical change point detection algorithms or machine learning-based approaches could offer more robust and nuanced regime shift identification.
*   **Configurability of Feature Extraction:** While core transform parameters are configurable (e.g., `nperseg`, `wavelet`), the definitions for feature extraction, such as frequency band cutoffs in [`_extract_stft_features`](../../recursive_training/data/time_frequency_decomposition.py:255) ([`recursive_training/data/time_frequency_decomposition.py:278-290`](../../recursive_training/data/time_frequency_decomposition.py:278-290)) and scale band cutoffs in [`_extract_cwt_features`](../../recursive_training/data/time_frequency_decomposition.py:304) ([`recursive_training/data/time_frequency_decomposition.py:326-339`](../../recursive_training/data/time_frequency_decomposition.py:326-339)), are hardcoded as percentages. Allowing these to be configured could increase flexibility.
*   **Richness of DWT Features:** The features extracted from DWT coefficients via [`_extract_dwt_features`](../../recursive_training/data/time_frequency_decomposition.py:352) primarily focus on energy and entropy. Expanding this to include other statistical measures (e.g., mean, standard deviation, skewness, kurtosis) for each decomposition level could provide a richer feature set.
*   **Parameter Validation:** More extensive validation of configuration parameters (e.g., ensuring `nperseg` is appropriate for data length beyond the current basic checks) could prevent runtime issues.

## 4. Connections & Dependencies

*   **Direct Imports from Other Project Modules:** None are directly imported within this file, suggesting it's designed as a self-contained utility for time-frequency analysis that can be consumed by other parts of the `recursive_training` project.
*   **External Library Dependencies:**
    *   `numpy`: Essential for numerical operations and array manipulation.
    *   `scipy`: Optional. Used for:
        *   `signal.stft` in [`_apply_stft`](../../recursive_training/data/time_frequency_decomposition.py:106).
        *   `interpolate.interp1d` in [`_interpolate_nans`](../../recursive_training/data/time_frequency_decomposition.py:538).
    *   `pywavelets` (`pywt`): Optional. Used for:
        *   `pywt.cwt` in [`_apply_cwt`](../../recursive_training/data/time_frequency_decomposition.py:159).
        *   `pywt.wavedec` in [`_apply_dwt`](../../recursive_training/data/time_frequency_decomposition.py:210).
    *   `logging`: Standard Python library for logging messages.
*   **Interaction with Other Modules via Shared Data:**
    *   The module is intended to be invoked by other components that manage or generate time series data. The primary entry point for batch processing, [`apply_time_frequency_decomposition`](../../recursive_training/data/time_frequency_decomposition.py:586), expects a list of dictionaries, each containing time series data. This implies integration into a larger data processing pipeline.
*   **Input/Output Files:**
    *   **Input:**
        *   The [`TimeFrequencyDecomposer.decompose()`](../../recursive_training/data/time_frequency_decomposition.py:62) method takes a Python list of floats representing a single time series.
        *   The [`apply_time_frequency_decomposition()`](../../recursive_training/data/time_frequency_decomposition.py:586) function expects a list of dictionaries. It attempts to find time series data within these dictionaries under keys such as `"time_series"`, `"values"`, or `"data"`, and can also identify lists of numeric values directly within the dictionary items.
    *   **Output:**
        *   The module returns Python dictionaries containing the decomposition results (e.g., STFT/CWT coefficients, frequencies, time points) and extracted features.
        *   It does not directly write to or read from files, apart from logging information.

## 5. Function and Class Example Usages

### `TimeFrequencyDecomposer` Class

```python
from recursive_training.data.time_frequency_decomposition import TimeFrequencyDecomposer
import numpy as np

# Sample time series data
sample_data = list(np.sin(np.linspace(0, 100, 1000)) + np.random.rand(1000) * 0.5)
config = {} # An empty config will use defaults

# Check if SciPy is available for STFT (default method)
scipy_available = False
try:
    from scipy import signal
    scipy_available = True
except ImportError:
    pass

if scipy_available:
    # Initialize with default STFT
    decomposer_stft = TimeFrequencyDecomposer(config=config)
    stft_results = decomposer_stft.decompose(sample_data)
    print(f"STFT Keys: {list(stft_results.keys())}")

# Check if PyWavelets is available for CWT/DWT
pywt_available = False
try:
    import pywt
    pywt_available = True
except ImportError:
    pass

if pywt_available:
    # Initialize for CWT
    decomposer_cwt = TimeFrequencyDecomposer(config={"tf_method": "cwt", "wavelet": "morl"})
    cwt_results = decomposer_cwt.decompose(sample_data)
    print(f"CWT Keys: {list(cwt_results.keys())}")

    # Initialize for DWT
    decomposer_dwt = TimeFrequencyDecomposer(config={"tf_method": "dwt", "wavelet": "db4", "level": 4})
    dwt_results = decomposer_dwt.decompose(sample_data)
    print(f"DWT Keys: {list(dwt_results.keys())}")
else:
    print("PyWavelets not available, skipping CWT/DWT examples.")
```

### `apply_time_frequency_decomposition` Function

```python
from recursive_training.data.time_frequency_decomposition import apply_time_frequency_decomposition
import numpy as np

data_items = [
    {"id": "series1", "time_series": list(np.random.rand(500) + np.arange(500)/50)},
    {"id": "series2", "values": list(np.cos(np.linspace(0, 50, 600)))},
    {"id": "series3", "data": [str(x) for x in np.random.rand(400)]}, # Test string conversion
    {"id": "series4", "raw_numbers": [10, 12, None, 15, 18, "20.5"]} # Test mixed types and None
]
# Configuration for STFT with specific nperseg
config_stft = {"tf_method": "stft", "nperseg": 128} 

# Check if SciPy is available
if scipy_available:
    all_features_stft = apply_time_frequency_decomposition(data_items, config=config_stft)
    if "time_frequency" in all_features_stft:
        print(f"Processed items (STFT): {list(all_features_stft['time_frequency'].keys())}")
        if "item_0" in all_features_stft["time_frequency"]:
             print(f"Features for item_0 (STFT): {list(all_features_stft['time_frequency']['item_0'].keys())}")
else:
    print("SciPy not available, apply_time_frequency_decomposition with STFT might be limited.")

# Configuration for CWT (if PyWavelets is available)
if pywt_available:
    config_cwt = {"tf_method": "cwt", "wavelet": "cmor1.5-1.0"}
    all_features_cwt = apply_time_frequency_decomposition(data_items, config=config_cwt)
    if "time_frequency" in all_features_cwt:
        print(f"Processed items (CWT): {list(all_features_cwt['time_frequency'].keys())}")
```

## 6. Hardcoding Issues

Several instances of hardcoded values or default parameters exist:

*   **Default Configuration:** The [`TimeFrequencyDecomposer.__init__()`](../../recursive_training/data/time_frequency_decomposition.py:39) method defines default values for various parameters:
    *   `tf_method`: `"stft"` ([`recursive_training/data/time_frequency_decomposition.py:50`](../../recursive_training/data/time_frequency_decomposition.py:50))
    *   `nperseg`: `256` ([`recursive_training/data/time_frequency_decomposition.py:51`](../../recursive_training/data/time_frequency_decomposition.py:51))
    *   `noverlap`: Calculated as `nperseg // 4 * 3` if not provided ([`recursive_training/data/time_frequency_decomposition.py:60`](../../recursive_training/data/time_frequency_decomposition.py:60))
    *   `wavelet`: `"morl"` for CWT/DWT ([`recursive_training/data/time_frequency_decomposition.py:53`](../../recursive_training/data/time_frequency_decomposition.py:53))
    *   `scales`: `None` (auto-generated if not provided for CWT) ([`recursive_training/data/time_frequency_decomposition.py:54`](../../recursive_training/data/time_frequency_decomposition.py:54))
    *   `level`: `5` for DWT ([`recursive_training/data/time_frequency_decomposition.py:55`](../../recursive_training/data/time_frequency_decomposition.py:55))
    *   `regime_shift_threshold`: `2.0` ([`recursive_training/data/time_frequency_decomposition.py:56`](../../recursive_training/data/time_frequency_decomposition.py:56))
*   **Feature Extraction Bands:**
    *   STFT frequency bands in [`_extract_stft_features`](../../recursive_training/data/time_frequency_decomposition.py:255) are defined by hardcoded percentages of Nyquist frequency (e.g., `0.2`, `0.6`) ([`recursive_training/data/time_frequency_decomposition.py:278-290`](../../recursive_training/data/time_frequency_decomposition.py:278-290)).
    *   CWT scale bands in [`_extract_cwt_features`](../../recursive_training/data/time_frequency_decomposition.py:304) are defined by hardcoded fractions (e.g., `0.33`, `0.67`) ([`recursive_training/data/time_frequency_decomposition.py:327-339`](../../recursive_training/data/time_frequency_decomposition.py:327-339)).
*   **Numerical Constants:**
    *   `eps = 1e-10`: A small constant to prevent `log(0)` errors in entropy calculations is used in multiple places ([`recursive_training/data/time_frequency_decomposition.py:294`](../../recursive_training/data/time_frequency_decomposition.py:294), [`recursive_training/data/time_frequency_decomposition.py:342`](../../recursive_training/data/time_frequency_decomposition.py:342), [`recursive_training/data/time_frequency_decomposition.py:387`](../../recursive_training/data/time_frequency_decomposition.py:387)).
*   **Regime Shift Detection Parameters:**
    *   The rolling window size calculation includes a hardcoded `10` (e.g., `min(10, len(total_power) // 3)`) ([`recursive_training/data/time_frequency_decomposition.py:427`](../../recursive_training/data/time_frequency_decomposition.py:427), [`recursive_training/data/time_frequency_decomposition.py:492`](../../recursive_training/data/time_frequency_decomposition.py:492)).
    *   Grouping of adjacent shift indices uses a hardcoded maximum gap of `2` time steps ([`recursive_training/data/time_frequency_decomposition.py:450`](../../recursive_training/data/time_frequency_decomposition.py:450), [`recursive_training/data/time_frequency_decomposition.py:515`](../../recursive_training/data/time_frequency_decomposition.py:515)).
*   **Input Data Keys:** The [`apply_time_frequency_decomposition`](../../recursive_training/data/time_frequency_decomposition.py:586) function searches for hardcoded keys (`"time_series"`, `"values"`, `"data"`) in the input dictionaries ([`recursive_training/data/time_frequency_decomposition.py:611-615`](../../recursive_training/data/time_frequency_decomposition.py:611-615)).
*   **Logger Names:** Logger names such as `"TimeFrequencyDecomposer"` ([`recursive_training/data/time_frequency_decomposition.py:46`](../../recursive_training/data/time_frequency_decomposition.py:46)) and `"TimeFrequencyProcessor"` ([`recursive_training/data/time_frequency_decomposition.py:600`](../../recursive_training/data/time_frequency_decomposition.py:600)) are hardcoded strings.

## 7. Coupling Points

*   **Configuration Dictionary:** The module's behavior, particularly of the [`TimeFrequencyDecomposer`](../../recursive_training/data/time_frequency_decomposition.py:27) class, is tightly coupled to the structure and specific keys expected within the `config` dictionary provided during initialization.
*   **External Libraries:**
    *   Strongly coupled with `numpy` for all numerical computations.
    *   Conditionally coupled with `scipy.signal` (for STFT), `scipy.interpolate` (for NaN handling), and `pywt` (for CWT and DWT). The module's functionality is reduced if these optional libraries are not installed.
*   **Input Data Structure:** The [`apply_time_frequency_decomposition`](../../recursive_training/data/time_frequency_decomposition.py:586) function is coupled to the expected input format: a list of dictionaries, where each dictionary should contain time series data under one of several predefined keys or as a direct list of numerics.
*   **Output Data Structure:** Consumers of this module will be coupled to the dictionary structure it returns, including keys for different features and decomposition results (e.g., `"stft_magnitude"`, `"dominant_frequencies"`, `"regime_shifts"`).

## 8. Existing Tests

A specific test file for this module (e.g., `tests/recursive_training/data/test_time_frequency_decomposition.py`) is not immediately apparent in the provided high-level workspace file listing. A more detailed search within the `tests/` directory would be needed to confirm if dedicated unit tests exist. If not, this would be a significant gap, as the module contains complex numerical logic and multiple execution paths based on configuration and available libraries.

## 9. Module Architecture and Flow

The module is structured around a central class and a utility function:

1.  **`TimeFrequencyDecomposer` Class:**
    *   **Initialization (`__init__`)**: Configures the decomposer instance by setting the desired decomposition method (`stft`, `cwt`, `dwt`), parameters for these methods (e.g., `nperseg`, `wavelet`, `level`), and the threshold for regime shift detection. It also initializes a logger.
    *   **Core Decomposition (`decompose`)**: This is the main public method of the class.
        1.  It accepts a list of numerical values representing a time series.
        2.  Converts the input list to a `numpy` array.
        3.  Handles potential NaN values using the `_interpolate_nans` helper method.
        4.  Based on the configured `method` and the availability of `scipy` and `pywt`, it dispatches the task to one of the private methods: `_apply_stft`, `_apply_cwt`, or `_apply_dwt`.
        5.  If a selected wavelet method is unavailable due to missing `pywt`, it logs a warning and falls back to STFT (if `scipy` is available).
        6.  Returns a dictionary containing the decomposition results and extracted features.
    *   **Private Decomposition Methods (`_apply_stft`, `_apply_cwt`, `_apply_dwt`)**:
        *   Each method performs its specific time-frequency transform.
        *   They store the raw transform outputs (e.g., coefficients, frequencies, time bins).
        *   They subsequently call respective private feature extraction methods (e.g., `_extract_stft_features`).
        *   `_apply_stft` and `_apply_cwt` also invoke regime shift detection (`_detect_regime_shifts` or `_detect_regime_shifts_wavelet`).
        *   They handle errors during the process and return a result dictionary.
    *   **Private Feature Extraction Methods (`_extract_stft_features`, `_extract_cwt_features`, `_extract_dwt_features`)**:
        *   These methods calculate various features from the transform outputs, such as dominant frequencies/scales, power/energy in predefined bands, and spectral or wavelet entropy.
    *   **Private Regime Shift Detection (`_detect_regime_shifts`, `_detect_regime_shifts_wavelet`)**:
        *   These methods analyze the power spectrum (from STFT) or wavelet coefficient magnitudes (from CWT) over time to identify significant changes that might indicate regime shifts. They use a rolling window approach to compare current power/energy to a local mean.
    *   **NaN Handling (`_interpolate_nans`)**:
        *   Attempts to use linear interpolation via `scipy.interpolate.interp1d` if `scipy` is available.
        *   If interpolation fails or `scipy` is unavailable, it replaces NaNs with zeros.

2.  **`apply_time_frequency_decomposition` Function:**
    *   This standalone function acts as a higher-level wrapper.
    *   It instantiates `TimeFrequencyDecomposer`.
    *   It iterates through a list of `data_items` (expected to be dictionaries).
    *   For each item, it heuristically tries to locate the time series data by checking common key names (`"time_series"`, `"values"`, `"data"`) or any list of numeric-convertible values.
    *   It preprocesses the found series to ensure it's numeric (converting strings, handling `None` as NaN).
    *   It calls the `decomposer.decompose()` method for each valid time series.
    *   It aggregates all results into a single dictionary, keyed by `item_<index>`.
    *   Returns a dictionary containing all processed time-frequency features under a top-level key `"time_frequency"`.

**Control Flow:**
The control flow is primarily driven by the configuration provided to `TimeFrequencyDecomposer`. The `decompose` method acts as a router. Error handling is present at various stages, typically logging issues and returning empty or partial results to allow processing to continue where possible. The availability of `scipy` and `pywt` also significantly influences the execution paths.

## 10. Naming Conventions

The module generally adheres well to PEP 8 naming conventions:

*   **Class Names:** `TimeFrequencyDecomposer` uses CapWords (PascalCase).
*   **Function and Method Names:** Functions like [`apply_time_frequency_decomposition`](../../recursive_training/data/time_frequency_decomposition.py:586) and methods like [`decompose`](../../recursive_training/data/time_frequency_decomposition.py:62) or [`_apply_stft`](../../recursive_training/data/time_frequency_decomposition.py:106) use snake_case. Private helper methods are correctly prefixed with a single underscore.
*   **Variable Names:** Variables such as `time_series`, `data_array`, `nperseg`, and `regime_shift_threshold` consistently use snake_case.
*   **Constants:** Module-level constants like `SCIPY_AVAILABLE` ([`recursive_training/data/time_frequency_decomposition.py:15`](../../recursive_training/data/time_frequency_decomposition.py:15)) and `PYWT_AVAILABLE` ([`recursive_training/data/time_frequency_decomposition.py:22`](../../recursive_training/data/time_frequency_decomposition.py:22)) are in all uppercase.
*   **Clarity and Descriptiveness:** Most names are clear and accurately reflect the purpose of the variable, function, or class (e.g., `dominant_frequencies`, `spectral_entropy`, `_interpolate_nans`).
*   **Standard Conventions:** The use of `Zxx` for STFT output from `scipy.signal.stft` and `coeffs` for DWT coefficients from `pywt.wavedec` aligns with common practices in these libraries.

No significant deviations from PEP 8 or obvious AI-generated naming errors were observed. The naming is consistent and contributes to the readability of the code.