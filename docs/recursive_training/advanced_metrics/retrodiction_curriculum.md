# Enhanced Retrodiction Curriculum

## Overview

The `EnhancedRetrodictionCurriculum` module, located at [`recursive_training/advanced_metrics/retrodiction_curriculum.py`](../../../../recursive_training/advanced_metrics/retrodiction_curriculum.py), is designed to dynamically select training data for the historical retrodiction process. It aims to improve training efficiency and model performance by focusing on data points that are most informative, particularly those where the model exhibits high uncertainty or where recent performance metrics indicate a decline.

## Purpose

The primary purpose of this module is to implement an intelligent curriculum learning strategy for retrodiction. Instead of using all available historical data uniformly in each training iteration, this curriculum prioritizes data based on:

*   **Model Uncertainty:** Identifies and selects data points where the model is least confident in its predictions.
*   **Performance Degradation:** Adapts the sampling strategy if the model's performance starts to degrade, potentially by re-introducing data that was previously mastered or by increasing the focus on challenging samples.
*   **Cost Control:** Integrates with a cost controller to manage the computational resources used during data selection and training.

By strategically selecting data, the curriculum aims to accelerate learning, improve model robustness, and make efficient use of computational resources.

## Key Components

### `EnhancedRetrodictionCurriculum` Class

This is the main class in the module.

*   **Initialization (`__init__`)**:
    *   Takes an optional configuration dictionary to customize parameters like `uncertainty_threshold_multiplier`, `performance_degradation_threshold`, and `uncertainty_sampling_ratio`.
    *   Initializes a logger, an `EnhancedRecursiveTrainingMetrics` tracker, a data store (currently a `DummyDataStore` for illustrative purposes in the provided code, but intended to connect to `RecursiveDataStore`), and a `CostController`.

*   **`select_data_for_training(...)`**:
    *   This is the core method for selecting the next batch of training data.
    *   It assesses overall training performance and uncertainty using `EnhancedRecursiveTrainingMetrics`.
    *   Calculates an `uncertainty_threshold`.
    *   If a model with `predict` and `predict_proba` methods is provided, it scores data points based on prediction uncertainty (e.g., variance of predicted probabilities).
    *   Prioritizes data:
        *   If performance is degrading, it prioritizes all uncertain data points.
        *   Otherwise, it samples a portion of uncertain data (defined by `uncertainty_sampling_ratio`) and the rest from other data.
    *   Returns a list of selected data points.

*   **`update_curriculum(...)`**:
    *   Adjusts curriculum parameters (like `uncertainty_sampling_ratio` and `uncertainty_threshold_multiplier`) based on recent training performance.
    *   If performance degradation is detected (via `EnhancedRecursiveTrainingMetrics`), it increases the focus on uncertain data.
    *   If performance is stable or improving, it gradually reduces the focus on uncertain data.

*   **`get_curriculum_state()`**:
    *   Returns a dictionary representing the current state of the curriculum parameters.

### `get_data_store()` Function

*   A helper function that currently returns an instance of `DummyDataStore`. In a production environment, this would likely return an instance of `RecursiveDataStore` or a similar interface for accessing the actual historical data.

## Usage

The `EnhancedRetrodictionCurriculum` is typically used within a recursive training loop for historical retrodiction.

1.  **Initialization:** An instance of `EnhancedRetrodictionCurriculum` is created, potentially with custom configuration.
    ```python
    from recursive_training.advanced_metrics.retrodiction_curriculum import EnhancedRetrodictionCurriculum

    config = {
        "uncertainty_threshold_multiplier": 1.8,
        "performance_degradation_threshold": 0.05, # 5%
        "uncertainty_sampling_ratio": 0.4 # 40%
    }
    curriculum = EnhancedRetrodictionCurriculum(config=config)
    ```

2.  **Data Selection:** In each training iteration, `select_data_for_training()` is called to get the next batch of data. This method might require the current model to assess uncertainty.
    ```python
    # Assuming 'model' is the current trained model and 'metrics' are from the last iteration
    # model = get_current_model()
    # recent_metrics = get_last_iteration_metrics()
    # selected_data = curriculum.select_data_for_training(current_iteration=i, recent_metrics=recent_metrics, model=model)
    # train_model_on(selected_data)
    ```
    Refer to the docstring examples in [`recursive_training/advanced_metrics/retrodiction_curriculum.py`](../../../../recursive_training/advanced_metrics/retrodiction_curriculum.py:161) for more detailed usage.

3.  **Curriculum Update:** After evaluating the model's performance on the selected data, `update_curriculum()` is called to adapt the selection strategy for future iterations.
    ```python
    # new_metrics = evaluate_model_performance()
    # curriculum.update_curriculum(current_iteration=i, recent_metrics=new_metrics, model=model)
    ```

Examples demonstrating the use of historical retrodiction components, including how a curriculum might fit into the broader training loop, can be found in the `examples/historical_retrodiction/` directory, such as [`advanced_retrodiction_example.py`](../../../examples/historical_retrodiction/advanced_retrodiction_example.py).

## Relationship to Other Modules

*   **[`recursive_training.data.data_store.RecursiveDataStore`](../../../recursive_training/data/data_store.py):** (Implicitly) The curriculum relies on a data store (currently mocked by `DummyDataStore`) to fetch the pool of historical data from which to select training samples.
*   **[`recursive_training.advanced_metrics.enhanced_metrics.EnhancedRecursiveTrainingMetrics`](../../../recursive_training/advanced_metrics/enhanced_metrics.py):** This module is used to track and retrieve performance summaries, including uncertainty and drift metrics, which are crucial inputs for the curriculum's decision-making process.
*   **[`recursive_training.integration.cost_controller.get_cost_controller`](../../../recursive_training/integration/cost_controller.py):** Used to track the operational costs associated with curriculum selection and updates.
*   **Model (Implicit):** The `select_data_for_training` method can optionally take a `model` object. If provided, and if the model has `predict` and `predict_proba` methods, the curriculum uses it to calculate uncertainty scores for individual data points. This implies an interaction with the model being trained.
*   **Training Orchestrator (e.g., [`recursive_training.run_training.py`](../../../recursive_training/run_training.py) or [`recursive_training.parallel_trainer.py`](../../../recursive_training/parallel_trainer.py)):** The curriculum is designed to be a component within a larger training orchestration system. This system would call the curriculum's methods at appropriate points in the training loop.