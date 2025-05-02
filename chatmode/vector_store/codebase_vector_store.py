import os
import numpy as np
from sentence_transformers import SentenceTransformer
import faiss

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
        self.document_metadata = [] # To store metadata corresponding to the index

        print(f"Initialized CodebaseVectorStore with model: {model_name} and Faiss index with dimension {self.embedding_dimension}")
        # TODO: Implement int8 quantization if needed and supported by the chosen library

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

        texts = [doc['text'] for doc in documents]
        metadata = [doc['metadata'] for doc in documents]

        print(f"Generating embeddings for {len(texts)} documents...")
        embeddings = self.model.encode(texts, show_progress_bar=True)
        print("Embedding generation complete.")

        # Convert embeddings to numpy array with float32 dtype for Faiss
        embeddings = np.array(embeddings).astype('float32')

        # Add embeddings to the Faiss index
        self.index.add(embeddings)

        # Store metadata, maintaining the same order as the embeddings added to the index
        self.document_metadata.extend(metadata)

        print(f"Added {len(documents)} documents to the vector store. Total documents: {self.index.ntotal}")


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
            print("Vector store is empty. Cannot perform search.")
            return []

        query_embedding = self.model.encode(query)
        query_embedding = np.array([query_embedding]).astype('float32') # Faiss expects a 2D array

        # Perform search
        distances, indices = self.index.search(query_embedding, k)

        results = []
        # Retrieve results and their metadata
        for i in range(len(indices[0])):
            doc_index = indices[0][i]
            if doc_index != -1: # Check if a valid result was found
                score = distances[0][i]
                metadata = self.document_metadata[doc_index]
                text = metadata.get('text', 'N/A') # Extract the original text
                results.append({
                    'text': text,
                    'metadata': metadata,
                    'score': score
                })

        print(f"Found {len(results)} results for query: '{query}'")
        return results

if __name__ == '__main__':
    # Example Usage (for testing the class structure)
    vector_store = CodebaseVectorStore()

    # Example documents (replace with actual codebase artifacts)
    sample_documents = [
        {'text': 'def calculate_forecast(data): # Calculates the forecast', 'metadata': {'file_path': 'forecast_engine/forecaster.py', 'text': 'def calculate_forecast(data): # Calculates the forecast'}},
        {'text': 'class SimulationEngine: # Handles running simulations', 'metadata': {'file_path': 'simulation_engine/engine.py', 'text': 'class SimulationEngine: # Handles running simulations'}},
        {'text': 'def get_historical_data(symbol): # Retrieves historical data', 'metadata': {'file_path': 'data_access/data_retriever.py', 'text': 'def get_historical_data(symbol): # Retrieves historical data'}},
        {'text': 'The main function to run the Pulse application.', 'metadata': {'file_path': 'main.py', 'text': 'The main function to run the Pulse application.'}},
        {'text': 'This file contains utility functions for data processing.', 'metadata': {'file_path': 'utils/data_utils.py', 'text': 'This file contains utility functions for data processing.'}},
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