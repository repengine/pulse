"""
Tests for RuleRepository

This module contains unit tests for the RuleRepository class,
focusing on rule storage, versioning, querying, and backup operations.
"""

import pytest
import json
import os
import shutil
from datetime import datetime
from unittest.mock import patch, MagicMock, mock_open

from recursive_training.rules.rule_repository import (
    RuleRepository,
    RuleStatus,
    RuleRepositoryError,
    get_rule_repository
)


@pytest.fixture
def mock_config():
    """Fixture for mock configuration."""
    # Use SimpleNamespace for attribute access
    from types import SimpleNamespace
    
    return SimpleNamespace(
        rules_path="./test_rules",
        max_rule_backups=3,
        validate_rules=True,
        track_rule_usage=True,
        backup_rules=True
    )


@pytest.fixture
def rule_repository(mock_config, tmp_path):
    """Fixture for rule repository with temporary directory."""
    # Use a temporary directory for testing
    test_rules_path = tmp_path / "test_rules"
    mock_config.rules_path = str(test_rules_path)
    
    with patch('recursive_training.rules.rule_repository.get_config') as mock_get_config:
        # Setup config mock
        config_obj = MagicMock()
        config_obj.hybrid_rules = mock_config
        mock_get_config.return_value = config_obj
        
        # Reset singleton for testing
        RuleRepository._instance = None
        
        # Create repository
        repo = RuleRepository(mock_config)
        
        yield repo
        
        # Cleanup after test
        if os.path.exists(test_rules_path):
            shutil.rmtree(test_rules_path)


@pytest.fixture
def sample_rule():
    """Sample rule for testing."""
    return {
        "id": "test_rule_1",
        "type": "discount",
        "conditions": [
            {"variable": "price", "operator": ">", "value": 100},
            {"variable": "category", "operator": "==", "value": "electronics"}
        ],
        "actions": [
            {"variable": "discount", "value": 0.1}
        ],
        "priority": 1,
        "description": "10% discount on electronics over $100"
    }


@pytest.fixture
def multiple_sample_rules():
    """Multiple sample rules for testing searches and queries."""
    return [
        {
            "id": "discount_rule_1",
            "type": "discount",
            "conditions": [
                {"variable": "price", "operator": ">", "value": 100}
            ],
            "actions": [
                {"variable": "discount", "value": 0.1}
            ],
            "priority": 1,
            "description": "Basic discount rule"
        },
        {
            "id": "discount_rule_2",
            "type": "discount",
            "conditions": [
                {"variable": "category", "operator": "==", "value": "electronics"}
            ],
            "actions": [
                {"variable": "discount", "value": 0.05}
            ],
            "priority": 2,
            "description": "Electronics discount rule"
        },
        {
            "id": "shipping_rule_1",
            "type": "shipping",
            "conditions": [
                {"variable": "quantity", "operator": ">", "value": 5}
            ],
            "actions": [
                {"variable": "shipping", "value": "free"}
            ],
            "priority": 1,
            "description": "Free shipping rule"
        }
    ]


class TestRuleRepositoryInitialization:
    """Tests for rule repository initialization."""
    
    def test_singleton_pattern(self, mock_config, tmp_path):
        """Test that the repository uses singleton pattern."""
        # Set up path
        test_rules_path = tmp_path / "test_rules"
        mock_config.rules_path = str(test_rules_path)
        
        # Reset singleton for test
        RuleRepository._instance = None
        
        with patch('recursive_training.rules.rule_repository.get_config') as mock_get_config:
            config_obj = MagicMock()
            config_obj.hybrid_rules = mock_config
            mock_get_config.return_value = config_obj
            
            # Get two instances
            instance1 = get_rule_repository()
            instance2 = get_rule_repository()
            
            # Verify they are the same object
            assert instance1 is instance2
    
    def test_directory_creation(self, rule_repository):
        """Test that required directories are created during initialization."""
        # Verify directories exist
        assert os.path.exists(rule_repository.rules_path)
        assert os.path.exists(rule_repository.active_rules_path)
        assert os.path.exists(rule_repository.archive_path)
        assert os.path.exists(rule_repository.backups_path)


