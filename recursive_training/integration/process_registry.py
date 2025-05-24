"""
Process Registry for Recursive Learning

Provides a simple registry for keeping track of running recursive learning processes.
This allows for monitoring and controlling long-running training processes from
the conversational interface.
"""

import threading
from typing import Dict, List, Any, Optional

# Thread-safe lock for registry access
_registry_lock = threading.RLock()

# Global registry of active processes
_process_registry: Dict[str, Any] = {}


def register_process(process_id: str, process_obj: Any) -> None:
    """
    Register a process in the registry.

    Args:
        process_id: Unique identifier for the process
        process_obj: The process object (typically a ParallelTrainingCoordinator)
    """
    with _registry_lock:
        _process_registry[process_id] = process_obj


def unregister_process(process_id: str) -> bool:
    """
    Remove a process from the registry.

    Args:
        process_id: Identifier of the process to remove

    Returns:
        bool: True if the process was found and removed, False otherwise
    """
    with _registry_lock:
        if process_id in _process_registry:
            del _process_registry[process_id]
            return True
        return False


def get_process(process_id: str) -> Optional[Any]:
    """
    Get a process from the registry.

    Args:
        process_id: Identifier of the process to get

    Returns:
        The process object, or None if not found
    """
    with _registry_lock:
        return _process_registry.get(process_id)


def list_processes() -> List[str]:
    """
    List all process IDs in the registry.

    Returns:
        List of process IDs
    """
    with _registry_lock:
        return list(_process_registry.keys())


def get_all_processes() -> Dict[str, Any]:
    """
    Get all processes in the registry.

    Returns:
        Dictionary mapping process IDs to process objects
    """
    with _registry_lock:
        # Return a copy to avoid clients modifying the registry directly
        return dict(_process_registry)


def clear_registry() -> int:
    """
    Clear all processes from the registry.

    Returns:
        Number of processes removed
    """
    with _registry_lock:
        count = len(_process_registry)
        _process_registry.clear()
        return count
