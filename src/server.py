"""
MCP Tools Server - A Model Context Protocol server with weather and events tools.

This module implements an MCP server using FastAPI that provides two tools:
1. Weather Tool - Get current weather for any city
2. Events Search Tool - Search for events happening today in a city

The server follows the MCP specification and can be used by any MCP client.
"""

import logging

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse

from src.mcp_adapters import EventSearchToolMCPAdapter, WeatherToolMCPAdapter
from src.tools.events_tool import EventSearchTool
from src.tools.weather_tool import WeatherTool

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="MCP Tools Server",
    description="An MCP server providing weather and events search tools",
    version="0.1.0",
)

# Initialize business logic tools (protocol-agnostic)
weather_tool = WeatherTool()
events_tool = EventSearchTool()

# Wrap tools with MCP adapters (following Adapter/Facade pattern)
weather_adapter = WeatherToolMCPAdapter(weather_tool)
events_adapter = EventSearchToolMCPAdapter(events_tool)

# Store adapters in a registry for easy lookup
tools_registry = {"get_weather": weather_adapter, "search_events": events_adapter}


@app.get("/")
async def root():
    """
    Root endpoint providing basic server information.

    Returns:
        Dict[str, Any]: Server information and available endpoints
    """
    return {
        "name": "MCP Tools Server",
        "version": "0.1.0",
        "protocol": "MCP",
        "description": "A Model Context Protocol server with weather and events tools",
        "endpoints": {
            "info": "/mcp/info",
            "tools": "/mcp/tools/list",
            "call": "/mcp/tools/call",
        },
    }


@app.get("/mcp/info")
async def mcp_info():
    """
    MCP server information endpoint.

    Returns:
        Dict[str, Any]: Server metadata and capabilities
    """
    return {
        "protocolVersion": "2024-11-05",
        "serverInfo": {"name": "mcp-tools-server", "version": "0.1.0"},
        "capabilities": {"tools": True},
    }


@app.get("/mcp/tools/list")
async def list_tools():
    """
    List all available tools.

    This endpoint returns the MCP tool definitions for all registered tools,
    allowing clients to discover available functionality.

    Returns:
        Dict[str, List]: Dictionary containing list of tool definitions
    """
    tools = [adapter.get_tool_definition() for adapter in tools_registry.values()]

    return {"tools": tools}


@app.post("/mcp/tools/call")
async def call_tool(request: Request):
    """
    Execute a tool with provided parameters.

    This endpoint handles tool execution requests following the MCP protocol.
    It routes the request to the appropriate tool and returns the result.

    Args:
        request (Request): FastAPI request object containing tool call data

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
            raise HTTPException(status_code=404, detail=f"Tool '{tool_name}' not found")

        # Get the adapter and execute the tool
        # The adapter handles argument validation and tool invocation
        adapter = tools_registry[tool_name]
        result = await adapter.execute(arguments)

        # Return result in MCP format
        return JSONResponse(
            content={"content": [{"type": "text", "text": str(result)}]}
        )

    except ValueError as e:
        # Handle validation errors
        logger.error(f"Validation error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e)) from e

    except Exception as e:
        # Handle unexpected errors
        logger.error(f"Error executing tool: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Error executing tool: {str(e)}"
        ) from e


@app.get("/health")
async def health_check():
    """
    Health check endpoint.

    Returns:
        Dict[str, str]: Server health status
    """
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn

    # Run the server
    uvicorn.run(
        "src.server:app", host="0.0.0.0", port=8000, reload=True, log_level="info"
    )
