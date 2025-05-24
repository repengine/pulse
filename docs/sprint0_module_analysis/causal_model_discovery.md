# Module Analysis: causal_model/discovery.py

## Module Intent/Purpose
The `discovery.py` module serves as an interface for performing causal discovery on a dataset. It aims to utilize optimized implementations of algorithms like PC and FCI to infer the causal structure, represented as a Structural Causal Model (SCM) or Partial Ancestral Graph (PAG).
# Module Analysis: causal_model/discovery.py

## Module Intent/Purpose
The `discovery.py` module serves as an interface for performing causal discovery on a dataset. It aims to utilize optimized implementations of algorithms like PC and FCI to infer the causal structure, represented as a Structural Causal Model (SCM) or Partial Ancestral Graph (PAG).

## Operational Status/Completeness
The module provides the main `CausalDiscovery` class with methods to run the PC and FCI algorithms. It includes logic to check for and utilize optimized implementations from `causal_model.optimized_discovery`. However, the core causal discovery logic for the standard implementation (fallback) is simplified (correlation-based) and not a full implementation of PC or FCI. The completeness depends heavily on the implementation within `causal_model.optimized_discovery` and `causal_model.vectorized_operations`.

## Implementation Gaps / Unfinished Next Steps
- The standard (fallback) implementations of PC and FCI are not complete and rely on simple correlation. Full implementations of these algorithms are needed if the optimized versions are not available or suitable.
- The integration with `causal_model.optimized_discovery` and `causal_model.vectorized_operations` assumes these modules provide the necessary vectorized and optimized causal discovery functions. Their completeness directly impacts this module's functionality.
- More robust error handling and validation of input data and parameters could be added.

## Connections & Dependencies
- **Internal Dependencies:**
    - [`causal_model.structural_causal_model`](causal_model/structural_causal_model.py:1): Used to represent the inferred causal structure.
    - [`causal_model.optimized_discovery`](causal_model/optimized_discovery.py:1): Expected to provide optimized implementations of causal discovery algorithms.
    - [`causal_model.vectorized_operations`](causal_model/vectorized_operations.py:1): Provides vectorized operations used in the discovery process (e.g., conditional independence tests, edge detection).
- **External Dependencies:**
    - `os`: Not directly used in the provided code snippet, but often used in related file operations.
    - `logging`: For logging information and warnings.
    - `pandas`: For data handling (DataFrames).
    - `numpy`: For numerical operations.
    - `typing`: For type hints.
    - `itertools`: Used for generating combinations of variables.

## Function and Class Example Usages

### `CausalDiscovery` Class
Encapsulates causal discovery methods.

```python
import pandas as pd
from causal_model.discovery import CausalDiscovery

# Example DataFrame (replace with actual data loading)
data = pd.DataFrame({
    'A': [1, 2, 3, 4, 5],
    'B': [5, 4, 3, 2, 1],
    'C': [1, 3, 5, 2, 4]
})

# Initialize CausalDiscovery
discovery_engine = CausalDiscovery(data)

# Run PC algorithm
scm_pc = discovery_engine.run_pc(alpha=0.05)
print("SCM from PC:", scm_pc.edges())

# Run FCI algorithm
scm_fci = discovery_engine.run_fci(alpha=0.05)
print("SCM from FCI:", scm_fci.edges())

# Get adjacency matrix
adj_matrix = discovery_engine.get_adjacency_matrix(scm_pc)
print("Adjacency Matrix:\n", adj_matrix)
```

## Hardcoding Issues
No obvious hardcoded secrets or environment variables were found.

## Coupling Points
- Tightly coupled with `StructuralCausalModel`, `OptimizedCausalDiscovery`, and `VectorizedOperations`.
- Depends on the Pandas DataFrame format for input data.
- The fallback implementations are overly simplistic and coupled to basic correlation.

## Existing Tests
Based on the provided file list, there is a [`tests/test_causal_model.py`](tests/test_causal_model.py:1) which likely contains tests for this module and related causal components.

## Module Architecture and Flow
The module is centered around the `CausalDiscovery` class. Upon initialization, it attempts to load an optimized implementation. The `run_pc` and `run_fci` methods serve as the main entry points, directing the execution to the optimized implementation if available, or falling back to a basic implementation. The `get_adjacency_matrix` is a utility method to represent the discovered structure.

