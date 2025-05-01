"""
RuleRepository Module

This module implements a repository for storing, versioning, and querying rules
in the recursive training system. It supports persisting rules to disk,
managing rule versions, and retrieving rules based on various criteria.
"""

import os
import json
import logging
import time
import shutil
from datetime import datetime
from typing import Any, Dict, List, Optional, Union, Callable
from enum import Enum

# Import recursive training components
from recursive_training.config.default_config import get_config


class RuleRepositoryError(Exception):
    """Exception raised for repository errors."""
    pass


class RuleStatus(Enum):
    """Status of a rule in the repository."""
    DRAFT = "draft"        # Rule is in development/draft stage
    ACTIVE = "active"      # Rule is active and in use
    DEPRECATED = "deprecated"  # Rule is deprecated but still available
    ARCHIVED = "archived"  # Rule is archived and not in use


class RuleRepository:
    """
    Repository for storing, versioning, and querying rules.
    
    Features:
    - Persistent storage of rules
    - Rule versioning with history tracking
    - Querying rules by type, status, and other attributes
    - Rule activation and deactivation
    - Rule validation and consistency checks
    - Backup and restore capabilities
    """
    
    # Singleton instance
    _instance = None
    
    @classmethod
    def get_instance(cls, config: Optional[Dict[str, Any]] = None) -> 'RuleRepository':
        """
        Get or create the singleton instance of RuleRepository.
        
        Args:
            config: Optional configuration dictionary
            
        Returns:
            RuleRepository instance
        """
        if cls._instance is None:
            cls._instance = RuleRepository(config)
        return cls._instance
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the RuleRepository.
        
        Args:
            config: Optional configuration dictionary
        """
        self.logger = logging.getLogger("RuleRepository")
        
        # Load configuration
        self.config = config or get_config().hybrid_rules
        
        # Set up repository paths
        self.rules_path = self.config.rules_path
        self.active_rules_path = os.path.join(self.rules_path, "active")
        self.archive_path = os.path.join(self.rules_path, "archive")
        self.backups_path = os.path.join(self.rules_path, "backups")
        
        # Ensure directories exist
        self._ensure_directories()
        
        # Initialize rule index
        self.rule_index = {}
        self._load_rule_index()
        
        # Configure repository settings
        self.max_backups = self.config.max_rule_backups
        self.validate_on_save = self.config.validate_rules
        self.track_usage = self.config.track_rule_usage
        
        self.logger.info("RuleRepository initialized")
    
    def _ensure_directories(self):
        """Ensure all necessary directories exist."""
        for path in [self.rules_path, self.active_rules_path, self.archive_path, self.backups_path]:
            if not os.path.exists(path):
                os.makedirs(path)
                self.logger.debug(f"Created directory: {path}")
    
    def _load_rule_index(self):
        """Load the rule index from disk."""
        index_path = os.path.join(self.rules_path, "rule_index.json")
        
        if os.path.exists(index_path):
            try:
                with open(index_path, 'r') as f:
                    self.rule_index = json.load(f)
                    self.logger.debug(f"Loaded rule index with {len(self.rule_index)} entries")
            except Exception as e:
                self.logger.error(f"Error loading rule index: {e}")
                # Initialize an empty index if loading fails
                self.rule_index = {}
        else:
            self.logger.debug("Rule index not found, starting with empty index")
            self.rule_index = {}
    
    def _save_rule_index(self):
        """Save the rule index to disk."""
        index_path = os.path.join(self.rules_path, "rule_index.json")
        
        try:
            with open(index_path, 'w') as f:
                json.dump(self.rule_index, f, indent=2)
            self.logger.debug(f"Saved rule index with {len(self.rule_index)} entries")
        except Exception as e:
            self.logger.error(f"Error saving rule index: {e}")
            raise RuleRepositoryError(f"Failed to save rule index: {e}")
    
    def _create_backup(self):
        """Create a backup of the current rules."""
        if not self.config.backup_rules:
            return
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_dir = os.path.join(self.backups_path, f"backup_{timestamp}")
        
        try:
            # Create backup directory
            os.makedirs(backup_dir)
            
            # Copy active rules
            active_backup = os.path.join(backup_dir, "active")
            os.makedirs(active_backup)
            for file_name in os.listdir(self.active_rules_path):
                if file_name.endswith('.json'):
                    shutil.copy2(
                        os.path.join(self.active_rules_path, file_name),
                        os.path.join(active_backup, file_name)
                    )
            
            # Copy rule index
            index_path = os.path.join(self.rules_path, "rule_index.json")
            if os.path.exists(index_path):
                shutil.copy2(index_path, os.path.join(backup_dir, "rule_index.json"))
            
            self.logger.info(f"Created rules backup: {backup_dir}")
            
            # Clean up old backups if needed
            self._clean_old_backups()
            
            return backup_dir
            
        except Exception as e:
            self.logger.error(f"Error creating backup: {e}")
            raise RuleRepositoryError(f"Failed to create backup: {e}")
    
    def _clean_old_backups(self):
        """Remove old backups exceeding the maximum allowed."""
        if not os.path.exists(self.backups_path):
            return
        
        backups = [d for d in os.listdir(self.backups_path) if d.startswith("backup_")]
        
        if len(backups) <= self.max_backups:
            return
        
        # Sort backups by name (timestamp) in ascending order
        backups.sort()
        
        # Delete oldest backups
        for old_backup in backups[:len(backups) - self.max_backups]:
            old_path = os.path.join(self.backups_path, old_backup)
            try:
                shutil.rmtree(old_path)
                self.logger.debug(f"Removed old backup: {old_path}")
            except Exception as e:
                self.logger.warning(f"Failed to remove old backup {old_path}: {e}")
    
    def _validate_rule(self, rule: Dict[str, Any]) -> bool:
        """
        Validate a rule's structure and content.
        
        Args:
            rule: Rule to validate
            
        Returns:
            True if valid, False otherwise
        """
        if not self.validate_on_save:
            return True
            
        # Check for required fields
        required_fields = ["id", "type", "conditions", "actions"]
        for field in required_fields:
            if field not in rule:
                self.logger.warning(f"Rule validation failed: missing required field '{field}'")
                return False
        
        # Check ID format
        if not isinstance(rule["id"], str):
            self.logger.warning("Rule validation failed: ID must be a string")
            return False
        
        # Check conditions and actions are lists
        if not isinstance(rule.get("conditions", []), list):
            self.logger.warning("Rule validation failed: conditions must be a list")
            return False
            
        if not isinstance(rule.get("actions", []), list):
            self.logger.warning("Rule validation failed: actions must be a list")
            return False
        
        # Add more validation rules as needed...
        
        return True
    
    def _get_rule_path(self, rule_id: str, version: Optional[int] = None) -> str:
        """
        Get the file path for a rule.
        
        Args:
            rule_id: ID of the rule
            version: Optional version number
            
        Returns:
            File path for the rule
        """
        # Get rule info from index
        rule_info = self.rule_index.get(rule_id)
        
        if not rule_info:
            raise RuleRepositoryError(f"Rule not found: {rule_id}")
        
        # Determine which version to use
        if version is None:
            # Use latest version by default
            version = rule_info["latest_version"]
        elif version > rule_info["latest_version"] or version < 1:
            raise RuleRepositoryError(f"Invalid version {version} for rule {rule_id}. " 
                                     f"Valid versions: 1-{rule_info['latest_version']}")
        
        # Determine location based on status
        if rule_info["status"] == RuleStatus.ARCHIVED.value:
            base_path = self.archive_path
        else:
            base_path = self.active_rules_path
        
        # Construct filename with version
        filename = f"{rule_id}_v{version}.json"
        return os.path.join(base_path, filename)
    
    def add_rule(self, rule: Dict[str, Any], activate: bool = True) -> Dict[str, Any]:
        """
        Add a new rule to the repository.
        
        Args:
            rule: Rule to add
            activate: Whether to activate the rule immediately
            
        Returns:
            Added rule with repository metadata
        """
        # Ensure rule has an ID
        if "id" not in rule:
            rule["id"] = f"rule_{int(time.time())}"
            self.logger.debug(f"Assigned ID to rule: {rule['id']}")
        
        rule_id = rule["id"]
        
        # Check if rule already exists
        if rule_id in self.rule_index:
            raise RuleRepositoryError(f"Rule with ID {rule_id} already exists. Use update_rule instead.")
        
        # Validate rule structure
        if not self._validate_rule(rule):
            raise RuleRepositoryError(f"Rule validation failed for rule {rule_id}")
        
        # Create backup before making changes
        self._create_backup()
        
        # Add repository metadata
        rule["metadata"] = rule.get("metadata", {})
        rule["metadata"].update({
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "version": 1,
            "status": RuleStatus.ACTIVE.value if activate else RuleStatus.DRAFT.value
        })
        
        # Add to index
        self.rule_index[rule_id] = {
            "id": rule_id,
            "type": rule.get("type", "unknown"),
            "latest_version": 1,
            "status": rule["metadata"]["status"],
            "created_at": rule["metadata"]["created_at"],
            "updated_at": rule["metadata"]["updated_at"],
            "versions": {
                "1": {
                    "created_at": rule["metadata"]["created_at"],
                    "status": rule["metadata"]["status"]
                }
            }
        }
        
        # Save rule file
        rule_path = os.path.join(
            self.active_rules_path, 
            f"{rule_id}_v1.json"
        )
        
        try:
            with open(rule_path, 'w') as f:
                json.dump(rule, f, indent=2)
        except Exception as e:
            self.logger.error(f"Error saving rule file: {e}")
            raise RuleRepositoryError(f"Failed to save rule file: {e}")
        
        # Save updated index
        self._save_rule_index()
        
        self.logger.info(f"Added new rule: {rule_id} (Status: {rule['metadata']['status']})")
        return rule
    
    def update_rule(self, rule: Dict[str, Any], create_new_version: bool = True) -> Dict[str, Any]:
        """
        Update an existing rule in the repository.
        
        Args:
            rule: Updated rule
            create_new_version: Whether to create a new version
            
        Returns:
            Updated rule with repository metadata
        """
        # Ensure rule has an ID
        if "id" not in rule:
            raise RuleRepositoryError("Cannot update rule without ID")
        
        rule_id = rule["id"]
        
        # Check if rule exists
        if rule_id not in self.rule_index:
            raise RuleRepositoryError(f"Rule with ID {rule_id} not found")
        
        # Validate rule structure
        if not self._validate_rule(rule):
            raise RuleRepositoryError(f"Rule validation failed for rule {rule_id}")
        
        # Create backup before making changes
        self._create_backup()
        
        # Get current rule info
        rule_info = self.rule_index[rule_id]
        current_version = rule_info["latest_version"]
        
        # Determine new version
        if create_new_version:
            new_version = current_version + 1
        else:
            new_version = current_version
        
        # Update repository metadata
        rule["metadata"] = rule.get("metadata", {})
        rule["metadata"].update({
            "updated_at": datetime.now().isoformat(),
            "version": new_version,
            "previous_version": current_version if create_new_version else rule["metadata"].get("previous_version"),
            "status": rule["metadata"].get("status", rule_info["status"])
        })
        
        # If this is a new version, copy created_at from the current version
        if create_new_version and "created_at" not in rule["metadata"]:
            try:
                current_rule = self.get_rule(rule_id)
                rule["metadata"]["created_at"] = current_rule["metadata"]["created_at"]
            except Exception:
                rule["metadata"]["created_at"] = datetime.now().isoformat()
        
        # Update index
        if create_new_version:
            rule_info["latest_version"] = new_version
            rule_info["versions"][str(new_version)] = {
                "created_at": datetime.now().isoformat(),
                "status": rule["metadata"]["status"]
            }
        
        rule_info["updated_at"] = rule["metadata"]["updated_at"]
        rule_info["status"] = rule["metadata"]["status"]
        
        # Save rule file
        rule_path = os.path.join(
            self.active_rules_path if rule_info["status"] != RuleStatus.ARCHIVED.value else self.archive_path, 
            f"{rule_id}_v{new_version}.json"
        )
        
        try:
            with open(rule_path, 'w') as f:
                json.dump(rule, f, indent=2)
        except Exception as e:
            self.logger.error(f"Error saving rule file: {e}")
            raise RuleRepositoryError(f"Failed to save rule file: {e}")
        
        # Save updated index
        self._save_rule_index()
        
        self.logger.info(
            f"Updated rule: {rule_id} "
            f"(Version: {new_version}, Status: {rule['metadata']['status']})"
        )
        return rule
    
    def get_rule(self, rule_id: str, version: Optional[int] = None) -> Dict[str, Any]:
        """
        Get a rule from the repository.
        
        Args:
            rule_id: ID of the rule to get
            version: Optional version number (defaults to latest)
            
        Returns:
            Rule dictionary
        """
        rule_path = self._get_rule_path(rule_id, version)
        
        try:
            with open(rule_path, 'r') as f:
                rule = json.load(f)
            
            # Track usage if enabled
            if self.track_usage:
                self._track_rule_access(rule_id, version)
            
            return rule
            
        except Exception as e:
            self.logger.error(f"Error loading rule {rule_id}: {e}")
            raise RuleRepositoryError(f"Failed to load rule {rule_id}: {e}")
    
    def _track_rule_access(self, rule_id: str, version: Optional[int] = None):
        """Track rule access for usage statistics."""
        # This is a placeholder for rule usage tracking
        # In a real implementation, this would update access counters,
        # timestamps, etc.
        pass
    
    def delete_rule(self, rule_id: str, hard_delete: bool = False) -> bool:
        """
        Delete a rule from the repository.
        
        Args:
            rule_id: ID of the rule to delete
            hard_delete: If True, permanently delete; if False, archive
            
        Returns:
            True if successful
        """
        if rule_id not in self.rule_index:
            raise RuleRepositoryError(f"Rule with ID {rule_id} not found")
        
        # Create backup before making changes
        self._create_backup()
        
        rule_info = self.rule_index[rule_id]
        
        if hard_delete:
            # Permanently delete all versions
            for version in range(1, rule_info["latest_version"] + 1):
                try:
                    # Try both active and archive paths
                    active_path = os.path.join(self.active_rules_path, f"{rule_id}_v{version}.json")
                    archive_path = os.path.join(self.archive_path, f"{rule_id}_v{version}.json")
                    
                    if os.path.exists(active_path):
                        os.remove(active_path)
                    elif os.path.exists(archive_path):
                        os.remove(archive_path)
                except Exception as e:
                    self.logger.warning(f"Error deleting rule file {rule_id}_v{version}.json: {e}")
            
            # Remove from index
            del self.rule_index[rule_id]
            self._save_rule_index()
            
            self.logger.info(f"Permanently deleted rule: {rule_id}")
            
        else:
            # Archive the rule
            current_rule = self.get_rule(rule_id)
            
            # Update metadata
            current_rule["metadata"]["status"] = RuleStatus.ARCHIVED.value
            current_rule["metadata"]["archived_at"] = datetime.now().isoformat()
            
            # Update index
            rule_info["status"] = RuleStatus.ARCHIVED.value
            
            # Move all versions to archive
            for version in range(1, rule_info["latest_version"] + 1):
                try:
                    src_path = os.path.join(self.active_rules_path, f"{rule_id}_v{version}.json")
                    dst_path = os.path.join(self.archive_path, f"{rule_id}_v{version}.json")
                    
                    # Only move if file exists in active path
                    if os.path.exists(src_path):
                        # Ensure we have the updated metadata for the latest version
                        if version == rule_info["latest_version"]:
                            with open(src_path, 'w') as f:
                                json.dump(current_rule, f, indent=2)
                        
                        # Move to archive
                        shutil.move(src_path, dst_path)
                except Exception as e:
                    self.logger.warning(f"Error archiving rule file {rule_id}_v{version}.json: {e}")
            
            # Save updated index
            self._save_rule_index()
            
            self.logger.info(f"Archived rule: {rule_id}")
        
        return True
    
    def change_rule_status(self, rule_id: str, status: RuleStatus) -> Dict[str, Any]:
        """
        Change the status of a rule.
        
        Args:
            rule_id: ID of the rule
            status: New status
            
        Returns:
            Updated rule
        """
        if rule_id not in self.rule_index:
            raise RuleRepositoryError(f"Rule with ID {rule_id} not found")
        
        # Special handling for ARCHIVED status
        if status == RuleStatus.ARCHIVED:
            return self.delete_rule(rule_id, hard_delete=False)
        
        # Get current rule
        current_rule = self.get_rule(rule_id)
        
        # Update status
        current_rule["metadata"]["status"] = status.value
        current_rule["metadata"]["status_changed_at"] = datetime.now().isoformat()
        
        # Update index
        self.rule_index[rule_id]["status"] = status.value
        
        # Save changes
        return self.update_rule(current_rule, create_new_version=False)
    
    def list_rules(self, 
                  rule_type: Optional[str] = None,
                  status: Optional[RuleStatus] = None,
                  limit: Optional[int] = None,
                  offset: int = 0) -> List[Dict[str, Any]]:
        """
        List rules in the repository.
        
        Args:
            rule_type: Optional filter by rule type
            status: Optional filter by status
            limit: Optional maximum number of rules to return
            offset: Number of rules to skip
            
        Returns:
            List of rule summaries
        """
        # Filter rules based on criteria
        filtered_rules = []
        
        for rule_id, rule_info in self.rule_index.items():
            # Apply type filter
            if rule_type is not None and rule_info["type"] != rule_type:
                continue
            
            # Apply status filter
            if status is not None and rule_info["status"] != status.value:
                continue
            
            # Add to results
            filtered_rules.append({
                "id": rule_id,
                "type": rule_info["type"],
                "status": rule_info["status"],
                "latest_version": rule_info["latest_version"],
                "created_at": rule_info["created_at"],
                "updated_at": rule_info["updated_at"]
            })
        
        # Sort by updated_at (newest first)
        filtered_rules.sort(key=lambda r: r["updated_at"], reverse=True)
        
        # Apply pagination
        paginated_rules = filtered_rules[offset:]
        if limit is not None:
            paginated_rules = paginated_rules[:limit]
        
        return paginated_rules
    
    def search_rules(self, query: Dict[str, Any], limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Search for rules matching the query criteria.
        
        Args:
            query: Search criteria
            limit: Optional maximum number of results
            
        Returns:
            List of matching rules
        """
        # This is a basic implementation - in a real system, this would be more sophisticated
        all_rules = []
        
        # Load all rules that may match
        for rule_id in self.rule_index:
            try:
                rule = self.get_rule(rule_id)
                all_rules.append(rule)
            except Exception as e:
                self.logger.warning(f"Error loading rule {rule_id} during search: {e}")
        
        # Filter rules based on query criteria
        results = []
        
        for rule in all_rules:
            matches = True
            
            for key, value in query.items():
                # Handle nested keys (e.g., metadata.created_at)
                if "." in key:
                    parts = key.split(".")
                    current = rule
                    for part in parts:
                        if part not in current:
                            matches = False
                            break
                        current = current[part]
                    
                    if matches and current != value:
                        matches = False
                
                # Handle top-level keys
                elif key not in rule or rule[key] != value:
                    matches = False
            
            if matches:
                results.append(rule)
            
            # Apply limit if specified
            if limit is not None and len(results) >= limit:
                break
        
        return results
    
    def get_rule_history(self, rule_id: str) -> Dict[str, Any]:
        """
        Get the version history of a rule.
        
        Args:
            rule_id: ID of the rule
            
        Returns:
            Rule history information
        """
        if rule_id not in self.rule_index:
            raise RuleRepositoryError(f"Rule with ID {rule_id} not found")
        
        rule_info = self.rule_index[rule_id]
        
        # Collect basic info and version history
        history = {
            "id": rule_id,
            "type": rule_info["type"],
            "current_status": rule_info["status"],
            "latest_version": rule_info["latest_version"],
            "created_at": rule_info["created_at"],
            "updated_at": rule_info["updated_at"],
            "versions": []
        }
        
        # Get details for each version
        for version in range(1, rule_info["latest_version"] + 1):
            try:
                version_info = rule_info["versions"].get(str(version), {})
                
                # Try to load additional metadata from the actual rule file
                try:
                    rule = self.get_rule(rule_id, version)
                    version_metadata = rule.get("metadata", {})
                except Exception:
                    version_metadata = {}
                
                history["versions"].append({
                    "version": version,
                    "created_at": version_info.get("created_at"),
                    "status": version_info.get("status"),
                    "is_latest": version == rule_info["latest_version"],
                    "metadata": version_metadata
                })
            except Exception as e:
                self.logger.warning(f"Error getting history for {rule_id} v{version}: {e}")
        
        return history
    
    def restore_backup(self, backup_name: str) -> bool:
        """
        Restore rules from a backup.
        
        Args:
            backup_name: Name of the backup directory
            
        Returns:
            True if successful
        """
        backup_path = os.path.join(self.backups_path, backup_name)
        
        if not os.path.exists(backup_path):
            raise RuleRepositoryError(f"Backup not found: {backup_name}")
        
        try:
            # Create a backup of current state before restoring
            current_backup = self._create_backup()
            
            # Clear active rules directory
            for file_name in os.listdir(self.active_rules_path):
                if file_name.endswith('.json'):
                    os.remove(os.path.join(self.active_rules_path, file_name))
            
            # Copy rules from backup
            backup_active = os.path.join(backup_path, "active")
            if os.path.exists(backup_active):
                for file_name in os.listdir(backup_active):
                    if file_name.endswith('.json'):
                        shutil.copy2(
                            os.path.join(backup_active, file_name),
                            os.path.join(self.active_rules_path, file_name)
                        )
            
            # Restore rule index
            backup_index = os.path.join(backup_path, "rule_index.json")
            if os.path.exists(backup_index):
                shutil.copy2(
                    backup_index,
                    os.path.join(self.rules_path, "rule_index.json")
                )
                
                # Reload rule index
                self._load_rule_index()
            
            self.logger.info(f"Restored rules from backup: {backup_name}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error restoring from backup: {e}")
            raise RuleRepositoryError(f"Failed to restore from backup: {e}")
    
    def list_backups(self) -> List[Dict[str, Any]]:
        """
        List available backups.
        
        Returns:
            List of backup information
        """
        if not os.path.exists(self.backups_path):
            return []
        
        backups = []
        
        for backup_dir in os.listdir(self.backups_path):
            if not backup_dir.startswith("backup_"):
                continue
                
            backup_path = os.path.join(self.backups_path, backup_dir)
            
            if not os.path.isdir(backup_path):
                continue
                
            # Extract timestamp from directory name
            try:
                timestamp_str = backup_dir.replace("backup_", "")
                timestamp = datetime.strptime(timestamp_str, "%Y%m%d_%H%M%S")
                
                # Count rules in backup
                rule_count = 0
                active_dir = os.path.join(backup_path, "active")
                if os.path.exists(active_dir):
                    rule_count = len([f for f in os.listdir(active_dir) if f.endswith('.json')])
                
                backups.append({
                    "name": backup_dir,
                    "created_at": timestamp.isoformat(),
                    "rule_count": rule_count
                })
            except Exception as e:
                self.logger.warning(f"Error processing backup {backup_dir}: {e}")
        
        # Sort by timestamp (newest first)
        backups.sort(key=lambda b: b["created_at"], reverse=True)
        
        return backups


def get_rule_repository(config: Optional[Dict[str, Any]] = None) -> RuleRepository:
    """
    Get the singleton instance of RuleRepository.
    
    Args:
        config: Optional configuration dictionary
        
    Returns:
        RuleRepository instance
    """
    return RuleRepository.get_instance(config)