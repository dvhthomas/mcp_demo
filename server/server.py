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

from server.config import DEFAULT_MAX_EVENT_RESULTS
from server.mcp_adapters import EventSearchToolMCPAdapter, WeatherToolMCPAdapter
from server.tools.events_tool import EventSearchTool
from server.tools.weather_tool import WeatherTool

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create business logic tools (protocol-agnostic)
weather_tool = WeatherTool()
events_tool = EventSearchTool()

# Wrap tools with MCP adapters
weather_adapter = WeatherToolMCPAdapter(weather_tool)
events_adapter = EventSearchToolMCPAdapter(events_tool)

# Create FastMCP server
mcp_server = FastMCP("mcp-tools-server")

# Register weather tool with FastMCP
weather_definition = weather_adapter.get_tool_definition()


@mcp_server.tool(
    name=weather_definition["name"], description=weather_definition["description"]
)
async def get_weather(city: str) -> str:
    """Get current weather information for a city."""
    result = await weather_adapter.execute({"city": city})
    return json.dumps(result, indent=2)


# Register events tool with FastMCP
events_definition = events_adapter.get_tool_definition()


@mcp_server.tool(
    name=events_definition["name"], description=events_definition["description"]
)
async def search_events(city: str, max_results: int = DEFAULT_MAX_EVENT_RESULTS) -> str:
    """Search for events happening today in a city."""
    result = await events_adapter.execute({"city": city, "max_results": max_results})
    return json.dumps(result, indent=2)


# REST API backward compatibility routes
# SSE endpoint at /sse for MCP SDK clients; REST endpoints for simple HTTP clients
tools_registry = {"get_weather": weather_adapter, "search_events": events_adapter}


@mcp_server.custom_route("/", ["GET"])
async def root(request: Request):
    """Root endpoint with server information and available endpoints.

    NOTE: This is a custom convenience endpoint for humans and simple HTTP clients.

    MCP clients (following the spec) will:
    1. Connect to /sse (the canonical MCP SSE endpoint)
    2. Use JSON-RPC to call tools/list over the MCP protocol

    The REST endpoints below (/mcp/tools/list, /mcp/tools/call) are also custom
    convenience wrappers, NOT part of the MCP specification. They exist for backward
    compatibility with simple HTTP clients that can't use the MCP protocol.
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
    """MCP server information endpoint."""
    return JSONResponse(
        content={
            "protocolVersion": "2024-11-05",
            "serverInfo": {"name": "mcp-tools-server", "version": "0.1.0"},
            "capabilities": {"tools": True},
        }
    )


@mcp_server.custom_route("/mcp/tools/list", ["GET"])
async def list_tools_rest(request: Request):
    """List all available tools."""
    tools = [adapter.get_tool_definition() for adapter in tools_registry.values()]
    return JSONResponse(content={"tools": tools})


@mcp_server.custom_route("/mcp/tools/call", ["POST"])
async def call_tool_rest(request: Request):
    """Execute a tool with provided parameters."""
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
    """Health check endpoint."""
    return JSONResponse(content={"status": "healthy"})


# Get the ASGI app from FastMCP (includes SSE endpoint at /sse and custom routes)
app = mcp_server.sse_app()


if __name__ == "__main__":
    import uvicorn

    # Run the server
    uvicorn.run(
        "src.server:app", host="0.0.0.0", port=8000, reload=True, log_level="info"
    )
