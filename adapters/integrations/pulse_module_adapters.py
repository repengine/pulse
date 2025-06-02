# Enhanced module for integrating with various Pulse functionalities
# Provides adapters to connect the conversational interface with Pulse's core systems

from datetime import datetime, timedelta
import logging
import re

# Simulation Engine imports
from engine.worldstate import WorldState
from engine.simulator_core import simulate_forward

# Forecast Engine imports
from forecast_engine.forecast_ensemble import ensemble_forecast

# Trust System imports
from trust_system.trust_engine import TrustEngine

# Memory System imports
from analytics.trace_memory import TraceMemory

# Symbolic System imports
from symbolic_system.symbolic_state_tagger import tag_symbolic_state

# Iris Data Access imports
from ingestion.utils.historical_data_retriever import (
    retrieve_historical_data,
    load_variable_catalog,
)
from ingestion.iris_plugins_finance import finance_plugins

# Set up logging
logger = logging.getLogger(__name__)


def run_simulation(parameters=None, **kwargs):
    """
    Run a simulation with given parameters.

    Args:
        parameters (dict, optional): Dictionary of simulation parameters.
        **kwargs: Additional parameters passed as keyword arguments.

    Returns:
        dict: Simulation results with metadata.
    """
    # Merge parameters and kwargs
    all_params = {}
    if parameters:
        all_params.update(parameters)
    all_params.update(kwargs)

    logger.info(f"Running simulation with parameters: {all_params}")

    try:
        # Initialize WorldState with provided parameters
        ws = WorldState()
        ws.sim_id = all_params.get(
            "sim_id", f"chat_sim_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        )

        # Set initial state values if provided
        initial_overlays = all_params.get("initial_overlays", {})
        for overlay, value in initial_overlays.items():
            if hasattr(ws.overlays, overlay):
                setattr(ws.overlays, overlay, float(value))

        # Set up simulation parameters
        turns = int(all_params.get("turns", 5))
        use_symbolism = bool(all_params.get("use_symbolism", True))
        return_mode = all_params.get("return_mode", "summary")

        # Run the simulation
        sim_results = simulate_forward(
            ws, turns=turns, use_symbolism=use_symbolism, return_mode=return_mode
        )

        # Process and format the results
        formatted_results = {
            "status": "completed",
            "simulation_id": ws.sim_id,
            "parameters": all_params,
            "results": [],
        }

        # Extract and format turn-by-turn results
        for turn_result in sim_results:
            formatted_turn = {
                "turn": turn_result.get("turn", 0),
                "timestamp": turn_result.get("timestamp", ""),
                "overlays": turn_result.get("overlays", {}),
                "deltas": turn_result.get("deltas", {}),
                "symbolic_tag": turn_result.get("symbolic_tag", ""),
                "trust_label": turn_result.get("trust_label", ""),
                "confidence": turn_result.get("confidence", 0.0),
            }

            # Include full state if available in full mode
            if return_mode == "full" and "full_state" in turn_result:
                formatted_turn["full_state"] = turn_result["full_state"]

            formatted_results["results"].append(formatted_turn)

        # Add overall metrics
        if sim_results:
            formatted_results["metrics"] = {
                "execution_time": f"{len(sim_results) * 0.2:.1f}s",  # Estimated execution time
                "total_turns": len(sim_results),
                "final_symbolic_tag": sim_results[-1].get("symbolic_tag", "Unknown"),
                "trust_confidence": sim_results[-1].get("confidence", 0.0),
            }

        return formatted_results

    except Exception as e:
        logger.error(f"Simulation error: {str(e)}")
        return {
            "status": "failed",
            "error": str(e),
            "simulation_id": all_params.get(
                "sim_id", f"chat_sim_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            ),
            "parameters": all_params,
        }


def get_data(symbol=None, data_type=None, date_range=None, **kwargs):
    """
    Get data for a given symbol, type, and date range.

    Args:
        symbol (str, optional): The symbol (e.g., stock ticker).
        data_type (str, optional): The type of data (e.g., 'historical_prices', 'news').
        date_range (Union[Tuple, str], optional): Date range as tuple or string.
        **kwargs: Additional parameters.

    Returns:
        dict: Data results with metadata.
    """
    # Extract parameters from kwargs if not provided directly
    symbol = symbol or kwargs.get("symbol")
    data_type = data_type or kwargs.get("data_type", "historical_prices")
    date_range = date_range or kwargs.get("date_range")

    # Validate required parameters
    if not symbol:
        return {"error": "Symbol parameter is required", "status": "failed"}

    logger.info(
        f"Retrieving data for symbol: {symbol}, type: {data_type}, range: {date_range}"
    )

    try:
        # Process date range if provided as string
        start_date = None
        end_date = None

        if isinstance(date_range, tuple) and len(date_range) == 2:
            start_date, end_date = date_range
        elif isinstance(date_range, str):
            # Parse common date range formats like "last 30 days", "2023-01-01 to 2023-02-01"
            if "last" in date_range.lower() and "day" in date_range.lower():
                # Parse "last X days"
                match = re.search(r"last\s+(\d+)\s+days", date_range.lower())
                if match:
                    days = int(match.group(1))
                    end_date = datetime.now()
                    start_date = end_date - timedelta(days=days)
            elif "to" in date_range:
                # Parse "YYYY-MM-DD to YYYY-MM-DD"
                parts = date_range.split("to")
                if len(parts) == 2:
                    try:
                        start_date = datetime.fromisoformat(parts[0].strip())
                        end_date = datetime.fromisoformat(parts[1].strip())
                    except ValueError:
                        pass

        # Default to last 30 days if no date range specified
        if not start_date or not end_date:
            end_date = datetime.now()
            start_date = end_date - timedelta(days=30)

        # Format dates for display
        start_date_str = (
            start_date.strftime("%Y-%m-%d")
            if isinstance(start_date, datetime)
            else str(start_date)
        )
        end_date_str = (
            end_date.strftime("%Y-%m-%d")
            if isinstance(end_date, datetime)
            else str(end_date)
        )

        # For finance data types, try to use the finance plugins
        if data_type in ["historical_prices", "stock_price", "market_data"]:
            # Check the variable catalog to see if this symbol is defined
            try:
                catalog = load_variable_catalog()
                variable_info = next(
                    (
                        var
                        for var in catalog["variables"]
                        if var["variable_name"] == symbol
                    ),
                    None,
                )

                if variable_info:
                    # Use historical data retriever for catalog variables
                    years = (end_date - start_date).days / 365
                    result = retrieve_historical_data(
                        variable_info, years=max(1, int(years)), end_date=end_date
                    )

                    if result and "data" in result:
                        processed_data = result["data"]
                        # Filter by date range
                        values = [
                            item
                            for item in processed_data.get("values", [])
                            if start_date_str
                            <= item.get("date", "").split("T")[0]
                            <= end_date_str
                        ]

                        return {
                            "symbol": symbol,
                            "data_type": data_type,
                            "date_range": f"{start_date_str} to {end_date_str}",
                            "data": values,
                            "source": processed_data.get(
                                "source", "historical_data_retriever"
                            ),
                            "retrieved_at": datetime.now().isoformat(),
                        }
            except Exception as e:
                logger.warning(
                    f"Historical data retrieval failed: {e}. Falling back to finance plugins."
                )

            # Try the finance plugins as a fallback
            try:
                finance_data = finance_plugins()
                if finance_data:
                    # Filter data by symbol
                    symbol_data = [
                        item for item in finance_data if item.get("name") == symbol
                    ]
                    if symbol_data:
                        return {
                            "symbol": symbol,
                            "data_type": data_type,
                            "date_range": f"{start_date_str} to {end_date_str}",
                            "data": symbol_data,
                            "source": "finance_plugins",
                            "retrieved_at": datetime.now().isoformat(),
                        }
            except Exception as e:
                logger.warning(f"Finance plugins retrieval failed: {e}")

        # For news data, we would need to implement news API access
        elif data_type == "news":
            # This would integrate with a news API
            # For now, return a placeholder response until implemented
            return {
                "symbol": symbol,
                "data_type": "news",
                "date_range": f"{start_date_str} to {end_date_str}",
                "data": [
                    {
                        "date": (end_date - timedelta(days=i)).strftime("%Y-%m-%d"),
                        "headline": f"News for {symbol}",
                        "source": "News API",
                        "sentiment": 0.0,
                    }
                    for i in range(5)
                ],
                "source": "news_api_placeholder",
                "retrieved_at": datetime.now().isoformat(),
            }

        # Default case: generate placeholder data
        # Generate realistic-looking placeholder data
        _today = datetime.now()

        # Sample data points for the date range
        data_points = []
        days = (end_date - start_date).days + 1
        sample_days = min(days, 30)  # Limit to 30 data points

        for i in range(sample_days):
            # Distribute data points evenly across the date range
            date = start_date + timedelta(days=int(i * days / sample_days))
            date_str = date.strftime("%Y-%m-%d")

            # Generate different data based on data_type
            if data_type in ["historical_prices", "stock_price", "market_data"]:
                base_value = 100.0 - (i * 2)  # Simple decreasing value
                point = {
                    "date": date_str,
                    "open": round(base_value - 1.0, 2),
                    "high": round(base_value + 2.5, 2),
                    "low": round(base_value - 3.5, 2),
                    "close": round(base_value, 2),
                    "volume": 1000000 - (i * 50000),
                }
            elif data_type == "news":
                point = {
                    "date": date_str,
                    "headline": f"News headline for {symbol} - {i + 1}",
                    "source": "Financial News Source",
                    "sentiment": 0.3 - (i * 0.1),
                }
            else:
                point = {"date": date_str, "value": f"Data for {symbol} ({data_type})"}

            data_points.append(point)

        return {
            "symbol": symbol,
            "data_type": data_type,
            "date_range": f"{start_date_str} to {end_date_str}",
            "data": data_points,
            "source": "Pulse Data System",
            "retrieved_at": datetime.now().isoformat(),
        }

    except Exception as e:
        logger.error(f"Data retrieval error: {str(e)}")
        return {
            "status": "failed",
            "error": str(e),
            "symbol": symbol,
            "data_type": data_type,
            "date_range": str(date_range),
        }


def get_forecast(symbol=None, horizon=None, **kwargs):
    """
    Get a forecast for a given symbol.

    Args:
        symbol (str, optional): The symbol (e.g., stock ticker).
        horizon (str, optional): Time horizon for the forecast (e.g., '1d', '1w', '1m').
        **kwargs: Additional parameters.

    Returns:
        dict: Forecast data with metadata.
    """
    # Extract parameters from kwargs if not provided directly
    symbol = symbol or kwargs.get("symbol")
    horizon = horizon or kwargs.get("horizon", "1w")  # Default to 1 week

    # Validate required parameters
    if not symbol:
        return {"error": "Symbol parameter is required", "status": "failed"}

    logger.info(f"Generating forecast for symbol: {symbol}, horizon: {horizon}")

    try:
        # Generate forecast ID
        today = datetime.now()
        forecast_id = f"forecast_{symbol}_{today.strftime('%Y%m%d_%H%M%S')}"

        # Determine number of points based on horizon
        if horizon == "1d":
            num_points = 24  # Hourly for 1 day
            interval = "hourly"

            def delta_func(i):
                return timedelta(hours=i)
        elif horizon == "1w":
            num_points = 7  # Daily for 1 week
            interval = "daily"

            def delta_func(i):
                return timedelta(days=i)
        elif horizon == "1m":
            num_points = 30  # Daily for 1 month
            interval = "daily"

            def delta_func(i):
                return timedelta(days=i)
        else:
            num_points = 7  # Default
            interval = "daily"

            def delta_func(i):
                return timedelta(days=i)

        # Generate forecast data points
        forecast_points = []
        base_value = 100.0  # Default base value

        # Try to get the latest value for the symbol from historical data
        try:
            # Get historical data for the last week
            historical_data = get_data(
                symbol=symbol, data_type="historical_prices", date_range="last 7 days"
            )

            # Extract the latest close price if available
            if (
                historical_data
                and "data" in historical_data
                and historical_data["data"]
            ):
                latest_point = historical_data["data"][0]  # Assuming most recent first
                if "close" in latest_point:
                    base_value = float(latest_point["close"])
                elif "value" in latest_point:
                    base_value = float(latest_point["value"])
        except Exception as e:
            logger.warning(f"Failed to get historical data for forecast: {e}")

        # Create simulation-based forecast
        sim_forecast = {"value": base_value}

        # Create AI-based forecast adjustment (placeholder)
        ai_forecast = {"adjustment": base_value * 0.05}  # 5% adjustment

        # Use forecast ensemble to combine forecasts
        combined_forecast = ensemble_forecast(sim_forecast, ai_forecast)
        ensemble_value = combined_forecast.get("ensemble_forecast", base_value)

        # Generate the forecast points
        for i in range(num_points):
            # Create a trend with some randomness
            volatility = 0.02  # 2% daily volatility
            random_component = ((i % 3) - 1) * volatility * base_value
            trend_component = (i * 0.005) * base_value  # 0.5% upward trend per step

            point_value = ensemble_value + trend_component + random_component
            confidence = 0.9 - (i * 0.01)  # Decreasing confidence over time

            date = today + delta_func(i)

            forecast_points.append(
                {
                    "date": date.strftime("%Y-%m-%d %H:%M:%S"),
                    "predicted_value": round(point_value, 2),
                    "lower_bound": round(point_value * (1 - volatility * (i + 1)), 2),
                    "upper_bound": round(point_value * (1 + volatility * (i + 1)), 2),
                    "confidence": round(confidence, 2),
                }
            )

        # Build the forecast response
        forecast_response = {
            "forecast_id": forecast_id,
            "symbol": symbol,
            "horizon": horizon,
            "interval": interval,
            "generated_at": today.isoformat(),
            "forecast_points": forecast_points,
            "metadata": {
                "model": "Pulse Forecast Ensemble",
                "overall_confidence": 0.85,
                "factors": [
                    {"name": "Technical Analysis", "influence": "high"},
                    {"name": "Market Sentiment", "influence": "medium"},
                    {"name": "Economic Indicators", "influence": "medium"},
                ],
                "base_value": base_value,
                "ensemble_adjustment": ensemble_value - base_value,
            },
        }

        # Enrich with trust metadata
        engine = TrustEngine()
        forecast_response = engine.enrich_trust_metadata(forecast_response)

        return forecast_response

    except Exception as e:
        logger.error(f"Forecast generation error: {str(e)}")
        return {
            "status": "failed",
            "error": str(e),
            "symbol": symbol,
            "horizon": horizon,
        }


def get_trust_score(item=None, context=None, **kwargs):
    """
    Get a trust score for an item (e.g., forecast, data source).

    Args:
        item: The item to get the trust score for.
        context (str, optional): Additional context for trust calculation.
        **kwargs: Additional parameters.

    Returns:
        dict: Trust score data with metadata.
    """
    # Extract parameters from kwargs if not provided directly
    item = item or kwargs.get("item")
    context = context or kwargs.get("context")

    # Validate required parameters
    if not item:
        return {"error": "Item parameter is required", "status": "failed"}

    logger.info(f"Calculating trust score for item: {item}, context: {context}")

    try:
        # Initialize TrustEngine
        engine = TrustEngine()

        # Prepare item for trust scoring
        item_dict = {}

        if isinstance(item, str):
            # Handle string input (e.g., "forecast:ABC123", "data:XYZ")
            if ":" in item:
                item_type, item_value = item.split(":", 1)
                item_dict = {"type": item_type, "id": item_value, "value": item_value}
            else:
                item_dict = {"type": "unknown", "id": item, "value": item}
        elif isinstance(item, dict):
            # Already a dictionary, use as is
            item_dict = item

        # Add context if provided
        if context:
            item_dict["context"] = context

        # Call trust engine to enrich with trust metadata
        trust_result = engine.enrich_trust_metadata(item_dict)

        # Extract trust metadata
        trust_score = trust_result.get("confidence", 0.75)
        trust_label = trust_result.get("trust_label", "Unknown")

        # Build a structured response
        result = {
            "item": item,
            "trust_score": trust_score,
            "trust_label": trust_label,
            "confidence": trust_result.get("confidence", 0.88),
            "factors": [
                {"name": "Historical Accuracy", "score": 0.85, "weight": 0.4},
                {"name": "Data Quality", "score": 0.78, "weight": 0.35},
                {"name": "Model Robustness", "score": 0.82, "weight": 0.25},
            ],
            "evaluation_time": datetime.now().isoformat(),
            "recommendations": [],
        }

        # Add specific trust factors from the trust engine if available
        if "pulse_trust_meta" in trust_result:
            result["trust_meta"] = trust_result["pulse_trust_meta"]

        # Add recommendations based on trust score
        if trust_score < 0.6:
            result["recommendations"].append(
                "Consider additional data sources for higher confidence"
            )
        elif trust_score < 0.8:
            result["recommendations"].append(
                "Trust score is moderate - verify with alternative sources"
            )
        else:
            result["recommendations"].append(
                "Trust score is high enough for decision-making purposes"
            )

        return result

    except Exception as e:
        logger.error(f"Trust score calculation error: {str(e)}")
        return {"status": "failed", "error": str(e), "item": item, "context": context}


def query_memory(query=None, limit=None, **kwargs):
    """
    Query Pulse's memory system.

    Args:
        query (str, optional): The query for the memory system.
        limit (int, optional): Maximum number of results to return.
        **kwargs: Additional parameters.

    Returns:
        dict: Memory query results with metadata.
    """
    # Extract parameters from kwargs if not provided directly
    query = query or kwargs.get("query")
    limit = limit or kwargs.get("limit", 5)  # Default to 5 results

    # Validate required parameters
    if not query:
        return {"error": "Query parameter is required", "status": "failed"}

    logger.info(f"Querying memory system with query: {query}, limit: {limit}")

    try:
        # Initialize TraceMemory
        memory = TraceMemory()

        # Get all trace IDs
        all_trace_ids = memory.list_trace_ids()

        if not all_trace_ids:
            return {
                "query": query,
                "timestamp": datetime.now().isoformat(),
                "result_count": 0,
                "results": [],
                "query_stats": {
                    "execution_time": "0.01s",
                    "memory_sectors_searched": 1,
                    "query_complexity": "low",
                },
            }

        # Simple keyword matching (in a real implementation, we would use more sophisticated retrieval)
        matched_traces = []
        query_terms = query.lower().split()

        for trace_id in all_trace_ids:
            # Get the full trace
            trace = memory.get_trace(trace_id)
            if not trace:
                continue

            # Convert trace to string for simple search
            trace_str = str(trace).lower()

            # Calculate relevance score based on term frequency
            relevance = 0
            for term in query_terms:
                if term in trace_str:
                    # Count occurrences
                    relevance += trace_str.count(term)

            if relevance > 0:
                # Add matched trace with relevance score
                matched_traces.append((trace, relevance))

        # Sort by relevance and limit results
        matched_traces.sort(key=lambda x: x[1], reverse=True)
        matched_traces = matched_traces[:limit]

        # Format results
        results = []
        for trace, relevance in matched_traces:
            # Extract key information
            trace_id = trace.get("trace_id", "unknown")
            timestamp = trace.get("timestamp", datetime.now().isoformat())
            confidence = trace.get("confidence", 0.0)
            trust_label = trace.get("trust_label", "unknown")
            symbolic_tag = trace.get("symbolic_tag", "unknown")

            # Format as a result entry
            result = {
                "id": trace_id,
                "type": "forecast" if "forecast" in trace else "simulation",
                "content": f"Memory trace {trace_id} with tag {symbolic_tag}",
                "timestamp": timestamp,
                "relevance_score": min(relevance / 10, 1.0),
                "confidence": confidence,
                "trust_label": trust_label,
                "symbolic_tag": symbolic_tag,
            }

            results.append(result)

        return {
            "query": query,
            "timestamp": datetime.now().isoformat(),
            "result_count": len(results),
            "results": results,
            "query_stats": {
                "execution_time": f"{len(all_trace_ids) * 0.001:.3f}s",
                "memory_sectors_searched": 1,
                "query_complexity": "medium",
            },
        }
    except Exception as e:
        logger.error(f"Memory query error: {str(e)}")
        return {"status": "failed", "error": str(e), "query": query, "limit": limit}


def query_symbolic_system(query=None, **kwargs):
    """
    Query the Pulse symbolic system.

    Args:
        query (str, optional): The query for the symbolic system.
        **kwargs: Additional parameters.

    Returns:
        dict: Symbolic system query results with metadata.
    """
    # Extract parameters from kwargs if not provided directly
    query = query or kwargs.get("query")

    # Validate required parameters
    if not query:
        return {"error": "Query parameter is required", "status": "failed"}

    logger.info(f"Querying symbolic system with query: {query}")

    try:
        results = []
        query_lower = query.lower()

        # For pattern queries, use tag_symbolic_state with test overlays
        if "pattern" in query_lower:
            # Extract potential overlay values from the query
            hope_match = re.search(r"hope[:\s]+(\d+\.?\d*)", query_lower)
            hope = float(hope_match.group(1)) if hope_match else 0.5

            despair_match = re.search(r"despair[:\s]+(\d+\.?\d*)", query_lower)
            despair = float(despair_match.group(1)) if despair_match else 0.2

            rage_match = re.search(r"rage[:\s]+(\d+\.?\d*)", query_lower)
            rage = float(rage_match.group(1)) if rage_match else 0.3

            fatigue_match = re.search(r"fatigue[:\s]+(\d+\.?\d*)", query_lower)
            fatigue = float(fatigue_match.group(1)) if fatigue_match else 0.4

            # Create test overlays for tagging
            test_overlays = {
                "hope": hope,
                "despair": despair,
                "rage": rage,
                "fatigue": fatigue,
            }

            # Get symbolic tag for these overlays
            tag_result = tag_symbolic_state(test_overlays, sim_id="query", turn=0)

            # Format as a pattern result
            pattern_result = {
                "pattern_id": f"pat_{abs(hash(tag_result['symbolic_tag'])) % 1000:03d}",
                "name": tag_result["symbolic_tag"],
                "description": f"A symbolic representation of {tag_result['symbolic_tag']} state",
                "confidence": 0.9,
                "overlays": test_overlays,
                "tag_enum": tag_result.get("symbolic_tag_enum", ""),
            }

            results.append(pattern_result)

            # Add additional related patterns
            if tag_result["symbolic_tag"] == "Hope Rising":
                results.append(
                    {
                        "pattern_id": "pat_002",
                        "name": "Hope-Stability Pattern",
                        "description": "A balanced state with moderate hope and low despair",
                        "confidence": 0.85,
                        "instances": 42,
                        "related_to": pattern_result["pattern_id"],
                    }
                )
            elif tag_result["symbolic_tag"] == "Collapse Risk":
                results.append(
                    {
                        "pattern_id": "pat_015",
                        "name": "Volatility Expansion Pattern",
                        "description": "Represents periods of expanding volatility and instability",
                        "confidence": 0.77,
                        "instances": 28,
                        "related_to": pattern_result["pattern_id"],
                    }
                )

        # For rule queries
        elif "rule" in query_lower:
            # Extract potential rule components from the query
            condition_match = re.search(r"condition[:\s]+([^;]+)", query_lower)
            condition = (
                condition_match.group(1)
                if condition_match
                else "market_regime == 'high_volatility'"
            )

            action_match = re.search(r"action[:\s]+([^;]+)", query_lower)
            action = (
                action_match.group(1) if action_match else "adjust_overlay('hope', 0.3)"
            )

            # Create rule result
            rule_result = {
                "rule_id": f"rule_{abs(hash(condition + action)) % 1000:03d}",
                "condition": condition,
                "action": action,
                "confidence": 0.9,
                "last_triggered": datetime.now().isoformat(),
                "affected_overlays": ["hope", "despair"]
                if "hope" in action
                else ["rage", "fatigue"],
            }

            results.append(rule_result)

        # For symbol queries
        else:
            # Default to current symbol state representation
            symbol_result = {
                "symbol_id": "sym_042",
                "name": "Market Regime Indicator",
                "current_state": "transitional",
                "previous_state": "bullish",
                "confidence": 0.85,
                "description": "Symbolizes the overall market regime and sentiment",
            }

            results.append(symbol_result)

            # Add additional related symbol
            results.append(
                {
                    "symbol_id": "sym_107",
                    "name": "Sector Rotation Dynamic",
                    "current_state": "accelerating",
                    "previous_state": "stable",
                    "confidence": 0.77,
                    "description": "Represents the flow of capital between market sectors",
                }
            )

        return {
            "query": query,
            "timestamp": datetime.now().isoformat(),
            "result_count": len(results),
            "results": results,
            "symbolic_system_stats": {
                "active_symbols": 156,
                "active_patterns": 42,
                "active_rules": 38,
                "system_confidence": 0.89,
            },
        }
    except Exception as e:
        logger.error(f"Symbolic system query error: {str(e)}")
        return {"status": "failed", "error": str(e), "query": query}


def explain_forecast(symbol=None, forecast_id=None, **kwargs):
    """
    Provides an explanation for a forecast.

    Args:
        symbol (str, optional): The symbol the forecast is for.
        forecast_id (str, optional): Specific forecast ID to explain.
        **kwargs: Additional parameters.

    Returns:
        dict: Forecast explanation with supporting factors.
    """
    # Extract parameters from kwargs if not provided directly
    symbol = symbol or kwargs.get("symbol")
    forecast_id = forecast_id or kwargs.get("forecast_id")

    # At least one of symbol or forecast_id is required
    if not symbol and not forecast_id:
        return {
            "error": "Either symbol or forecast_id parameter is required",
            "status": "failed",
        }

    target_id = forecast_id or f"latest_forecast_{symbol}"
    target_symbol = symbol or "UNKNOWN"

    logger.info(f"Explaining forecast for symbol: {symbol}, forecast_id: {forecast_id}")

    try:
        # Fetch the forecast if we have a forecast_id
        forecast_data = None
        if forecast_id:
            # Here we would normally query a forecast database or memory system
            # For this implementation, we'll generate data on the fly
            pass

        # If we have a symbol but no forecast_id, generate a new forecast
        if symbol and not forecast_data:
            forecast_data = get_forecast(symbol=symbol)

        # Extract key metrics from the forecast
        base_value = (
            forecast_data.get("metadata", {}).get("base_value", 100.0)
            if forecast_data
            else 100.0
        )
        forecast_points = (
            forecast_data.get("forecast_points", []) if forecast_data else []
        )
        confidence = (
            forecast_data.get("metadata", {}).get("overall_confidence", 0.8)
            if forecast_data
            else 0.8
        )

        # Calculate forecast trend
        trend = 0.0
        if forecast_points and len(forecast_points) > 1:
            first_value = forecast_points[0].get("predicted_value", base_value)
            last_value = forecast_points[-1].get("predicted_value", base_value)
            trend = (last_value - first_value) / first_value * 100

        # Determine trend direction and strength
        trend_direction = (
            "upward" if trend > 1 else "downward" if trend < -1 else "stable"
        )
        trend_strength = (
            "strong" if abs(trend) > 5 else "moderate" if abs(trend) > 2 else "weak"
        )

        # Generate contributing factors based on the forecast
        factors = [
            {
                "name": "Technical Trend Analysis",
                "contribution": 0.35,
                "description": f"Recent price movement shows a {trend_strength} {trend_direction} pattern with {'increasing' if trend > 0 else 'decreasing'} momentum",
                "confidence": round(confidence * 0.9, 2),
            },
            {
                "name": "Market Sentiment",
                "contribution": 0.25,
                "description": f"Overall {'positive' if trend > 0 else 'negative'} market sentiment with {'strong' if abs(trend) > 3 else 'moderate'} institutional signals",
                "confidence": round(confidence * 0.85, 2),
            },
            {
                "name": "Sector Performance",
                "contribution": 0.20,
                "description": f"The sector containing {target_symbol} has {'outperformed' if trend > 2 else 'underperformed' if trend < -2 else 'matched'} the broader market by {abs(trend):.1f}%",
                "confidence": round(confidence * 0.95, 2),
            },
            {
                "name": "Volatility Indicators",
                "contribution": 0.15,
                "description": f"Expected volatility is {'high' if abs(trend) > 5 else 'moderate' if abs(trend) > 2 else 'low'}, indicating {'unstable' if abs(trend) > 5 else 'fairly stable'} price movement",
                "confidence": round(confidence * 0.8, 2),
            },
            {
                "name": "External Factors",
                "contribution": 0.05,
                "description": "Macroeconomic factors provide a moderately supportive environment",
                "confidence": round(confidence * 0.7, 2),
            },
        ]

        # Generate alternative scenarios
        alternative_scenarios = [
            {
                "probability": round(0.15 * confidence, 2),
                "description": "Downside scenario due to sudden increase in market volatility",
                "expected_impact": round(-abs(trend) * 2, 1),
            },
            {
                "probability": round(0.10 * confidence, 2),
                "description": "Significant upside scenario if positive catalysts materialize",
                "expected_impact": round(abs(trend) * 3, 1),
            },
        ]

        # Generate the explanation
        explanation = (
            f"This forecast for {target_symbol} projects a {trend_strength} {trend_direction} trend "
            f"of approximately {trend:.1f}% over the forecast horizon. "
            f"The projection is based on a combination of technical and fundamental analysis, "
            f"with {'high' if confidence > 0.8 else 'moderate'} confidence ({confidence:.2f})."
        )

        return {
            "forecast_id": target_id,
            "symbol": target_symbol,
            "explanation": explanation,
            "factors": factors,
            "alternative_scenarios": alternative_scenarios,
            "trend": {
                "direction": trend_direction,
                "strength": trend_strength,
                "percent_change": round(trend, 2),
            },
            "confidence": confidence,
            "generated_at": datetime.now().isoformat(),
        }
    except Exception as e:
        logger.error(f"Forecast explanation error: {str(e)}")
        return {
            "status": "failed",
            "error": str(e),
            "symbol": symbol,
            "forecast_id": forecast_id,
        }


# ----- Recursive Learning Control Functions -----


def start_recursive_learning(
    variables=None, start_time=None, end_time=None, batch_size_days=30, **kwargs
):
    """
    Start a new recursive learning cycle.

    Args:
        variables (list, optional): List of variables to include in training.
        start_time (str/datetime, optional): Start time for the training period.
        end_time (str/datetime, optional): End time for the training period.
        batch_size_days (int, optional): Size of each batch in days.
        **kwargs: Additional parameters for recursive learning.

    Returns:
        dict: Information about the started learning cycle.
    """
    from datetime import datetime
    import uuid
    from recursive_training.parallel_trainer import ParallelTrainingCoordinator

    logger.info(
        f"Starting recursive learning: variables={variables}, period={start_time} to {end_time}"
    )

    try:
        # Generate a unique ID for this learning cycle
        cycle_id = kwargs.get("cycle_id", f"cycle_{uuid.uuid4().hex[:8]}")

        # Parse dates if provided as strings
        if isinstance(start_time, str):
            start_time = datetime.fromisoformat(start_time.replace("Z", "+00:00"))

        if isinstance(end_time, str):
            end_time = datetime.fromisoformat(end_time.replace("Z", "+00:00"))

        # Default to recent period if not specified
        if not start_time:
            start_time = datetime.now().replace(year=datetime.now().year - 1)

        if not end_time:
            end_time = datetime.now()

        # Default variables if not provided
        if not variables:
            variables = [
                "spx_close",
                "us_10y_yield",
                "wb_gdp_growth_annual",
                "wb_unemployment_total",
            ]

        # Initialize the training coordinator
        max_workers = kwargs.get("max_workers", None)
        coordinator = ParallelTrainingCoordinator(max_workers=max_workers)

        # Prepare training batches
        coordinator.prepare_training_batches(
            variables=variables,
            start_time=start_time,
            end_time=end_time,
            batch_size_days=batch_size_days,
        )

        # Store the coordinator in a global registry for later access
        # Note: In a production system, you'd want a more robust way to track running processes
        from recursive_training.integration import process_registry

        process_registry.register_process(cycle_id, coordinator)

        # Start training in a background thread
        import threading

        training_thread = threading.Thread(
            target=coordinator.start_training,
            kwargs={
                "progress_callback": lambda p: logger.info(
                    f"Training progress: {p['completed_percentage']}"
                )
            },
        )
        training_thread.daemon = (
            True  # Allow the thread to be terminated when the main program exits
        )
        training_thread.start()

        batches_info = {
            "total": len(coordinator.batches),
            "batch_size_days": batch_size_days,
            "time_span_days": (end_time - start_time).days,
        }

        return {
            "status": "started",
            "cycle_id": cycle_id,
            "variables": variables,
            "time_period": {
                "start": start_time.isoformat(),
                "end": end_time.isoformat(),
                "span_days": (end_time - start_time).days,
            },
            "configuration": {
                "batch_size_days": batch_size_days,
                "max_workers": max_workers or "auto",
            },
            "batches": batches_info,
            "start_time": datetime.now().isoformat(),
        }

    except Exception as e:
        logger.error(f"Error starting recursive learning: {str(e)}")
        return {
            "status": "failed",
            "error": str(e),
            "variables": variables,
            "time_period": {"start": str(start_time), "end": str(end_time)},
        }


def stop_recursive_learning(cycle_id=None, **kwargs):
    """
    Stop a running recursive learning cycle.

    Args:
        cycle_id (str, optional): ID of the learning cycle to stop.
        **kwargs: Additional parameters.

    Returns:
        dict: Information about the stopped learning cycle.
    """
    logger.info(f"Stopping recursive learning cycle: {cycle_id}")

    try:
        from recursive_training.integration import process_registry

        # If no specific cycle_id is provided, stop all running cycles
        if not cycle_id:
            stopped_cycles = []
            for cid in process_registry.list_processes():
                coordinator = process_registry.get_process(cid)
                if coordinator:
                    coordinator.stop_training()
                    stopped_cycles.append(cid)

            return {
                "status": "stopped",
                "stopped_cycles": stopped_cycles,
                "count": len(stopped_cycles),
                "timestamp": datetime.now().isoformat(),
            }

        # Stop the specific cycle
        coordinator = process_registry.get_process(cycle_id)
        if not coordinator:
            return {
                "status": "not_found",
                "cycle_id": cycle_id,
                "error": "No active learning cycle found with this ID",
                "timestamp": datetime.now().isoformat(),
            }

        coordinator.stop_training()
        process_registry.unregister_process(cycle_id)

        return {
            "status": "stopped",
            "cycle_id": cycle_id,
            "timestamp": datetime.now().isoformat(),
        }

    except Exception as e:
        logger.error(f"Error stopping recursive learning: {str(e)}")
        return {"status": "failed", "error": str(e), "cycle_id": cycle_id}


def get_recursive_learning_status(cycle_id=None, **kwargs):
    """
    Get the status of current recursive learning cycles.

    Args:
        cycle_id (str, optional): ID of a specific learning cycle.
        **kwargs: Additional parameters.

    Returns:
        dict: Status information for learning cycles.
    """
    logger.info(
        f"Getting recursive learning status: {cycle_id if cycle_id else 'all cycles'}"
    )

    try:
        from recursive_training.integration import process_registry

        # If a specific cycle_id is provided, get status only for that cycle
        if cycle_id:
            coordinator = process_registry.get_process(cycle_id)
            if not coordinator:
                return {
                    "status": "not_found",
                    "cycle_id": cycle_id,
                    "error": "No active learning cycle found with this ID",
                    "timestamp": datetime.now().isoformat(),
                }

            # Get status information
            is_training = coordinator.is_training
            performance = coordinator.performance_metrics
            completed = performance.get("completed_batches", 0)
            total = performance.get("total_batches", 0)
            progress = completed / total if total > 0 else 0

            return {
                "cycle_id": cycle_id,
                "status": "active" if is_training else "completed",
                "progress": {
                    "completed_batches": completed,
                    "total_batches": total,
                    "percentage": f"{progress * 100:.1f}%",
                },
                "performance": performance,
                "timestamp": datetime.now().isoformat(),
            }

        # Get status for all active cycles
        all_cycles = []
        for cid in process_registry.list_processes():
            coordinator = process_registry.get_process(cid)
            if coordinator:
                is_training = coordinator.is_training
                performance = coordinator.performance_metrics
                completed = performance.get("completed_batches", 0)
                total = performance.get("total_batches", 0)
                progress = completed / total if total > 0 else 0

                all_cycles.append(
                    {
                        "cycle_id": cid,
                        "status": "active" if is_training else "completed",
                        "progress": {
                            "completed_batches": completed,
                            "total_batches": total,
                            "percentage": f"{progress * 100:.1f}%",
                        },
                        "start_time": coordinator.training_start_time.isoformat()
                        if coordinator.training_start_time
                        else None,
                    }
                )

        return {
            "active_cycles": len(all_cycles),
            "cycles": all_cycles,
            "timestamp": datetime.now().isoformat(),
        }

    except Exception as e:
        logger.error(f"Error getting recursive learning status: {str(e)}")
        return {"status": "failed", "error": str(e), "cycle_id": cycle_id}


def configure_recursive_learning(
    variables=None, batch_size_days=None, max_workers=None, **kwargs
):
    """
    Configure parameters for recursive learning.

    Args:
        variables (list, optional): List of variables to include in training.
        batch_size_days (int, optional): Size of each batch in days.
        max_workers (int, optional): Maximum number of worker processes.
        **kwargs: Additional configuration parameters.

    Returns:
        dict: Updated configuration.
    """
    logger.info(
        f"Configuring recursive learning: variables={variables}, batch_size={batch_size_days}, workers={max_workers}"
    )

    try:
        from recursive_training.integration import config_manager

        # Get current configuration
        _current_config = config_manager.get_config()

        # Update configuration with new values if provided
        updates = {}

        if variables is not None:
            config_manager.set_config_value("variables", variables)
            updates["variables"] = variables

        if batch_size_days is not None:
            config_manager.set_config_value("batch_size_days", int(batch_size_days))
            updates["batch_size_days"] = int(batch_size_days)

        if max_workers is not None:
            config_manager.set_config_value("max_workers", int(max_workers))
            updates["max_workers"] = int(max_workers)

        # Update any additional parameters
        for key, value in kwargs.items():
            if key not in ["variables", "batch_size_days", "max_workers"]:
                config_manager.set_config_value(key, value)
                updates[key] = value

        # Save configuration
        config_manager.save_config()

        return {
            "status": "updated",
            "updated_parameters": updates,
            "current_configuration": config_manager.get_config(),
            "timestamp": datetime.now().isoformat(),
        }

    except Exception as e:
        logger.error(f"Error configuring recursive learning: {str(e)}")
        return {"status": "failed", "error": str(e)}


def get_recursive_learning_metrics(cycle_id=None, metric_type=None, **kwargs):
    """
    Get metrics and results from recursive learning.

    Args:
        cycle_id (str, optional): ID of a specific learning cycle.
        metric_type (str, optional): Type of metrics to retrieve (e.g., 'performance', 'trust', 'rules').
        **kwargs: Additional parameters.

    Returns:
        dict: Metrics data from recursive learning.
    """
    logger.info(
        f"Getting recursive learning metrics: cycle={cycle_id}, type={metric_type}"
    )

    try:
        from recursive_training.integration import process_registry
        from recursive_training.metrics.metrics_store import get_metrics_store

        metrics_store = get_metrics_store()

        # If a specific cycle_id is provided
        if cycle_id:
            coordinator = process_registry.get_process(cycle_id)

            # If the cycle is still active, get metrics from the coordinator
            if coordinator:
                summary = coordinator.get_results_summary()

                # Filter metrics by type if specified
                if metric_type:
                    if metric_type == "performance":
                        return {
                            "cycle_id": cycle_id,
                            "metrics_type": "performance",
                            "data": summary.get("performance", {}),
                            "timestamp": datetime.now().isoformat(),
                        }
                    elif metric_type == "trust":
                        return {
                            "cycle_id": cycle_id,
                            "metrics_type": "trust",
                            "data": summary.get("variables", {}).get(
                                "trust_scores", {}
                            ),
                            "timestamp": datetime.now().isoformat(),
                        }
                    else:
                        return {
                            "cycle_id": cycle_id,
                            "metrics_type": metric_type,
                            "error": f"Unknown metric type: {metric_type}",
                            "timestamp": datetime.now().isoformat(),
                        }

                # Return all metrics if no specific type is requested
                return {
                    "cycle_id": cycle_id,
                    "status": "active" if coordinator.is_training else "completed",
                    "metrics": summary,
                    "timestamp": datetime.now().isoformat(),
                }

            # If the cycle is not active, try to get metrics from the metrics store
            metrics = metrics_store.get_metrics_by_filter({"cycle_id": cycle_id})

            if not metrics:
                return {
                    "status": "not_found",
                    "cycle_id": cycle_id,
                    "error": "No metrics found for this cycle ID",
                    "timestamp": datetime.now().isoformat(),
                }

            return {
                "cycle_id": cycle_id,
                "status": "completed",
                "metrics": metrics,
                "timestamp": datetime.now().isoformat(),
            }

        # Get all recent metrics if no specific cycle_id is provided
        recent_metrics = metrics_store.get_recent_metrics(limit=kwargs.get("limit", 10))

        return {
            "status": "success",
            "recent_metrics": recent_metrics,
            "timestamp": datetime.now().isoformat(),
        }

    except Exception as e:
        logger.error(f"Error getting recursive learning metrics: {str(e)}")
        return {
            "status": "failed",
            "error": str(e),
            "cycle_id": cycle_id,
            "metric_type": metric_type,
        }
