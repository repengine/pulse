# Module Analysis: `recursive_training/data/self_supervised_learning.py`

## 1. Module Intent/Purpose

The primary role of the [`self_supervised_learning.py`](recursive_training/data/self_supervised_learning.py:1) module is to provide a framework for self-supervised representation learning from time series data. It aims to generate compact latent representations using autoencoder architectures. The module offers implementations for autoencoders using TensorFlow, PyTorch, and a simple NumPy-based version as a fallback. It includes functionality to build, train, encode, decode, and save/load these models. A key function, [`apply_self_supervised_learning()`](recursive_training/data/self_supervised_learning.py:1646), orchestrates the process of data preprocessing, model creation, training, and representation extraction.

## 2. Operational Status/Completeness

The module appears to be largely complete and operational for its defined scope.
*   It provides three distinct autoencoder implementations ([`TensorFlowAutoencoder`](recursive_training/data/self_supervised_learning.py:76), [`PyTorchAutoencoder`](recursive_training/data/self_supervised_learning.py:535), [`SimpleAutoencoder`](recursive_training/data/self_supervised_learning.py:1316)) with support for dense, LSTM, and Conv1D architectures (though LSTM and Conv1D in PyTorch are more complex and might require more testing).
*   The [`create_autoencoder()`](recursive_training/data/self_supervised_learning.py:1588) factory function correctly selects the implementation based on available libraries.
*   The main entry point, [`apply_self_supervised_learning()`](recursive_training/data/self_supervised_learning.py:1646), handles data ingestion, preprocessing (padding/truncating, normalization, NaN handling), model training, and result formatting.
*   Error handling for library imports and basic exceptions during processing is present.

There are no obvious `TODO` comments or major placeholders indicating unfinished core functionality. However, the complexity of the PyTorch LSTM and Conv1D implementations ([`_build_lstm_autoencoder()`](recursive_training/data/self_supervised_learning.py:682) and [`_build_conv_autoencoder()`](recursive_training/data/self_supervised_learning.py:825) within `PyTorchAutoencoder`) suggests they might be less robust or tested than the TensorFlow counterparts or the simpler dense versions.

## 3. Implementation Gaps / Unfinished Next Steps

*   **Advanced Preprocessing:** The current NaN handling is basic linear interpolation ([`apply_self_supervised_learning()`](recursive_training/data/self_supervised_learning.py:1724-1742)). More sophisticated methods could be beneficial. Similarly, normalization is per-series min-max scaling; other strategies might be relevant.
*   **Hyperparameter Optimization:** The module uses fixed or configurable hyperparameters. Integration with a hyperparameter optimization library could improve model performance.
*   **Model Evaluation Metrics:** Beyond reconstruction error (MSE), other metrics for evaluating the quality of latent representations (e.g., downstream task performance, separability) are not included.
*   **More Autoencoder Variants:** While common architectures are covered, more advanced self-supervised techniques like VAEs (Variational Autoencoders), contrastive learning methods (SimCLR, MoCo), or transformer-based autoencoders are not present. The docstring mentions "autoencoder architectures" primarily, so this might be outside the current intended scope but represents a logical extension.
*   **PyTorch Decoder in TensorFlowAutoencoder:** The [`decode()`](recursive_training/data/self_supervised_learning.py:400) method in [`TensorFlowAutoencoder`](recursive_training/data/self_supervised_learning.py:76) reconstructs the decoder on the fly. While functional, saving and loading a dedicated decoder model (similar to how the encoder is saved) could be more robust.
*   **PyTorch LSTM/Conv1D Complexity:** The PyTorch implementations for LSTM and Conv1D autoencoders are significantly more complex and manually constructed compared to their TensorFlow/Keras counterparts. This could indicate they were added later or might be less mature. For instance, the sequence length handling and padding/cropping in the PyTorch Conv1D decoder ([`Conv1DDecoder.forward()`](recursive_training/data/self_supervised_learning.py:952-983)) is quite manual.
*   **Configurable Optimizers in PyTorch:** The [`PyTorchAutoencoder`](recursive_training/data/self_supervised_learning.py:535) hardcodes `optim.Adam` ([`PyTorchAutoencoder.__init__()`](recursive_training/data/self_supervised_learning.py:590)), unlike TensorFlow which allows optimizer selection via string.

