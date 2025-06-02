#!/usr/bin/env python
"""
Script to build and save a vector store of Pulse codebase artifacts.
This vector store will be used by the conversational interface for
retrieval-augmented generation, providing relevant code context for user queries.
"""

import os
import sys
import argparse
import time
import faiss
import pickle
import logging

import json

from chatmode.vector_store.codebase_vector_store import CodebaseVectorStore
from chatmode.vector_store.codebase_parser import load_codebase_artifacts

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("VectorStore")

# Add parent directory to path to import local modules
parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)


# Define the directories to scan for codebase artifacts
# Including relevant directories based on the task scope but avoiding
# problematic directories
CODEBASE_DIRECTORIES = [
    # Skip scanning the root directory directly to avoid .venv and similar directories
    # Instead, list specific directories to include
    "./docs",
    "./tests",
    "./chatmode",
    "./core",
    "./intelligence",
    "./simulation_engine",
    "./forecast_engine",
    "./memory",
    "./symbolic_system",
    "./utils",
    "./adapters",
    "./interfaces",
    "./pipeline",
    "./recursive_training",
    "./trust_system",
]

# Directories to explicitly exclude from scanning
EXCLUDED_DIRECTORIES = [
    ".venv",
    "venv",
    "__pycache__",
    ".git",
    "node_modules",
    "context7",  # Per user instructions to ignore
    "mcp-servers",  # Per user instructions to ignore
    "memory-bank",  # Per user instructions to ignore
]

# Paths for vector store and metadata files
VECTOR_STORE_PATH = "./chatmode/vector_store/codebase.faiss"
METADATA_PATH = "./chatmode/vector_store/codebase_metadata.pkl"
STATS_PATH = "./chatmode/vector_store/build_stats.json"


def build_and_save_vector_store(
    directories=None, model_name="all-MiniLM-L6-v2", quantize=False
):
    """
    Builds the vector store from codebase artifacts and saves it to disk.

    Args:
        directories (list, optional): List of directories to scan. Defaults to None.
        model_name (str, optional): Name of the sentence transformer model to use.
        quantize (bool, optional): Whether to quantize vectors to reduce size.

    Returns:
        dict: Statistics about the build process
    """
    start_time = time.time()
    logger.info("Starting to build the codebase vector store...")

    # Use provided directories or default list
    directories = directories or CODEBASE_DIRECTORIES

    # 1. Make sure vector store directory exists
    os.makedirs(os.path.dirname(VECTOR_STORE_PATH), exist_ok=True)

    # 2. Load codebase artifacts
    logger.info(f"Loading codebase artifacts from {len(directories)} directories...")
    logger.info(f"Excluding directories: {EXCLUDED_DIRECTORIES}")

    try:
        documents = load_codebase_artifacts(directories=directories)
        logger.info(
            f"Loaded a total of {len(documents)} documents from specified directories."
        )

        if not documents:
            logger.error("No documents found to build the vector store.")
            return {
                "status": "failed",
                "reason": "No documents found",
                "elapsed_time": time.time() - start_time,
            }
    except Exception as e:
        logger.error(f"Error loading codebase artifacts: {str(e)}")
        return {
            "status": "failed",
            "reason": f"Error loading codebase: {str(e)}",
            "elapsed_time": time.time() - start_time,
        }

    # 2. Initialize the vector store with specified model
    logger.info(f"Initializing vector store with model: {model_name}")
    vector_store = CodebaseVectorStore(model_name=model_name)

    # 3. Add documents to the vector store
    logger.info("Adding documents to vector store and generating embeddings...")
    vector_store.add_documents(documents)

    # 4. Quantization has been temporarily disabled due to compatibility issues
    if quantize and hasattr(vector_store, "index"):
        logger.warning(
            "Quantization is disabled in this version - using standard index"
        )
        # The quantization functionality will be implemented in a future update
        # when we have better understanding of the faiss library's interfaces

    # 5. Save the Faiss index and metadata to disk
    os.makedirs(os.path.dirname(VECTOR_STORE_PATH), exist_ok=True)
    try:
        logger.info(f"Saving vector store to {VECTOR_STORE_PATH}")
        faiss.write_index(vector_store.index, VECTOR_STORE_PATH)

        logger.info(f"Saving metadata to {METADATA_PATH}")
        with open(METADATA_PATH, "wb") as f:
            pickle.dump(vector_store.document_metadata, f)

        # Create build statistics
        build_stats = {
            "status": "success",
            "build_time": time.strftime("%Y-%m-%d %H:%M:%S"),
            "elapsed_seconds": round(time.time() - start_time, 2),
            "document_count": len(documents),
            "vector_count": vector_store.index.ntotal,
            "embedding_dimension": vector_store.embedding_dimension,
            "model_name": model_name,
            "quantized": quantize,
            "directories": directories,
            "vector_store_path": VECTOR_STORE_PATH,
            "metadata_path": METADATA_PATH,
        }

        # Save build statistics
        with open(STATS_PATH, "w") as f:
            json.dump(build_stats, f, indent=2)

        logger.info(
            f"Vector store build complete in {build_stats['elapsed_seconds']} seconds."
        )
        logger.info(f"Processed {build_stats['document_count']} documents.")
        logger.info(f"Vector store contains {build_stats['vector_count']} vectors.")

        return build_stats

    except Exception as e:
        logger.error(f"Error saving vector store or metadata: {e}")
        return {
            "status": "failed",
            "reason": str(e),
            "elapsed_time": time.time() - start_time,
        }


