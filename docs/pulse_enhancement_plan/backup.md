# Pulse System Enhancement: Specification and Project Plan

## 1. Introduction

This document outlines the specification and project plan for enhancing the Pulse system. It incorporates functional requirements, system reviews, and a sprint-based development approach. A core focus is the implementation of robust **AI Coding Guardrails** to ensure system stability and reliability. The plan emphasizes an "Analysis First" approach, recognizing that many features may have existing scaffolding.

## 2. Guiding Principles

*   **Analysis First:** Thoroughly analyze existing modules before new implementation. The goal is often to "glue the system together."
*   **Modularity & Decoupling:** Strive for loosely coupled modules with clear interfaces to improve maintainability and testability, addressing known architectural concerns.
*   **Iterative Development:** Progress through manageable sprints, delivering verifiable functionality at each stage.
*   **Comprehensive Testing:** Every new or refactored component must have thorough tests (pytest).
*   **Full CLI Capability:** All modules must be accessible and controllable via a comprehensive CLI.
*   **Documentation Standard:** All functions (new or refactored) must include clear docstrings and usage examples.
*   **AI Safety:** Implement and adhere to strict AI Coding Guardrails.
*   **CONTEXT7 MCP Server:** All development sub-tasks assigned to `code` or `debug` modes MUST utilize the `context7` MCP server for up-to-date library information.

## 3. AI Coding Guardrails

The following guardrails MUST be implemented and adhered to throughout the development lifecycle, particularly when AI tools are used for code generation or modification:

1.  **Rigorous Automated Testing:**
    *   **Unit Tests:** Verify the correctness of individual functions and classes.
    *   **Integration Tests:** Ensure that AI-generated/modified code integrates correctly with existing modules.
    *   **Property-Based Tests:** (e.g., using Hypothesis) Define properties that code should satisfy and test with a wide range of inputs, especially useful for catching edge cases common in AI-generated code.
    *   **Specific AI Failure Mode Tests:** Develop tests that target known common failure modes of AI code generation (e.g., off-by-one errors, incorrect handling of nulls/empty collections, overly complex logic).
2.  **Mandatory Human Review Checkpoints:**
    *   All AI-generated or significantly AI-modified code MUST undergo a thorough review by at least one human developer before being merged into main development branches.
    *   Review focus: correctness, adherence to coding standards, security implications, maintainability, and potential for introducing subtle bugs.
3.  **Strict Validation Steps for AI Outputs:**
    *   Before integrating AI-generated code, validate its outputs against predefined criteria or golden datasets.
    *   For AI-generated rules or configurations, simulate their impact in a sandboxed environment before production deployment.
4.  **Specialized Linters & Static Analysis:**
    *   Utilize linters (e.g., Pylint, Flake8) and static analysis tools (e.g., SonarQube, Bandit for security) configured with strict rules.
    *   Explore or develop custom linting rules to catch patterns indicative of common AI errors if standard tools are insufficient.
5.  **Clear Rollback Plans:**
    *   Ensure all AI-driven changes are committed with clear, atomic commits.
    *   Maintain robust version control practices (e.g., feature branches) to allow for easy rollback of problematic changes.
    *   For critical systems, consider blue/green deployment or canary releases for AI-driven updates.
6.  **Modular Design & Isolation:**
    *   Design modules to encapsulate AI-generated components, limiting their potential blast radius.
    *   Define clear, stable interfaces for these modules. This allows AI-generated components to be updated or replaced with minimal impact on the rest of the system.
7.  **Monitoring and Alerting:**
    *   Implement monitoring for components heavily reliant on AI-generated code to detect unexpected behavior or performance degradation post-deployment.
    *   Set up alerts for critical failures or deviations from expected behavior.
8.  **Documentation of AI Involvement:**
    *   Clearly document where and how AI tools were used in the development of a component. This aids in future debugging and understanding.

## 4. Sprint Plan

The project will be broken down into the following sprints. Each sprint aims for a 2-4 week duration, adjustable based on complexity and findings during the analysis phase.

---

### Sprint 0: Foundation, Analysis & Stabilization

*   **Objective:** Establish a stable baseline for development. Conduct a thorough analysis of the existing codebase, address critical test failures, and formalize AI guardrail protocols and initial tooling.
*   **Scope & Constraints:**
    *   Full codebase review, focusing on modules relevant to upcoming sprints (hardcoding, Bayesian logic, AI rules, core systems).
    *   Identify and prioritize fixing the most critical failing tests (aim to significantly reduce the "24 failing tests" count).
    *   Document detailed AI Guardrail protocols, select/configure initial linting and static analysis tools.
    *   No new feature development.
