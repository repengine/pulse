# OpenAI Integration for Pulse Conversational Interface

This document provides instructions for setting up and using the OpenAI integration in the Pulse Conversational Interface.

## Overview

The Pulse Conversational Interface now supports OpenAI's GPT models for generating responses, enabling more sophisticated and accurate natural language understanding and generation. The integration supports both GPT-4 and GPT-3.5 models, with configurable settings for optimizing performance and cost.

## Configuration

### API Key Setup

To use the OpenAI integration, you need an OpenAI API key. You can set up your API key in one of the following ways:

1. **Environment Variable (Recommended)**
   
   Set the `OPENAI_API_KEY` environment variable:
   ```
   export OPENAI_API_KEY=your_api_key_here  # For Linux/macOS
   set OPENAI_API_KEY=your_api_key_here     # For Windows CMD
   $env:OPENAI_API_KEY="your_api_key_here"  # For Windows PowerShell
   ```

2. **Settings Dialog**
   
   In the Pulse Conversational Interface GUI, click the ⚙️ Settings button to open the settings dialog. Enter your API key in the API Key field.

### Model Selection

The OpenAI integration supports the following models:

- **GPT-4 Turbo** (`gpt-4-turbo`): Most powerful model, best for complex tasks
- **GPT-4o** (`gpt-4o`): Latest optimized GPT-4 model with multimodal capabilities
- **GPT-3.5 Turbo** (`gpt-3.5-turbo`): Fast and cost-effective model for most tasks

You can select the model in the settings dialog or in the code:

```python
from chatmode.conversational_core import ConversationalCore

# Initialize with GPT-4 Turbo
core = ConversationalCore(model_name="gpt-4-turbo", model_type="openai")
```

### Cost Considerations

When using OpenAI's API, be aware of the following approximate costs:

| Model | Input Cost (per 1K tokens) | Output Cost (per 1K tokens) |
|-------|----------------------------|------------------------------|
| GPT-4 Turbo | $0.01 | $0.03 |
| GPT-4o | $0.01 | $0.03 |
| GPT-3.5 Turbo | $0.0005 | $0.0015 |

The system will track token usage and estimated costs in the logs.

## Using the Integration Programmatically

### Basic Usage

```python
from chatmode.llm_integration.llm_model import LLMModel

# Initialize with OpenAI
llm = LLMModel(model_name="gpt-3.5-turbo", model_type="openai")

# Generate a response
response = llm.generate_response("What is the role of recursive learning in forecasting?")
print(response)
```

### Advanced Usage

```python
from chatmode.llm_integration.llm_model import LLMModel
from chatmode.conversational_core import ConversationalCore

# Initialize the core with specific model
core = ConversationalCore(model_name="gpt-4-turbo", model_type="openai")

# Process a query that will use the vector store for RAG
response, snippets = core.process_query("How does Pulse handle forecast drift?")
print(response)
```

## Testing the Integration

A test script is provided to verify that the OpenAI integration is working correctly:

```bash
python chatmode/test_openai_integration.py --model gpt-3.5-turbo
```

For testing without making API calls:

```bash
python chatmode/test_openai_integration.py --mock-only
```

## Fallback Mechanism

If the OpenAI API is not available or encounters an error, the system will automatically fall back to a mock implementation that returns placeholder responses. This ensures that the interface remains functional even when API access is limited or unavailable.

## Requirements

The OpenAI integration requires the following dependencies:

- `openai>=1.0.0`: The official OpenAI Python library
- `tiktoken>=0.4.0`: For token counting and cost estimation

These dependencies can be installed using:

```bash
pip install -r chatmode/requirements.txt
```

## Troubleshooting

If you encounter issues with the OpenAI integration:

1. Check that your API key is correctly set and has sufficient credits
2. Verify that you have installed the required dependencies
3. Check the logs for specific error messages
4. Try using the mock model to verify that the rest of the system is working

If problems persist, consider using a different model or checking the OpenAI status page for any service disruptions.