import os
import re
import json
import logging
from copy import deepcopy
from typing import Dict, List, Tuple, Any, Optional, Callable
from datetime import datetime
from chatmode.llm_integration.llm_model import LLMModel
from chatmode.llm_integration.domain_adapter import DomainAdapter
from chatmode.rag.context_provider import ContextProvider
from chatmode.config.llm_config import llm_config
from chatmode.integrations import pulse_module_adapters

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("ConversationalCore")


class Intent:
    """Class representing a detected intent with confidence and extracted entities"""

    def __init__(
        self,
        name: str,
        confidence: float = 0.0,
        entities: Optional[Dict[str, Any]] = None,
    ):
        self.name = name
        self.confidence = confidence
        self.entities = entities or {}

    def __repr__(self):
        return (
            f"Intent(name='{self.name}', confidence={self.confidence}, "
            f"entities={self.entities})"
        )


class PatternMatcher:
    """
    Pattern matcher for intent recognition that uses regex patterns and
    entity extraction techniques to identify user intents.
    """

    def __init__(self):
        # Dictionary mapping intent names to lists of patterns
        # Each pattern is a tuple of (regex pattern, confidence score)
        self.patterns = {
            "run_simulation": [
                (
                    r"(?i)run\s+(?:a\s+)?simulation(?:\s+with\s+)?(?P<parameters>.*)?",
                    0.9,
                ),
                (r"(?i)simulate(?:\s+with\s+)?(?P<parameters>.*)?", 0.8),
                (
                    r"(?i)create\s+(?:a\s+)?simulation(?:\s+using\s+)?(?P<parameters>.*)?",
                    0.7,
                ),
            ],
            "get_data": [
                (
                    r"(?i)(?:get|fetch|retrieve|show)\s+data(?:\s+for\s+)(?P<symbol>[A-Z]+)(?:.*?(?:type|kind)[\s:]+(?P<data_type>[a-zA-Z_]+))?(?:.*?(?:from|between|since|range)[\s:]+(?P<date_range>.+?))?",
                    0.9,
                ),
                (
                    r"(?i)(?:data\s+for|get)\s+(?P<symbol>[A-Z]+)(?:.*?(?:type|kind)[\s:]+(?P<data_type>[a-zA-Z_]+))?(?:.*?(?:from|between|since|range)[\s:]+(?P<date_range>.+?))?",
                    0.8,
                ),
            ],
            "get_forecast": [
                (
                    r"(?i)(?:get|show|display|create)\s+(?:a\s+)?forecast(?:\s+for\s+)?(?P<symbol>[A-Z]+)",
                    0.9,
                ),
                (r"(?i)forecast(?:\s+for\s+)(?P<symbol>[A-Z]+)", 0.8),
                (r"(?i)predict(?:\s+for\s+)(?P<symbol>[A-Z]+)", 0.7),
            ],
            "get_trust_score": [
                (
                    r"(?i)(?:get|show|display|what\s+is\s+the)\s+trust\s+score(?:\s+for\s+)?(?P<item>.+)",
                    0.9,
                ),
                (r"(?i)how\s+trustworthy\s+is(?:\s+the\s+)?(?P<item>.+)", 0.8),
                (r"(?i)trust(?:\s+level)?(?:\s+for\s+)?(?P<item>.+)", 0.7),
            ],
            "query_memory": [
                (
                    r"(?i)(?:query|search|look\s+up)\s+(?:the\s+)?memory(?:\s+for\s+)?(?P<query>.+)",
                    0.9,
                ),
                (
                    r"(?i)(?:find|retrieve)\s+from\s+memory(?:\s+about\s+)?(?P<query>.+)",
                    0.8,
                ),
                (
                    r"(?i)(?:what\s+do\s+you\s+remember\s+about|recall)\s+(?P<query>.+)",
                    0.7,
                ),
            ],
            "query_symbolic_system": [
                (
                    r"(?i)(?:query|ask)\s+(?:the\s+)?symbolic\s+system(?:\s+about\s+)?(?P<query>.+)",
                    0.9,
                ),
                (
                    r"(?i)symbolic\s+(?:query|question)(?:\s+about\s+)?(?P<query>.+)",
                    0.8,
                ),
                (
                    r"(?i)(?:what\s+does\s+the\s+)?symbolic\s+system\s+(?:say|think)\s+about\s+(?P<query>.+)",
                    0.7,
                ),
            ],
            "explain_forecast": [
                (
                    r"(?i)explain(?:\s+this)?\s+forecast(?:\s+for\s+)?(?P<symbol>[A-Z]+)?",
                    0.9,
                ),
                (
                    r"(?i)(?:why|how)\s+(?:did\s+you|is\s+this)\s+forecast(?:\s+for\s+)?(?P<symbol>[A-Z]+)?",
                    0.8,
                ),
                (
                    r"(?i)(?:details|more\s+information)\s+(?:about|on)\s+(?:this\s+)?forecast(?:\s+for\s+)?(?P<symbol>[A-Z]+)?",
                    0.7,
                ),
            ],
            "start_recursive_learning": [
                (
                    r"(?i)(?:start|begin|launch|initiate)\s+(?:a\s+)?recursive\s+learning(?:\s+cycle)?(?:\s+with\s+)?(?P<parameters>.*)?",
                    0.9,
                ),
                (
                    r"(?i)(?:run|execute)\s+(?:a\s+)?recursive\s+(?:learning|training)(?:\s+cycle)?(?:\s+with\s+)?(?P<parameters>.*)?",
                    0.8,
                ),
                (
                    r"(?i)(?:start|begin|launch)\s+(?:a\s+)?(?:new\s+)?training\s+cycle(?:\s+with\s+)?(?P<parameters>.*)?",
                    0.7,
                ),
            ],
            "stop_recursive_learning": [
                (
                    r"(?i)(?:stop|halt|end|terminate)\s+(?:the\s+)?recursive\s+learning(?:\s+cycle)?(?:\s+with\s+id\s+)?(?P<cycle_id>[a-zA-Z0-9_-]+)?",
                    0.9,
                ),
                (
                    r"(?i)(?:cancel|abort)\s+(?:the\s+)?recursive\s+(?:learning|training)(?:\s+cycle)?(?:\s+with\s+id\s+)?(?P<cycle_id>[a-zA-Z0-9_-]+)?",
                    0.8,
                ),
                (
                    r"(?i)(?:stop|halt|end|terminate)\s+(?:the\s+)?training\s+cycle(?:\s+with\s+id\s+)?(?P<cycle_id>[a-zA-Z0-9_-]+)?",
                    0.7,
                ),
            ],
            "get_recursive_learning_status": [
                (
                    r"(?i)(?:what\s+is\s+the\s+)?status\s+of\s+(?:the\s+)?recursive\s+learning(?:\s+cycle)?(?:\s+with\s+id\s+)?(?P<cycle_id>[a-zA-Z0-9_-]+)?",
                    0.9,
                ),
                (
                    r"(?i)(?:check|get|show)\s+(?:the\s+)?recursive\s+(?:learning|training)\s+status(?:\s+for\s+id\s+)?(?P<cycle_id>[a-zA-Z0-9_-]+)?",
                    0.8,
                ),
                (
                    r"(?i)(?:how\s+is|progress\s+of)\s+(?:the\s+)?recursive\s+learning(?:\s+cycle)?(?:\s+with\s+id\s+)?(?P<cycle_id>[a-zA-Z0-9_-]+)?",
                    0.7,
                ),
            ],
            "configure_recursive_learning": [
                (
                    r"(?i)(?:configure|setup|set)\s+(?:the\s+)?recursive\s+learning(?:\s+with\s+)?(?P<parameters>.*)?",
                    0.9,
                ),
                (
                    r"(?i)(?:update|change|modify)\s+(?:the\s+)?recursive\s+learning\s+(?:configuration|settings)(?:\s+with\s+)?(?P<parameters>.*)?",
                    0.8,
                ),
                (
                    r"(?i)(?:adjust|tune)\s+(?:the\s+)?recursive\s+learning\s+parameters(?:\s+with\s+)?(?P<parameters>.*)?",
                    0.7,
                ),
            ],
            "get_recursive_learning_metrics": [
                (
                    r"(?i)(?:get|show|display)\s+(?:the\s+)?recursive\s+learning\s+(?:metrics|results)(?:\s+for\s+cycle\s+)?(?P<cycle_id>[a-zA-Z0-9_-]+)?(?:\s+of\s+type\s+)?(?P<metric_type>[a-zA-Z_]+)?",
                    0.9,
                ),
                (
                    r"(?i)(?:metrics|results)\s+(?:of|for)\s+(?:the\s+)?recursive\s+learning(?:\s+cycle\s+)?(?P<cycle_id>[a-zA-Z0-9_-]+)?(?:\s+of\s+type\s+)?(?P<metric_type>[a-zA-Z_]+)?",
                    0.8,
                ),
                (
                    r"(?i)(?:how\s+is\s+the\s+)?performance\s+of\s+(?:the\s+)?recursive\s+learning(?:\s+cycle\s+)?(?P<cycle_id>[a-zA-Z0-9_-]+)?",
                    0.7,
                ),
            ],
        }

        # Entity pattern extractors
        self.entity_extractors = {
            "symbol": r"([A-Z]{1,6})",  # Stock ticker pattern
            "date_range": r"(\d{1,2}/\d{1,2}/\d{2,4})\s+to\s+(\d{1,2}/\d{1,2}/\d{2,4})",  # Date range pattern
            "parameters": self._extract_parameters,  # Function to extract key-value parameters
        }

    def _extract_parameters(self, param_text: str) -> Dict[str, Any]:
        """
        Extract parameter key-value pairs from text
        Example: "iterations=100, confidence=0.95, model=basic"
        """
        if not param_text:
            return {}

        params = {}
        # Look for key=value patterns
        pattern = r"(\w+)\s*=\s*([^,]+)"
        matches = re.findall(pattern, param_text)

        for key, value in matches:
            # Try to convert to appropriate type
            key = key.strip()
            value = value.strip()
            try:
                # Try as number first
                if "." in value:
                    params[key] = float(value)
                else:
                    params[key] = int(value)
            except ValueError:
                # Handle true/false values
                if value.lower() in ("true", "yes"):
                    params[key] = True
                elif value.lower() in ("false", "no"):
                    params[key] = False
                else:
                    # Keep as string
                    params[key] = value

        return params

    def extract_entities(
        self, text: str, entity_matches: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Process entity matches and apply specialized extractors if needed
        """
        entities = {}

        for key, value in entity_matches.items():
            if key in self.entity_extractors:
                # If the extractor is a function
                if callable(self.entity_extractors[key]):
                    entities[key] = self.entity_extractors[key](value)
                else:
                    # If the extractor is a regex pattern
                    pattern = self.entity_extractors[key]
                    matches = re.findall(pattern, value)
                    if matches:
                        entities[key] = matches[0]
                    else:
                        entities[key] = value
            else:
                entities[key] = value

        return entities

    def match(
        self, text: str, conversation_context: Optional[Dict[str, Any]] = None
    ) -> List[Intent]:
        """
        Match text against patterns and return a list of potential intents with confidence scores

        Args:
            text: The text to match against patterns
            conversation_context: Optional context from previous conversation turns

        Returns:
            List of Intent objects sorted by confidence (highest first)
        """
        matched_intents = []

        # Process through all intent patterns
        for intent_name, patterns in self.patterns.items():
            for pattern, base_confidence in patterns:
                match = re.search(pattern, text)
                if match:
                    # Extract named groups from the regex match
                    entity_matches = match.groupdict()

                    # Extract and process entities
                    entities = self.extract_entities(text, entity_matches)

                    # Adjust confidence based on entity extraction completeness
                    confidence = base_confidence
                    if entities:
                        # If we have entity matches, slightly boost confidence
                        confidence += 0.05

                    # Context-based confidence adjustment
                    if conversation_context:
                        # If this intent relates to previously mentioned entities, boost confidence
                        if any(
                            entity in conversation_context.get("mentioned_entities", {})
                            for entity in entities.keys()
                        ):
                            confidence += 0.1

                        # If this intent was previously used, boost confidence
                        if intent_name == conversation_context.get("last_intent"):
                            confidence += 0.05

                    # Cap confidence at 1.0
                    confidence = min(confidence, 1.0)

                    matched_intents.append(Intent(intent_name, confidence, entities))

        # If no intent matched, return a general query intent
        if not matched_intents:
            matched_intents.append(Intent("general_query", 0.5, {}))

        # Sort by confidence (highest first)
        matched_intents.sort(key=lambda x: x.confidence, reverse=True)

        return matched_intents


class Tool:
    """Class representing a tool that can be executed by the conversational core"""

    def __init__(
        self,
        name: str,
        function: Callable,
        description: str,
        required_params: Optional[List[str]] = None,
    ):
        self.name = name
        self.function = function
        self.description = description
        self.required_params = required_params or []

    def validate_params(self, params: Dict[str, Any]) -> Tuple[bool, str]:
        """
        Validate that the required parameters are present

        Returns:
            Tuple of (is_valid, error_message)
        """
        missing_params = [
            param for param in self.required_params if param not in params
        ]

        if missing_params:
            return False, f"Missing required parameters: {', '.join(missing_params)}"

        return True, ""

    def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the tool function with the given parameters

        Returns:
            The result of the tool execution
        """
        valid, error_msg = self.validate_params(params)
        if not valid:
            return {"error": error_msg, "status": "failed"}

        try:
            result = self.function(**params)
            return {"result": result, "status": "success"}
        except Exception as e:
            return {"error": str(e), "status": "failed"}


class ToolRegistry:
    """Registry for managing available tools"""

    def __init__(self):
        self.tools = {}

    def register_tool(self, tool: Tool):
        """Register a tool in the registry"""
        self.tools[tool.name] = tool

    def get_tool(self, tool_name: str) -> Optional[Tool]:
        """Get a tool by name"""
        return self.tools.get(tool_name)

    def list_tools(self) -> List[str]:
        """List all registered tool names"""
        return list(self.tools.keys())

    def get_tool_descriptions(self) -> List[str]:
        """Get descriptions of all registered tools"""
        return [f"{tool.name}: {tool.description}" for tool in self.tools.values()]


class ConversationSummary:
    """Class for managing and summarizing conversation history"""

    def __init__(self, max_turns: int = 10, max_tokens: int = 2000):
        self.history = []
        self.max_turns = max_turns
        self.max_tokens = max_tokens
        self.metadata = {
            "mentioned_entities": {},  # Track entities mentioned in conversation
            "last_intent": None,  # Track the last detected intent
            "last_tool_result": None,  # Track the last tool execution result
            "session_start": datetime.now().isoformat(),
        }

    def add_turn(
        self,
        user_query: str,
        assistant_response: str,
        detected_intent: Optional[Intent] = None,
        tool_result: Optional[Dict[str, Any]] = None,
    ):
        """
        Add a conversation turn and update metadata
        """
        turn = {
            "user": user_query,
            "assistant": assistant_response,
            "timestamp": datetime.now().isoformat(),
        }

        self.history.append(turn)

        # Update metadata
        if detected_intent:
            self.metadata["last_intent"] = detected_intent.name

            # Track entities
            for entity_name, entity_value in detected_intent.entities.items():
                if entity_name not in self.metadata["mentioned_entities"]:
                    self.metadata["mentioned_entities"][entity_name] = []

                if entity_value not in self.metadata["mentioned_entities"][entity_name]:
                    self.metadata["mentioned_entities"][entity_name].append(
                        entity_value
                    )

        if tool_result:
            self.metadata["last_tool_result"] = tool_result

        # Truncate history if necessary
        self._truncate_history()

    def _truncate_history(self):
        """
        Truncate history to stay within limits
        """
        # Truncate by number of turns
        if len(self.history) > self.max_turns:
            # Keep the most recent turns
            self.history = self.history[-self.max_turns :]

    def get_formatted_history(self, include_metadata: bool = False) -> str:
        """
        Get formatted conversation history for prompt assembly
        """
        formatted = []

        for turn in self.history:
            formatted.append(f"User: {turn['user']}")
            formatted.append(f"Assistant: {turn['assistant']}")

        if include_metadata and self.metadata:
            formatted.append("\nConversation Context:")
            for key, value in self.metadata.items():
                if value:  # Only include non-empty metadata
                    formatted.append(f"{key}: {value}")

        return "\n".join(formatted)

    def get_context(self) -> Dict[str, Any]:
        """
        Get conversation context for intent recognition
        """
        return deepcopy(self.metadata)  # Return a copy to prevent modification


class ConversationalCore:
    def __init__(self, model_name=None, model_type=None, api_key=None):
        """
        Initializes the core conversational logic component.

        Args:
            model_name (str, optional): Name of the LLM model to use.
                                      If None, uses the configured default.
            model_type (str, optional): Type of the model ("openai", "mock", etc.).
                                      If None, uses the configured default.
            api_key (str, optional): API key for the model service.
        """
        logger.info("Initializing ConversationalCore...")

        # 0. Load model configuration
        if model_name is None or model_type is None:
            config = llm_config.get_model_config()
            model_type = model_type or config["model_type"]
            model_name = model_name or config["model_name"]
            logger.info(f"Using configured model: {model_name} (type: {model_type})")

        # 1. Initialize context provider with vector store for RAG
        self.context_provider = ContextProvider()
        if self.context_provider.vector_store is None:
            logger.warning(
                "Vector store could not be loaded. RAG will not be available."
            )

        # 2. Initialize LLM and Domain Adapter
        try:
            self.llm_model = LLMModel(
                model_name=model_name, model_type=model_type, api_key=api_key
            )
            logger.info(f"Initialized LLM model: {model_name} (type: {model_type})")

            # Initialize domain adapter (disabled by default)
            self.domain_adapter = None
            adapter_path = os.environ.get("PULSE_DOMAIN_ADAPTER_PATH")
            if adapter_path and os.path.exists(adapter_path):
                try:
                    self.domain_adapter = DomainAdapter(adapter_path=adapter_path)
                    logger.info(f"Initialized domain adapter from {adapter_path}")
                except Exception as e:
                    logger.error(f"Failed to initialize domain adapter: {str(e)}")
        except ImportError as e:
            logger.warning(f"Could not initialize requested LLM model: {e}")
            logger.warning("Falling back to mock model...")
            self.llm_model = LLMModel(model_type="mock")

        # 3. Initialize conversation summary
        self.conversation_summary = ConversationSummary()

        # 4. Initialize pattern matcher
        self.pattern_matcher = PatternMatcher()

        # 5. Initialize tool registry
        self.tool_registry = ToolRegistry()
        self._register_tools()

        # 6. Define an improved system message template with better context utilization
        self.system_message_template = """You are Pulse AI, a helpful assistant for the Pulse codebase and financial forecasting system.
You analyze financial data, generate forecasts, run simulations, and help users understand market behavior.

IMPORTANT: Answer questions based on the provided CODEBASE CONTEXT snippets, conversation history, and tool results.
If you cannot find the answer in the context, clearly state that you don't have enough information.
Always provide accurate, helpful responses to user queries. Cite specific snippets when referencing code.

Capabilities:
- Retrieving and analyzing financial data
- Generating and explaining forecasts
- Running simulations
- Querying memory and symbolic systems
- Calculating trust scores

CODEBASE CONTEXT:
{codebase_context}

TOOL EXECUTION RESULT:
{tool_result_context}

CONVERSATION HISTORY:
{conversation_history}

USER QUERY:
{user_query}

Your response should be comprehensive, technically accurate, and directly answer the user's query
based on the available context. If referencing code, mention the specific file, function, or section.

RESPONSE:
"""
        logger.info("ConversationalCore initialized successfully.")

    def _register_tools(self):
        """Register available tools with the tool registry"""

        # Run Simulation tool
        self.tool_registry.register_tool(
            Tool(
                name="run_simulation",
                function=pulse_module_adapters.run_simulation,
                description="Run a simulation with the given parameters",
                required_params=[],  # Empty list since all params are optional in current implementation
            )
        )

        # Get Data tool
        self.tool_registry.register_tool(
            Tool(
                name="get_data",
                function=pulse_module_adapters.get_data,
                description="Get financial data for a symbol, of a certain type, within a date range",
                required_params=["symbol", "data_type", "date_range"],
            )
        )

        # Get Forecast tool
        self.tool_registry.register_tool(
            Tool(
                name="get_forecast",
                function=pulse_module_adapters.get_forecast,
                description="Get a forecast for a given symbol",
                required_params=["symbol"],
            )
        )

        # Get Trust Score tool
        self.tool_registry.register_tool(
            Tool(
                name="get_trust_score",
                function=pulse_module_adapters.get_trust_score,
                description="Get a trust score for an item",
                required_params=["item"],
            )
        )

        # Query Memory tool
        self.tool_registry.register_tool(
            Tool(
                name="query_memory",
                function=pulse_module_adapters.query_memory,
                description="Query Pulse's memory system",
                required_params=["query"],
            )
        )

        # Query Symbolic System tool
        self.tool_registry.register_tool(
            Tool(
                name="query_symbolic_system",
                function=pulse_module_adapters.query_symbolic_system,
                description="Query Pulse's symbolic system",
                required_params=["query"],
            )
        )

        # Recursive Learning Control tools

        # Start Recursive Learning tool
        self.tool_registry.register_tool(
            Tool(
                name="start_recursive_learning",
                function=pulse_module_adapters.start_recursive_learning,
                description="Start a new recursive learning cycle",
                required_params=[],  # All parameters are optional
            )
        )

        # Stop Recursive Learning tool
        self.tool_registry.register_tool(
            Tool(
                name="stop_recursive_learning",
                function=pulse_module_adapters.stop_recursive_learning,
                description="Stop a running recursive learning cycle",
                required_params=[],  # cycle_id is optional, can stop all cycles
            )
        )

        # Get Recursive Learning Status tool
        self.tool_registry.register_tool(
            Tool(
                name="get_recursive_learning_status",
                function=pulse_module_adapters.get_recursive_learning_status,
                description="Get the status of current recursive learning cycles",
                required_params=[],  # cycle_id is optional
            )
        )

        # Configure Recursive Learning tool
        self.tool_registry.register_tool(
            Tool(
                name="configure_recursive_learning",
                function=pulse_module_adapters.configure_recursive_learning,
                description="Configure parameters for recursive learning",
                required_params=[],  # All parameters are optional
            )
        )

        # Get Recursive Learning Metrics tool
        self.tool_registry.register_tool(
            Tool(
                name="get_recursive_learning_metrics",
                function=pulse_module_adapters.get_recursive_learning_metrics,
                description="Get metrics and results from recursive learning",
                required_params=[],  # All parameters are optional
            )
        )

    def recognize_intent(self, query, conversation_context=None):
        """
        Enhanced intent recognition using pattern matching and entity extraction.

        Args:
            query (str): The user query.
            conversation_context (dict, optional): Context from the conversation history.

        Returns:
            tuple: A tuple containing the top intent (Intent) and all recognized intents (list).
        """
        # Use the pattern matcher to identify potential intents
        intents = self.pattern_matcher.match(query, conversation_context)

        # Log the recognized intents for debugging
        print(
            f"Recognized intents: {[i.name for i in intents]} with confidences: {[i.confidence for i in intents]}"
        )

        # Return the top intent and the full list
        return intents[0], intents

    def execute_tool(self, intent_name, parameters):
        """
        Execute a tool based on the intent and parameters.

        Args:
            intent_name (str): The name of the intent.
            parameters (dict): Parameters for the tool.

        Returns:
            dict: The result of the tool execution.
        """
        # Get the tool from the registry
        tool = self.tool_registry.get_tool(intent_name)

        if not tool:
            return {
                "error": f"No tool found for intent: {intent_name}",
                "status": "failed",
            }

        # Execute the tool
        return tool.execute(parameters)

    def format_tool_result(self, tool_result):
        """
        Format a tool result for inclusion in the prompt.

        Args:
            tool_result (dict): The tool execution result.

        Returns:
            str: The formatted tool result.
        """
        if not tool_result:
            return "No specific action requested."

        status = tool_result.get("status", "unknown")

        if status == "failed":
            error = tool_result.get("error", "Unknown error")
            return f"Tool Execution Failed: {error}"

        result = tool_result.get("result", {})

        # Format the result based on its type
        if isinstance(result, dict):
            formatted_result = json.dumps(result, indent=2)
        elif isinstance(result, list):
            formatted_result = "\n".join([f"- {item}" for item in result])
        else:
            formatted_result = str(result)

        return f"Tool Execution Result: {formatted_result}"

    def process_query(self, user_query):
        """
        Processes a user query, recognizes intent, executes tools, retrieves context,
        and generates a response.

        Args:
            user_query (str): The user's input query.

        Returns:
            tuple: A tuple containing the generated response (str) and
                   a list of retrieved snippets (list).
        """
        print(f"Processing user query: '{user_query}'")

        # 1. Get conversation context for intent recognition
        conversation_context = self.conversation_summary.get_context()

        # 2. Recognize intent and extract parameters
        intent, all_intents = self.recognize_intent(user_query, conversation_context)
        print(f"Top intent: {intent.name} with confidence: {intent.confidence}")
        print(f"Extracted entities: {intent.entities}")

        # 3. Execute tool based on intent and get tool result context
        tool_result = None
        tool_result_context = "No specific action requested."

        if intent.name != "general_query":
            tool_result = self.execute_tool(intent.name, intent.entities)
            tool_result_context = self.format_tool_result(tool_result)
            print(f"Tool execution result: {tool_result_context}")

        # 4. Retrieve relevant snippets using the context provider
        retrieved_snippets = []
        try:
            if self.context_provider:
                search_results = self.context_provider.get_relevant_context(
                    user_query, k=5
                )
                # Format snippets for the prompt using the context provider's formatting
                codebase_context = self.context_provider.format_snippets_for_prompt(
                    search_results
                )
                retrieved_snippets = search_results
                logger.info(
                    f"Retrieved {len(retrieved_snippets)} relevant snippets for query."
                )
            else:
                codebase_context = (
                    "No relevant snippets found: context provider unavailable."
                )
                logger.warning(
                    "Context provider unavailable. Unable to retrieve snippets."
                )
        except Exception as e:
            codebase_context = "Error retrieving context snippets."
            logger.error(f"Error retrieving context snippets: {str(e)}")

        # 5. Get formatted conversation history
        conversation_history = self.conversation_summary.get_formatted_history()

        # 6. Assemble the prompt
        prompt = self.system_message_template.format(
            codebase_context=codebase_context,
            tool_result_context=tool_result_context,
            conversation_history=conversation_history,
            user_query=user_query,
        )
        print("Assembled prompt.")

        # 7. Call the LLM to generate a response
        try:
            # Measure token usage for the prompt
            prompt_tokens = self.llm_model.count_tokens(prompt)
            logger.info(f"Prompt size: ~{prompt_tokens} tokens")

            # Generate the response
            logger.info("Generating response from LLM...")
            generated_response = self.llm_model.generate_response(prompt)
            logger.info("Response generated successfully.")

            # Save the complete interaction for future reference if needed
            self._save_interaction_log(user_query, prompt, generated_response)
        except Exception as e:
            error_message = f"Error generating response: {str(e)}"
            logger.error(error_message)
            generated_response = f"I apologize, but I encountered an error while processing your request: {str(e)}"

        # 8. Update conversation summary
        self.conversation_summary.add_turn(
            user_query=user_query,
            assistant_response=generated_response,
            detected_intent=intent,
            tool_result=tool_result,
        )

        logger.info("Query processing complete.")
        return generated_response, retrieved_snippets

    def _save_interaction_log(
        self, user_query: str, prompt: str, response: str
    ) -> None:
        """
        Save the complete interaction log for future analysis.

        Args:
            user_query: The original user query
            prompt: The full prompt sent to the LLM
            response: The generated response
        """
        try:
            # Create log directory if it doesn't exist
            log_dir = os.path.join("chatmode", "logs")
            os.makedirs(log_dir, exist_ok=True)

            # Create a timestamped log file
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            log_path = os.path.join(log_dir, f"interaction_{timestamp}.json")

            # Prepare log data
            log_data = {
                "timestamp": datetime.now().isoformat(),
                "user_query": user_query,
                "prompt": prompt,
                "response": response,
                "model_info": self.llm_model.get_model_info(),
            }

            # Write log to file
            with open(log_path, "w") as f:
                json.dump(log_data, f, indent=2)

            logger.debug(f"Interaction log saved to {log_path}")
        except Exception as e:
            logger.error(f"Failed to save interaction log: {str(e)}")


if __name__ == "__main__":
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

    # response_2, snippets_2 = core.process_query("Get forecast for NVDA")
    # print("\n--- Response ---")
    # print(response_2)
    # print("--- Retrieved Snippets ---")
    # for snippet in snippets_2:
    #     print(f"Snippet:\n{snippet[:200]}...")
    #     print("-" * 10)