*   **Potential Challenges & Dependencies:**
    *   Complexity of the existing codebase.
    *   Difficulty in diagnosing and fixing long-standing test failures.
    *   Setting up and configuring new analysis tools.
*   **Suggested SPARC Mode(s):** `architect` (for codebase review), `debug` (for test fixing), `docs-writer` (for guardrail documentation).
*   **High-Level Pseudocode/Integration Points:**
    ```
    // Phase 1: Codebase Analysis
    FUNCTION analyze_codebase(modules_to_review)
      // TEST: Ensure all specified modules are reviewed and key areas of concern documented.
      FOR each module IN modules_to_review
        identify_coupling_points()
        identify_hardcoded_elements_locations()
        review_existing_tests()
        document_module_architecture_and_flow()
      ENDFOR
      generate_analysis_report()
    ENDFUNCTION

    // Phase 2: Test Stabilization
    FUNCTION stabilize_tests(test_suite)
      // TEST: Verify that a target percentage of critical tests are passing.
      identify_failing_tests(test_suite)
      prioritize_critical_failures()
      FOR each critical_failure
        diagnose_root_cause()
        implement_fix()
        verify_fix_and_no_regressions()
      ENDFOR
    ENDFUNCTION

    // Phase 3: AI Guardrail Setup
    FUNCTION setup_ai_guardrails()
      // TEST: Confirm selected linting/static analysis tools are configured and run on a sample module.
      document_ai_review_process()
      document_ai_validation_steps()
      configure_linters_and_static_analysis_tools()
      define_rollback_strategy_template()
    ENDFUNCTION
    ```
*   **TDD Anchors:**
    *   `// TEST: Codebase analysis report identifies key areas for refactoring hardcoded elements.`
    *   `// TEST: At least 50% of previously failing critical tests now pass.`
    *   `// TEST: AI Guardrail documentation is complete and approved.`
    *   `// TEST: Selected static analysis tools successfully scan the 'core' module and report findings.`

---

### Sprint 1: Refactoring Hardcoded Elements (Part 1 - Symbolism & Variables)

*   **Objective:** Identify and refactor hardcoded symbolism (including financial symbols like MSFT, IBIT) and other variables throughout the Pulse system, moving towards dynamic configuration.
*   **Scope & Constraints:**
    *   Systematic scan of the codebase for hardcoded symbols and variables.
    *   Design and implement a dynamic configuration mechanism (e.g., extending `core/pulse_config.py` or a new configuration service).
    *   Refactor identified instances to use the new dynamic configuration.
    *   Ensure no disruption to existing functionality.
    *   Adhere to AI Guardrail protocols if AI tools assist in identification or refactoring.
*   **Potential Challenges & Dependencies:**
    *   Widespread use of hardcoded values.
    *   Ensuring the new configuration system is robust and easy to use.
    *   Dependency on Sprint 0 for a stable codebase.
*   **Suggested SPARC Mode(s):** `code` (for refactoring), `architect` (for configuration system design), `tdd` (for testing new configurations).
*   **High-Level Pseudocode/Integration Points:**
    ```
    FUNCTION identify_hardcoded_elements(codebase_path, patterns_to_search)
      // TEST: Ensure a comprehensive list of hardcoded symbols and variables is generated.
      hardcoded_list = []
      FOR each file IN codebase_path
        IF file matches_code_file_type
          scan_file_for_patterns(file, patterns_to_search, hardcoded_list)
        ENDIF
      ENDFOR
      RETURN hardcoded_list
    ENDFUNCTION

    FUNCTION implement_dynamic_config_system(config_schema)
      // TEST: Verify config system can load, validate, and provide various data types.
      // TEST: Ensure financial symbols (e.g., MSFT) can be loaded from config.
      // ... (design for loading from file, env vars, etc.)
    ENDFUNCTION

    FUNCTION refactor_hardcoded_instance(file_path, line_number, old_value, config_key)
      // TEST: Check that a specific hardcoded value is replaced by a config lookup.
      replace_hardcoded_value_with_config_lookup(file_path, line_number, old_value, config_key)
    ENDFUNCTION
    ```
*   **TDD Anchors:**
    *   `// TEST: Financial symbols (MSFT, IBIT, SPY, NVDA) are loaded from a configuration file, not hardcoded.`
    *   `// TEST: A sample module's hardcoded variable is successfully refactored to use the dynamic config system.`
    *   `// TEST: Configuration system supports various data types (string, int, float, list, dict).`
    *   `// TEST: Attempting to access a non-existent config key raises an appropriate error.`