## Naming Conventions
Variable, function, and class names generally follow standard Python conventions (snake_case for functions/variables, CamelCase for classes). Names are descriptive and reflect the purpose of the components.

## Overall Assessment
The `discovery.py` module provides a high-level interface for causal discovery, with a clear intention to leverage optimized implementations. However, the standard fallback implementations are incomplete and not representative of true PC or FCI algorithms. The module's effectiveness is currently dependent on the completeness and correctness of the `optimized_discovery` and `vectorized_operations` modules. Further development is needed to provide robust standard implementations or ensure the optimized versions are fully functional.
# Causal Model Discovery Module Analysis

## Module Path

[`causal_model/discovery.py`](causal_model/discovery.py:1)

## Purpose & Functionality

The primary purpose of the [`discovery.py`](causal_model/discovery.py:1) module is to implement and provide access to causal discovery algorithms. These algorithms are designed to infer causal structures (relationships between variables) from observational data. The module supports well-known algorithms such as the PC (Peter-Clark) algorithm and the FCI (Fast Causal Inference) algorithm.

Key functionalities include:
*   Encapsulating causal discovery logic within the [`CausalDiscovery`](causal_model/discovery.py:24) class.
*   Initializing with a `pandas.DataFrame` representing the dataset.
*   Attempting to use optimized, vectorized implementations of discovery algorithms for performance, with fallbacks to standard implementations if optimized versions are unavailable or fail.
*   Running the PC algorithm to infer a Directed Acyclic Graph (DAG) representing causal relationships, returned as a [`StructuralCausalModel`](causal_model/structural_causal_model.py:13).
*   Running the FCI algorithm to infer a Partial Ancestral Graph (PAG), which can represent latent confounders, also returned as a [`StructuralCausalModel`](causal_model/structural_causal_model.py:13) (though a PAG has different edge types).
*   Providing a utility to convert the resulting [`StructuralCausalModel`](causal_model/structural_causal_model.py:13) into an adjacency matrix.

The module plays a crucial role within the `causal_model/` directory by providing the foundational tools for learning the structure of causal models from data, which can then be used for other causal inference tasks like estimating causal effects or counterfactual reasoning.

## Key Components / Classes / Functions

*   **Class: [`CausalDiscovery(data: pd.DataFrame, max_workers: Optional[int] = None)`](causal_model/discovery.py:24)**
    *   **`__init__(self, data: pd.DataFrame, max_workers: Optional[int] = None)`:** Initializes the engine with data and optionally the number of workers for parallel processing. It attempts to load an [`OptimizedCausalDiscovery`](causal_model/optimized_discovery.py:14) engine.
    *   **`run_pc(self, alpha: float = 0.05) -> StructuralCausalModel`](causal_model/discovery.py:51):** Executes the PC algorithm. It prioritizes an optimized/vectorized version from [`OptimizedCausalDiscovery.vectorized_pc_algorithm()`](causal_model/optimized_discovery.py:14) and falls back to a standard implementation using [`batch_edge_detection()`](causal_model/vectorized_operations.py:18) or simple pairwise correlations if the former fails.
    *   **`run_fci(self, alpha: float = 0.05) -> StructuralCausalModel`](causal_model/discovery.py:89):** Executes the FCI algorithm. Similar to `run_pc`, it attempts to use an optimized version ([`OptimizedCausalDiscovery.vectorized_fci_algorithm()`](causal_model/optimized_discovery.py:14)). The fallback implementation uses [`compute_correlation_matrix()`](causal_model/vectorized_operations.py:16) or pairwise correlations to add bidirectional edges.
    *   **`get_adjacency_matrix(self, scm: StructuralCausalModel) -> pd.DataFrame`](causal_model/discovery.py:143):** Converts a given [`StructuralCausalModel`](causal_model/structural_causal_model.py:13) into a pandas DataFrame representing its adjacency matrix.

## Dependencies