## 4. Connections & Dependencies

### Direct Project Module Imports:
*   None. This module is self-contained in terms of project-specific code.

### External Library Dependencies:
*   **Core:**
    *   [`logging`](recursive_training/data/self_supervised_learning.py:9)
    *   [`numpy`](recursive_training/data/self_supervised_learning.py:10) (as `np`)
    *   [`typing`](recursive_training/data/self_supervised_learning.py:11) (Dict, List, Any, Tuple, Optional, Union)
    *   [`json`](recursive_training/data/self_supervised_learning.py:12)
    *   [`os`](recursive_training/data/self_supervised_learning.py:13)
    *   [`datetime`](recursive_training/data/self_supervised_learning.py:14)
*   **Deep Learning (Optional):**
    *   [`tensorflow`](recursive_training/data/self_supervised_learning.py:18) (as `tf`): Conditional import, checked by `TF_AVAILABLE`.
        *   `tensorflow.keras.models` ([`Model`](recursive_training/data/self_supervised_learning.py:19), [`Sequential`](recursive_training/data/self_supervised_learning.py:19), [`load_model`](recursive_training/data/self_supervised_learning.py:19), [`save_model`](recursive_training/data/self_supervised_learning.py:19))
        *   `tensorflow.keras.layers` ([`Input`](recursive_training/data/self_supervised_learning.py:21), [`Dense`](recursive_training/data/self_supervised_learning.py:21), [`LSTM`](recursive_training/data/self_supervised_learning.py:21), [`GRU`](recursive_training/data/self_supervised_learning.py:21), [`Conv1D`](recursive_training/data/self_supervised_learning.py:21), [`MaxPooling1D`](recursive_training/data/self_supervised_learning.py:21), [`UpSampling1D`](recursive_training/data/self_supervised_learning.py:22), [`Flatten`](recursive_training/data/self_supervised_learning.py:22), [`Reshape`](recursive_training/data/self_supervised_learning.py:22), [`RepeatVector`](recursive_training/data/self_supervised_learning.py:22), [`BatchNormalization`](recursive_training/data/self_supervised_learning.py:23), [`Dropout`](recursive_training/data/self_supervised_learning.py:23), [`TimeDistributed`](recursive_training/data/self_supervised_learning.py:23))
        *   `tensorflow.keras.callbacks` ([`EarlyStopping`](recursive_training/data/self_supervised_learning.py:25), [`ModelCheckpoint`](recursive_training/data/self_supervised_learning.py:25))
    *   [`torch`](recursive_training/data/self_supervised_learning.py:31): Conditional import, checked by `TORCH_AVAILABLE`.
        *   `torch.nn` (as `nn`)
        *   `torch.optim` (as `optim`)
        *   `torch.utils.data` ([`DataLoader`](recursive_training/data/self_supervised_learning.py:34), [`TensorDataset`](recursive_training/data/self_supervised_learning.py:34))

### Interaction with Other Modules via Shared Data:
*   **Input:** The module expects input data as a list of dictionaries (`data_items`) where each dictionary contains time series data, typically under keys like `"time_series"`, `"values"`, or `"data"` ([`apply_self_supervised_learning()`](recursive_training/data/self_supervised_learning.py:1678-1700)). This suggests it's designed to consume data prepared by other (unseen in this module) data processing or ingestion modules.
*   **Output:**
    *   The primary output of [`apply_self_supervised_learning()`](recursive_training/data/self_supervised_learning.py:1646) is a dictionary containing latent representations, model information, and series information. This dictionary is likely consumed by downstream modules for further analysis, storage, or model building.
    *   Models can be saved to files ([`TensorFlowAutoencoder.save()`](recursive_training/data/self_supervised_learning.py:465), [`PyTorchAutoencoder.save()`](recursive_training/data/self_supervised_learning.py:1242), [`SimpleAutoencoder.save()`](recursive_training/data/self_supervised_learning.py:1544)). TensorFlow models are saved in Keras format, PyTorch models as state dictionaries, and SimpleAutoencoder models as JSON. TensorFlow also saves a separate encoder model and a JSON config file.