---

### Sprint 2: Refactoring Hardcoded Elements (Part 2 - Secrets Management)

*   **Objective:** Identify and implement secure management for any hardcoded secrets (API keys, database credentials, etc.).
*   **Scope & Constraints:**
    *   Thorough audit of the codebase for hardcoded secrets.
    *   Select and implement a secrets management strategy (e.g., environment variables, HashiCorp Vault, AWS Secrets Manager).
    *   Refactor code to retrieve secrets from the chosen secure source.
    *   Ensure secrets are not logged or exposed.
    *   Strict adherence to AI Guardrail protocols, especially human review for any AI-assisted changes in this area.
*   **Potential Challenges & Dependencies:**
    *   Ensuring all secrets are identified.
    *   Complexity of integrating with a secrets management tool.
    *   Securely managing secrets in development, testing, and production environments.
*   **Suggested SPARC Mode(s):** `security-review` (for audit and strategy selection), `code` (for implementation), `devops` (for infrastructure setup if using a vault).
*   **High-Level Pseudocode/Integration Points:**
    ```
    FUNCTION audit_for_secrets(codebase_path, secret_patterns)
      // TEST: Ensure audit identifies known types of secrets (API keys, passwords).
      identified_secrets = []
      // ... (similar to identify_hardcoded_elements but focused on secret patterns)
      RETURN identified_secrets
    ENDFUNCTION

    FUNCTION initialize_secret_manager(type, config) // type e.g., "env_var", "vault"
      // TEST: Secret manager can connect and retrieve a test secret.
      // ...
    ENDFUNCTION

    FUNCTION get_secret(secret_name)
      // TEST: Retrieve a known secret successfully.
      // TEST: Attempting to retrieve a non-existent secret returns null or raises error.
      FROM secret_manager retrieve secret_value
      RETURN secret_value
    ENDFUNCTION

    FUNCTION refactor_to_use_secret_manager(file_path, old_secret_usage, secret_name)
      // TEST: Verify hardcoded secret is replaced by call to get_secret().
      replace_hardcoded_secret_with_get_secret_call(file_path, old_secret_usage, secret_name)
    ENDFUNCTION
    ```
*   **TDD Anchors:**
    *   `// TEST: API keys are retrieved via the chosen secret management solution, not hardcoded.`
    *   `// TEST: Attempting to run a module requiring a secret without it configured fails gracefully.`
    *   `// TEST: Secrets are not present in log outputs.`
    *   `// TEST: Code audit confirms no new hardcoded secrets are introduced.`

---

### Sprint 3: Bayesian Integration & Confidence Bands

*   **Objective:** Apply Bayesian updating principles and confidence bands to all relevant variables and metrics within the Pulse system, enhancing uncertainty quantification.
*   **Scope & Constraints:**
    *   Review existing [`recursive_training/metrics/bayesian_adapter.py`](recursive_training/metrics/bayesian_adapter.py) and other relevant metrics/trust modules.
    *   Identify all variables and metrics where Bayesian updating and confidence bands are applicable (e.g., forecasts, trust scores, rule performance).
    *   Implement or extend Bayesian updating mechanisms.
    *   Calculate and store confidence bands (e.g., using bootstrap resampling or analytical methods where appropriate).
    *   Ensure outputs (CLI, logs, potential UI) can represent these confidence intervals.
    *   Adhere to AI Guardrail protocols.
*   **Potential Challenges & Dependencies:**
    *   Complexity of Bayesian statistics.
    *   Performance implications of Bayesian calculations.
    *   Integrating confidence bands into existing data structures and reporting.
    *   Dependency on Sprint 0 for stable metrics modules.
*   **Suggested SPARC Mode(s):** `code` (specializing in statistical programming), `architect` (for integration design), `tdd`.
*   **High-Level Pseudocode/Integration Points:**
    ```
    // Potentially extending BayesianAdapter or creating new components
    CLASS BayesianUpdater
      METHOD constructor(prior_distribution)
        // ...
      ENDMETHOD

      METHOD update(observed_data)
        // TEST: Posterior distribution correctly updated given new data.
        // ... (Bayes' theorem application)
        calculate_confidence_band(alpha_level)
        RETURN posterior_distribution, confidence_interval
      ENDMETHOD

      METHOD get_confidence_band(alpha_level)
        // TEST: Confidence band matches expected range for a known distribution.
        // ...
      ENDMETHOD
    ENDCLASS

    FUNCTION apply_bayesian_to_forecast(forecast_value, historical_data, prior_info)
      // TEST: Forecast output includes a value and a confidence interval.
      updater = NEW BayesianUpdater(prior_info)
      posterior, interval = updater.update(historical_data + forecast_value)
      RETURN forecast_value_from_posterior, interval
    ENDFUNCTION
    ```
