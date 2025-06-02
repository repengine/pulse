import json
import os

# Assuming the active rule set is in a JSON file, adjust import if needed
# import your_rule_module


def load_proposed_rule_changes(
    file_path="pipeline/rule_proposals/proposed_rule_changes.json",
):
    """Loads proposed rule changes from a JSON file."""
    if not os.path.exists(file_path):
        print(f"Error: Proposed rule changes file not found at {file_path}")
        return None
    try:
        with open(file_path, "r") as f:
            content = f.read().strip()
            if not content:  # Handle empty file case
                print(f"Empty file found at {file_path}, treating as empty array")
                return []
            changes = json.loads(content)
        print(f"Successfully loaded proposed rule changes from {file_path}")
        return changes
    except json.JSONDecodeError:
        print(f"Error: Could not decode JSON from {file_path}")
        return None
    except Exception as e:
        print(f"An error occurred while loading rule changes: {e}")
        return None


def apply_rule_changes(proposed_changes, active_rules):
    """
    Applies proposed rule changes (modification, generation, pruning)
    to the active rule set.
    """
    if not proposed_changes:
        print("No proposed changes to apply.")
        return active_rules  # Return original rules if no changes

    # Assuming proposed_changes is a dict with keys 'modifications',
    # 'generations', 'prunings'
    modifications = proposed_changes.get("modifications", [])
    generations = proposed_changes.get("generations", [])
    prunings = proposed_changes.get("prunings", [])

    print(
        f"Applying {
            len(modifications)} modifications, {
            len(generations)} generations, {
                len(prunings)} prunings.")

    # --- Rule Application Logic Goes Here ---
    # This is a placeholder. The actual logic will depend on the structure
    # of your active_rules and proposed_changes.

    # Example: Simple pruning (assuming active_rules is a list of rule objects/dicts
    # with a unique 'id' or 'name' field)
    # updated_rules = [rule for rule in active_rules if rule.get('id') not in prunings]
    # print(f"Pruned {len(active_rules) - len(updated_rules)} rules.")

    # Example: Simple generation (assuming generations are full rule objects/dicts)
    # updated_rules.extend(generations)
    # print(f"Generated {len(generations)} rules.")

    # Example: Simple modification (assuming modifications are dicts like {'id': rule_id, 'changes': {field: new_value}})
    # for modification in modifications:
    #     rule_id = modification.get('id')
    #     changes = modification.get('changes', {})
    #     for rule in updated_rules:
    #         if rule.get('id') == rule_id:
    #             for field, new_value in changes.items():
    #                 rule[field] = new_value
    #             print(f"Modified rule {rule_id}.")
    #             break # Assuming unique rule IDs

    # For this task, we will focus on generating a new rule set file.
    # This requires knowing the structure of the active rules and the proposed changes.
    # Let's assume active_rules is a list of dictionaries, and proposed_changes
    # follows the structure:
    # {
    #   "modifications": [{"id": "rule_id", "changes": {"field": "new_value"}}],
    #   "generations": [{"id": "new_rule_id", "field": "value"}], # full new rule dicts
    #   "prunings": ["rule_id_to_remove"]
    # }

    # Create a mutable copy of active rules
    updated_rules = [rule.copy() for rule in active_rules] if active_rules else []

    # Apply Prunings
    pruned_count = 0
    initial_rule_count = len(updated_rules)
    updated_rules = [rule for rule in updated_rules if rule.get("id") not in prunings]
    pruned_count = initial_rule_count - len(updated_rules)
    if pruned_count > 0:
        print(f"Pruned {pruned_count} rules.")
        for rule_id in prunings:
            print(f"  - Pruned rule: {rule_id}")

    # Apply Modifications
    modified_count = 0
    for modification in modifications:
        rule_id = modification.get("id")
        changes = modification.get("changes", {})
        found = False
        for rule in updated_rules:
            if rule.get("id") == rule_id:
                for field, new_value in changes.items():
                    rule[field] = new_value
                print(f"  - Modified rule: {rule_id}")
                modified_count += 1
                found = True
                break  # Assuming unique rule IDs
        if not found:
            print(f"Warning: Modification proposed for non-existent rule ID: {rule_id}")
    if modified_count > 0:
        print(f"Modified {modified_count} rules.")

    # Apply Generations
    generated_count = 0
    for new_rule in generations:
        # Basic check to avoid adding duplicates if 'id' exists
        if "id" in new_rule and any(
            rule.get("id") == new_rule["id"] for rule in updated_rules
        ):
            print(
                f"Warning: Rule with ID {
                    new_rule.get('id')} already exists. Skipping generation.")
            continue
        updated_rules.append(new_rule)
        print(f"  - Generated rule: {new_rule.get('id', 'Unnamed Rule')}")
        generated_count += 1
    if generated_count > 0:
        print(f"Generated {generated_count} rules.")

    print("Rule application complete.")
    return updated_rules


# Example Usage (for testing purposes, not part of the final integration)
# if __name__ == "__main__":
#     # Create a dummy proposed_rule_changes.json for testing
#     dummy_changes = {
#         "modifications": [
#             {"id": "rule_1", "changes": {"description": "Updated description"}}
#         ],
#         "generations": [
#             {"id": "rule_3", "name": "New Rule", "condition": "...", "action": "..."}
#         ],
#         "prunings": ["rule_2"]
#     }
#     dummy_changes_file = "pipeline/rule_proposals/proposed_rule_changes.json"
#     os.makedirs(os.path.dirname(dummy_changes_file), exist_ok=True)
#     with open(dummy_changes_file, 'w') as f:
#         json.dump(dummy_changes, f, indent=4)

#     # Create a dummy active_rules list for testing
#     dummy_active_rules = [
#         {"id": "rule_1", "name": "Rule One", "description": "Original description"},
#         {"id": "rule_2", "name": "Rule Two", "description": "Another rule"}
#     ]

#     proposed_changes = load_proposed_rule_changes(dummy_changes_file)
#     if proposed_changes:
#         updated_rules = apply_rule_changes(proposed_changes, dummy_active_rules)
#         print("\nUpdated Rules:")
#         print(json.dumps(updated_rules, indent=4))

#     # Clean up dummy file
#     # os.remove(dummy_changes_file)
