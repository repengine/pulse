import os
from chatmode.vector_store.codebase_vector_store import CodebaseVectorStore
from chatmode.vector_store.build_vector_store import load_vector_store # To load the saved store
from chatmode.llm_integration.llm_model import LLMModel
from chatmode.llm_integration.domain_adapter import DomainAdapter
from chatmode.integrations import pulse_module_adapters # Import the adapters

class ConversationalCore:
    def __init__(self):
        """
        Initializes the core conversational logic component.
        """
        print("Initializing ConversationalCore...")

        # 1. Load the vector store
        self.vector_store = load_vector_store()
        if self.vector_store is None:
            print("Warning: Vector store could not be loaded. RAG will not be available.")

        # 2. Initialize LLM and Domain Adapter (placeholders)
        self.llm_model = LLMModel()
        # TODO: Load and apply domain adapter if available
        # self.domain_adapter = DomainAdapter()
        # self.llm_model.load_model()
        # self.llm_model.apply_lora_adapter("./path/to/trained/adapter") # Example

        # 3. Initialize conversation summary
        self.conversation_summary = "" # Or a list of turns

        # 4. Define a basic system message template
        self.system_message_template = """You are Pulse AI, a helpful assistant for the Pulse codebase.
Answer questions based on the provided context snippets from the codebase and the conversation history.
If you cannot find the answer in the context, state that you don't have enough information.
Avoid making up information.

Codebase Context:
{codebase_context}

Tool Execution Result:
{tool_result_context}

Conversation History:
{conversation_history}

User Query:
{user_query}

Response:
"""
        print("ConversationalCore initialized.")

    def recognize_intent(self, query):
        """
        Basic rule-based intent recognition and parameter extraction.
        (Placeholder - replace with a more sophisticated NLU approach later)

        Args:
            query (str): The user query.

        Returns:
            tuple: A tuple containing the intent type (str) and extracted parameters (dict).
                   Returns ('general_query', {}) if no specific intent is recognized.
        """
        query_lower = query.lower()

        if "run simulation" in query_lower:
            # Basic parameter extraction placeholder
            parameters = {}
            # TODO: Implement actual parameter extraction from the query
            return ('run_simulation', parameters)
        elif "get data" in query_lower or "fetch data" in query_lower:
             # Basic parameter extraction placeholder
            parameters = {}
            # TODO: Implement actual parameter extraction (symbol, type, date range)
            return ('get_data', parameters)
        elif "get forecast" in query_lower or "show forecast" in query_lower:
             # Basic parameter extraction placeholder
            parameters = {}
            # TODO: Implement actual parameter extraction (symbol)
            return ('get_forecast', parameters)
        elif "get trust score" in query_lower or "check trust" in query_lower:
             # Basic parameter extraction placeholder
            parameters = {}
            # TODO: Implement actual parameter extraction (item)
            return ('get_trust_score', parameters)
        elif "query memory" in query_lower or "search memory" in query_lower:
             # Basic parameter extraction placeholder
            parameters = {}
            # TODO: Implement actual parameter extraction (query)
            return ('query_memory', parameters)
        elif "query symbolic system" in query_lower or "ask symbolic system" in query_lower:
             # Basic parameter extraction placeholder
            parameters = {}
            # TODO: Implement actual parameter extraction (query)
            return ('query_symbolic_system', parameters)
        else:
            return ('general_query', {})


    def process_query(self, user_query):
        """
        Processes a user query, retrieves context, and generates a response.

        Args:
            user_query (str): The user's input query.

        Returns:
            tuple: A tuple containing the generated response (str) and
                   a list of retrieved snippets (list).
        """
        print(f"Processing user query: '{user_query}'")

        # 1. Recognize intent and extract parameters
        intent, parameters = self.recognize_intent(user_query)
        print(f"Recognized intent: {intent} with parameters: {parameters}")

        # 2. Execute tool/adapter based on intent and get tool result context
        tool_result_context = "No specific action requested."
        if intent == 'run_simulation':
            result = pulse_module_adapters.run_simulation(parameters)
            tool_result_context = f"Simulation Tool Result: {result}"
        elif intent == 'get_data':
            result = pulse_module_adapters.get_data(**parameters) # Assuming parameters match function args
            tool_result_context = f"Get Data Tool Result: {result}"
        elif intent == 'get_forecast':
            result = pulse_module_adapters.get_forecast(**parameters) # Assuming parameters match function args
            tool_result_context = f"Get Forecast Tool Result: {result}"
        elif intent == 'get_trust_score':
            result = pulse_module_adapters.get_trust_score(**parameters) # Assuming parameters match function args
            tool_result_context = f"Get Trust Score Tool Result: {result}"
        elif intent == 'query_memory':
            result = pulse_module_adapters.query_memory(**parameters) # Assuming parameters match function args
            tool_result_context = f"Query Memory Tool Result: {result}"
        elif intent == 'query_symbolic_system':
            result = pulse_module_adapters.query_symbolic_system(**parameters) # Assuming parameters match function args
            tool_result_context = f"Query Symbolic System Tool Result: {result}"

        # 3. Retrieve relevant snippets from the vector store (using the original query)
        retrieved_snippets = []
        if self.vector_store:
            search_results = self.vector_store.search(user_query, k=5) # Retrieve top 5 snippets
            retrieved_snippets = [result['text'] for result in search_results]
            print(f"Retrieved {len(retrieved_snippets)} snippets.")

        # Format retrieved snippets for the prompt
        codebase_context = "\n\n".join(retrieved_snippets) if retrieved_snippets else "No relevant snippets found."

        # 4. Get current conversation summary
        # For now, the summary is just the history. Implement summarization later.
        conversation_history = self.conversation_summary

        # 5. Assemble the prompt
        prompt = self.system_message_template.format(
            codebase_context=codebase_context,
            tool_result_context=tool_result_context,
            conversation_history=conversation_history,
            user_query=user_query
        )
        print("Assembled prompt.")
        # print(f"--- Prompt ---\n{prompt}\n--- End Prompt ---") # Uncomment for debugging

        # 6. Call the LLM to generate a response
        # This will use the placeholder generate_response for now
        generated_response = self.llm_model.generate_response(prompt)
        print("Generated response placeholder.")

        # 7. Update conversation summary
        # Basic update: append user query and response. Implement proper summarization later.
        self.conversation_summary += f"\nUser: {user_query}\nAI: {generated_response}"

        print("Query processing complete.")
        return generated_response, retrieved_snippets

if __name__ == '__main__':
    # Example Usage
    # Note: This requires the vector store to be built first by running build_vector_store.py
    # Run build_vector_store.py once before running this example.

    # Build the vector store if it doesn't exist (optional, can be done separately)
    # from chatmode.vector_store.build_vector_store import build_and_save_vector_store
    # if not os.path.exists('./chatmode/vector_store/codebase.faiss'):
    #      print("Vector store not found, building it now...")
    #      build_and_save_vector_store()

    core = ConversationalCore()

    # Example queries
    # response, snippets = core.process_query("How does the SimulationEngine work?")
    # print("\n--- Response ---")
    # print(response)
    # print("--- Retrieved Snippets ---")
    # for snippet in snippets:
    #     print(f"Snippet:\n{snippet[:200]}...") # Print first 200 chars of snippet
    #     print("-" * 10)

    # response_2, snippets_2 = core.process_query("What is the purpose of the CodebaseVectorStore?")
    # print("\n--- Response ---")
    # print(response_2)
    # print("--- Retrieved Snippets ---")
    # for snippet in snippets_2:
    #     print(f"Snippet:\n{snippet[:200]}...")
    #     print("-" * 10)