### Internal Pulse Modules:
*   [`causal_model.structural_causal_model.StructuralCausalModel`](causal_model/structural_causal_model.py:13)
*   [`causal_model.optimized_discovery.OptimizedCausalDiscovery`](causal_model/optimized_discovery.py:14)
*   [`causal_model.optimized_discovery.get_optimized_causal_discovery`](causal_model/optimized_discovery.py:14)
*   [`causal_model.vectorized_operations.compute_correlation_matrix`](causal_model/vectorized_operations.py:16)
*   [`causal_model.vectorized_operations.batch_conditional_independence_test`](causal_model/vectorized_operations.py:17) (Imported but not directly used in the provided snippet of `CausalDiscovery` class methods, likely used by `OptimizedCausalDiscovery`)
*   [`causal_model.vectorized_operations.batch_edge_detection`](causal_model/vectorized_operations.py:18)
*   [`causal_model.vectorized_operations.optimize_graph_queries`](causal_model/vectorized_operations.py:19) (Imported but not directly used, likely for `OptimizedCausalDiscovery`)

### External Libraries:
*   `os`
*   `logging`
*   `pandas` (as `pd`)
*   `numpy` (as `np`)
*   `typing` (List, Optional, Dict, Any)
*   `itertools`

## SPARC Analysis

*   **Specification:**
    *   The purpose of the module (causal discovery using PC and FCI) is clearly stated in the module docstring ([`causal_model/discovery.py:1-6`](causal_model/discovery.py:1)) and class docstring ([`causal_model/discovery.py:25-28`](causal_model/discovery.py:25)).
    *   The discovery algorithms (PC, FCI) are named.
    *   Key assumptions, like the significance level (`alpha`) for conditional independence tests, are exposed as parameters to the respective methods ([`run_pc()`](causal_model/discovery.py:51), [`run_fci()`](causal_model/discovery.py:89)).

*   **Architecture & Modularity:**
    *   The module is well-structured with the [`CausalDiscovery`](causal_model/discovery.py:24) class encapsulating the core logic.
    *   It demonstrates good modularity by attempting to delegate to an `OptimizedCausalDiscovery` module and providing fallback implementations. This separation allows for independent development and optimization of the core algorithms.
    *   Dependencies on other parts of the `causal_model` (like [`StructuralCausalModel`](causal_model/structural_causal_model.py:13), [`OptimizedCausalDiscovery`](causal_model/optimized_discovery.py:14), and [`vectorized_operations`](causal_model/vectorized_operations.py:15)) are clear.

*   **Refinement - Testability:**
    *   There are no explicit unit tests visible within this file.
    *   The module's design, which allows for injecting data (`pd.DataFrame`), and its reliance on standard interfaces (like those for `OptimizedCausalDiscovery`) suggest it could be testable.
    *   Testability would involve creating synthetic datasets with known causal graphs and verifying that the discovery algorithms can recover them (or aspects of them, given the inherent limitations of causal discovery).
    *   The fallback mechanisms would also need to be tested.

*   **Refinement - Maintainability:**
    *   The code is generally clear, with good use of docstrings for the module, class, and methods.
    *   Type hints are used, which improves readability and helps with static analysis.
    *   Logging ([`logger = logging.getLogger(__name__)`](causal_model/discovery.py:22)) is implemented to provide insights into the execution flow (e.g., whether optimized or standard paths are taken).
    *   The try-except blocks for optimized implementations and vectorized operations enhance robustness but also add to the code paths to maintain.

*   **Refinement - Security:**
    *   No obvious security concerns are apparent from the code. The module primarily performs data processing and algorithmic computations. It does not handle sensitive information directly, engage in network communication, or execute arbitrary code based on external inputs in a way that would typically raise security flags.

*   **Refinement - No Hardcoding:**
    *   The significance level `alpha` for independence tests is parameterized in [`run_pc()`](causal_model/discovery.py:51) and [`run_fci()`](causal_model/discovery.py:89).
    *   The `max_workers` for parallel processing is a parameter in the [`__init__`](causal_model/discovery.py:29) method.
    *   There are no other obvious hardcoded algorithm parameters, significance levels, or model constraints directly visible in the `CausalDiscovery` class. These might exist within the `OptimizedCausalDiscovery` or `vectorized_operations` modules, which are treated as black/grey boxes from this module's perspective.

## Identified Gaps & Areas for Improvement

