"""
MCP Tools Server - A Model Context Protocol server with weather and events tools.

This module implements an MCP server using the official MCP SDK's FastMCP class.
It provides two tools:
1. Weather Tool - Get current weather for any city
2. Events Search Tool - Search for events happening today in a city

The server uses FastMCP with HTTP SSE transport for MCP communication while
maintaining backward compatibility with the existing HTTP REST API.
"""

import json
import logging

from mcp.server.fastmcp import FastMCP
from starlette.requests import Request
from starlette.responses import JSONResponse

from server.mcp_adapters import EventSearchToolMCPAdapter, WeatherToolMCPAdapter
from server.tools.events_tool import EventSearchTool
from server.tools.weather_tool import WeatherTool

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# LAYER 1: Create business logic tools (protocol-agnostic)
# These tools don't know about MCP - they just do weather/events logic
# This means they can be reused with other protocols (REST, GraphQL, gRPC)
weather_tool = WeatherTool()
events_tool = EventSearchTool()

# LAYER 2: Wrap tools with MCP adapters (Adapter Pattern)
# Adapters translate between tool APIs and MCP protocol expectations
# They handle: tool definitions, argument mapping, error formatting
weather_adapter = WeatherToolMCPAdapter(weather_tool)
events_adapter = EventSearchToolMCPAdapter(events_tool)

# LAYER 3: Create FastMCP server using official SDK
# FastMCP handles all MCP protocol details (SSE transport, message format, etc.)
mcp_server = FastMCP("mcp-tools-server")

# Register weather tool with FastMCP
# Get the MCP tool definition (name, description, schema) from the adapter
weather_def = weather_adapter.get_tool_definition()


@mcp_server.tool(name=weather_def["name"], description=weather_def["description"])
async def get_weather(city: str) -> str:
    """
    Get current weather information for any city.

    This function is what the LLM "calls" when it wants weather data.
    FastMCP handles all the protocol details - we just execute the tool.

    Args:
        city: Name of the city to get weather for

    Returns:
        JSON string with weather information
    """
    result = await weather_adapter.execute({"city": city})
    return json.dumps(result, indent=2)


# Register events tool with FastMCP
events_def = events_adapter.get_tool_definition()


@mcp_server.tool(name=events_def["name"], description=events_def["description"])
async def search_events(city: str, max_results: int = 5) -> str:
    """
    Search for events happening today in a city.

    Args:
        city: Name of the city to search events for
        max_results: Maximum number of results to return (default: 5)

    Returns:
        JSON string with event search results
    """
    result = await events_adapter.execute({"city": city, "max_results": max_results})
    return json.dumps(result, indent=2)


# Add custom REST API routes to FastMCP for backward compatibility
# This allows existing HTTP REST clients to continue working
# while official MCP SDK clients use the SSE endpoint at /sse

# Registry for backward compatibility with REST API
# Newer clients use /sse endpoint; older REST clients use /mcp/tools/call
tools_registry = {"get_weather": weather_adapter, "search_events": events_adapter}


@mcp_server.custom_route("/", ["GET"])
async def root(request: Request):
    """
    Root endpoint providing basic server information.

    Args:
        request: Starlette request object

    Returns:
        Dict[str, Any]: Server information and available endpoints
    """
    return JSONResponse(
        content={
            "name": "MCP Tools Server",
            "version": "0.1.0",
            "protocol": "MCP",
            "description": (
                "A Model Context Protocol server with weather and events tools"
            ),
            "endpoints": {
                "info": "/mcp/info",
                "tools": "/mcp/tools/list",
                "call": "/mcp/tools/call",
                "mcp_sse": "/sse",
                "health": "/health",
            },
        }
    )


@mcp_server.custom_route("/mcp/info", ["GET"])
async def mcp_info(request: Request):
    """
    MCP server information endpoint (REST API compatibility).

    Args:
        request: Starlette request object

    Returns:
        Dict[str, Any]: Server metadata and capabilities
    """
    return JSONResponse(
        content={
            "protocolVersion": "2024-11-05",
            "serverInfo": {"name": "mcp-tools-server", "version": "0.1.0"},
            "capabilities": {"tools": True},
        }
    )


@mcp_server.custom_route("/mcp/tools/list", ["GET"])
async def list_tools_rest(request: Request):
    """
    List all available tools (REST API compatibility endpoint).

    This endpoint maintains compatibility with existing HTTP REST clients.

    Args:
        request: Starlette request object

    Returns:
        Dict[str, List]: Dictionary containing list of tool definitions
    """
    tools = [adapter.get_tool_definition() for adapter in tools_registry.values()]
    return JSONResponse(content={"tools": tools})


@mcp_server.custom_route("/mcp/tools/call", ["POST"])
async def call_tool_rest(request: Request):
    """
    Execute a tool with provided parameters (REST API compatibility endpoint).

    This endpoint maintains compatibility with existing HTTP REST clients.

    Args:
        request (Request): Starlette request object containing tool call data

    Returns:
        JSONResponse: Tool execution result in MCP format

    Raises:
        HTTPException: If tool is not found or execution fails
    """
    try:
        # Parse request body
        body = await request.json()
        tool_name = body.get("name")
        arguments = body.get("arguments", {})

        logger.info(f"Tool call: {tool_name} with arguments: {arguments}")

        # Validate tool exists
        if tool_name not in tools_registry:
            return JSONResponse(
                status_code=404, content={"error": f"Tool '{tool_name}' not found"}
            )

        # Execute via adapter
        adapter = tools_registry[tool_name]
        result = await adapter.execute(arguments)

        # Return result in MCP format
        return JSONResponse(
            content={"content": [{"type": "text", "text": str(result)}]}
        )

    except ValueError as e:
        logger.error(f"Validation error: {str(e)}")
        return JSONResponse(status_code=400, content={"error": str(e)})

    except Exception as e:
        logger.error(f"Error executing tool: {str(e)}")
        return JSONResponse(
            status_code=500, content={"error": f"Error executing tool: {str(e)}"}
        )


@mcp_server.custom_route("/health", ["GET"])
async def health_check(request: Request):
    """
    Health check endpoint.

    Args:
        request: Starlette request object

    Returns:
        Dict[str, str]: Server health status
    """
    return JSONResponse(content={"status": "healthy"})


# Get the ASGI app from FastMCP (includes SSE endpoint at /sse and custom routes)
app = mcp_server.sse_app()


if __name__ == "__main__":
    import uvicorn

    # Run the server
    uvicorn.run(
        "src.server:app", host="0.0.0.0", port=8000, reload=True, log_level="info"
    )
