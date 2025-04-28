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

class UpgradeSandboxManager:
    def __init__(self, sandbox_dir: str = "data/upgrade_sandbox"):
        """
        Initialize the Upgrade Sandbox Manager.

        Args:
            sandbox_dir (str): Directory to store pending upgrades.
        """
        self.sandbox_dir = sandbox_dir
        os.makedirs(self.sandbox_dir, exist_ok=True)
        self.pending_upgrades_path = os.path.join(self.sandbox_dir, "pending_upgrades.jsonl")

    def submit_upgrade(self, upgrade_data: Dict[str, Any]) -> str:
        """
        Submit a new proposed upgrade to the sandbox.

        Args:
            upgrade_data (Dict[str, Any]): Upgrade proposal data.

        Returns:
            str: Unique upgrade ID assigned.
        """
        upgrade_id = str(uuid.uuid4())
        upgrade_data["upgrade_id"] = upgrade_id
        with open(self.pending_upgrades_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(upgrade_data) + "\n")
        print(f"[Sandbox] ✅ Upgrade proposal {upgrade_id} submitted.")
        return upgrade_id

    def list_pending_upgrades(self) -> List[str]:
        """
        List all pending upgrade IDs.

        Returns:
            List[str]: Upgrade IDs.
        """
        upgrades = []
        if os.path.exists(self.pending_upgrades_path):
            with open(self.pending_upgrades_path, "r", encoding="utf-8") as f:
                for line in f:
                    upgrade = json.loads(line)
                    upgrades.append(upgrade.get("upgrade_id", "unknown"))
        return upgrades

    def get_upgrade_details(self, upgrade_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve details for a specific pending upgrade.

        Args:
            upgrade_id (str): The unique upgrade ID.

        Returns:
            Optional[Dict[str, Any]]: Upgrade data if found.
        """
        if os.path.exists(self.pending_upgrades_path):
            with open(self.pending_upgrades_path, "r", encoding="utf-8") as f:
                for line in f:
                    upgrade = json.loads(line)
                    if upgrade.get("upgrade_id") == upgrade_id:
                        return upgrade
        return None

# Example CLI usage for testing
if __name__ == "__main__":
    print("[UpgradeSandbox] 🚀 Running standalone sandbox test...")
    sandbox = UpgradeSandboxManager()
    dummy_upgrade = {
        "proposed_variables": ["hope_drift", "trust_collapse"],
        "proposed_consequences": ["market_stability_shift"],
        "notes": "Test upgrade example."
    }
    upgrade_id = sandbox.submit_upgrade(dummy_upgrade)
    print("[UpgradeSandbox] Pending upgrades:", sandbox.list_pending_upgrades())
    if upgrade_id:
        print("[UpgradeSandbox] Details for upgrade:", sandbox.get_upgrade_details(upgrade_id))
