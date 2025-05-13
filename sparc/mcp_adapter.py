"""
SPARC MCP Adapter

This module provides low-level integration with MCP servers.
It handles the actual mechanics of MCP calls including formatting,
execution, response parsing, and error handling.
"""

import json
import logging
import os
import time
import tempfile
from typing import Dict, Any, Optional, Union

# Configure logging
logger = logging.getLogger(__name__)

# Constants
MAX_RETRIES = 3
RETRY_DELAY_BASE = 1.0  # seconds
CIRCUIT_BREAKER_THRESHOLD = 5  # failures
CIRCUIT_BREAKER_RESET_TIME = 60  # seconds

# Circuit breaker state
_circuit_breakers = {}  # server_name -> {failures: int, last_failure_time: float}


def execute_raw_mcp_call(server_name: str, tool_name: str, arguments: Dict[str, Any]) -> str:
    """
    Execute a raw MCP call to the specified server.
    
    This is the lowest-level function for making MCP calls. It handles:
    - Circuit breaking to protect services
    - Proper formatting of MCP requests
    - Response parsing and validation
    - Error handling

    Args:
        server_name: The name of the MCP server
        tool_name: The name of the tool to execute
        arguments: A dictionary of arguments for the tool
        
    Returns:
        The string result from the MCP tool
        
    Raises:
        ValueError: If the MCP call fails or is invalid
        RuntimeError: If the circuit breaker is open
    """
    # Check circuit breaker
    if _is_circuit_open(server_name):
        raise RuntimeError(f"Circuit breaker open for server '{server_name}'")
    
    try:
        # Validate inputs
        if not server_name:
            raise ValueError("Server name cannot be empty")
        if not tool_name:
            raise ValueError("Tool name cannot be empty")
        if not isinstance(arguments, dict):
            raise TypeError("Arguments must be a dictionary")
        
        # Format arguments as JSON
        arguments_json = json.dumps(arguments, default=str)
        
        # Execute the MCP call via the system's mechanism
        # This is where we'd use the actual platform-specific way to make MCP calls
        # For now, we'll implement a development version that uses temporary files
        response = _execute_mcp_call_dev_mode(server_name, tool_name, arguments_json)
        
        # Reset circuit breaker on success
        _reset_circuit_breaker(server_name)
        
        return response
        
    except Exception as e:
        # Increment circuit breaker failure count
        _record_failure(server_name)
        
        logger.error(f"Error executing raw MCP call to {server_name}/{tool_name}: {str(e)}")
        raise ValueError(f"MCP call failed: {str(e)}") from e


def _execute_mcp_call_dev_mode(server_name: str, tool_name: str, arguments_json: str) -> str:
    """
    Development-mode implementation of MCP calls.
    
    In production, this would be replaced with the platform's actual mechanism.
    
    Args:
        server_name: The name of the MCP server
        tool_name: The name of the tool to execute
        arguments_json: JSON-formatted arguments
        
    Returns:
        The string result from the MCP tool
    """
    # Only for development/testing environments
    sparc_env_value = os.environ.get("SPARC_ENV")
    # Make the check case-insensitive for string values
    if isinstance(sparc_env_value, str):
        sparc_env_value = sparc_env_value.lower()
        
    if sparc_env_value not in ["development", "testing", None]:
        raise ValueError("Development mode MCP calls are only available in development/testing environments")
    
    # In a real implementation, this would use the platform's MCP call mechanism
    # For now, we'll simulate it with a placeholder
    
    # Check for expected tools and provide simulated responses
    if server_name == "context7" and tool_name == "resolve-library-id":
        args = json.loads(arguments_json)
        library_name = args.get("libraryName", "")
        return _simulate_resolve_library_id(library_name)
    
    elif server_name == "context7" and tool_name == "get-library-docs":
        args = json.loads(arguments_json)
        library_id = args.get("context7CompatibleLibraryID", "")
        topic = args.get("topic", "")
        tokens = args.get("tokens", 10000)
        return _simulate_get_library_docs(library_id, topic, tokens)
    
    # For unknown tools, return a placeholder indicating we need a real implementation
    return f"[Simulated MCP response from {server_name}/{tool_name} with arguments: {arguments_json}]"


def _simulate_resolve_library_id(library_name: str) -> str:
    """
    Simulate the resolve-library-id tool response.
    This is only for development/testing.
    
    Args:
        library_name: The library name to resolve
        
    Returns:
        A simulated response as a string
    """
    if not library_name:
        return "Error: No library name provided"
    
    # Simulate a response with some fake library data
    return f"""
Available Libraries (top matches):

Each result includes:
- Library ID: Context7-compatible identifier
- Name: Library or package name
- Description: Short summary
- Code Snippets: Number of available code examples
- GitHub Stars: Popularity indicator

---

- Title: {library_name}
- Context7-compatible library ID: /{library_name.lower()}/docs
- Description: Official documentation for {library_name}
- Code Snippets: 2500
- GitHub Stars: 15000
---
- Title: {library_name}-contrib
- Context7-compatible library ID: /community/{library_name.lower()}-contrib
- Description: Community contributions for {library_name}
- Code Snippets: 650
- GitHub Stars: 2300
---
"""


def _simulate_get_library_docs(library_id: str, topic: str, tokens: int) -> str:
    """
    Simulate the get-library-docs tool response.
    This is only for development/testing.
    
    Args:
        library_id: The library ID to get docs for
        topic: Optional topic filter
        tokens: Maximum tokens to return
        
    Returns:
        A simulated response as a string
    """
    if not library_id:
        return "Error: No library ID provided"
    
    # Simulate a response with some fake documentation
    topic_str = f" on {topic}" if topic else ""
    
    return f"""
TITLE: {library_id} Documentation{topic_str}
DESCRIPTION: Simulated documentation for {library_id}

This is a simulated documentation response for {library_id}{topic_str}.
In a real environment, this would contain actual documentation content
from the Context7 service.

The content would include code examples, explanations, and reference material
relevant to the requested library and topic. The token limit would be respected.

This simulation is provided for development and testing purposes only.
"""


def _is_circuit_open(server_name: str) -> bool:
    """
    Check if the circuit breaker is open for a server.
    
    Args:
        server_name: The name of the server to check
        
    Returns:
        True if the circuit is open (too many failures), False otherwise
    """
    if server_name not in _circuit_breakers:
        return False
    
    breaker = _circuit_breakers[server_name]
    
    # If we've hit the threshold of failures
    if breaker["failures"] >= CIRCUIT_BREAKER_THRESHOLD:
        # Check if enough time has passed to attempt a reset
        time_since_failure = time.time() - breaker["last_failure_time"]
        if time_since_failure < CIRCUIT_BREAKER_RESET_TIME:
            # Circuit is still open
            return True
        
        # Enough time has passed, reset to half-open state
        breaker["failures"] = CIRCUIT_BREAKER_THRESHOLD - 1
        
    # Circuit is closed or half-open
    return False


def _record_failure(server_name: str) -> None:
    """
    Record a failure for a server in the circuit breaker.
    
    Args:
        server_name: The name of the server
    """
    now = time.time()
    
    if server_name not in _circuit_breakers:
        _circuit_breakers[server_name] = {
            "failures": 1,
            "last_failure_time": now
        }
    else:
        breaker = _circuit_breakers[server_name]
        breaker["failures"] += 1
        breaker["last_failure_time"] = now


def _reset_circuit_breaker(server_name: str) -> None:
    """
    Reset the circuit breaker for a server after a successful call.
    
    Args:
        server_name: The name of the server
    """
    if server_name in _circuit_breakers:
        _circuit_breakers[server_name]["failures"] = 0