"""
Context7 Integration Example

This example demonstrates how to use the Context7 client to retrieve
documentation for Python libraries through the Context7 MCP server.
"""

import os
import logging
from utils.context7_client import Context7Client, get_library_documentation

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def basic_usage_example():
    """Demonstrates the basic usage of the Context7 client."""
    print("\n===== Basic Usage Example =====\n")

    # Using the convenience function
    print("Retrieving Python documentation...")
    python_docs = get_library_documentation("python", tokens=2000)

    # Display first 500 characters
    print(f"\nDocumentation preview (first 500 chars):\n{python_docs[:500]}...\n")

    print("Documentation retrieved successfully!\n")


def advanced_usage_example():
    """Demonstrates more advanced usage of the Context7 client."""
    print("\n===== Advanced Usage Example =====\n")

    # Creating a client instance
    client = Context7Client()

    # First resolve a library ID
    print("Resolving library ID for 'numpy'...")
    library_id = client.resolve_library_id("numpy")
    print(f"Resolved ID: {library_id}")

    # Get documentation for a specific topic
    print("\nRetrieving documentation for 'numpy' on topic 'arrays'...")
    docs = client.get_library_docs(library_id, topic="arrays", tokens=3000)

    # Display first 500 characters
    print(f"\nDocumentation preview (first 500 chars):\n{docs[:500]}...\n")

    print("Documentation retrieved successfully!\n")


def error_handling_example():
    """Demonstrates error handling with the Context7 client."""
    print("\n===== Error Handling Example =====\n")

    try:
        # Try to get documentation for a non-existent library
        print("Attempting to retrieve documentation for a non-existent library...")
        _ = get_library_documentation("this_library_does_not_exist_123456789")
    except ValueError as e:
        print(f"Caught error as expected: {e}")


def environment_example():
    """Demonstrates how environment settings affect the Context7 client."""
    print("\n===== Environment Configuration Example =====\n")

    # Save current environment
    old_env = os.environ.get("SPARC_ENV")

    try:
        # Set to development mode
        os.environ["SPARC_ENV"] = "development"
        print("Using development mode...")

        _ = Context7Client() # Instantiation is part of the example
        print("Client initialized in development mode")

        # Get documentation
        docs = get_library_documentation("pandas", tokens=1000)
        print(f"Retrieved {len(docs)} characters of documentation in development mode")

        # Switch to production mode if you want to test with real server
        # Note: This will actually contact the server, so it's commented out
        # os.environ["SPARC_ENV"] = "production"
        # print("\nSwitching to production mode...")
        #
        # client = Context7Client()
        # print("Client initialized in production mode")
        #
        # # Get documentation
        # docs = get_library_documentation("pandas", tokens=1000)
        # print(f"Retrieved {len(docs)} characters of documentation in production mode")

    finally:
        # Restore original environment
        if old_env is not None:
            os.environ["SPARC_ENV"] = old_env
        else:
            del os.environ["SPARC_ENV"]


def main():
    """Run all examples."""
    print("\nContext7 Integration Examples\n" + "=" * 30)

    basic_usage_example()
    advanced_usage_example()
    error_handling_example()
    environment_example()

    print("\nAll examples completed successfully!")


if __name__ == "__main__":
    main()
