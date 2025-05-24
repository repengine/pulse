# Module Analysis: `recursive_training.rules.rule_repository`

## 1. Module Intent/Purpose

The primary role of the [`recursive_training.rules.rule_repository`](recursive_training/rules/rule_repository.py:) module is to provide a persistent repository for managing rules within the recursive training system. Its responsibilities include storing rules to disk, versioning them, tracking their history, and allowing them to be queried based on various criteria such as type and status. It also handles rule activation, deactivation, validation, and provides backup and restore capabilities.

## 2. Operational Status/Completeness

The module appears largely complete for its core defined functionalities. It implements comprehensive CRUD (Create, Read, Update, Delete) operations for rules, along with version control, status management ([`RuleStatus`](recursive_training/rules/rule_repository.py:28)), and a backup/restore mechanism.

However, there are a few areas with placeholders or basic implementations:
- **Rule Validation:** The [`_validate_rule()`](recursive_training/rules/rule_repository.py:208) method includes a comment: `# Add more validation rules as needed...` (line 242), suggesting that more sophisticated validation logic was envisioned.
- **Usage Tracking:** The [`_track_rule_access()`](recursive_training/rules/rule_repository.py:469) method is a placeholder (lines 471-474), indicating that detailed rule usage analytics are not yet implemented.
- **Search Functionality:** The [`search_rules()`](recursive_training/rules/rule_repository.py:632) method is described as a basic implementation (line 643), implying that more advanced search capabilities (e.g., full-text search, complex query language) could be future enhancements.

## 3. Implementation Gaps / Unfinished Next Steps

- **Advanced Usage Tracking:** The placeholder in [`_track_rule_access()`](recursive_training/rules/rule_repository.py:469) suggests an intent for more detailed analytics on rule usage, which is currently missing.
- **Sophisticated Search:** The [`search_rules()`](recursive_training/rules/rule_repository.py:632) method is basic. Enhancements could include a more robust query language or integration with a search index.
- **Comprehensive Rule Validation:** The current validation in [`_validate_rule()`](recursive_training/rules/rule_repository.py:208) is minimal. A more extensive schema validation (e.g., using JSON Schema) or custom validation logic based on rule types could be beneficial.
- **Workflow and Collaboration:** There are no explicit features for rule approval workflows, collaborative editing, or peer review, which might be valuable in a system managing critical rules.
- **Error Handling in Restore:** The [`restore_backup()`](recursive_training/rules/rule_repository.py:737) method has a complex flow. Lines 809-810 appear to be a duplicate `_save_rule_index()` call that might be unreachable due to the `return True` on line 807.

## 4. Connections & Dependencies

### Internal Project Dependencies:
- [`recursive_training.config.default_config`](recursive_training/config/default_config.py:): Uses [`get_config()`](recursive_training/config/default_config.py:) to load repository configuration, specifically from `config.hybrid_rules`.

### External Library Dependencies:
- `os`: For file system operations (paths, directories).
- `json`: For serializing and deserializing rule data to/from JSON files.
- `logging`: For logging module activities.
- `time`: Used for generating timestamps (e.g., for default rule IDs).
- `shutil`: For file operations like copying and moving (e.g., backups, archiving).
- `datetime` (from `datetime`): For timestamping rule creation, updates, and backups.
- `typing` (Any, Dict, List, Optional, Union, Callable): For type hinting.
- `types` (SimpleNamespace): For handling configuration objects.
- `enum` (Enum): Used for defining [`RuleStatus`](recursive_training/rules/rule_repository.py:28).

### Shared Data / Files:
- **Rule Files:** Stores individual rules as JSON files (e.g., `[rules_path]/active/[rule_id]_v[version].json`).
- **Rule Index:** Maintains a central index of all rules in [`[rules_path]/rule_index.json`](recursive_training/rules/rule_repository.py:121).
- **Backup Files:** Stores backups of rules and the index in `[rules_path]/backups/backup_[timestamp]/`.
- **Configuration:** Reads its configuration (paths, behavior flags) from a configuration object.
- **Logs:** Outputs log messages via the standard `logging` module.

## 5. Function and Class Example Usages

### `RuleRepository` Class ([`RuleRepository`](recursive_training/rules/rule_repository.py:36))
The `RuleRepository` is a singleton class.

**Initialization:**
```python
from recursive_training.rules.rule_repository import get_rule_repository, RuleStatus

# Get the repository instance (loads config automatically or use provided)
repo = get_rule_repository() 
# repo = get_rule_repository(custom_config_dict)
```