*   **Fallback FCI Implementation:** The standard fallback implementation for [`run_fci()`](causal_model/discovery.py:89) (lines 115-140) appears to be a very basic version, primarily adding bidirectional edges for pairs of variables whose correlation exceeds `alpha`. A full FCI algorithm involves more complex steps, including orientation rules to identify colliders, and handling of unobserved confounders to produce a PAG. This fallback might be a placeholder or a highly simplified version.
*   **Clarity on PAG Representation:** The FCI algorithm should return a PAG. While the return type is [`StructuralCausalModel`](causal_model/structural_causal_model.py:13), it's not explicitly clear how different edge types of a PAG (e.g., o->, o-o, <->) are represented within the SCM object, which typically implies directed edges. This might be handled by conventions within the `OptimizedCausalDiscovery` or how `StructuralCausalModel` handles edge attributes.
*   **Missing Unit Tests:** The lack of visible unit tests is a significant gap. Robust tests are crucial for validating the correctness of causal discovery algorithms, especially given their complexity and sensitivity to data.
*   **Documentation for Optimized Modules:** While this module tries to use optimized versions, detailed documentation or specifications for [`OptimizedCausalDiscovery`](causal_model/optimized_discovery.py:14) and [`vectorized_operations`](causal_model/vectorized_operations.py:15) would be beneficial for understanding the complete discovery pipeline and its assumptions.
*   **Error Handling in Fallbacks:** The fallback in [`run_pc()`](causal_model/discovery.py:51) (lines 81-85) uses `abs(corr_val) >= alpha`. Typically, `alpha` is a p-value threshold (small values are significant). Using it directly as a correlation threshold might be a simplification or require `alpha` to be interpreted differently in this context (e.g., as a minimum correlation magnitude). This needs clarification. The same applies to the FCI fallback.

## Overall Assessment & Next Steps

The [`causal_model/discovery.py`](causal_model/discovery.py:1) module provides a well-structured entry point for performing causal discovery using PC and FCI algorithms. Its design, which includes attempting to use optimized backends and providing fallbacks, is sound. The code is reasonably clear and maintainable.

**Quality:** Good, with potential for improvement.

**Completeness:** The PC algorithm's interface seems robust. The FCI algorithm's fallback implementation appears incomplete or highly simplified compared to a full FCI. The reliance on external optimized modules means the completeness of the actual discovery process depends heavily on those modules.

**Next Steps:**
1.  **Clarify FCI Implementation:** Investigate the `OptimizedCausalDiscovery.vectorized_fci_algorithm()` and improve the fallback FCI implementation in [`discovery.py`](causal_model/discovery.py:1) if it's intended to be more than a basic correlation check.
2.  **Develop Unit Tests:** Create a comprehensive test suite using synthetic data with known causal graphs to validate both the optimized and standard execution paths of PC and FCI algorithms.
3.  **Review Alpha Interpretation:** Ensure the `alpha` parameter is used consistently and correctly as a significance level in all conditional independence tests, especially in fallback mechanisms. If it's used as a correlation threshold, this should be clearly documented or refactored.
4.  **Document PAG Representation:** Clarify how PAGs (from FCI) are represented using the [`StructuralCausalModel`](causal_model/structural_causal_model.py:13) object, including how different edge types are stored or interpreted.
5.  **Review Dependencies:** Ensure that the external libraries potentially used by optimized versions (e.g., `pgmpy`, `causal-learn`/`cdt`, `networkx`) are correctly managed and documented if they are indeed part of the dependency chain for the optimized paths.
## Operational Status/Completeness
The module provides the main `CausalDiscovery` class with methods to run the PC and FCI algorithms. It includes logic to check for and utilize optimized implementations from `causal_model.optimized_discovery`. However, the core causal discovery logic for the standard implementation (fallback) is simplified (correlation-based) and not a full implementation of PC or FCI. The completeness depends heavily on the implementation within `causal_model.optimized_discovery` and `causal_model.vectorized_operations`.
## Implementation Gaps / Unfinished Next Steps
- The standard (fallback) implementations of PC and FCI are not complete and rely on simple correlation. Full implementations of these algorithms are needed if the optimized versions are not available or suitable.
- The integration with `causal_model.optimized_discovery` and `causal_model.vectorized_operations` assumes these modules provide the necessary vectorized and optimized causal discovery functions. Their completeness directly impacts this module's functionality.
- More robust error handling and validation of input data and parameters could be added.
## Connections & Dependencies
- **Internal Dependencies:**
    - [`causal_model.structural_causal_model`](causal_model/structural_causal_model.py:1): Used to represent the inferred causal structure.
    - [`causal_model.optimized_discovery`](causal_model/optimized_discovery.py:1): Expected to provide optimized implementations of causal discovery algorithms.
    - [`causal_model.vectorized_operations`](causal_model/vectorized_operations.py:1): Provides vectorized operations used in the discovery process (e.g., conditional independence tests, edge detection).
