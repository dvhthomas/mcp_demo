# MCP Tools Server

A Model Context Protocol (MCP) server implementation that provides two powerful tools for getting information about cities:

1. **Weather Tool** - Get current weather conditions for any city worldwide
2. **Events Search Tool** - Search for events happening today in any city

## Features

- **Clean Architecture**: Separation of concerns using the Adapter/Facade pattern
- **Protocol-Agnostic Tools**: Business logic tools have no MCP dependencies
- **Reusable Components**: Tools can be used in non-MCP contexts
- **Well-Documented**: Comprehensive docstrings and comments throughout
- **Fast & Modern**: Built with FastAPI and async/await for high performance
- **No API Keys Required**: Uses free APIs (Open-Meteo for weather, DuckDuckGo for search)
- **MCP Compatible**: Follows the Model Context Protocol specification

## Architecture

This project follows the **Adapter Pattern** to separate business logic from protocol concerns:

```
┌─────────────────┐
│  MCP Server     │  ← FastAPI HTTP endpoints
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  MCP Adapters   │  ← Protocol translation layer (MCP-specific)
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Business Tools │  ← Pure logic (protocol-agnostic)
└─────────────────┘
```

**Benefits:**
- Tools are reusable in any context (CLI, API, other protocols)
- Easy to test business logic without MCP concerns
- Can add other protocols (OpenAPI, GraphQL) without changing tools
- Follows SOLID principles (Single Responsibility, Open/Closed)

## Project Structure

```
mcp_demo/
├── src/
│   ├── __init__.py
│   ├── server.py              # MCP server with FastAPI
│   ├── mcp_adapters.py        # Adapter layer for MCP protocol
│   └── tools/
│       ├── __init__.py
│       ├── weather_tool.py    # Business logic: Weather tool
│       └── events_tool.py     # Business logic: Events search
├── main.py                     # Entry point
├── example.py                  # Direct tool usage example
├── test_adapters.py            # Adapter testing
├── pyproject.toml             # Project dependencies
└── README.md                  # This file
```

## Prerequisites