**Adding a Rule:**
```python
new_rule_data = {
    "id": "example_rule_001",
    "type": "data_validation",
    "description": "Ensures data field X is positive.",
    "conditions": [{"field": "X", "operator": "gt", "value": 0}],
    "actions": [{"type": "log_pass", "message": "Field X is valid."}]
}
added_rule = repo.add_rule(new_rule_data, activate=True)
```

**Getting a Rule:**
```python
rule = repo.get_rule("example_rule_001")
specific_version_rule = repo.get_rule("example_rule_001", version=1)
```

**Updating a Rule:**
```python
rule_to_update = repo.get_rule("example_rule_001")
rule_to_update["description"] = "Ensures data field X is greater than zero."
updated_rule = repo.update_rule(rule_to_update, create_new_version=True)
```

**Changing Rule Status:**
```python
repo.change_rule_status("example_rule_001", RuleStatus.DEPRECATED)
```

**Listing Rules:**
```python
active_rules = repo.list_rules(status=RuleStatus.ACTIVE)
all_rules_summary = repo.list_rules()
```

**Deleting/Archiving a Rule:**
```python
# Archive the rule (soft delete)
repo.delete_rule("example_rule_001")

# Permanently delete the rule
# repo.delete_rule("example_rule_001", hard_delete=True) 
```

### `RuleStatus` Enum ([`RuleStatus`](recursive_training/rules/rule_repository.py:28))
Used to manage the lifecycle state of rules.
```python
from recursive_training.rules.rule_repository import RuleStatus

status = RuleStatus.ACTIVE  # Other values: DRAFT, DEPRECATED, ARCHIVED
```

## 6. Hardcoding Issues

- **Default Paths:**
    - `rules_path`: Defaults to `"./rules"` if not in config or if config value is not a string (lines 90, 92).
- **Default Configuration Values:**
    - `max_rule_backups`: Defaults to `3` (line 106).
    - `validate_on_save`: Defaults to `True` (line 107).
    - `track_rule_usage`: Defaults to `True` (line 108).
    - `backup_rules`: Defaults to `True` within [`_create_backup()`](recursive_training/rules/rule_repository.py:148) (line 150).
- **File/Directory Naming Conventions:**
    - Backup directory prefix: `"backup_"` (lines 154, 191, 832).
    - Rule file extension: Hardcoded as `".json"` throughout.
    - Rule index filename: Hardcoded as `"rule_index.json"` (lines 121, 138, 171).
- **Default Values in Logic:**
    - Default rule ID prefix: `"rule_"` if ID is not provided in [`add_rule()`](recursive_training/rules/rule_repository.py:281) (line 294).
    - Default rule type: `"unknown"` if not provided (lines 322, 790).
- **Validation Logic:**
    - Required fields for validation: `["id", "type", "conditions", "actions"]` are hardcoded in [`_validate_rule()`](recursive_training/rules/rule_repository.py:222).
- **Test-Specific Logic (?):**
    - In [`list_backups()`](recursive_training/rules/rule_repository.py:819), lines 853-854: `if rule_count == 0 and os.path.exists(active_dir): rule_count = 1`. This seems unusual for production logic and might be a test artifact or workaround.

While many of these are configurable, the hardcoded defaults and naming conventions are embedded in the code.

## 7. Coupling Points

- **File System:** The repository is tightly coupled to the local file system for storing rules, index, and backups. Migrating to a database or a different storage backend would require substantial modifications.
- **Configuration Structure:** Depends on a specific configuration structure, expected to be provided via [`get_config().hybrid_rules`](recursive_training/config/default_config.py:). Changes in the config schema could break the repository.
- **Rule Dictionary Schema:** The internal structure of rule dictionaries (e.g., required fields like `id`, `type`, `metadata`, `conditions`, `actions`) is implicitly defined and expected by various methods. Lack of a formal schema could lead to inconsistencies.
- **Singleton Pattern:** The use of a singleton ([`get_instance()`](recursive_training/rules/rule_repository.py:52)) creates a global state, which can sometimes make testing and dependency management more complex in larger applications.

## 8. Existing Tests

