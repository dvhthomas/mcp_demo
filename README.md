# MCP Demo: Agent + LLM + MCP Tools

A demonstration of how an AI agent backed by an LLM can interact with tools provided by an MCP (Model Context Protocol) server.

**What it does:** A LangGraph ReACT agent uses Ollama (llama3.2:3b) to reason about user queries and call MCP tools (weather, events) to answer questions.

## Quick Start

### 1. Install Ollama and get the model

```bash
# Install Ollama
# Mac: brew install ollama
# Or download from https://ollama.ai

# Start Ollama server (keep this running)
ollama serve

# In a separate terminal, pull the model:
ollama pull llama3.2:3b
```

### 2. Install dependencies

```bash
uv sync
```

### 3. Run the MCP server

```bash
# Terminal 2 (Ollama serve is in Terminal 1)
uv run python main.py
```

Server starts on http://localhost:8000

### 4. Run the agent

```bash
# Terminal 3
uv run python client/agent.py
```

### Example Usage

```bash
# Interactive mode
uv run python client/agent.py

You: What's the weather in Tokyo?
Agent: The current weather in Tokyo is 18°C...

# Single query
uv run python client/agent.py --query "What events are happening in Paris today?"

# Verbose mode (for learning) - streams ReACT steps in real-time
uv run python client/agent.py --verbose --query "What's the weather in Berlin?"
```

## Project Structure

```
mcp_demo/
├── server/              # MCP server (FastMCP + tools)
│   ├── server.py       # FastMCP server with SSE
│   ├── mcp_adapters.py # Protocol adapters
│   └── tools/          # Weather & Events tools
├── client/              # LangGraph agent
│   └── agent.py        # LangGraph ReACT agent with MCP
├── tests/              # Pytest tests
├── main.py             # Server entry point
└── example.py          # Direct tool usage
```

## Documentation

- **[AGENT_README.md](AGENT_README.md)** - Understanding AI agents, ReACT pattern theory, reasoning examples
- **[ARCHITECTURE.md](ARCHITECTURE.md)** - Server architecture, adapter pattern, how to add tools
- **[TESTING.md](TESTING.md)** - Testing guide

## Requirements

### Core Requirements
- Python 3.13+
- [uv](https://github.com/astral-sh/uv) package manager

### For Running the Agent (Optional for Testing)
- [Ollama](https://ollama.ai) with llama3.2:3b model

**Note**: You can run the MCP server and integration tests without Ollama. Ollama is only required when using the LangGraph agent (`client/agent.py`).

## Tools Provided

1. **get_weather** - Current weather for any city (Open-Meteo API, no key required)
2. **search_events** - Events happening today in any city (DuckDuckGo search)

## Testing

```bash
# Run all tests
uv run pytest

# Run unit tests only
uv run pytest tests/server/

# Run with verbose output
uv run pytest -v
```

## Troubleshooting

### Error: `[Errno 48] Address already in use`

This error occurs when port 8000 is already occupied by another process.

**On Mac, find and kill the process:**

```bash
# Option 1: Find what's using port 8000
lsof -i :8000

# Look for the PID in the output, then kill it:
kill -9 <PID>

# Option 2: One-liner to find and kill the process
lsof -ti :8000 | xargs kill -9

# Verify the port is free
lsof -i :8000
# (should return nothing)
```

**Common causes:**
- Previous server instance didn't shut down properly
- Another application is using port 8000
- Tests left a server running in the background

## Key Technologies

- **MCP SDK** - Official Model Context Protocol implementation (FastMCP server, SSE client)
- **LangGraph** - Modern agent framework (pre-built ReACT agent)
- **LangChain MCP Adapters** - Official integration between LangChain and MCP
- **Ollama** - Local LLM inference (llama3.2:3b)
- **FastAPI/Starlette** - HTTP server framework
- **pytest** - Testing framework
