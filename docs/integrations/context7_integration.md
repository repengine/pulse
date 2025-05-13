# Context7 Integration with SPARC

This document provides information about the integration between SPARC and the Context7 MCP server for accessing up-to-date library documentation.

## Overview

Context7 is an MCP server that provides access to current documentation for various libraries and frameworks. This integration allows SPARC to retrieve the most recent documentation for Python and other libraries during development and analysis tasks.

## Architecture

The integration follows a layered architecture:

1. **MCP Interface Layer** (`sparc/mcp_interface.py`): Provides low-level communication with MCP servers
2. **Context7 Client** (`utils/context7_client.py`): High-level client that simplifies interactions with Context7
3. **Application Layer**: Application code that uses the Context7 client to retrieve documentation

## Usage

### Basic Usage

```python
from utils import get_library_documentation

# Get documentation for a library (resolves ID and fetches docs in one call)
python_docs = get_library_documentation("python")

# Get documentation for a specific topic
exception_docs = get_library_documentation("python", topic="exception handling")

# Limit the token count
limited_docs = get_library_documentation("python", tokens=5000)
```

### Advanced Usage

```python
from utils import Context7Client

# Create a client instance
client = Context7Client()

# First resolve a library ID
library_id = client.resolve_library_id("python")
print(f"Resolved ID: {library_id}")  # e.g., "/python/cpython"

# Then get documentation using the ID
docs = client.get_library_docs(library_id, topic="exception handling")
```

## Features

- **Library ID Resolution**: Automatically finds the correct Context7-compatible library ID
- **Topic Filtering**: Retrieve documentation focused on specific topics
- **Token Control**: Limit the amount of documentation retrieved
- **Error Handling**: Robust error handling with meaningful error messages
- **Server Verification**: Checks server availability before operations
- **Development Mode**: Supports development environment with simulated responses

## Error Handling

The integration includes comprehensive error handling:

- Server unavailability detection
- Invalid library name handling
- Documentation retrieval errors
- Input validation for all parameters

Example:

```python
try:
    docs = get_library_documentation("non_existent_library")
except ValueError as e:
    print(f"Error: {e}")
```

## Testing

A test suite is available in `tests/test_context7_integration.py` that verifies:

- Connection to the Context7 MCP server
- Library ID resolution
- Documentation retrieval
- Error handling
- Development vs. production modes

Run the tests with:

```
pytest tests/test_context7_integration.py
```

## Environment Configuration

The integration checks for the `SPARC_ENV` environment variable:

- `development`: Uses simulated responses for testing
- `production`: Connects to the actual Context7 MCP server

## Dependencies

- `sparc.mcp_interface` module for MCP communication
- Python 3.7 or higher
- Logging system for error and operation logging

## Security Considerations

- No credentials are stored in code
- All errors are properly logged but don't expose sensitive information
- Input validation is performed on all parameters

## Limitations

- Documentation retrieval is limited by token count
- Some libraries might not be available in Context7
- Topic filtering depends on the library's documentation structure

## Troubleshooting

1. **Server Connectivity Issues**:
   - Verify the Context7 MCP server is running
   - Check network connectivity

2. **Library Not Found**:
   - Ensure the library name is correct
   - Try alternative names or spellings

3. **Documentation Not Relevant**:
   - Refine the topic parameter
   - Increase the token limit

## Future Enhancements

- Caching mechanism for frequently accessed documentation
- Batch operations for multiple libraries
- Enhanced filtering capabilities
- Documentation comparison between versions