*   **TDD Anchors:**
    *   `// TEST: A core forecast output now includes a 95% confidence interval.`
    *   `// TEST: Trust scores are updated using Bayesian methods and have associated confidence bands.`
    *   `// TEST: Performance of a rule in the AI rule system is reported with a confidence interval.`
    *   `// TEST: BayesianAdapter correctly updates priors based on new evidence.`

---

### Sprint 4: AI Rule System & Training/Evaluation Pipeline

*   **Objective:** Implement AI rule generation capabilities and a robust training/evaluation pipeline for these rules, building upon existing patterns like the GPT-Symbolic Feedback Loop.
*   **Scope & Constraints:**
    *   Design the AI rule generation process (e.g., using LLMs, genetic algorithms, or other ML techniques).
    *   Develop a pipeline for training rule generation models (if applicable).
    *   Develop a pipeline for evaluating generated rules (metrics: accuracy, coverage, interpretability, F1 score with confidence bands from Sprint 3).
    *   Integrate with the existing hybrid rules system and GPT-Symbolic feedback loop.
    *   Ensure the pipeline is auditable and rules are versioned.
    *   Strict adherence to AI Guardrails, especially for rule validation and human review.
    *   Utilize `context7` MCP server for library information.
*   **Potential Challenges & Dependencies:**
    *   Complexity of designing effective rule generation algorithms.
    *   Ensuring generated rules are meaningful and not just overfitting.
    *   Building a scalable and efficient training/evaluation pipeline.
    *   Dependency on Sprint 3 for confidence-banded evaluation metrics.
*   **Suggested SPARC Mode(s):** `architect` (for pipeline design), `code` (for implementation, ML expertise), `tdd`, `mcp` (for `context7`).
*   **High-Level Pseudocode/Integration Points:**
    ```
    FUNCTION generate_ai_rules(input_data, existing_rules, generation_params)
      // TEST: Generated rules adhere to a predefined structural schema.
      // ... (logic for rule generation, possibly involving LLM calls or other ML models)
      // TEST: Ensure generated rules are novel or significant improvements over existing ones.
      RETURN new_candidate_rules
    ENDFUNCTION

    FUNCTION train_rule_generation_model(training_data, model_config) // If applicable
      // TEST: Training process completes and model achieves a baseline performance.
      // ...
    ENDFUNCTION

    FUNCTION evaluate_rules(rules_to_evaluate, evaluation_data, metrics_config)
      // TEST: Evaluation produces standard metrics (accuracy, F1) with confidence intervals.
      // ... (apply rules to data, calculate performance, including confidence from Sprint 3)
      // TEST: Rules flagged as low-confidence or poor-performing are identified.
      RETURN evaluation_results
    ENDFUNCTION

    FUNCTION rule_pipeline_orchestrator()
      // TEST: Full pipeline runs end-to-end from data to evaluated/refined rules.
      candidate_rules = generate_ai_rules(...)
      evaluated_rules = evaluate_rules(candidate_rules, ...)
      refined_rules = apply_gpt_symbolic_feedback(evaluated_rules, ...) // Leverage existing pattern
      store_and_version_rules(refined_rules)
    ENDFUNCTION
    ```
*   **TDD Anchors:**
    *   `// TEST: AI rule generation produces at least one valid new rule from sample data.`
    *   `// TEST: Rule evaluation pipeline correctly calculates F1 score with confidence interval for a set of test rules.`
    *   `// TEST: GPT-Symbolic feedback loop successfully refines a candidate AI-generated rule.`
    *   `// TEST: Generated rules are stored and versioned correctly in the rule repository.`

---

### Sprint 5: Data Storage Uniformity & Full Dockerization

*   **Objective:** Ensure data storage uniformity across all Pulse modules and achieve full Dockerization of the system for cloud-readiness and reproducible environments.
*   **Scope & Constraints:**
    *   Review current data storage mechanisms across all modules (building on recent work like `OptimizedDataStore`, `StreamingDataStore`, `S3DataStore`).
    *   Define and implement a unified data storage strategy/interface if gaps exist.
    *   Create Dockerfiles for all Pulse modules and a Docker Compose setup for local development and testing.
    *   Ensure Docker images are optimized for size and security.
    *   Test Dockerized application thoroughly.
    *   Adhere to AI Guardrail protocols for any AI-assisted Dockerfile generation.
