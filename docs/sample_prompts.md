# Sample Prompts for Pulse Conversational Interface

This document contains sample prompts and commands to test various features of the Pulse Conversational Interface.

## Basic Queries

- "What is Pulse?"
- "How does the forecasting system work?"
- "Explain the core components of Pulse."
- "Tell me about the symbolic system in Pulse."
- "What is recursive learning?"

## Forecast Commands

- "Get forecast for SPX"
- "Generate a forecast for NVDA"
- "Create a forecast for MSFT with high confidence"
- "Show me a forecast for BTC"

## Data Retrieval

- "Get data for AAPL"
- "Retrieve historical prices for TSLA from 2023-01-01 to 2023-12-31"
- "Show me the latest data for SPX"
- "Get fundamental data for AMZN"

## Simulation Commands

- "Run a simulation with high volatility"
- "Simulate market crash scenario"
- "Run a simulation with parameters: time_steps=20, cycles=5"
- "Simulate bull market conditions"

## Trust Scoring

- "What is the trust score for the latest SPX forecast?"
- "Get trust score for simulation model"
- "How trustworthy is the recursive learning output?"
- "Show trust scores for all forecasts"

## Memory Queries

- "Query memory for past SPX forecasts"
- "What do you remember about AAPL price trends?"
- "Retrieve past simulations with high accuracy"
- "Search memory for inflation forecasts"

## Symbolic System Queries

- "Query symbolic system about market crash patterns"
- "What does the symbolic system say about tech sector trends?"
- "Ask symbolic system about correlation between SPX and BTC"
- "Symbolic query: causal relationships in energy markets"

## Recursive Learning Controls

- "Start recursive learning with variables=spx_close,us_10y_yield"
- "Get recursive learning status"
- "Stop recursive learning cycle"
- "Configure recursive learning with batch_size_days=30, iterations=5"
- "Get recursive learning metrics for the latest cycle"

## Testing Edge Cases

- "Generate a very long forecast with multiple variables" (tests token handling)
- "Run a complex simulation with 20 variables" (tests performance)
- "Give me technical details about the symbolic reasoning engine" (tests RAG)
- "[Empty query]" (tests error handling)

## Using the GUI Controls

1. Use the command dropdown to select specific command types
2. Try the quick access buttons for common operations
3. Test the settings panel (gear icon) to switch between models
4. Use the tab interface to view different types of structured outputs

## Testing OpenAI Integration (if API key configured)

1. Switch between GPT-3.5 Turbo and GPT-4 Turbo in settings
2. Ask complex questions to test GPT-4's capabilities
3. Try generating both short and very long responses to test token usage