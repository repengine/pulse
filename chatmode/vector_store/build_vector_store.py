import os
import faiss
import pickle
from codebase_vector_store import CodebaseVectorStore
from codebase_parser import load_codebase_artifacts

# Define the directories to scan for codebase artifacts
# Including relevant directories based on the task scope (docs, tests, potentially core modules)
CODEBASE_DIRECTORIES = [
    '.', # Root directory
    './docs',
    './tests',
    './chatmode',
    './core',
    './intelligence',
    './simulation_engine',
    './forecast_engine',
    './memory',
    './symbolic_system',
    './utils',
    './adapters',
    './interfaces',
    './pipeline',
    './recursive_training',
    './trust_system',
]

VECTOR_STORE_PATH = './chatmode/vector_store/codebase.faiss'
METADATA_PATH = './chatmode/vector_store/codebase_metadata.pkl'

def build_and_save_vector_store():
    """
    Builds the vector store from codebase artifacts and saves it to disk.
    """
    print("Starting to build the codebase vector store...")

    # 1. Load codebase artifacts
    documents = load_codebase_artifacts(directories=CODEBASE_DIRECTORIES)
    print(f"Loaded a total of {len(documents)} documents from specified directories.")

    if not documents:
        print("No documents found to build the vector store.")
        return

    # 2. Initialize the vector store
    vector_store = CodebaseVectorStore()

    # 3. Add documents to the vector store
    vector_store.add_documents(documents)

    # 4. Save the Faiss index and metadata to disk
    try:
        faiss.write_index(vector_store.index, VECTOR_STORE_PATH)
        with open(METADATA_PATH, 'wb') as f:
            pickle.dump(vector_store.document_metadata, f)
        print(f"Vector store saved to {VECTOR_STORE_PATH}")
        print(f"Metadata saved to {METADATA_PATH}")
    except Exception as e:
        print(f"Error saving vector store or metadata: {e}")

def load_vector_store():
    """
    Loads the vector store and metadata from disk.

    Returns:
        CodebaseVectorStore or None: The loaded vector store instance, or None if loading fails.
    """
    if not os.path.exists(VECTOR_STORE_PATH) or not os.path.exists(METADATA_PATH):
        print("Vector store files not found. Please build the vector store first.")
        return None

    try:
        # Initialize a CodebaseVectorStore to load the model and get embedding dimension
        # We don't need the index initialized here as we will load it
        temp_vector_store = CodebaseVectorStore()
        embedding_dimension = temp_vector_store.embedding_dimension

        index = faiss.read_index(VECTOR_STORE_PATH)
        # Ensure the loaded index has the correct dimension
        if index.d != embedding_dimension:
             print(f"Error loading index: Dimension mismatch. Expected {embedding_dimension}, got {index.d}")
             return None

        with open(METADATA_PATH, 'rb') as f:
            metadata = pickle.load(f)

        # Create a new CodebaseVectorStore instance and assign the loaded index and metadata
        loaded_vector_store = CodebaseVectorStore()
        loaded_vector_store.index = index
        loaded_vector_store.document_metadata = metadata

        print(f"Vector store loaded from {VECTOR_STORE_PATH}. Total documents: {loaded_vector_store.index.ntotal}")
        return loaded_vector_store

    except Exception as e:
        print(f"Error loading vector store or metadata: {e}")
        return None


if __name__ == '__main__':
    # Example Usage: Build the vector store
    build_and_save_vector_store()

    # Example Usage: Load the vector store and perform a search
    # loaded_store = load_vector_store()
    # if loaded_store:
    #     search_query = "how to run a simulation"
    #     search_results = loaded_store.search(search_query, k=3)
    #     print(f"\nSearch Results for '{search_query}':")
    #     for result in search_results:
    #         # In the current search implementation, 'text' is not returned, only metadata and score
    #         # To get the text, you would need to retrieve it based on the file_path in metadata
    #         print(f"Score: {result['score']:.4f}, File: {result['metadata'].get('file_path', 'N/A')}")