- Python 3.13 or higher
- [uv](https://github.com/astral-sh/uv) - Fast Python package installer

## Installation

1. **Clone or navigate to the project directory:**

   ```bash
   cd mcp_demo
   ```

2. **Install dependencies using uv:**

   ```bash
   uv sync
   ```

   This will create a virtual environment and install all required packages:
   - fastapi
   - uvicorn
   - mcp
   - httpx
   - beautifulsoup4

## Usage

### Starting the Server

You can start the server in two ways:

**Option 1: Using the main entry point**
```bash
uv run python main.py
```

**Option 2: Direct uvicorn command**
```bash
uv run uvicorn src.server:app --host 0.0.0.0 --port 8000 --reload
```

The server will start on `http://localhost:8000`

### API Endpoints

#### Root Endpoint
```bash
curl http://localhost:8000/
```
Returns server information and available endpoints.

#### MCP Info
```bash
curl http://localhost:8000/mcp/info
```
Returns MCP protocol version and server capabilities.

#### List Available Tools
```bash
curl http://localhost:8000/mcp/tools/list
```
Returns definitions for all available tools.

#### Call a Tool

**Get Weather:**
```bash
curl -X POST http://localhost:8000/mcp/tools/call \
  -H "Content-Type: application/json" \
  -d '{
    "name": "get_weather",
    "arguments": {
      "city": "Paris"
    }
  }'
```

**Search Events:**
```bash
curl -X POST http://localhost:8000/mcp/tools/call \
  -H "Content-Type: application/json" \
  -d '{
    "name": "search_events",
    "arguments": {
      "city": "New York",
      "max_results": 5
    }
  }'
```

#### Health Check
```bash
curl http://localhost:8000/health
```

## Tool Documentation

### WeatherTool

Located in `src/tools/weather_tool.py`

**Purpose:** Fetch current weather conditions for any city worldwide.

**How it works:**
1. Uses Open-Meteo's geocoding API to convert city name to coordinates
2. Fetches current weather data for those coordinates
3. Returns temperature, wind speed, weather code, and location info

**No API key required!**

**Example Response:**
```json
{
  "city": "Paris",
  "country": "France",
  "temperature": 18.5,
  "temperature_unit": "°C",
  "wind_speed": 12.3,
  "wind_speed_unit": "km/h",
  "weather_code": 2,
  "coordinates": {
    "latitude": 48.8566,
    "longitude": 2.3522
  }
}
```

### EventSearchTool

Located in `src/tools/events_tool.py`

**Purpose:** Search for events happening today in a specified city.

**How it works:**
1. Constructs a search query for events in the city
2. Uses DuckDuckGo's HTML search interface
3. Parses results to extract titles, snippets, and URLs
4. Returns up to N results (default: 5)

**No API key required!**

**Example Response:**
```json
{
  "city": "New York",
  "date": "2025-10-25",
  "search_query": "events happening today in New York",
  "results_count": 5,
  "results": [
    {
      "title": "NYC Events Calendar",
      "snippet": "Find events happening today in New York City...",
      "url": "https://example.com/events"
    }
  ]
}
```

## Development

### Understanding the Adapter Pattern

This project uses the **Adapter Pattern** to separate concerns:

**Business Logic Tools** (`src/tools/`)
- Pure business logic, no protocol knowledge
- Reusable in any context (CLI, API, other servers)
- Easy to test independently

**MCP Adapters** (`src/mcp_adapters.py`)
- Wrap business logic tools
- Provide MCP-specific interface (tool definitions, argument handling)
- Handle protocol translation

**MCP Server** (`src/server.py`)
- HTTP endpoints for MCP protocol
- Routes requests to appropriate adapters
- Returns responses in MCP format

### Adding a New Tool

Follow these steps to add a new tool using the adapter pattern:

**Step 1: Create the business logic tool** in `src/tools/my_new_tool.py`:
```python
from typing import Any

class MyNewTool:
    """Pure business logic - no MCP dependencies."""

    async def do_something(self, param: str) -> dict[str, Any]:
        """
        Implement your business logic here.

        Args:
            param: Input parameter

        Returns:
            dict: Result data
        """
        # Your implementation
        return {"result": f"Processed: {param}"}
```

**Step 2: Create an MCP adapter** in `src/mcp_adapters.py`:
```python
class MyNewToolMCPAdapter:
    """MCP adapter for MyNewTool."""

    def __init__(self, tool: MyNewTool):
        self.tool = tool

    def get_tool_definition(self) -> dict[str, Any]:
        """MCP tool definition."""
        return {
            "name": "do_something",
            "description": "Does something useful",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "param": {
                        "type": "string",
                        "description": "Input parameter"
                    }
                },
                "required": ["param"]
            }
        }

    async def execute(self, arguments: dict[str, Any]) -> dict[str, Any]:
        """Execute with MCP arguments."""
        param = arguments.get("param")
        if not param:
            raise ValueError("Missing required argument: param")
        return await self.tool.do_something(param)
```

**Step 3: Register in server** (`src/server.py`):
```python
from src.tools.my_new_tool import MyNewTool
from src.mcp_adapters import MyNewToolMCPAdapter

# Initialize business logic
my_tool = MyNewTool()

# Wrap with adapter
my_adapter = MyNewToolMCPAdapter(my_tool)

# Register
tools_registry["do_something"] = my_adapter
```

**Step 4: Test your tool** directly (without MCP):
```python
# test_my_tool.py
import asyncio
from src.tools.my_new_tool import MyNewTool

async def test():
    tool = MyNewTool()
    result = await tool.do_something("test")
    print(result)

asyncio.run(test())
```

### Running Tests

(Tests to be added in future versions)

```bash
uv run pytest
```

### Code Style & Linting

This project uses **Ruff** for linting and formatting, ensuring consistent code quality and style.

**Check for issues:**
```bash
uv run ruff check .
```

**Auto-fix issues:**
```bash
uv run ruff check --fix .
```

**Format code:**
```bash
uv run ruff format .
```

**Check formatting:**
```bash
uv run ruff format --check .
```

The project is configured to follow:
- PEP 8 style guidelines
- Python 3.13+ best practices
- Comprehensive docstrings for all classes and methods
- Import sorting with isort
- Modern type annotations (using built-in `dict`, `list` instead of `typing.Dict`, `typing.List`)

## Technologies Used

- **FastAPI**: Modern, fast web framework for building APIs
- **uvicorn**: ASGI server for running FastAPI
- **httpx**: Async HTTP client for API requests
- **BeautifulSoup4**: HTML parsing for web scraping
- **MCP SDK**: Model Context Protocol implementation
- **uv**: Fast Python package and project manager
- **Ruff**: Lightning-fast Python linter and formatter

## MCP Protocol

This server implements the Model Context Protocol (MCP), which allows AI models to interact with external tools in a standardized way. The protocol defines:

- Tool discovery (`/mcp/tools/list`)
- Tool execution (`/mcp/tools/call`)
- Standardized request/response formats
- Error handling conventions

## License

This project is provided as-is for demonstration and educational purposes.

## Contributing

Contributions are welcome! Please ensure:
- Code is well-documented with docstrings
- Each tool is in its own class
- Follow existing code style
- Update this README with any changes

## Troubleshooting

**Server won't start:**
- Ensure port 8000 is not in use
- Check Python version: `python --version` (should be 3.13+)
- Reinstall dependencies: `uv sync`

**Weather tool returns "City not found":**
- Check spelling of city name
- Try adding country name: "Springfield, USA"

**Events search returns no results:**
- DuckDuckGo might be temporarily unavailable
- Try a different city name
- Check internet connection

## Future Enhancements

- Add caching for weather data
- Support for multiple languages
- More search filters for events
- Rate limiting
- Authentication
- WebSocket support for real-time updates
- Comprehensive test suite

## Contact

For issues, questions, or suggestions, please open an issue in the project repository.
