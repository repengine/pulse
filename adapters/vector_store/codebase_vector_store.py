import numpy as np
import logging
from sentence_transformers import SentenceTransformer
import faiss

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("CodebaseVectorStore")


class CodebaseVectorStore:
    def __init__(self, model_name="all-MiniLM-L6-v2"):
        """
        Initializes the CodebaseVectorStore with a SentenceTransformer model and Faiss index.

        Args:
            model_name (str): The name of the SentenceTransformer model to use.
        """
        self.model = SentenceTransformer(model_name)
        self.embedding_dimension = self.model.get_sentence_embedding_dimension()

        # Initialize Faiss index
        # Using IndexFlatL2 for simplicity, stores vectors directly and uses L2 distance
        self.index = faiss.IndexFlatL2(self.embedding_dimension)
        # Store metadata and original texts for lookup
        self.document_metadata = []  # To store metadata corresponding to the index
        self.document_texts = []  # To store the original text for each document

        logger.info(f"Initialized CodebaseVectorStore with model: {model_name}")
        logger.info(
            f"Faiss index initialized with dimension {self.embedding_dimension}"
        )

    def add_documents(self, documents):
        """
        Adds documents to the vector store.

        Args:
            documents (list): A list of dictionaries, where each dictionary
                              contains 'text' and 'metadata' keys.
                              Metadata should include information like 'file_path'.
        """
        if not documents:
            return

        texts = [doc["text"] for doc in documents]
        metadata = [doc["metadata"] for doc in documents]

        # Store the original texts for retrieval during search
        self.document_texts.extend(texts)

        logger.info(f"Generating embeddings for {len(texts)} documents...")
        try:
            embeddings = self.model.encode(texts, show_progress_bar=True)
            logger.info("Embedding generation complete.")
        except Exception as e:
            logger.error(f"Error generating embeddings: {str(e)}")
            raise

        # Convert embeddings to numpy array with float32 dtype for Faiss
        embeddings = np.array(embeddings).astype("float32")

        # Add embeddings to the Faiss index
        # Note: Ignoring Pylance warnings about parameter names as faiss bindings work correctly at runtime
        try:
            self.index.add(embeddings)
            logger.debug(f"Added {embeddings.shape[0]} embeddings to index")
        except Exception as e:
            logger.error(f"Error adding embeddings to index: {str(e)}")
            raise

        # Store metadata, maintaining the same order as the embeddings added to the index
        self.document_metadata.extend(metadata)

        logger.info(
            f"Added {len(documents)} documents to the vector store. Total documents: {self.index.ntotal}"
        )

    def search(self, query, k=5):
        """
        Searches the vector store for relevant snippets.

        Args:
            query (str): The user query.
            k (int): The number of top relevant snippets to retrieve.

        Returns:
            list: A list of dictionaries, each containing 'text', 'metadata', and 'score'.
        """
        if self.index.ntotal == 0:
            logger.warning("Vector store is empty. Cannot perform search.")
            return []

        try:
            logger.info(f"Generating embedding for query: '{query}'")
            query_embedding = self.model.encode(query)
        except Exception as e:
            logger.error(f"Error encoding query: {str(e)}")
            return []
        query_embedding = np.array([query_embedding]).astype(
            "float32"
        )  # Faiss expects a 2D array

        # Perform search
        # Note: Ignoring Pylance warnings about parameter names as faiss bindings work correctly at runtime
        try:
            distances, indices = self.index.search(query_embedding, k)
            logger.debug(f"Search returned {len(indices[0])} results")
        except Exception as e:
            logger.error(f"Error searching index: {str(e)}")
            return []

        results = []
        # Retrieve results and their metadata
        for i in range(len(indices[0])):
            doc_index = indices[0][i]
            if doc_index != -1:  # Check if a valid result was found
                score = float(
                    distances[0][i]
                )  # Convert from numpy float to Python float
                metadata = self.document_metadata[doc_index]

                # Get the text from our stored document_texts to ensure we have the right text
                text = (
                    self.document_texts[doc_index]
                    if doc_index < len(self.document_texts)
                    else "Text not found"
                )

                results.append({"text": text, "metadata": metadata, "score": score})

        logger.info(f"Found {len(results)} results for query: '{query}'")
        return results


if __name__ == "__main__":
    # Example Usage (for testing the class structure)
    vector_store = CodebaseVectorStore()

    # Example documents (replace with actual codebase artifacts)
    sample_documents = [
        {
            "text": "def calculate_forecast(data): # Calculates the forecast",
            "metadata": {
                "file_path": "forecast_engine/forecaster.py",
                "text": "def calculate_forecast(data): # Calculates the forecast",
            },
        },
        {
            "text": "class SimulationEngine: # Handles running simulations",
            "metadata": {
                "file_path": "simulation_engine/engine.py",
                "text": "class SimulationEngine: # Handles running simulations",
            },
        },
        {
            "text": "def get_historical_data(symbol): # Retrieves historical data",
            "metadata": {
                "file_path": "data_access/data_retriever.py",
                "text": "def get_historical_data(symbol): # Retrieves historical data",
            },
        },
        {
            "text": "The main function to run the Pulse application.",
            "metadata": {
                "file_path": "main.py",
                "text": "The main function to run the Pulse application.",
            },
        },
        {
            "text": "This file contains utility functions for data processing.",
            "metadata": {
                "file_path": "utils/data_utils.py",
                "text": "This file contains utility functions for data processing.",
            },
        },
    ]

    vector_store.add_documents(sample_documents)

    search_results = vector_store.search("how to get historical data", k=2)
    print("Search Results:")
    for result in search_results:
        print(f"Score: {result['score']:.4f}, Metadata: {result['metadata']}")

    search_results_2 = vector_store.search("what is the main entry point", k=1)
    print("\nSearch Results 2:")
    for result in search_results_2:
        print(f"Score: {result['score']:.4f}, Metadata: {result['metadata']}")