*   **Potential Challenges & Dependencies:**
    *   Diverse data storage needs of different modules.
    *   Complexity of Dockerizing a multi-module system.
    *   Ensuring inter-container communication and data sharing.
*   **Suggested SPARC Mode(s):** `architect` (for data storage strategy), `devops` (for Dockerization), `code` (for refactoring storage access), `tdd`.
*   **High-Level Pseudocode/Integration Points:**
    ```
    FUNCTION define_unified_data_interface()
      // TEST: Interface supports common operations (read, write, query, list) for key data types.
      // ... (define abstract methods/properties)
    ENDFUNCTION

    FUNCTION adapt_module_to_unified_storage(module_name, storage_interface)
      // TEST: A specific module (e.g., forecast_engine) correctly uses the unified storage interface.
      // ... (refactor module's data access logic)
    ENDFUNCTION

    // Dockerfile example structure (per module or for the whole system)
    // FROM base_python_image
    // WORKDIR /app
    // COPY requirements.txt .
    // RUN pip install -r requirements.txt
    // COPY . .
    // CMD ["python", "module_entrypoint.py"]
    // TEST: Docker image for 'core' module builds successfully.
    // TEST: Dockerized 'simulation_engine' can run a basic simulation.

    // Docker Compose example structure
    // version: '3.8'
    // services:
    //   pulse_core:
    //     build: ./core
    //   pulse_simulation:
    //     build: ./simulation_engine
    //     depends_on:
    //       - pulse_core
    // ...
    // TEST: `docker-compose up` starts all essential Pulse services without errors.
    ```
*   **TDD Anchors:**
    *   `// TEST: All major modules utilize a common interface for primary data storage operations.`
    *   `// TEST: The entire Pulse application can be started using Docker Compose.`
    *   `// TEST: A core simulation workflow runs successfully within the Dockerized environment.`
    *   `// TEST: Docker images are scanned for vulnerabilities and meet a defined security baseline.`

---

### Sprint 6: Core Systems Review & Integration (Recursive Systems)

*   **Objective:** Conduct a full review of recursive-training, learning, memory, and intelligence systems. Provide analysis, recommendations for integration, and enhancements, focusing on "gluing the system together."
*   **Scope & Constraints:**
    *   In-depth analysis of `recursive_training/`, `learning/`, `memory/`, and `intelligence/` modules.
    *   Identify areas of overlap, inconsistency, or poor integration.
    *   Develop recommendations for tighter integration and improved data flow between these systems.
    *   Implement high-priority integration enhancements.
    *   Focus on leveraging existing functionalities and patterns (e.g., GPT-Symbolic Feedback Loop, curriculum testing).
    *   Adhere to AI Guardrail protocols.
    *   Utilize `context7` MCP server.
*   **Potential Challenges & Dependencies:**
    *   High complexity and interconnectedness of these core systems.
    *   Potential for significant refactoring to achieve better integration.
    *   Ensuring changes don't negatively impact existing functionalities.
*   **Suggested SPARC Mode(s):** `architect` (for system analysis and redesign), `code` (for implementation), `tdd`, `mcp` (for `context7`).
*   **High-Level Pseudocode/Integration Points:**
    ```
    FUNCTION analyze_recursive_systems(modules_list)
      // TEST: Analysis report clearly identifies at least 3 key integration points or redundancies.
      FOR each module IN modules_list
        map_data_inputs_outputs()
        identify_dependencies_on_other_systems()
        review_internal_logic_and_state_management()
      ENDFOR
      document_current_system_interactions()
      propose_integration_enhancements_and_refactoring_plan()
    ENDFUNCTION

    FUNCTION implement_recursive_system_integration(change_plan)
      // TEST: A specific data flow between 'learning' and 'memory' is streamlined as per plan.
      // ... (apply refactoring based on the plan, focusing on interfaces and data exchange)
    ENDFUNCTION
    ```
*   **TDD Anchors:**
    *   `// TEST: Data generated by the 'recursive_training' module is seamlessly consumed by the 'learning' module.`
    *   `// TEST: The 'intelligence' module correctly utilizes information from the 'memory' system for a decision-making task.`
    *   `// TEST: Refactoring of a shared component between 'learning' and 'recursive_training' passes all existing tests for both.`
    *   `// TEST: A documented redundancy between two recursive systems has been eliminated.`

---

### Sprint 7: Symbolic System Review & Integration