def load_vector_store(model_name="all-MiniLM-L6-v2"):
    """
    Loads the vector store and metadata from disk.

    Args:
        model_name (str, optional): Name of the sentence transformer model.
                                   Must match the model used to build the store.

    Returns:
        CodebaseVectorStore or None: The loaded vector store instance, or None if loading fails.
    """
    if not os.path.exists(VECTOR_STORE_PATH) or not os.path.exists(METADATA_PATH):
        logger.warning(
            "Vector store files not found. Please build the vector store first."
        )
        return None

    try:
        # Initialize a CodebaseVectorStore to load the model and get embedding dimension
        # We don't need the index initialized here as we will load it
        temp_vector_store = CodebaseVectorStore(model_name=model_name)
        embedding_dimension = temp_vector_store.embedding_dimension

        logger.info(f"Loading vector store from {VECTOR_STORE_PATH}")
        index = faiss.read_index(VECTOR_STORE_PATH)

        # Ensure the loaded index has the correct dimension
        if index.d != embedding_dimension:
            logger.error(
                f"Error loading index: Dimension mismatch. Expected {embedding_dimension}, got {
                    index.d}")
            return None

        logger.info(f"Loading metadata from {METADATA_PATH}")
        with open(METADATA_PATH, "rb") as f:
            metadata = pickle.load(f)

        # Create a new CodebaseVectorStore instance and assign the loaded index
        # and metadata
        loaded_vector_store = CodebaseVectorStore(model_name=model_name)
        loaded_vector_store.index = index
        loaded_vector_store.document_metadata = metadata

        logger.info(
            f"Vector store loaded successfully. Total vectors: {
                loaded_vector_store.index.ntotal}")
        return loaded_vector_store

    except Exception as e:
        logger.error(f"Error loading vector store or metadata: {e}")
        return None


def test_vector_store(query="How does the conversational interface work?", k=3):
    """
    Test the vector store with a sample query.

    Args:
        query (str): The query to search for
        k (int): Number of results to return

    Returns:
        list: The search results
    """
    vector_store = load_vector_store()
    if not vector_store:
        return []

    logger.info(f"Testing vector store with query: '{query}'")
    results = vector_store.search(query, k=k)

    logger.info(f"Found {len(results)} results:")
    for i, result in enumerate(results):
        logger.info(f"Result {i + 1}:")
        logger.info(f"  Score: {result['score']:.4f}")
        logger.info(f"  Path: {result['metadata'].get('file_path', 'N/A')}")
        logger.info(f"  Type: {result['metadata'].get('type', 'N/A')}")
        if "name" in result["metadata"]:
            logger.info(f"  Name: {result['metadata']['name']}")
        logger.info(f"  Text: {result['text'][:200]}...")

    return results


def main():
    """Command-line interface for the vector store builder."""
    parser = argparse.ArgumentParser(
        description="Build and test the Pulse codebase vector store."
    )
    parser.add_argument(
        "--action",
        choices=["build", "test", "info"],
        default="build",
        help="Action to perform: build, test, or show info (default: build)",
    )
    parser.add_argument(
        "--model",
        default="all-MiniLM-L6-v2",
        help="Name of the sentence transformer model to use (default: all-MiniLM-L6-v2)",
    )
    parser.add_argument(
        "--quantize", action="store_true", help="Quantize vectors to reduce size"
    )
    parser.add_argument(
        "--query",
        default="How does the conversational interface work?",
        help="Query to test the vector store with (for test action)",
    )
    parser.add_argument(
        "--results",
        type=int,
        default=3,
        help="Number of results to return (for test action)",
    )

    args = parser.parse_args()

    if args.action == "build":
        build_stats = build_and_save_vector_store(
            model_name=args.model, quantize=args.quantize
        )
        if build_stats.get("status") == "success":
            logger.info("Vector store build completed successfully!")
        else:
            logger.error(
                f"Vector store build failed: {
                    build_stats.get(
                        'reason',
                        'Unknown error')}")

    elif args.action == "test":
        test_vector_store(query=args.query, k=args.results)

    elif args.action == "info":
        if os.path.exists(STATS_PATH):
            import json

            with open(STATS_PATH, "r") as f:
                stats = json.load(f)
                logger.info("Vector store build information:")
                for key, value in stats.items():
                    logger.info(f"  {key}: {value}")
        else:
            logger.warning("No build statistics found. Run the build action first.")


if __name__ == "__main__":
    main()