- **External Dependencies:**
    - `os`: Not directly used in the provided code snippet, but often used in related file operations.
    - `logging`: For logging information and warnings.
    - `pandas`: For data handling (DataFrames).
    - `numpy`: For numerical operations.
    - `typing`: For type hints.
    - `itertools`: Used for generating combinations of variables.
## Function and Class Example Usages

### `CausalDiscovery` Class
Encapsulates causal discovery methods.

```python
import pandas as pd
from causal_model.discovery import CausalDiscovery

# Example DataFrame (replace with actual data loading)
data = pd.DataFrame({
    'A': [1, 2, 3, 4, 5],
    'B': [5, 4, 3, 2, 1],
    'C': [1, 3, 5, 2, 4]
})

# Initialize CausalDiscovery
discovery_engine = CausalDiscovery(data)

# Run PC algorithm
scm_pc = discovery_engine.run_pc(alpha=0.05)
print("SCM from PC:", scm_pc.edges())

# Run FCI algorithm
scm_fci = discovery_engine.run_fci(alpha=0.05)
print("SCM from FCI:", scm_fci.edges())

# Get adjacency matrix
adj_matrix = discovery_engine.get_adjacency_matrix(scm_pc)
print("Adjacency Matrix:\n", adj_matrix)
```
## Hardcoding Issues
No obvious hardcoded secrets or environment variables were found.
## Coupling Points
- Tightly coupled with `StructuralCausalModel`, `OptimizedCausalDiscovery`, and `VectorizedOperations`.
- Depends on the Pandas DataFrame format for input data.
- The fallback implementations are overly simplistic and coupled to basic correlation.
## Existing Tests
Based on the provided file list, there is a [`tests/test_causal_model.py`](tests/test_causal_model.py:1) which likely contains tests for this module and related causal components.
## Module Architecture and Flow
The module is centered around the `CausalDiscovery` class. Upon initialization, it attempts to load an optimized implementation. The `run_pc` and `run_fci` methods serve as the main entry points, directing the execution to the optimized implementation if available, or falling back to a basic implementation. The `get_adjacency_matrix` is a utility method to represent the discovered structure.
## Naming Conventions
Variable, function, and class names generally follow standard Python conventions (snake_case for functions/variables, CamelCase for classes). Names are descriptive and reflect the purpose of the components.
## Overall Assessment
The `discovery.py` module provides a high-level interface for causal discovery, with a clear intention to leverage optimized implementations. However, the standard fallback implementations are incomplete and not representative of true PC or FCI algorithms. The module's effectiveness is currently dependent on the completeness and correctness of the `optimized_discovery` and `vectorized_operations` modules. Further development is needed to provide robust standard implementations or ensure the optimized versions are fully functional.
## Module Architecture and Flow
The module is centered around the `CausalDiscovery` class. Upon initialization, it attempts to load an optimized implementation. The `run_pc` and `run_fci` methods serve as the main entry points, directing the execution to the optimized implementation if available, or falling back to a basic implementation. The `get_adjacency_matrix` is a utility method to represent the discovered structure.
## Naming Conventions
Variable, function, and class names generally follow standard Python conventions (snake_case for functions/variables, CamelCase for classes). Names are descriptive and reflect the purpose of the components.
## Overall Assessment
The `discovery.py` module provides a high-level interface for causal discovery, with a clear intention to leverage optimized implementations. However, the standard fallback implementations are incomplete and not representative of true PC or FCI algorithms. The module's effectiveness is currently dependent on the completeness and correctness of the `optimized_discovery` and `vectorized_operations` modules. Further development is needed to provide robust standard implementations or ensure the optimized versions are fully functional.
## Overall Assessment
The `discovery.py` module provides a high-level interface for causal discovery, with a clear intention to leverage optimized implementations. However, the standard fallback implementations are incomplete and not representative of true PC or FCI algorithms. The module's effectiveness is currently dependent on the completeness and correctness of the `optimized_discovery` and `vectorized_operations` modules. Further development is needed to provide robust standard implementations or ensure the optimized versions are fully functional.