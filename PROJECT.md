# Telogical Chatbot Framework

A modular AI framework for building and deploying intelligent telecom market intelligence chatbots with reasoning visualization capabilities.

## Overview

The Telogical Chatbot is a comprehensive framework for creating, deploying, and interacting with AI agents that can answer telecommunications market intelligence questions. It features a multi-agent architecture, a client-server design, and supports transparent reasoning visualization.

The framework is designed to work with various LLM providers (Azure OpenAI, OpenAI, Anthropic, Google, etc.), can be deployed using Docker, and includes both API and streaming capabilities.

## Key Features

- **Multi-Agent Workflow**: Dynamic agent architecture with specialized capabilities
- **Reasoning Visualization**: Transparent display of agent thinking process and tool usage
- **LLM Flexibility**: Support for multiple LLM providers
- **Database Integration**: PostgreSQL for conversation history and state storage
- **Client Libraries**: Both sync and async client interfaces with streaming support
- **Dockerized Deployment**: Containerized setup for easy deployment
- **Streamlit UI**: Built-in web interface

## Components

### Core Architecture

```
src/
├── agents/              # AI agent implementations
│   ├── dynamic_agents/  # Telogical-specific agents
│   └── ...
├── client/              # Client libraries
├── core/                # Core functionality (LLMs, settings)
├── memory/              # Database integrations
├── schema/              # Data models and schemas
├── service/             # FastAPI service
└── streamlit_app.py     # Web UI implementation
```

### Agent Types

- **Telogical Assistant**: Specialized telecom market intelligence agent
- **Research Assistant**: General-purpose research agent with web search capabilities
- **RAG Assistant**: Retrieval-augmented generation agent for document Q&A

### Client Integration

The `TelogicalClient` provides an enhanced interface for interacting with agents, with special support for reasoning visualization:

```python
from src.client.telogical_client import TelogicalClient
from src.schema.schema import ChatMessage

# Create client
client = TelogicalClient(base_url="http://localhost:8081")

# Create message
message = ChatMessage(
    type="human",
    content="What internet plans are available from AT&T in Dallas, TX?"
)

# Stream response with reasoning visualization
async for item in client.chat_stream(
    messages=[message],
    show_reasoning=True
):
    # Handle different types of responses
    if isinstance(item, dict) and "type" in item:
        if item["type"] == "reasoning":
            print(f"\nREASONING: {item['content']}")
        elif item["type"] == "tool":
            print(f"\nTOOL: {item['name']}, Output: {item['output']}")
    elif isinstance(item, str):
        print(item, end="", flush=True)
```

## Directory Structure

```
Telogical_Chatbot/
├── data/                # CSV data and documentation
├── docker/              # Docker configuration
├── docs/                # Documentation files
├── examples/            # Example usage scripts
├── media/               # Images and diagrams
├── scripts/             # Utility scripts
├── src/                 # Source code
│   ├── agents/          # Agent implementations
│   ├── client/          # Client libraries
│   ├── core/            # Core functionality
│   ├── memory/          # Database integrations
│   ├── schema/          # Data models
│   ├── service/         # API service
│   └── streamlit_app.py # Web UI
└── tests/               # Test suite
```

## Running the Project

### Environment Setup

1. Create a `.env` file with required configuration:
   ```
   # Azure OpenAI Configuration
   AZURE_OPENAI_API_KEY=your_key_here
   AZURE_OPENAI_ENDPOINT=your_endpoint_here
   AZURE_OPENAI_DEPLOYMENT_MAP={"gpt-4o": "your_deployment_name", "gpt-4o-mini": "your_deployment_name"}
   
   # PostgreSQL Configuration
   POSTGRES_USER=postgres_user
   POSTGRES_PASSWORD=postgres_password
   POSTGRES_HOST=localhost
   POSTGRES_PORT=5432
   POSTGRES_DB=chatbot
   DATABASE_TYPE=postgres
   
   # Web server configuration
   HOST=0.0.0.0
   PORT=8081
   ```

2. Install dependencies:
   ```bash
   pip install -e .
   ```

### Starting the Service

Run the service with:

```bash
python src/run_service.py
```

This starts a FastAPI server at `http://localhost:8081`.

### Running the Client

Test the client with:

```bash
python examples/telogical_client_demo.py
```

### Using the Web UI

Launch the Streamlit web interface:

```bash
python src/streamlit_app.py
```

Then navigate to `http://localhost:8501` in your browser.

### Docker Deployment

Deploy with Docker:

```bash
docker-compose up -d
```

## Integration Points

The framework can be integrated with:

1. **Custom UIs**: Use the TelogicalClient to build custom web or mobile interfaces
2. **Other Backend Systems**: Connect through the API service
3. **Custom Agents**: Add new agent types by extending the framework

## Technical Notes

- The framework uses async/await extensively for high performance
- The agent system is built on LangGraph for structured agent workflows
- Trace information is added to responses for reasoning visualization
- The framework supports streaming responses for real-time UI feedback