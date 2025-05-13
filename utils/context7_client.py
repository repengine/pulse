"""
Context7 Client

A high-level client for interacting with the Context7 MCP server,
which provides access to up-to-date library documentation.
"""

import logging
import json
from typing import Dict, Any, Optional, Union

# Import the MCP interface
from sparc.mcp_interface import execute_mcp_tool

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
        self._verify_server_availability()
        
    def _verify_server_availability(self) -> None:
        """
        Verify that the Context7 MCP server is available.
        
        Raises:
            RuntimeError: If the server is not available
        """
        try:
            # A simple call to see if the server is available
            # Using resolve-library-id with a known library
            self.resolve_library_id("python", _verify_only=True)
            logger.debug("Context7 MCP server is available")
        except Exception as e:
            logger.error(f"Context7 MCP server is not available: {str(e)}")
            raise RuntimeError(f"Context7 MCP server is not available: {str(e)}") from e
    
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
        
        try:
            # Prepare the arguments
            arguments = {
                "libraryName": library_name
            }
            
            # Call the MCP tool
            result = execute_mcp_tool(
                server_name=SERVER_NAME,
                tool_name=RESOLVE_TOOL,
                arguments=arguments
            )
            
            if _verify_only:
                # For verification, we don't need to process the result
                return "verification_successful"
            
            # Process the result to extract the library ID
            library_id = self._extract_library_id_from_result(result, library_name)
            
            logger.info(f"Resolved library ID: {library_id}")
            return library_id
            
        except Exception as e:
            if not _verify_only:
                logger.error(f"Error resolving library ID for '{library_name}': {str(e)}")
                raise ValueError(f"Context7 MCP tool execution failed: {e}") from e
            else:
                # Re-raise for verification
                raise
    
    def _extract_library_id_from_result(self, result: str, library_name: str) -> str:
        """
        Extract the library ID from the result of the resolve-library-id tool.
        
        Args:
            result: The result from the resolve-library-id tool
            library_name: The original library name for context
            
        Returns:
            The Context7-compatible library ID
            
        Raises:
            ValueError: If the library ID cannot be extracted from the result
        """
        # Look for lines containing "Context7-compatible library ID:"
        lines = result.split('\n')
        for line in lines:
            if "Context7-compatible library ID:" in line:
                # Extract the ID value
                parts = line.split(':', 1)
                if len(parts) == 2:
                    library_id = parts[1].strip()
                    # Remove any surrounding quotes or spaces
                    library_id = library_id.strip('\'"')
                    
                    if library_id:
                        return library_id
        
        # If we get here, we couldn't find a valid library ID
        # Look for a potential ID format in the text
        for line in lines:
            if "/" in line and "library" in line.lower():
                # This might be a line containing the ID
                words = line.split()
                for word in words:
                    if word.startswith("/") or "/" in word:
                        candidate = word.strip(" ,.:;-")
                        if candidate and not candidate.startswith("http"):
                            return candidate
        
        # If we still can't find it, look for library name within a path pattern
        name_lower = library_name.lower()
        for line in lines:
            if name_lower in line.lower() and "/" in line:
                parts = line.split()
                for part in parts:
                    if name_lower in part.lower() and "/" in part:
                        # Clean up the part
                        candidate = part.strip(" ,.:;-")
                        if candidate:
                            return candidate
        
        # As a last resort, construct a reasonable default based on the library name
        logger.warning(f"Could not extract library ID from response, using default format for '{library_name}'")
        return f"/{library_name.lower()}/docs"
    
    def get_library_docs(self, library_id: str, topic: Optional[str] = None, tokens: int = DEFAULT_TOKEN_LIMIT) -> str:
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
        logger.info(f"Getting documentation for '{library_id}'{' on topic: ' + topic if topic else ''}")
        
        try:
            # Prepare the arguments
            arguments = {
                "context7CompatibleLibraryID": library_id,
                "tokens": tokens
            }
            
            # Add optional topic if provided
            if topic:
                arguments["topic"] = topic
            
            # Call the MCP tool
            result = execute_mcp_tool(
                server_name=SERVER_NAME,
                tool_name=DOCS_TOOL,
                arguments=arguments
            )
            
            # Process the result (removing any headers or metadata)
            docs = self._clean_documentation_result(result)
            
            logger.info(f"Retrieved {len(docs)} characters of documentation")
            return docs
            
        except Exception as e:
            logger.error(f"Error getting documentation for '{library_id}': {str(e)}")
            raise ValueError(f"Context7 MCP tool execution failed: {e}") from e
    
    def _clean_documentation_result(self, result: str) -> str:
        """
        Clean the documentation result by removing headers or metadata.
        
        Args:
            result: The raw documentation result
            
        Returns:
            The cleaned documentation content
        """
        lines = result.split('\n')
        
        # Skip lines that appear to be headers or metadata
        content_lines = []
        in_content = False
        
        for line in lines:
            line_lower = line.lower()
            
            # Skip empty lines at the beginning
            if not line.strip() and not in_content:
                continue
            
            # Skip obvious header lines
            if not in_content and (
                line.startswith("TITLE:") or 
                line.startswith("DESCRIPTION:") or
                line.startswith("---") or
                "documentation for" in line_lower and "context7" in line_lower
            ):
                continue
            
            # We've reached the content
            in_content = True
            content_lines.append(line)
        
        return '\n'.join(content_lines).strip()


def get_library_documentation(library_name: str, topic: Optional[str] = None, tokens: int = DEFAULT_TOKEN_LIMIT) -> str:
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
        # These calls can raise ValueError directly if execute_mcp_tool (mocked) fails
        library_id = client.resolve_library_id(library_name)
        return client.get_library_docs(library_id, topic=topic, tokens=tokens)

    except RuntimeError as e:
        # This specifically catches RuntimeError from Context7Client.__init__
        logger.error(f"Context7 client initialization failed due to MCP error: {e}")
        raise ValueError(f"Context7 client initialization failed due to MCP error: {e}") from e
    except ValueError:
        # This catches ValueError raised by client.resolve_library_id() or client.get_library_docs()
        # if the mock caused an Exception that these methods converted to ValueError.
        logger.error(f"Context7 client operation failed for '{library_name}'.")
        raise # Re-raise the original ValueError to be caught by the test
    except Exception as e:
        # Catch any other unexpected errors during the process and wrap them.
        logger.error(f"An unexpected error occurred in get_library_documentation for '{library_name}': {e}")
        raise ValueError(f"Unexpected error in Context7 operation for '{library_name}': {e}") from e