### Input/Output Files:
*   **Model Files:**
    *   TensorFlow: Saves the main model (e.g., `model.keras`), a separate encoder model (e.g., `model_encoder.keras`), and a configuration JSON (e.g., `model_config.json`).
    *   PyTorch: Saves a single file containing state dictionaries for the model, encoder, decoder, optimizer, and configuration parameters (e.g., `model.pth`).
    *   SimpleAutoencoder: Saves a JSON file with model parameters (e.g., `model.json`).
*   **Logs:** Uses the `logging` module, implying logs could be written depending on the application's logging configuration.

## 5. Function and Class Example Usages

### `AutoencoderModel` (Base Class)
This is an abstract base class and not used directly. Its subclasses are used.

### `TensorFlowAutoencoder`
```python
# Assuming TF_AVAILABLE is True
config_tf = {
    "architecture": "dense", # or "lstm", "conv1d"
    "hidden_dims": [64, 32],
    "activation": "relu",
    "learning_rate": 0.001,
    # For sequence models:
    # "sequence_mode": True,
    # "sequence_length": 50,
    # "feature_dim": 1
}
tf_ae = TensorFlowAutoencoder(input_dim=100, latent_dim=10, **config_tf)
# Assuming 'train_data_normalized' is a NumPy array of shape (n_samples, 100)
history = tf_ae.fit(train_data_normalized, epochs=50, batch_size=32)
latent_vecs = tf_ae.encode(train_data_normalized)
reconstructed_data = tf_ae.reconstruct(train_data_normalized)
# tf_ae.save("path/to/tf_model.keras")
# loaded_tf_ae = TensorFlowAutoencoder(input_dim=1, latent_dim=1) # Dummy dims, will be overwritten
# loaded_tf_ae.load("path/to/tf_model.keras")
```

### `PyTorchAutoencoder`
```python
# Assuming TORCH_AVAILABLE is True
config_torch = {
    "architecture": "lstm", # or "dense", "conv1d"
    "hidden_dims": [64, 32],
    "activation": "tanh",
    "learning_rate": 0.002,
    "sequence_mode": True, # Required for LSTM/Conv1D if data is sequential
    "sequence_length": 50,
    "feature_dim": 1,
    "device": "cuda" if torch.cuda.is_available() else "cpu"
}
# For LSTM/Conv1D, input_dim is often the sequence length if not in sequence_mode,
# or feature_dim if in sequence_mode (though the class handles this internally).
# Let's assume input_dim is sequence_length for this example if not sequence_mode,
# or feature_dim if sequence_mode.
# The class structure for PyTorch LSTM/Conv1D expects feature_dim as input_size for LSTMs
# and channels for Conv1D.
# If sequence_mode=True, input_dim for constructor is effectively feature_dim.
# If sequence_mode=False, input_dim for constructor is sequence_length.

# Example for LSTM:
# input_dim here would be feature_dim if sequence_mode=True
pt_ae = PyTorchAutoencoder(input_dim=1, latent_dim=10, **config_torch)
# Assuming 'train_data_torch_reshaped' is NumPy array (n_samples, seq_len, feature_dim)
history = pt_ae.fit(train_data_torch_reshaped, epochs=50, batch_size=32)
latent_vecs = pt_ae.encode(train_data_torch_reshaped)
reconstructed_data = pt_ae.reconstruct(train_data_torch_reshaped)
# pt_ae.save("path/to/pt_model.pth")
# loaded_pt_ae = PyTorchAutoencoder(input_dim=1, latent_dim=1) # Dummy dims
# loaded_pt_ae.load("path/to/pt_model.pth")
```

### `SimpleAutoencoder`
```python
simple_ae_config = {"hidden_dims": [50]}
simple_ae = SimpleAutoencoder(input_dim=100, latent_dim=10, **simple_ae_config)
# Assuming 'train_data_normalized' is a NumPy array of shape (n_samples, 100)
history = simple_ae.fit(train_data_normalized, epochs=20, learning_rate=0.01)
latent_vecs = simple_ae.encode(train_data_normalized)
reconstructed_data = simple_ae.decode(latent_vecs) # or simple_ae.reconstruct(train_data)
# simple_ae.save("path/to/simple_model.json")
# loaded_simple_ae = SimpleAutoencoder(input_dim=1, latent_dim=1) # Dummy dims
# loaded_simple_ae.load("path/to/simple_model.json")
```