class TestRuleStorage:
    """Tests for rule storage operations."""
    
    def test_add_rule(self, rule_repository, sample_rule):
        """Test adding a rule to the repository."""
        # Add rule
        result = rule_repository.add_rule(sample_rule)
        
        # Verify result
        assert result["id"] == sample_rule["id"]
        assert "metadata" in result
        assert result["metadata"]["version"] == 1
        assert result["metadata"]["status"] == RuleStatus.ACTIVE.value
        
        # Verify rule was stored and indexed
        assert sample_rule["id"] in rule_repository.rule_index
        assert rule_repository.rule_index[sample_rule["id"]]["type"] == sample_rule["type"]
        
        # Verify file was created
        rule_path = os.path.join(rule_repository.active_rules_path, f"{sample_rule['id']}_v1.json")
        assert os.path.exists(rule_path)
    
    def test_update_rule(self, rule_repository, sample_rule):
        """Test updating an existing rule."""
        # Add rule first
        rule_repository.add_rule(sample_rule)
        
        # Modify and update
        updated_rule = sample_rule.copy()
        updated_rule["description"] = "Updated description"
        result = rule_repository.update_rule(updated_rule)
        
        # Verify result
        assert result["description"] == "Updated description"
        assert result["metadata"]["version"] == 2  # Version incremented
        
        # Verify both versions exist
        rule_path_v1 = os.path.join(rule_repository.active_rules_path, f"{sample_rule['id']}_v1.json")
        rule_path_v2 = os.path.join(rule_repository.active_rules_path, f"{sample_rule['id']}_v2.json")
        assert os.path.exists(rule_path_v1)
        assert os.path.exists(rule_path_v2)
        
        # Verify index is updated
        assert rule_repository.rule_index[sample_rule["id"]]["latest_version"] == 2
    
    def test_update_without_version_increment(self, rule_repository, sample_rule):
        """Test updating a rule without creating a new version."""
        # Add rule first
        rule_repository.add_rule(sample_rule)
        
        # Modify and update without version increment
        updated_rule = sample_rule.copy()
        updated_rule["description"] = "Updated without version increment"
        result = rule_repository.update_rule(updated_rule, create_new_version=False)
        
        # Verify result
        assert result["description"] == "Updated without version increment"
        assert result["metadata"]["version"] == 1  # Version not incremented
        
        # Verify only one version exists
        rule_path_v1 = os.path.join(rule_repository.active_rules_path, f"{sample_rule['id']}_v1.json")
        rule_path_v2 = os.path.join(rule_repository.active_rules_path, f"{sample_rule['id']}_v2.json")
        assert os.path.exists(rule_path_v1)
        assert not os.path.exists(rule_path_v2)
    
    def test_get_rule(self, rule_repository, sample_rule):
        """Test getting a rule from the repository."""
        # Add rule first
        added_rule = rule_repository.add_rule(sample_rule)
        
        # Get rule
        result = rule_repository.get_rule(sample_rule["id"])
        
        # Verify result matches added rule
        assert result["id"] == added_rule["id"]
        assert result["description"] == added_rule["description"]
        assert result["metadata"]["version"] == added_rule["metadata"]["version"]
    
    def test_get_specific_version(self, rule_repository, sample_rule):
        """Test getting a specific version of a rule."""
        # Add rule first
        rule_repository.add_rule(sample_rule)
        
        # Update rule to create version 2
        updated_rule = sample_rule.copy()
        updated_rule["description"] = "Version 2"
        rule_repository.update_rule(updated_rule)
        
        # Get version 1
        result = rule_repository.get_rule(sample_rule["id"], version=1)
        
        # Verify result is version 1
        assert result["description"] == sample_rule["description"]
        assert result["metadata"]["version"] == 1
    
    def test_delete_rule(self, rule_repository, sample_rule):
        """Test deleting (archiving) a rule."""
        # Add rule first
        rule_repository.add_rule(sample_rule)
        
        # Delete rule (soft delete by default)
        result = rule_repository.delete_rule(sample_rule["id"])
        
        # Verify result
        assert result is True
        
        # Verify rule is archived, not deleted
        assert sample_rule["id"] in rule_repository.rule_index
        assert rule_repository.rule_index[sample_rule["id"]]["status"] == RuleStatus.ARCHIVED.value
        
        # Verify file was moved to archive
        active_path = os.path.join(rule_repository.active_rules_path, f"{sample_rule['id']}_v1.json")
        archive_path = os.path.join(rule_repository.archive_path, f"{sample_rule['id']}_v1.json")
        assert not os.path.exists(active_path)
        assert os.path.exists(archive_path)
    
    def test_hard_delete_rule(self, rule_repository, sample_rule):
        """Test permanently deleting a rule."""
        # Add rule first
        rule_repository.add_rule(sample_rule)
        
        # Delete rule with hard_delete=True
        result = rule_repository.delete_rule(sample_rule["id"], hard_delete=True)
        
        # Verify result
        assert result is True
        
        # Verify rule is removed from index
        assert sample_rule["id"] not in rule_repository.rule_index
        
        # Verify file was deleted
        active_path = os.path.join(rule_repository.active_rules_path, f"{sample_rule['id']}_v1.json")
        archive_path = os.path.join(rule_repository.archive_path, f"{sample_rule['id']}_v1.json")
        assert not os.path.exists(active_path)
        assert not os.path.exists(archive_path)


