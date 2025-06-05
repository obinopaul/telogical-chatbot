# Dynamic Agents Integration

This document explains how the Dynamic Agents from a previous project were integrated into the Telogical Chatbot framework.

## Architecture Overview

The integration follows the modular architecture of the Telogical Chatbot framework while preserving the functionality of the Dynamic Agents. Key changes include:

1. **LLM Management**: Moved LLM initialization from agent.py to the framework's core/llm.py
2. **Memory Management**: Moved Postgres connection handling to the framework's memory/postgres.py
3. **Agent Registration**: Updated the agents.py to properly register the dynamic agents with the framework
4. **Reasoning Visualization**: Added trace information to agent output enabling visualization of reasoning steps and tool calls

## Key Components

### LLM Integration

The Dynamic Agents originally used two LLMs:
- A primary LLM (Azure OpenAI) for main agent interactions
- A secondary LLM (Standard OpenAI) for specific tasks like query contextualization

These are now accessible through framework functions:
- `get_telogical_primary_llm()`
- `get_telogical_secondary_llm()`

### Database Integration

The original agent had custom Postgres initialization code. This has been moved to the framework's postgres.py module with a new function:
- `get_telogical_postgres_saver()`

### Agent Registration

The Dynamic Agents are registered in the framework's agent registry in src/agents/agents.py. The integration changed:
- Updated the Agent class to handle async factory functions
- Modified get_agent to be async and handle agent initialization

### Reasoning Visualization

To enable transparency into the agent's decision-making process, we've added:
- Trace information in the AIMessage's custom_data field containing:
  - Contextual analysis of user queries
  - Database/schema usage information
  - Tool execution details with inputs and outputs
- Integration with TelogicalClient for visualization:
  - Show reasoning steps during streaming responses
  - Extract reasoning information for non-streaming responses

## Environment Variables

The Dynamic Agents require the following environment variables:

```
# Primary LLM (Azure OpenAI)
TELOGICAL_MODEL_ENDPOINT_GPT=<azure-endpoint>
TELOGICAL_API_KEY_GPT=<azure-api-key>
TELOGICAL_MODEL_DEPLOYMENT_GPT=<azure-deployment-name>
TELOGICAL_MODEL_API_VERSION_GPT=<azure-api-version>

# Secondary LLM (OpenAI)
OPENAI_API_KEY=<openai-api-key>
TELOGICAL_SECONDARY_MODEL=gpt-4.1-nano-2025-04-14

# Database
DB_HOST=<postgres-host>
DB_PORT=<postgres-port>
DB_NAME=<postgres-db-name>
DB_USER=<postgres-user>
DB_PASSWORD=<postgres-password>
```

## Usage

The Dynamic Agents can be used like any other agent in the framework:

```python
from src.client.telogical_client import TelogicalClient
from src.schema.schema import ChatMessage

# Create client
client = TelogicalClient(base_url="http://localhost:8000")

# Create message
message = ChatMessage(
    type="human",
    content="What are AT&T's internet options in Dallas?"
)

# Get response with reasoning visualization
async for item in client.chat_stream(
    messages=[message],
    agent_type="telogical-assistant",
    show_reasoning=True
):
    if isinstance(item, dict):
        # Handle reasoning or tool call info
        if item["type"] == "reasoning":
            print(f"\nREASONING: {item['content']}")
        elif item["type"] == "tool":
            print(f"\nTOOL ({item['name']}): {item['input']} -> {item['output']}")
    elif isinstance(item, str):
        # Handle token
        print(item, end="", flush=True)
    elif isinstance(item, ChatMessage):
        # Handle complete message
        print(item.content)
```

## Customization

To customize the Dynamic Agents:
1. Modify prompts in `src/agents/dynamic_agents/prompts.py`
2. Add or modify tools in `src/agents/dynamic_agents/tools.py`
3. Adjust agent logic in `src/agents/dynamic_agents/agent.py`

## Testing

The agents can be tested using the standard framework test approach:

```
python -m pytest tests/
```

## Troubleshooting

Common issues:
1. **Missing Environment Variables**: Ensure all required variables are set
2. **Database Connection**: Check that the Postgres connection is properly configured
3. **LLM API Errors**: Verify the LLM API keys and endpoints are correct

If using multiple agents that require different configurations, you may need to extend the core/llm.py and memory/postgres.py modules to support different configurations.