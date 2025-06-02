"""
Context7 Client

A high-level client for interacting with the Context7 MCP server,
which provides access to up-to-date library documentation.
"""

import logging
from typing import Optional

# Import the MCP interface
# from sparc.mcp_interface import execute_mcp_tool # Commented out as
# sparc is not desired

# Configure logging
logger = logging.getLogger(__name__)

# Constants
DEFAULT_TOKEN_LIMIT = 10000
SERVER_NAME = "context7"
RESOLVE_TOOL = "resolve-library-id"
DOCS_TOOL = "get-library-docs"


class Context7Client:
    """
    Client for the Context7 MCP server.

    This client provides a high-level interface to the Context7 MCP server,
    which provides access to up-to-date library documentation.
    """

    def __init__(self):
        """Initialize the Context7 client."""
        pass  # No server verification needed for mock implementation

    def resolve_library_id(self, library_name: str, _verify_only: bool = False) -> str:
        """
        Resolve a library name to a Context7-compatible library ID.

        Args:
            library_name: The name of the library to resolve
            _verify_only: Internal parameter used for server availability checks

        Returns:
            The Context7-compatible library ID

        Raises:
            ValueError: If the library name is invalid or the library cannot be found
        """
        # Validate input
        if not library_name:
            raise ValueError("Library name cannot be empty")

        # Log the operation
        logger.info(f"Resolving library ID for '{library_name}'")

        # For mock implementation, just return a formatted library ID
        return f"/{library_name.lower()}/docs"

    def get_library_docs(
        self,
        library_id: str,
        topic: Optional[str] = None,
        tokens: int = DEFAULT_TOKEN_LIMIT,
    ) -> str:
        """
        Get documentation for a specific library.

        Args:
            library_id: The Context7-compatible library ID (from resolve_library_id)
            topic: Optional topic to focus the documentation on
            tokens: Maximum number of tokens to return

        Returns:
            The documentation content as a string

        Raises:
            ValueError: If the library ID is invalid or the documentation cannot be retrieved
        """
        # Validate inputs
        if not library_id:
            raise ValueError("Library ID cannot be empty")
        if tokens <= 0:
            raise ValueError("Token limit must be positive")

        # Log the operation
        logger.info(
            f"Getting documentation for '{library_id}'{
                ' on topic: ' +
                topic if topic else ''}")

        # For mock implementation, return simulated documentation
        content = f"Documentation for {library_id}"
        if topic:
            content += f" on topic: {topic}"

        # Add some fake content to make it look more realistic
        content += "\n\n# Overview\n\nThis is simulated documentation for development and testing purposes.\n"
        content += "\n## Usage Examples\n\n```python\n# Example code would be here\nprint('Hello, world!')\n```\n"

        logger.info(f"Retrieved {len(content)} characters of documentation")
        return content


def get_library_documentation(
    library_name: str, topic: Optional[str] = None, tokens: int = DEFAULT_TOKEN_LIMIT
) -> str:
    """
    Convenience function to get documentation for a library in one step.

    This function resolves the library ID and gets the documentation in a single call.

    Args:
        library_name: The name of the library to get documentation for
        topic: Optional topic to focus the documentation on
        tokens: Maximum number of tokens to return

    Returns:
        The documentation content as a string

    Raises:
            ValueError: If the library name is invalid or the documentation cannot be retrieved,
                    or if client initialization fails due to an MCP error.
    """
    try:
        client = Context7Client()
        # If init succeeds, proceed to use the client
        library_id = client.resolve_library_id(library_name)
        return client.get_library_docs(library_id, topic=topic, tokens=tokens)

    except Exception as e:
        # Catch any unexpected errors during the process and wrap them.
        logger.error(
            f"An unexpected error occurred in get_library_documentation for '{library_name}': {e}")
        raise ValueError(
            f"Unexpected error in Context7 operation for '{library_name}': {e}"
        ) from e