### `create_autoencoder()`
```python
factory_config = {
    "framework": "tensorflow", # or "pytorch", "simple", "auto"
    "architecture": "dense",
    "hidden_dims": [128, 64],
    "learning_rate": 0.001
}
autoencoder_instance = create_autoencoder(input_dim=100, latent_dim=20, config=factory_config)
# autoencoder_instance can then be used like TensorFlowAutoencoder, PyTorchAutoencoder, or SimpleAutoencoder
```

### `apply_self_supervised_learning()`
```python
sample_data_items = [
    {"name": "series_A", "values": [1.0, 2.0, 1.5, 2.5, 3.0, 2.8, None, 4.0]}, # Will be padded/truncated and NaN handled
    {"name": "series_B", "time_series": [10, 12, 11, 13, 14, 100, 102, 101, 103, 104]},
    {"data": [0.1, 0.2, 0.1, 0.3, 0.4]} # Name will be "data"
]
ssl_config = {
    "latent_dim": 8,
    "epochs": 30,
    "framework": "auto", # Tries TF, then PyTorch, then Simple
    "architecture": "dense",
    "hidden_dims": [32, 16]
}
results = apply_self_supervised_learning(data_items=sample_data_items, config=ssl_config)
# 'results' will be a dictionary:
# {"self_supervised": {"model_info": {...}, "series_info": {...}, "representations": {"series_A": {...}, ...}}}
# or {"self_supervised": {"error": "..."}} if an error occurred.
# print(json.dumps(results, indent=2))
```

## 6. Hardcoding Issues

*   **Default Hyperparameters:** Many parameters in class constructors and the [`apply_self_supervised_learning()`](recursive_training/data/self_supervised_learning.py:1646) function have default values (e.g., `latent_dim=16`, `epochs=100`, `hidden_dims=[128, 64]`). While configurable, these act as implicit hardcodings if not overridden.
*   **TensorFlow Conv1D Filters:** In [`TensorFlowAutoencoder._build_conv_autoencoder()`](recursive_training/data/self_supervised_learning.py:251), the starting number of filters is `filters = 32` ([`TensorFlowAutoencoder._build_conv_autoencoder()`](recursive_training/data/self_supervised_learning.py:269)). This is not directly configurable via constructor arguments.
*   **PyTorch Conv1D Filter Base:** In [`PyTorchAutoencoder._build_conv_autoencoder()`](recursive_training/data/self_supervised_learning.py:825), `filter_base = 16` ([`Conv1DEncoder.__init__()`](recursive_training/data/self_supervised_learning.py:852)) is used.
*   **PyTorch LSTM Decoder Input Size:** In [`PyTorchAutoencoder._build_lstm_autoencoder()`](recursive_training/data/self_supervised_learning.py:682), the `LSTMDecoder`'s first LSTM layer has `input_size=1` ([`LSTMDecoder.__init__()`](recursive_training/data/self_supervised_learning.py:759)), assuming it processes a repeated vector. This is an architectural choice.
*   **Data Keys for Time Series:** [`apply_self_supervised_learning()`](recursive_training/data/self_supervised_learning.py:1646) looks for specific keys (`"time_series"`, `"values"`, `"data"`) to find time series data ([`apply_self_supervised_learning()`](recursive_training/data/self_supervised_learning.py:1683-1700)). While it has a fallback to find any list of numbers, these primary keys are hardcoded.
*   **NaN Handling Threshold:** The NaN ratio threshold for skipping a series is `0.3` ([`apply_self_supervised_learning()`](recursive_training/data/self_supervised_learning.py:1720)).
*   **SimpleAutoencoder Activation:** The [`SimpleAutoencoder`](recursive_training/data/self_supervised_learning.py:1316) uses a hardcoded sigmoid activation function ([`_sigmoid()`](recursive_training/data/self_supervised_learning.py:1358)).
*   **File Suffixes for TensorFlow Models:** When saving TensorFlow models, `_encoder` and `_config.json` suffixes are hardcoded ([`TensorFlowAutoencoder.save()`](recursive_training/data/self_supervised_learning.py:482), [`TensorFlowAutoencoder.save()`](recursive_training/data/self_supervised_learning.py:498)).
*   **Default Optimizer for PyTorch:** [`PyTorchAutoencoder`](recursive_training/data/self_supervised_learning.py:535) defaults to `optim.Adam` ([`PyTorchAutoencoder.__init__()`](recursive_training/data/self_supervised_learning.py:590)) and this is not configurable via constructor arguments in the same way as TensorFlow's optimizer.

