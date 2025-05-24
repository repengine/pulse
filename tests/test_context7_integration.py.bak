"""
Tests for Context7 MCP integration.

This module contains tests for the Context7 MCP integration,
verifying that the client can properly resolve library IDs and
retrieve documentation from the Context7 MCP server.
"""

import os
import unittest
from unittest import mock

# Import the modules we want to test
from utils.context7_client import Context7Client, get_library_documentation
from sparc.mcp_interface import execute_mcp_tool


class TestContext7Integration(unittest.TestCase):
    """Test suite for the Context7 MCP integration."""

    def setUp(self):
        """Set up the test environment."""
        # Enable development mode for tests
        os.environ["SPARC_ENV"] = "development"
        
        # Create a client instance
        self.client = Context7Client()

    def tearDown(self):
        """Clean up after tests."""
        # Remove environment variable
        if "SPARC_ENV" in os.environ:
            del os.environ["SPARC_ENV"]

    def test_resolve_library_id(self):
        """Test that the client can resolve a library ID."""
        # Test with a known library
        library_id = self.client.resolve_library_id("python")
        
        # Check that we got a valid library ID (should match '/python/docs' or similar)
        self.assertIsNotNone(library_id)
        self.assertIsInstance(library_id, str)
        self.assertIn("python", library_id.lower())
        
        # Test with invalid input
        with self.assertRaises(ValueError):
            self.client.resolve_library_id("")

    def test_get_library_docs(self):
        """Test that the client can retrieve library documentation."""
        # First resolve a library ID
        library_id = self.client.resolve_library_id("python")
        
        # Then get the documentation
        docs = self.client.get_library_docs(library_id)
        
        # Check that we got valid documentation
        self.assertIsNotNone(docs)
        self.assertIsInstance(docs, str)
        self.assertGreater(len(docs), 0)
        
        # Test with topic
        topic_docs = self.client.get_library_docs(library_id, topic="exception handling")
        self.assertIsNotNone(topic_docs)
        self.assertIsInstance(topic_docs, str)
        self.assertGreater(len(topic_docs), 0)
        
        # Test with invalid input
        with self.assertRaises(ValueError):
            self.client.get_library_docs("")
        
        with self.assertRaises(ValueError):
            self.client.get_library_docs(library_id, tokens=-1)

    def test_convenience_function(self):
        """Test the convenience function get_library_documentation."""
        # Get documentation directly
        docs = get_library_documentation("python")
        
        # Check that we got valid documentation
        self.assertIsNotNone(docs)
        self.assertIsInstance(docs, str)
        self.assertGreater(len(docs), 0)
        
        # Test with topic
        topic_docs = get_library_documentation("python", topic="exception handling")
        self.assertIsNotNone(topic_docs)
        self.assertIsInstance(topic_docs, str)
        self.assertGreater(len(topic_docs), 0)
        
        # Test with invalid input
        with self.assertRaises(ValueError):
            get_library_documentation("")

    @mock.patch('utils.context7_client.execute_mcp_tool')
    def test_error_handling(self, mock_execute):
        """Test error handling in the client."""
        # Mock the execute_mcp_tool function to raise an exception
        mock_execute.side_effect = Exception("Test error")
        
        # Test that the client handles errors properly
        with self.assertRaises(ValueError):
            self.client.resolve_library_id("python")
        
        with self.assertRaises(ValueError):
            self.client.get_library_docs("/python/docs")
        
        with self.assertRaises(ValueError):
            get_library_documentation("python")

    def test_development_mode(self):
        """Test that development mode works correctly."""
        # Ensure we're in development mode
        os.environ["SPARC_ENV"] = "development"
        
        # Get documentation
        docs = get_library_documentation("python")
        
        # Check that we got simulated documentation
        self.assertIsNotNone(docs)
        self.assertIsInstance(docs, str)
        self.assertGreater(len(docs), 0)
        
        # Switch to production mode (but since we don't have actual MCP server,
        # we don't want to actually run this test - just verify the code path)
        # Instead, we'll mock the execute_mcp_tool function
        # Patch where it's looked up (in utils.context7_client)
        with mock.patch('utils.context7_client.execute_mcp_tool') as mock_execute:
            # Mock the execute_mcp_tool to return valid responses
            mock_execute.return_value = """
            TITLE: /python/docs Documentation
            DESCRIPTION: Python Standard Library Documentation
            
            This is the Python Standard Library documentation.
            """
            
            # Temporarily set to production mode
            temp_env = os.environ.copy()
            os.environ["SPARC_ENV"] = "production"
            
            try:
                # Get documentation in production mode
                docs = get_library_documentation("python")
                
                # Check that we got valid documentation
                self.assertIsNotNone(docs)
                self.assertIsInstance(docs, str)
                self.assertGreater(len(docs), 0)
                
                # Verify that execute_mcp_tool was called
                mock_execute.assert_called()
            finally:
                # Restore environment
                os.environ.clear()
                os.environ.update(temp_env)


if __name__ == '__main__':
    unittest.main()