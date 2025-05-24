# pulse/intelligence/upgrade_sandbox_manager.py

"""
Pulse Upgrade Sandbox Manager

Receives, stores, and manages epistemic upgrade proposals before trust-gated promotion.

- Submit new upgrade proposals
- List pending upgrades
- Retrieve details for review

Author: Pulse Intelligence Core
Version: 0.5
"""

import json
import os
import uuid
from typing import Dict, Any, List, Optional
from intelligence.intelligence_config import UPGRADE_SANDBOX_DIR


class UpgradeSandboxManager:
    """
    Manages epistemic upgrade proposals in a sandbox directory.
    """

    def __init__(self, sandbox_dir: str = UPGRADE_SANDBOX_DIR) -> None:
        """
        Initialize the Upgrade Sandbox Manager.

        Args:
            sandbox_dir: Directory to store pending upgrades.
        """
        self.sandbox_dir: str = sandbox_dir
        os.makedirs(self.sandbox_dir, exist_ok=True)
        self.pending_upgrades_path: str = os.path.join(
            self.sandbox_dir, "pending_upgrades.jsonl"
        )

    def submit_upgrade(self, upgrade_data: Dict[str, Any]) -> str:
        """
        Submit a new proposed upgrade to the sandbox.

        Assigns a unique ID and appends the proposal to a JSONL file.

        Args:
            upgrade_data: Upgrade proposal data (dictionary).

        Returns:
            The unique upgrade ID assigned to the proposal.
        """
        upgrade_id: str = str(uuid.uuid4())
        upgrade_data["upgrade_id"] = upgrade_id
        try:
            with open(self.pending_upgrades_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(upgrade_data) + "\n")
            print(f"[Sandbox] ✅ Upgrade proposal {upgrade_id} submitted.")
        except IOError as e:
            print(
                f"[Sandbox] ❌ Error writing upgrade proposal to {self.pending_upgrades_path}: {e}"
            )
            # Depending on desired error handling, you might re-raise or return a specific error indicator
            raise
        return upgrade_id

    def list_pending_upgrades(self) -> List[str]:
        """
        List all pending upgrade IDs from the sandbox file.

        Returns:
            A list of upgrade IDs (strings). Returns an empty list if the file
            does not exist or is empty, or if there's a reading error.
        """
        upgrades: List[str] = []
        if not os.path.exists(self.pending_upgrades_path):
            return upgrades
        try:
            with open(self.pending_upgrades_path, "r", encoding="utf-8") as f:
                for line in f:
                    try:
                        upgrade: Dict[str, Any] = json.loads(line)
                        upgrades.append(upgrade.get("upgrade_id", "unknown"))
                    except json.JSONDecodeError as e:
                        print(
                            f"[Sandbox] ❌ Error decoding JSON line in {self.pending_upgrades_path}: {e}"
                        )
                        # Continue processing other lines
                        continue
        except IOError as e:
            print(
                f"[Sandbox] ❌ Error reading pending upgrades from {self.pending_upgrades_path}: {e}"
            )
            return []  # Return empty list on read error
        return upgrades

    def get_upgrade_details(self, upgrade_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve details for a specific pending upgrade by its ID.

        Reads through the pending upgrades file to find the matching ID.

        Args:
            upgrade_id: The unique upgrade ID (string).

        Returns:
            The upgrade data dictionary if found, otherwise None. Returns None
            if the file does not exist or there's a reading/decoding error.
        """
        if not os.path.exists(self.pending_upgrades_path):
            return None
        try:
            with open(self.pending_upgrades_path, "r", encoding="utf-8") as f:
                for line in f:
                    try:
                        upgrade: Dict[str, Any] = json.loads(line)
                        if upgrade.get("upgrade_id") == upgrade_id:
                            return upgrade
                    except json.JSONDecodeError as e:
                        print(
                            f"[Sandbox] ❌ Error decoding JSON line while searching for {upgrade_id} in {self.pending_upgrades_path}: {e}"
                        )
                        # Continue searching other lines
                        continue
        except IOError as e:
            print(
                f"[Sandbox] ❌ Error reading pending upgrades from {self.pending_upgrades_path}: {e}"
            )
            return None  # Return None on read error
        return None


# Example CLI usage for testing
if __name__ == "__main__":
    print("[UpgradeSandbox] 🚀 Running standalone sandbox test...")
    sandbox: UpgradeSandboxManager = UpgradeSandboxManager()
    dummy_upgrade: Dict[str, Any] = {
        "proposed_variables": ["hope_drift", "trust_collapse"],
        "proposed_consequences": ["market_stability_shift"],
        "notes": "Test upgrade example.",
    }
    upgrade_id: str = sandbox.submit_upgrade(dummy_upgrade)
    print("[UpgradeSandbox] Pending upgrades:", sandbox.list_pending_upgrades())
    if upgrade_id:
        details: Optional[Dict[str, Any]] = sandbox.get_upgrade_details(upgrade_id)
        print("[UpgradeSandbox] Details for upgrade:", details)