## 7. Coupling Points

*   **Framework Availability:** The module's behavior, particularly in [`create_autoencoder()`](recursive_training/data/self_supervised_learning.py:1588), is tightly coupled to the presence of TensorFlow and PyTorch in the environment.
*   **Input Data Structure:** The [`apply_self_supervised_learning()`](recursive_training/data/self_supervised_learning.py:1646) function is coupled to the expected structure of `data_items` (list of dicts with specific keys for time series).
*   **Configuration Dictionary:** All classes and the main application function rely on a configuration dictionary for various settings. Changes to expected config keys could break functionality if not handled gracefully.
*   **Internal Model Structure (for TF decode):** The [`TensorFlowAutoencoder.decode()`](recursive_training/data/self_supervised_learning.py:400) method relies on introspecting the layers of the full model to reconstruct a decoder. Changes to how the encoder part of the model is named or structured could break this.
*   **File Saving/Loading Conventions:** Each autoencoder class has its own save/load format. The TensorFlow version has a multi-file convention. Consistency is internal to each class but differs between them.

## 8. Existing Tests

*   A search in `tests/recursive_training/data/` revealed no specific test file for `self_supervised_learning.py`.
*   **Assessment:** There are no dedicated unit tests or integration tests apparent for this module within the specified test directory. This is a significant gap, especially given the complexity of the different autoencoder implementations and architectures.
*   **Obvious Gaps:**
    *   Unit tests for each autoencoder class ([`TensorFlowAutoencoder`](recursive_training/data/self_supervised_learning.py:76), [`PyTorchAutoencoder`](recursive_training/data/self_supervised_learning.py:535), [`SimpleAutoencoder`](recursive_training/data/self_supervised_learning.py:1316)) covering:
        *   Model building for each architecture (dense, LSTM, Conv1D).
        *   Fitting process.
        *   Encoding and decoding consistency.
        *   Reconstruction quality (even if just checking shapes and basic error reduction).
        *   Save and load functionality.
    *   Tests for the [`create_autoencoder()`](recursive_training/data/self_supervised_learning.py:1588) factory function to ensure it returns the correct type based on framework availability and configuration.
    *   Tests for [`apply_self_supervised_learning()`](recursive_training/data/self_supervised_learning.py:1646) covering:
        *   Data preprocessing logic (NaN handling, padding, normalization).
        *   Correct parsing of various `data_items` formats.
        *   End-to-end representation generation.
        *   Error handling for invalid inputs or missing libraries.

## 9. Module Architecture and Flow

1.  **Base Class (`AutoencoderModel`):** Defines the interface for autoencoder models ([`fit()`](recursive_training/data/self_supervised_learning.py:51), [`encode()`](recursive_training/data/self_supervised_learning.py:55), [`decode()`](recursive_training/data/self_supervised_learning.py:59), [`save()`](recursive_training/data/self_supervised_learning.py:67), [`load()`](recursive_training/data/self_supervised_learning.py:71)).
2.  **Concrete Implementations:**
    *   [`TensorFlowAutoencoder`](recursive_training/data/self_supervised_learning.py:76): Implements autoencoders using Keras. Builds separate encoder and full autoencoder models. Supports "dense", "lstm", and "conv1d" architectures.
    *   [`PyTorchAutoencoder`](recursive_training/data/self_supervised_learning.py:535): Implements autoencoders using PyTorch. Defines `encoder` and `decoder` as separate `nn.Module` instances, combined into a full `model`. Supports "dense", "lstm", and "conv1d" architectures.
    *   [`SimpleAutoencoder`](recursive_training/data/self_supervised_learning.py:1316): A basic NumPy-based implementation with a feedforward neural network, primarily for fallback.