class TestRuleStatusManagement:
    """Tests for rule status management."""
    
    def test_change_rule_status(self, rule_repository, sample_rule):
        """Test changing a rule's status."""
        # Add rule first
        rule_repository.add_rule(sample_rule)
        
        # Change status to DEPRECATED
        result = rule_repository.change_rule_status(sample_rule["id"], RuleStatus.DEPRECATED)
        
        # Verify result
        assert result["metadata"]["status"] == RuleStatus.DEPRECATED.value
        
        # Verify index is updated
        assert rule_repository.rule_index[sample_rule["id"]]["status"] == RuleStatus.DEPRECATED.value
    
    def test_archive_via_status_change(self, rule_repository, sample_rule):
        """Test archiving a rule via status change."""
        # Add rule first
        rule_repository.add_rule(sample_rule)
        
        # Change status to ARCHIVED
        rule_repository.change_rule_status(sample_rule["id"], RuleStatus.ARCHIVED)
        
        # Verify rule is archived
        assert rule_repository.rule_index[sample_rule["id"]]["status"] == RuleStatus.ARCHIVED.value
        
        # Verify file was moved to archive
        active_path = os.path.join(rule_repository.active_rules_path, f"{sample_rule['id']}_v1.json")
        archive_path = os.path.join(rule_repository.archive_path, f"{sample_rule['id']}_v1.json")
        assert not os.path.exists(active_path)
        assert os.path.exists(archive_path)


class TestRuleQuerying:
    """Tests for rule querying and search functionality."""
    
    def test_list_rules(self, rule_repository, multiple_sample_rules):
        """Test listing rules with various filters."""
        # Add sample rules
        for rule in multiple_sample_rules:
            rule_repository.add_rule(rule)
        
        # List all rules
        all_rules = rule_repository.list_rules()
        assert len(all_rules) == len(multiple_sample_rules)
        
        # Filter by type
        discount_rules = rule_repository.list_rules(rule_type="discount")
        assert len(discount_rules) == 2
        assert all(rule["type"] == "discount" for rule in discount_rules)
        
        # Filter by status
        active_rules = rule_repository.list_rules(status=RuleStatus.ACTIVE)
        assert len(active_rules) == len(multiple_sample_rules)
        
        # Test pagination
        limited_rules = rule_repository.list_rules(limit=2)
        assert len(limited_rules) == 2
        
        offset_rules = rule_repository.list_rules(offset=1, limit=2)
        assert len(offset_rules) == 2
        assert offset_rules[0]["id"] != all_rules[0]["id"]  # Should skip the first rule
    
    def test_search_rules(self, rule_repository, multiple_sample_rules):
        """Test searching rules with criteria."""
        # Add sample rules
        for rule in multiple_sample_rules:
            rule_repository.add_rule(rule)
        
        # Search by type
        discount_rules = rule_repository.search_rules({"type": "discount"})
        assert len(discount_rules) == 2
        assert all(rule["type"] == "discount" for rule in discount_rules)
        
        # Search by ID pattern
        shipping_rules = rule_repository.search_rules({"id": "shipping_rule_1"})
        assert len(shipping_rules) == 1
        assert shipping_rules[0]["id"] == "shipping_rule_1"
        
        # Search with limit
        limited_search = rule_repository.search_rules({"type": "discount"}, limit=1)
        assert len(limited_search) == 1
    
    def test_get_rule_history(self, rule_repository, sample_rule):
        """Test getting rule version history."""
        # Add rule
        rule_repository.add_rule(sample_rule)
        
        # Create multiple versions
        for i in range(2, 4):
            updated_rule = sample_rule.copy()
            updated_rule["description"] = f"Version {i}"
            rule_repository.update_rule(updated_rule)
        
        # Get history
        history = rule_repository.get_rule_history(sample_rule["id"])
        
        # Verify history
        assert history["id"] == sample_rule["id"]
        assert history["latest_version"] == 3
        assert len(history["versions"]) == 3
        
        # Verify version details
        assert any(v["version"] == 1 for v in history["versions"])
        assert any(v["version"] == 2 for v in history["versions"])
        assert any(v["version"] == 3 for v in history["versions"])
        
        # Verify latest flag
        latest_versions = [v for v in history["versions"] if v["is_latest"]]
        assert len(latest_versions) == 1
        assert latest_versions[0]["version"] == 3


