"""
Retrieval-Augmented Generation (RAG) module for the Pulse Conversational Interface.

This module provides the components for implementing the hybrid RAG system:
1. Vector store management for storing embeddings of codebase artifacts
2. Context provider for retrieving relevant snippets based on user queries
3. Context augmentation for enhancing prompts with retrieved information

The RAG implementation follows these principles:
- Lightweight: Minimizes computational overhead and token costs
- Maintainable: Clear separation of concerns for easy maintenance
- Efficient: Optimized for performance with caching and smart retrieval
"""

from chatmode.rag.context_provider import ContextProvider

__all__ = ["ContextProvider"]