*   **Objective:** Review the existing [`symbolic_system/`](symbolic_system/) (including [`symbolic_system/pulse_symbolic_learning_loop.py`](symbolic_system/pulse_symbolic_learning_loop.py) and [`symbolic_system/gravity/test_residual_gravity_engine.py`](tests/symbolic_system/gravity/test_residual_gravity_engine.py)). Determine its future (deprecation or integration), particularly concerning the "gravity smoothing equation," and ensure it doesn't negatively impact variable simulations.
*   **Scope & Constraints:**
    *   Detailed analysis of the `symbolic_system/` codebase, its current state (Symbolic Pillar Gravity Fabric), and its interactions.
    *   Evaluate the effectiveness and necessity of the "gravity smoothing equation" and overall symbolic approach.
    *   Decision: Deprecate, refactor for better integration, or enhance the symbolic system.
    *   If integrating/enhancing, ensure clear interfaces and testable interactions with simulation and forecasting.
    *   If deprecating, ensure safe removal and update dependent modules.
    *   Adhere to AI Guardrail protocols.
    *   Utilize `context7` MCP server.
*   **Potential Challenges & Dependencies:**
    *   Complexity of the symbolic concepts and their implementation.
    *   Making an objective decision about deprecation vs. integration.
    *   Ensuring no adverse effects on simulation accuracy if changes are made.
*   **Suggested SPARC Mode(s):** `architect` (for review and decision), `code` (for implementation), `tdd`, `mcp` (for `context7`).
*   **High-Level Pseudocode/Integration Points:**
    ```
    FUNCTION review_symbolic_system()
      // TEST: Review produces a clear recommendation (deprecate, integrate, enhance) with justifications.
      analyze_code_quality_and_maintainability('symbolic_system/')
      evaluate_impact_on_simulations('gravity_smoothing_equation')
      assess_alignment_with_overall_pulse_goals()
      document_findings_and_recommendation()
    ENDFUNCTION

    IF recommendation IS "integrate" OR "enhance"
      FUNCTION integrate_or_enhance_symbolic_system(plan)
        // TEST: Symbolic system correctly modifies a forecast based on gravity equation.
        // TEST: `test_residual_gravity_engine.py` passes after changes.
        // ... (refactor interfaces, improve logic, add tests)
      ENDFUNCTION
    ELSE IF recommendation IS "deprecate"
      FUNCTION deprecate_symbolic_system()
        // TEST: Symbolic system code is removed, and dependent systems are updated or fail gracefully.
        identify_dependent_modules()
        remove_symbolic_system_code()
        refactor_or_update_dependent_modules()
      ENDFUNCTION
    ENDIF
    ```
*   **TDD Anchors:**
    *   `// TEST: Decision on symbolic system (deprecate/integrate/enhance) is documented with clear rationale.`
    *   `// TEST: If integrated, the symbolic system's gravity smoothing correctly adjusts a set of test simulations.`
    *   `// TEST: If integrated, `pulse_symbolic_learning_loop.py` functions as expected within the larger system.`
    *   `// TEST: If deprecated, no critical system relies on the removed symbolic components, and all tests pass.`
    *   `// TEST: `test_residual_gravity_engine.py` continues to pass or is appropriately updated/removed.`

---

### Sprint 8: Trust System Review & Enhancement

*   **Objective:** Conduct a thorough review of the [`trust_system/`](trust_system/) (including [`tests/test_bayesian_trust_tracker.py`](tests/test_bayesian_trust_tracker.py)) and plan for its enhancement or integration with other systems like Bayesian updating and AI rule evaluation.
*   **Scope & Constraints:**
    *   Detailed analysis of the `trust_system/` codebase and its current functionalities.
    *   Identify opportunities for enhancement (e.g., more sophisticated trust metrics, better integration with Bayesian confidence).
    *   Plan and implement chosen enhancements.
    *   Ensure trust scores are utilized effectively in forecast aggregation and rule evaluation.
    *   Adhere to AI Guardrail protocols.
    *   Utilize `context7` MCP server.
*   **Potential Challenges & Dependencies:**
    *   Defining "trust" in a quantifiable and meaningful way.
    *   Integrating trust metrics with other complex systems.
    *   Dependency on Sprint 3 (Bayesian Integration).
*   **Suggested SPARC Mode(s):** `architect` (for review and enhancement design), `code` (for implementation), `tdd`, `mcp` (for `context7`).
*   **High-Level Pseudocode/Integration Points:**
    ```
    FUNCTION review_trust_system()
      // TEST: Review identifies at least two concrete areas for enhancement or better integration.
      analyze_code_quality_and_current_metrics('trust_system/')
      evaluate_integration_with_forecasting_and_rules()
      propose_enhancements_or_new_integration_points() // e.g., use confidence bands in trust calculation
    ENDFUNCTION

    FUNCTION enhance_trust_system(enhancement_plan)
      // TEST: Trust score calculation incorporates Bayesian confidence from Sprint 3.
      // TEST: `test_bayesian_trust_tracker.py` passes after changes.
      // ... (implement new metrics, refactor existing logic, improve interfaces)
    ENDFUNCTION
    ```