3.  **Factory Function (`create_autoencoder()`):**
    *   Takes `input_dim`, `latent_dim`, and an optional `config` dictionary.
    *   Determines the framework ("tensorflow", "pytorch", "simple") based on availability and config.
    *   Instantiates and returns the appropriate autoencoder class.
4.  **Main Application Function (`apply_self_supervised_learning()`):**
    *   **Input:** A list of `data_items` (dictionaries containing time series) and a `config` dictionary.
    *   **Preprocessing:**
        *   Extracts time series from `data_items`.
        *   Handles NaN values through interpolation.
        *   Pads or truncates series to a common `input_dim` (median length).
        *   Normalizes each series to the [0, 1] range.
    *   **Model Training:**
        *   Calls [`create_autoencoder()`](recursive_training/data/self_supervised_learning.py:1588) to get a model instance.
        *   Fits the autoencoder on the preprocessed (normalized) data.
    *   **Representation Extraction:**
        *   Uses the trained autoencoder's [`encode()`](recursive_training/data/self_supervised_learning.py:55) method to get latent representations.
    *   **Output:** Returns a dictionary containing model info, series info, and the latent representations for each input series, along with reconstruction error.
5.  **Control Flow for Library Availability:**
    *   Global boolean flags `TF_AVAILABLE` and `TORCH_AVAILABLE` are set at import time.
    *   Implementations raise `ImportError` if their required library is missing.
    *   [`create_autoencoder()`](recursive_training/data/self_supervised_learning.py:1588) and [`apply_self_supervised_learning()`](recursive_training/data/self_supervised_learning.py:1646) have fallback logic to the `SimpleAutoencoder` if preferred frameworks are unavailable.

## 10. Naming Conventions

*   **Classes:** Use PascalCase (e.g., [`AutoencoderModel`](recursive_training/data/self_supervised_learning.py:40), [`TensorFlowAutoencoder`](recursive_training/data/self_supervised_learning.py:76)), which is standard (PEP 8).
*   **Functions and Methods:** Use snake_case (e.g., [`apply_self_supervised_learning()`](recursive_training/data/self_supervised_learning.py:1646), [`_build_dense_autoencoder()`](recursive_training/data/self_supervised_learning.py:151)), also standard. Private methods are correctly prefixed with an underscore.
*   **Variables:** Generally use snake_case (e.g., `latent_dim`, `time_series_data`). Some exceptions for loop variables (e.g., `i`) or common ML abbreviations (e.g., `X` for input data in `SimpleAutoencoder`).
*   **Constants:** Global flags `TF_AVAILABLE` ([`TF_AVAILABLE`](recursive_training/data/self_supervised_learning.py:26)) and `TORCH_AVAILABLE` ([`TORCH_AVAILABLE`](recursive_training/data/self_supervised_learning.py:35)) are uppercase, which is correct.
*   **TensorFlow/Keras Layers:** Variable names for layers often follow Keras conventions (e.g., `inputs`, `x`, `latent`, `outputs`).
*   **PyTorch Modules:** Sub-modules within PyTorch autoencoders (e.g., `lstm_layers`, `fc`) are generally descriptive.
*   **Consistency:** Naming is largely consistent within each class and function.
*   **Potential AI Assumption Errors/Deviations:**
    *   No obvious AI-generated naming errors. The names are generally human-readable and conventional for Python and ML contexts.
    *   The module largely adheres to PEP 8.
    *   The use of `X` for input data and `Z` for pre-activation values in [`SimpleAutoencoder`](recursive_training/data/self_supervised_learning.py:1316) is common in mathematical/ML literature but less descriptive than, say, `input_data`. However, it's confined to that class's internal methods.
    *   The variable `temp_input` in [`TensorFlowAutoencoder.decode()`](recursive_training/data/self_supervised_learning.py:420) is a bit generic but its scope is small.