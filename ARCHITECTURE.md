# Architecture

This document describes the architecture of the MCP Demo server, the adapter pattern used, and how to extend the system with new tools.

## Overview

The MCP Demo follows a clean architecture pattern that separates business logic from protocol concerns. This makes the tools reusable and testable while providing a standards-compliant MCP server interface.

## High-Level Architecture

```
┌──────────────┐
│     User     │
└──────┬───────┘
       │
       ▼
┌──────────────────────┐
│  LangGraph ReACT     │  ← client/agent.py
│  Agent (Ollama)      │
└──────┬───────────────┘
       │ langchain-mcp-adapters
       ▼
┌──────────────────────┐
│  MultiServerMCP      │  ← langchain-mcp-adapters (Official)
│  Client              │
└──────┬───────────────┘
       │ SSE/HTTP
       ▼
┌──────────────────────┐
│  MCP Server          │  ← server/server.py (FastMCP)
│  (FastMCP + SSE)    │
└──────┬───────────────┘
       │
       ▼
┌──────────────────────┐
│  MCP Adapters        │  ← server/mcp_adapters.py
│  (Protocol Layer)   │
└──────┬───────────────┘
       │
       ▼
┌──────────────────────┐
│  Business Tools      │  ← server/tools/
│  (Weather, Events)  │     (Protocol-agnostic)
└──────────────────────┘
```

## Adapter Pattern

The project uses the **Adapter/Facade Pattern** to separate concerns:

### 1. Business Logic Layer (`server/tools/`)

**Protocol-agnostic tools** that contain pure business logic:

```python
# server/tools/weather_tool.py
class WeatherTool:
    async def get_weather(self, city: str) -> dict:
        # Pure business logic - no MCP knowledge
        # Returns plain Python dict
        pass
```

**Benefits:**
- Reusable in any context (CLI, API, different protocols)
- Easy to test without MCP concerns
- No protocol dependencies
- Can be used directly (see `example.py`)

### 2. Adapter Layer (`server/mcp_adapters.py`)

**Protocol adapters** that wrap business logic for MCP:

```python
# server/mcp_adapters.py
class WeatherToolMCPAdapter:
    def __init__(self, tool: WeatherTool):
        self.tool = tool

    def get_tool_definition(self) -> dict:
        # Returns MCP-compliant tool definition
        # with JSON Schema for inputs
        pass

    async def execute(self, arguments: dict) -> dict:
        # Validates MCP arguments
        # Calls business logic tool
        # Returns MCP-formatted response
        pass
```

**Responsibilities:**
- Provide MCP tool definitions (name, description, JSON Schema)
- Validate and map MCP arguments to tool parameters
- Handle MCP-specific error formatting
- Return MCP-compliant responses

### 3. Server Layer (`server/server.py`)

**FastMCP server** using the official MCP SDK:

```python
# server/server.py
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("mcp-tools-server")

# Register tools with FastMCP
@mcp.tool(name="get_weather", description="...")
async def get_weather(city: str) -> str:
    result = await weather_adapter.execute({"city": city})
    return json.dumps(result)

# FastMCP handles:
# - SSE endpoint (/sse) for official MCP SDK clients
# - Protocol negotiation
# - Request/response formatting
# - Session management
```

**Features:**
- SSE endpoint at `/sse` for official MCP SDK clients
- Custom REST API routes for backward compatibility
- Built-in session management
- Protocol-compliant request/response handling

## Server Implementation

### FastMCP Integration

The server uses the official MCP SDK's `FastMCP` class:

```python
from mcp.server.fastmcp import FastMCP
from starlette.responses import JSONResponse

# Create FastMCP server
mcp = FastMCP("mcp-tools-server")

# Register tools using @mcp.tool decorator
weather_definition = weather_adapter.get_tool_definition()

@mcp.tool(name=weather_definition["name"], description=weather_definition["description"])
async def get_weather(city: str) -> str:
    result = await weather_adapter.execute({"city": city})
    return json.dumps(result, indent=2)

# Add REST API routes for backward compatibility
@mcp.custom_route("/health", ["GET"])
async def health_check(request: Request):
    return JSONResponse(content={"status": "healthy"})

# Get the ASGI app (includes SSE endpoint + custom routes)
app = mcp.sse_app()
```

**Endpoints:**
- `/sse` - SSE endpoint for official MCP SDK clients
- `/health` - Health check
- `/mcp/info` - Server info (REST compatibility)
- `/mcp/tools/list` - List tools (REST compatibility)
- `/mcp/tools/call` - Call tools (REST compatibility)