*   **TDD Anchors:**
    *   `// TEST: Trust scores for data sources are updated based on new evidence and Bayesian principles.`
    *   `// TEST: Forecasts from low-trust sources are appropriately down-weighted in an ensemble forecast.`
    *   `// TEST: The `test_bayesian_trust_tracker.py` suite passes with any new enhancements.`
    *   `// TEST: AI-generated rules are assigned trust scores based on their evaluation performance.`

---

### Sprint 9: Full CLI Implementation

*   **Objective:** Develop FULL CLI capabilities for all Pulse modules, with considerations for future chatmode or GUI integration at each CLI step.
*   **Scope & Constraints:**
    *   Design a consistent and user-friendly CLI structure (e.g., using `click` or `argparse`).
    *   Implement CLI commands for all key functionalities of each module (simulation, forecasting, training, data management, etc.).
    *   Ensure CLI commands provide clear output and error handling.
    *   Document all CLI commands and their usage.
    *   Design CLI commands with future extensibility for chatmode/GUI in mind (e.g., by having underlying functions that CLI/chat/GUI can all call).
    *   Adhere to AI Guardrail protocols.
*   **Potential Challenges & Dependencies:**
    *   Defining a comprehensive set of CLI commands for a complex system.
    *   Ensuring consistency across different modules' CLIs.
    *   Making the CLI user-friendly for complex operations.
*   **Suggested SPARC Mode(s):** `architect` (for CLI design), `code` (for implementation), `docs-writer` (for CLI documentation), `tdd`.
*   **High-Level Pseudocode/Integration Points:**
    ```
    // Main CLI entry point (e.g., pulse_cli.py)
    FUNCTION main_cli_handler(command, subcommand, options)
      // TEST: `pulse_cli run simulation --config my_sim.json` executes a simulation.
      // TEST: `pulse_cli train rule_model --data recent_data.csv` starts rule model training.
      SWITCH command
        CASE "run":
          handle_run_subcommand(subcommand, options) // e.g., simulation, forecast
        CASE "train":
          handle_train_subcommand(subcommand, options) // e.g., rule_model, forecast_model
        CASE "manage":
          handle_manage_subcommand(subcommand, options) // e.g., data, config, secrets
        // ... etc.
      ENDSWITCH
    ENDFUNCTION

    // Example module-specific CLI function
    FUNCTION cli_run_simulation(config_path, output_dir)
      // This function is called by the main CLI handler
      // It wraps the core simulation logic
      // TEST: Ensure simulation output is correctly placed in output_dir.
      core_simulation_logic(config_path, output_dir)
      print_simulation_summary()
    ENDFUNCTION
    ```
*   **TDD Anchors:**
    *   `// TEST: CLI command to run a full simulation executes successfully and produces expected output files.`
    *   `// TEST: CLI command to initiate recursive AI training for rules starts the process.`
    *   `// TEST: CLI command to manage (e.g., list, add) financial symbols in the configuration works.`
    *   `// TEST: CLI provides helpful error messages for invalid commands or options.`
    *   `// TEST: All major module functionalities are accessible via a documented CLI command.`

---

### Sprint 10: Comprehensive Testing (Pytest) & Documentation

*   **Objective:** Implement comprehensive tests (using pytest) for every module, including those addressing AI guardrails. Finalize documentation for all functions.
*   **Scope & Constraints:**
    *   Write unit, integration, and where applicable, property-based tests for all Pulse modules.
    *   Ensure test coverage meets a predefined target (e.g., 80-90%).
    *   Specifically include tests for AI guardrail compliance (e.g., testing AI-generated components against known failure modes).
    *   Ensure all tests pass consistently.
    *   Complete docstrings and usage examples for all public functions and classes across the codebase.
    *   This sprint runs in parallel or as a final validation stage for features developed in other sprints.
*   **Potential Challenges & Dependencies:**
    *   Achieving high test coverage for a complex system.
    *   Writing effective tests for AI-driven components.
    *   Time-consuming nature of writing comprehensive tests and documentation.
    *   Dependent on all other sprints for feature completeness.