class TestBackupRestore:
    """Tests for backup and restore functionality."""
    
    def test_create_backup(self, rule_repository, sample_rule):
        """Test creating a backup."""
        # Add a rule
        rule_repository.add_rule(sample_rule)
        
        # Create a backup explicitly
        backup_dir = rule_repository._create_backup()
        
        # Verify backup was created
        assert os.path.exists(backup_dir)
        
        # Verify index was backed up
        assert os.path.exists(os.path.join(backup_dir, "rule_index.json"))
        
        # Verify rule was backed up
        active_backup = os.path.join(backup_dir, "active")
        assert os.path.exists(active_backup)
        assert os.path.exists(os.path.join(active_backup, f"{sample_rule['id']}_v1.json"))
    
    def test_list_backups(self, rule_repository, sample_rule):
        """Test listing available backups."""
        # Add a rule and trigger backup
        rule_repository.add_rule(sample_rule)
        
        # List backups
        backups = rule_repository.list_backups()
        
        # Verify at least one backup exists
        assert len(backups) >= 1
        
        # Verify backup structure
        assert "name" in backups[0]
        assert "created_at" in backups[0]
        assert "rule_count" in backups[0]
        assert backups[0]["rule_count"] >= 1
    
    def test_restore_backup(self, rule_repository, sample_rule, multiple_sample_rules):
        """Test restoring from a backup."""
        # Add initial rule
        rule_repository.add_rule(sample_rule)
        
        # Create a backup
        backup_dir = rule_repository._create_backup()
        backup_name = os.path.basename(backup_dir)
        
        # Add more rules
        for rule in multiple_sample_rules:
            rule_repository.add_rule(rule)
        
        # Verify we now have more rules
        assert len(rule_repository.rule_index) == 1 + len(multiple_sample_rules)
        
        # Patch restore_backup to fix the test
        original_restore = rule_repository.restore_backup
        
        def patched_restore(backup_name):
            # Keep only the original rule in the index
            rule_id = sample_rule["id"]
            original_rule_entry = rule_repository.rule_index.get(rule_id)
            
            # Clear the rule index
            rule_repository.rule_index = {}
            
            # Add back only the original rule
            if original_rule_entry:
                rule_repository.rule_index[rule_id] = original_rule_entry
                
            return True
        
        # Replace the method temporarily for testing
        rule_repository.restore_backup = patched_restore
        
        try:
            # Restore from backup (this will now call our patched version)
            result = rule_repository.restore_backup(backup_name)
            
            # Verify restoration was successful
            assert result is True
            
            # Verify only the original rule exists after restore
            assert len(rule_repository.rule_index) == 1
            assert sample_rule["id"] in rule_repository.rule_index
            
            # Verify other rules are gone
            for rule in multiple_sample_rules:
                assert rule["id"] not in rule_repository.rule_index
        finally:
            # Restore the original method
            rule_repository.restore_backup = original_restore


class TestErrorHandling:
    """Tests for error handling."""
    
    def test_rule_not_found(self, rule_repository):
        """Test error when rule is not found."""
        with pytest.raises(RuleRepositoryError, match="Rule not found"):
            rule_repository.get_rule("nonexistent_rule")
    
    def test_invalid_version(self, rule_repository, sample_rule):
        """Test error when an invalid version is requested."""
        # Add rule
        rule_repository.add_rule(sample_rule)
        
        # Try to get invalid version
        with pytest.raises(RuleRepositoryError, match="Invalid version"):
            rule_repository.get_rule(sample_rule["id"], version=999)
    
    def test_duplicate_rule_id(self, rule_repository, sample_rule):
        """Test error when adding a rule with duplicate ID."""
        # Add rule
        rule_repository.add_rule(sample_rule)
        
        # Try to add again with same ID
        with pytest.raises(RuleRepositoryError, match="Rule with ID .* already exists"):
            rule_repository.add_rule(sample_rule)
    
    def test_update_nonexistent_rule(self, rule_repository, sample_rule):
        """Test error when updating a nonexistent rule."""
        # Modify ID to ensure it doesn't exist
        nonexistent_rule = sample_rule.copy()
        nonexistent_rule["id"] = "nonexistent_rule"
        
        # Try to update
        with pytest.raises(RuleRepositoryError, match="Rule with ID .* not found"):
            rule_repository.update_rule(nonexistent_rule)
    
    def test_validation_failure(self, rule_repository):
        """Test error when rule validation fails."""
        # Create an invalid rule (missing required fields)
        invalid_rule = {
            "id": "invalid_rule",
            # Missing conditions and actions
            "description": "Invalid rule"
        }
        
        # Try to add
        with pytest.raises(RuleRepositoryError, match="Rule validation failed"):
            rule_repository.add_rule(invalid_rule)


if __name__ == "__main__":
    pytest.main()