### Why Two Protocols?

The server provides **both SSE and REST** endpoints:

1. **SSE (`/sse`)** - Official MCP protocol
   - Used by official MCP SDK clients
   - Full protocol compliance
   - Session management
   - Real-time communication

2. **REST API (`/mcp/tools/*`)** - Backward compatibility
   - Simple HTTP requests
   - Easy to test with curl
   - Works with existing HTTP clients
   - No session management needed

## Client Implementation

### MCP Client

The client uses the official MCP SDK:

```python
from mcp import ClientSession
from mcp.client.sse import sse_client

# Connect via SSE
async with sse_client(url) as (read, write):
    session = ClientSession(read, write)
    await session.initialize()

    # List tools
    tools = await session.list_tools()

    # Call tool
    result = await session.call_tool("get_weather", {"city": "Paris"})
```

### LangGraph Integration

The project uses the **official `langchain-mcp-adapters` package** for seamless MCP integration:

1. **MultiServerMCPClient**: Official adapter that connects to MCP servers
2. **Automatic Tool Conversion**: Converts MCP tools to LangChain StructuredTool format
3. **Native LangGraph Support**: Works out-of-the-box with LangGraph's `create_react_agent`

```python
# Connect to MCP server and get tools (official package)
from langchain_mcp_adapters.client import MultiServerMCPClient

client = MultiServerMCPClient({
    "mcp-tools": {
        "url": "http://localhost:8000/sse",
        "transport": "sse",
    }
})

tools = await client.get_tools()  # Returns LangChain StructuredTools

# Create LangGraph ReACT agent
from langchain.agents import create_agent
agent = create_agent(llm, tools)
```

## Adding a New Tool

Follow these steps to add a new tool while maintaining the adapter pattern:

### Step 1: Create Business Logic Tool

Create a new file in `server/tools/`:

```python
# server/tools/my_new_tool.py
from typing import Any

class MyNewTool:
    """
    Pure business logic - no MCP dependencies.

    This tool can be used directly or wrapped by any protocol adapter.
    """

    async def do_something(self, param: str) -> dict[str, Any]:
        """
        Implement your business logic here.

        Args:
            param: Input parameter

        Returns:
            dict: Result data
        """
        # Your implementation
        result = f"Processed: {param}"

        return {
            "result": result,
            "status": "success"
        }
```

### Step 2: Create MCP Adapter

Add adapter to `server/mcp_adapters.py`:

```python
# server/mcp_adapters.py
from server.tools.my_new_tool import MyNewTool

class MyNewToolMCPAdapter:
    """MCP adapter for MyNewTool."""

    def __init__(self, tool: MyNewTool):
        self.tool = tool

    def get_tool_definition(self) -> dict[str, Any]:
        """
        Get the MCP tool definition.

        Returns MCP-compliant tool definition with JSON Schema.
        """
        return {
            "name": "do_something",
            "description": "Does something useful with the input",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "param": {
                        "type": "string",
                        "description": "Input parameter to process"
                    }
                },
                "required": ["param"]
            }
        }

    async def execute(self, arguments: dict[str, Any]) -> dict[str, Any]:
        """
        Execute the tool with MCP-provided arguments.

        Args:
            arguments: Arguments from MCP call

        Returns:
            Result from the tool

        Raises:
            ValueError: If required arguments are missing
        """
        param = arguments.get("param")
        if not param:
            raise ValueError("Missing required argument: param")

        return await self.tool.do_something(param)
```

### Step 3: Register in Server

Update `server/server.py`:

```python
# server/server.py
from server.tools.my_new_tool import MyNewTool
from server.mcp_adapters import MyNewToolMCPAdapter

# Initialize business logic tool
my_tool = MyNewTool()

# Wrap with adapter
my_adapter = MyNewToolMCPAdapter(my_tool)

# Register with FastMCP
tool_definition = my_adapter.get_tool_definition()

@mcp.tool(name=tool_definition["name"], description=tool_definition["description"])
async def do_something(param: str) -> str:
    result = await my_adapter.execute({"param": param})
    return json.dumps(result, indent=2)

# Add to REST API registry for backward compatibility
tools_registry["do_something"] = my_adapter
```

### Step 4: Test the Tool

Create tests in `tests/server/`:

```python
# tests/server/test_my_new_tool.py
import pytest
from server.mcp_adapters import MyNewToolMCPAdapter
from server.tools.my_new_tool import MyNewTool

@pytest.fixture
def my_adapter():
    tool = MyNewTool()
    return MyNewToolMCPAdapter(tool)

class TestMyNewToolMCPAdapter:
    def test_get_tool_definition(self, my_adapter):
        definition = my_adapter.get_tool_definition()
        assert definition["name"] == "do_something"
        assert "inputSchema" in definition

    @pytest.mark.asyncio
    async def test_execute_success(self, my_adapter):
        result = await my_adapter.execute({"param": "test"})
        assert "result" in result
        assert result["status"] == "success"
```

### Step 5: Test Directly

Test business logic without MCP:

```python
# test_direct.py
import asyncio
from server.tools.my_new_tool import MyNewTool

async def main():
    tool = MyNewTool()
    result = await tool.do_something("hello")
    print(result)

asyncio.run(main())
```

## Design Principles

### Separation of Concerns

**Business Logic** (tools)
- No protocol knowledge
- Pure Python functions/classes
- Reusable in any context
- Easy to test

**Protocol Adapter** (adapters)
- MCP-specific interface
- Validation and mapping
- Error handling
- Protocol compliance

**Server** (FastMCP)
- HTTP/SSE transport
- Request routing
- Session management
- Protocol negotiation

### Benefits

1. **Testability**: Test business logic without protocol concerns
2. **Reusability**: Use tools in CLI, API, or other protocols
3. **Maintainability**: Changes to MCP don't affect business logic
4. **Extensibility**: Easy to add new tools or protocols
5. **Clarity**: Each layer has a single responsibility

## Technology Stack

### Server Side
- **FastMCP** - Official MCP SDK server implementation
- **Starlette** - ASGI framework (used by FastMCP)
- **Uvicorn** - ASGI server
- **Open-Meteo API** - Weather data (free, no key)
- **DuckDuckGo Search** - Event search (free, no key)

### Client Side
- **LangGraph** - Modern agent framework (create_agent ReACT implementation)
- **langchain-mcp-adapters** - Official MCP to LangChain integration
- **Ollama** - Local LLM inference
- **httpx** - Async HTTP client (via MCP adapters)

### Development
- **pytest** - Testing framework
- **pytest-asyncio** - Async test support
- **ruff** - Linting and formatting
- **uv** - Package management

## API Reference

### MCP Server Endpoints

#### SSE Endpoint (Official MCP Protocol)
```
GET /sse
```
Server-Sent Events endpoint for official MCP SDK clients.

#### REST API Endpoints (Backward Compatibility)

**Health Check**
```
GET /health
→ {"status": "healthy"}
```

**List Tools**
```
GET /mcp/tools/list
→ {"tools": [{"name": "...", "description": "...", "inputSchema": {...}}]}
```

**Call Tool**
```
POST /mcp/tools/call
Content-Type: application/json

{
  "name": "get_weather",
  "arguments": {"city": "Paris"}
}

→ {"content": [{"type": "text", "text": "..."}]}
```

## Performance Considerations

### Async/Await Throughout
All I/O operations use async/await for optimal performance:
- HTTP requests to external APIs
- Tool execution
- MCP client/server communication

### Connection Pooling
httpx AsyncClient provides connection pooling for external API calls.

### Caching Opportunities
Consider adding caching for:
- Weather data (e.g., 15-minute TTL)
- Geocoding results (persistent cache)
- Event search results (short TTL)

## Error Handling

### Business Logic Layer
- Raises domain-specific exceptions
- Returns error information in result dict
- Logs errors for debugging

### Adapter Layer
- Validates MCP arguments
- Converts exceptions to MCP error format
- Provides user-friendly error messages

### Server Layer
- HTTP status codes for REST API
- MCP error protocol for SSE
- Structured error responses

## Security Considerations

### Input Validation
- All inputs validated via JSON Schema (MCP)
- Automatic validation via langchain-mcp-adapters
- Adapter layer validates business logic inputs

### API Keys
Currently no API keys required (free APIs). If adding paid APIs:
- Store keys in environment variables
- Never commit keys to git
- Use secrets management in production

### Rate Limiting
Consider adding rate limiting for:
- External API calls
- Tool execution per user
- MCP requests

## Future Enhancements

- [ ] Add more tools (e.g., news, stock prices, translations)
- [ ] Implement caching layer
- [ ] Add authentication/authorization
- [ ] WebSocket support for real-time updates
- [ ] Metrics and monitoring
- [ ] Docker containerization
- [ ] Kubernetes deployment
- [ ] Multi-language support
- [ ] Tool composition (chain multiple tools)