- A corresponding test file exists at [`tests/recursive_training/rules/test_rule_repository.py`](tests/recursive_training/rules/test_rule_repository.py:).
- The code includes comments suggesting consideration for test environments, such as `exist_ok=True` when creating directories to handle parallel test execution (e.g., line 158).
- The logic in [`list_backups()`](recursive_training/rules/rule_repository.py:853-854) that sets `rule_count = 1` if an empty backup directory exists might be related to specific test setup or assertions.
- Without inspecting the test file's content, a detailed assessment of test coverage, types of tests (unit, integration), and specific gaps is not possible. However, the presence of a dedicated test module is positive.

## 9. Module Architecture and Flow

- **Design Pattern:** Implements the Singleton pattern for the [`RuleRepository`](recursive_training/rules/rule_repository.py:36) class, ensuring a single instance manages all rules.
- **Core Components:**
    - [`RuleRepository`](recursive_training/rules/rule_repository.py:36): The central class orchestrating all operations.
    - [`RuleStatus`](recursive_training/rules/rule_repository.py:28) (Enum): Defines the lifecycle states of a rule (DRAFT, ACTIVE, DEPRECATED, ARCHIVED).
    - [`RuleRepositoryError`](recursive_training/rules/rule_repository.py:23): Custom exception for repository-specific errors.
- **Storage Mechanism:**
    - Rules are serialized as JSON objects and stored in individual files.
    - A master `rule_index.json` file maintains metadata, status, and version information for all rules.
    - Directory structure under `rules_path` (default: `./rules`):
        - `active/`: Stores JSON files for active, draft, or deprecated rules.
        - `archive/`: Stores JSON files for archived rules.
        - `backups/`: Contains timestamped subdirectories for backups.
- **Key Operational Flows:**
    - **Initialization (`__init__`)**:
        - Loads configuration (paths, backup settings, validation flags).
        - Ensures necessary directories (`active`, `archive`, `backups`) exist.
        - Loads the `rule_index.json` into memory.
    - **Rule Creation/Update ([`add_rule()`](recursive_training/rules/rule_repository.py:281), [`update_rule()`](recursive_training/rules/rule_repository.py:354)):
        - Validates the rule structure (basic).
        - Creates a backup of the current repository state.
        - Assigns/updates metadata (version, timestamps, status).
        - Saves the rule as `[rule_id]_v[version].json` in the `active` directory.
        - Updates the in-memory `rule_index` and persists it to `rule_index.json`.
    - **Rule Retrieval ([`get_rule()`](recursive_training/rules/rule_repository.py:442)):
        - Consults `rule_index` to locate the file path for the requested rule ID and version.
        - Reads the JSON file and returns the rule dictionary.
        - Includes a placeholder for usage tracking.
    - **Rule Deletion/Archival ([`delete_rule()`](recursive_training/rules/rule_repository.py:476)):
        - **Archival (default):** Moves rule files from `active` to `archive`, updates status in `rule_index`.
        - **Hard Delete:** Removes all version files and the entry from `rule_index`.
        - Creates a backup before modification.
    - **Backup and Restore ([`_create_backup()`](recursive_training/rules/rule_repository.py:148), [`restore_backup()`](recursive_training/rules/rule_repository.py:737)):
        - `_create_backup`: Copies the `active` rules directory and `rule_index.json` to a new timestamped backup folder. Manages `max_backups`.
        - `restore_backup`: Clears current active rules and index, then copies files from a specified backup into the active directory and rebuilds the index. Creates a safety backup of the current state before restoring.

## 10. Naming Conventions

- **Overall:** The module generally adheres to PEP 8 naming conventions.
    - Classes (`RuleRepository`, `RuleStatus`, `RuleRepositoryError`) use PascalCase.
    - Functions, methods, and variables (e.g., [`add_rule()`](recursive_training/rules/rule_repository.py:281), `rules_path`, `rule_index`) use snake_case.
- **Internal Methods:** Private/internal helper methods are prefixed with a single underscore (e.g., [`_ensure_directories()`](recursive_training/rules/rule_repository.py:112), [`_validate_rule()`](recursive_training/rules/rule_repository.py:208)).
- **Clarity:** Names are generally descriptive and convey their purpose well (e.g., `latest_version`, `active_rules_path`).
- **`_get_config_value`:** The helper function [`_get_config_value()`](recursive_training/rules/rule_repository.py:80) defined within [`__init__()`](recursive_training/rules/rule_repository.py:67) and assigned to `self._get_config_value` is slightly unconventional but clear in its local context.
- **Constants/Enums:** `RuleStatus` members (`DRAFT`, `ACTIVE`, etc.) are uppercase, which is standard for enums.
- No significant deviations or potential AI assumption errors in naming were observed.