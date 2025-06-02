"""
Context Provider module for the RAG (Retrieval-Augmented Generation) system.
This module retrieves relevant code snippets and documentation to enhance
the conversational interface with specific codebase knowledge.
"""

import logging
from typing import List, Dict, Any, Optional

from chatmode.vector_store.codebase_vector_store import CodebaseVectorStore
from chatmode.vector_store.build_vector_store import load_vector_store

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("ContextProvider")


class ContextProvider:
    """
    Provides relevant context from the codebase for a given query.
    The context provider is responsible for retrieving relevant code snippets
    and documentation to enhance the LLM's responses with specific knowledge.
    """

    def __init__(
        self,
        vector_store: Optional[CodebaseVectorStore] = None,
        max_snippets: int = 5,
        min_similarity: float = 0.9,
    ):
        """
        Initialize the context provider.

        Args:
            vector_store: Pre-loaded vector store, or None to load the default one
            max_snippets: Maximum number of snippets to retrieve
            min_similarity: Minimum similarity score for snippets to be included
        """
        self.vector_store = vector_store
        if not self.vector_store:
            try:
                self.vector_store = load_vector_store()
                if not self.vector_store:
                    logger.warning(
                        "Failed to load vector store automatically. Some features will be limited."
                    )
            except Exception as e:
                logger.error(f"Error loading vector store: {str(e)}")
                self.vector_store = None

        self.max_snippets = max_snippets
        self.min_similarity = min_similarity

        # Cache of recently retrieved contexts for optimization
        self._context_cache = {}

    def get_relevant_context(
        self, query: str, k: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Get relevant context snippets for a query.

        Args:
            query: The user query to get context for
            k: Number of snippets to return, or None to use default

        Returns:
            List of context snippets with metadata
        """
        # Check if query is in cache
        if query in self._context_cache:
            logger.info(f"Using cached context for query: '{query[:30]}...'")
            return self._context_cache[query]

        # Return empty list if vector store is not available
        if not self.vector_store:
            logger.warning("Vector store not available. Cannot retrieve context.")
            return []

        # Get number of snippets to return
        k = k or self.max_snippets

        try:
            # Get context from vector store
            results = self.vector_store.search(query, k=k)

            # Filter out low similarity results
            filtered_results = [
                r
                for r in results
                if r.get("score", float("inf")) <= self.min_similarity
            ]

            # Log results
            logger.info(
                f"Retrieved {len(filtered_results)} relevant context snippets for query: '{query[:30]}...'"
            )

            # Cache results
            self._context_cache[query] = filtered_results

            return filtered_results
        except Exception as e:
            logger.error(f"Error retrieving context: {str(e)}")
            return []

    def format_snippets_for_prompt(
        self, snippets: List[Dict[str, Any]], max_chars: int = 12000
    ) -> str:
        """
        Format retrieved snippets for inclusion in a prompt.

        Args:
            snippets: List of snippets from get_relevant_context
            max_chars: Maximum total characters to include

        Returns:
            Formatted string of snippets
        """
        if not snippets:
            return "No relevant code snippets found."

        formatted_snippets = []
        total_chars = 0

        for i, snippet in enumerate(snippets):
            metadata = snippet.get("metadata", {})
            file_path = metadata.get("file_path", "Unknown file")
            snippet_type = metadata.get("type", "code")
            name = metadata.get("name", "")
            heading = metadata.get("heading", "")

            # Format specific identifying information
            identifier = ""
            if name:
                identifier = f"{snippet_type} '{name}'"
            elif heading:
                identifier = f"section '{heading}'"
            else:
                identifier = f"code from {file_path}"

            # Get the text content
            text = snippet.get("text", "")

            # Format the snippet
            formatted_snippet = (
                f"SNIPPET {i + 1}: {identifier} in {file_path}\n{text}\n"
            )

            # Check if adding this snippet would exceed max_chars
            if total_chars + len(formatted_snippet) > max_chars:
                # If we're about to exceed, add a truncation note
                formatted_snippets.append(
                    f"\n[Additional {len(snippets) - i} snippets omitted due to length limits]"
                )
                break

            # Add snippet and update character count
            formatted_snippets.append(formatted_snippet)
            total_chars += len(formatted_snippet)

        return "\n".join(formatted_snippets)

    def clear_cache(self):
        """Clear the context cache."""
        self._context_cache = {}
        logger.info("Context cache cleared.")


if __name__ == "__main__":
    # Example usage
    provider = ContextProvider()
    query = "How does the conversational interface handle user queries?"

    snippets = provider.get_relevant_context(query)
    formatted_text = provider.format_snippets_for_prompt(snippets)

    print(f"Query: {query}")
    print(f"Retrieved {len(snippets)} snippets")
    print("\nFormatted for prompt:")
    print(formatted_text[:500] + "..." if len(formatted_text) > 500 else formatted_text)