*   **Suggested SPARC Mode(s):** `tdd` (for test writing), `code` (for implementing missing tests), `docs-writer` (for documentation), `security-review` (to ensure tests cover security aspects).
*   **High-Level Pseudocode/Integration Points:**
    ```
    FUNCTION write_module_tests(module_path, test_coverage_target)
      // TEST: Test suite for 'core' module achieves >85% line coverage.
      FOR each component IN module
        write_unit_tests(component)
        write_integration_tests_for_component_interactions(component)
        IF component_is_ai_driven OR uses_ai_generated_code
          write_ai_guardrail_tests(component) // e.g., robustness to unexpected inputs
        ENDIF
      ENDFOR
      run_tests_and_generate_coverage_report()
    ENDFUNCTION

    FUNCTION document_function(function_signature, file_path)
      // TEST: A sample function in 'forecast_engine' has a complete docstring with an example.
      generate_docstring_template()
      add_parameter_descriptions()
      add_return_description()
      add_usage_example()
      // ... (ensure adherence to project's docstring format e.g. Google, NumPy)
    ENDFUNCTION
    ```
*   **TDD Anchors:**
    *   `// TEST: Overall project test coverage exceeds 85%.`
    *   `// TEST: All AI-related modules have specific guardrail tests implemented and passing.`
    *   `// TEST: All public functions in a critical module (e.g., `simulation_engine`) have complete docstrings with usage examples.`
    *   `// TEST: `pytest` runs successfully with no failing tests across the entire project.`
    *   `// TEST: Sprint completion criteria (working functionality, tests, CLI, verifiable I/O) are met for all major features.`

---

## 5. Prioritization Recommendations

1.  **Sprint 0: Foundation, Analysis & Stabilization:** Absolutely critical to start here. A stable, understood baseline is essential.
2.  **Sprint 1 & 2: Refactoring Hardcoded Elements:** Addresses fundamental code quality and security issues.
3.  **Sprint 5: Data Storage Uniformity & Full Dockerization (Part 1 - Docker Basics):** Early Dockerization helps with reproducible environments for all subsequent sprints. Data uniformity can be phased.
4.  **Sprint 10: Comprehensive Testing & Documentation (Ongoing):** While listed as a later sprint for "finalization," test and documentation development should be an ongoing activity within *each* sprint. This sprint represents a final sweep and coverage push.
5.  **Sprint 3: Bayesian Integration & Confidence Bands:** Foundational for robust metrics in other areas (AI rules, trust).
6.  **Sprint 6, 7, 8: Core Systems Reviews (Recursive, Symbolic, Trust):** These analytical sprints can run somewhat in parallel after Sprint 0, informing subsequent implementation.
7.  **Sprint 4: AI Rule System & Training/Evaluation Pipeline:** Builds on stabilized systems and Bayesian metrics.
8.  **Sprint 9: Full CLI Implementation:** Can be developed incrementally as modules are stabilized/enhanced.
9.  **Sprint 5: Data Storage Uniformity (Part 2 - Full Uniformity):** Can be completed after core functionalities are stable.

## 6. Further Information / Clarifications Needed

While the provided information is comprehensive, the following clarifications would be beneficial:

1.  **Specifics of "Hardcoded Symbolism":** Beyond financial symbols, are there other categories of "symbolism" that are hardcoded and need refactoring? Examples would be helpful.
2.  **Preferred Secrets Management Solution:** Is there a preferred solution (env vars, specific vault tech) for secrets management, or is this to be determined during Sprint 2?
3.  **Existing "Gravity Smoothing Equation":** Could you point to the specific file/lines where the current "gravity smoothing equation" is implemented or defined, to aid in its review during Sprint 7?
4.  **Priority within "Recursive Systems Review" (Sprint 6):** Are there specific sub-modules within `recursive-training/`, `learning/`, `memory/`, or `intelligence/` that are of higher concern or priority for review and integration?
5.  **Definition of "Data Storage Uniformity":** What are the key criteria for uniformity? Is it about using a single database type, a common abstraction layer, standardized schemas, or something else?
6.  **Current State of `pytest` Tests:** While "24 failing tests" was mentioned, an up-to-date `pytest -q` summary or a list of the most problematic test files would help prioritize in Sprint 0. (User has indicated this might not be easily available, which is understood).
7.  **Access to `context7` MCP Server:** Confirmation of how SPARC modes will interface with `context7` (e.g., API details, tool name if it's a `use_mcp_tool` scenario) would be useful for planning sub-tasks.

This plan provides a structured approach to enhancing the Pulse system. Flexibility will be key, and findings in earlier sprints (especially Sprint 0) will likely refine the scope and tasks of later sprints.