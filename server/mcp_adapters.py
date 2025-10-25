"""
MCP Adapters - The Protocol Translation Layer (Educational Demo)

This module demonstrates the ADAPTER PATTERN - a key software design principle
that separates business logic from protocol specifics.

THE 3-LAYER PATTERN:
1. Business Tools (weather_tool.py, events_tool.py) - Protocol-agnostic logic
2. MCP Adapters (THIS FILE) - Translate between tools and MCP protocol
3. Server (server.py) - FastMCP server that exposes tools via SSE

WHY THIS MATTERS FOR STUDENTS:
- Business tools can work with ANY protocol (REST, GraphQL, gRPC, MCP)
- Changing protocols doesn't require rewriting business logic
- Each layer has a single responsibility (Single Responsibility Principle)
- Testing is easier - test business logic separately from protocol concerns

LEARNING GOAL: Understand how to build flexible, maintainable systems
by keeping protocol concerns separate from business logic.

WHAT THESE ADAPTERS DO:
- Convert tool functions into MCP tool definitions (name, description, schema)
- Validate and map MCP arguments to tool function parameters
- Handle errors and return results in MCP format
"""

from typing import Any

from server.tools.events_tool import EventSearchTool
from server.tools.weather_tool import WeatherTool


class WeatherToolMCPAdapter:
    """
    MCP adapter for the WeatherTool.

    This adapter wraps a WeatherTool instance and provides the MCP-specific
    interface, including tool definitions and parameter mapping.

    Attributes:
        tool (WeatherTool): The underlying weather tool instance
    """

    def __init__(self, tool: WeatherTool):
        """
        Initialize the adapter with a WeatherTool instance.

        Args:
            tool (WeatherTool): The weather tool to adapt for MCP
        """
        self.tool = tool

    def get_tool_definition(self) -> dict[str, Any]:
        """
        Get the MCP tool definition for the weather tool.

        This method defines how the tool appears in the MCP protocol,
        including its name, description, and input schema.

        Returns:
            dict[str, Any]: MCP tool definition
        """
        return {
            "name": "get_weather",
            "description": "Get current weather information for any city in the world",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "city": {
                        "type": "string",
                        "description": "The name of the city to get weather for",
                    }
                },
                "required": ["city"],
            },
        }

    async def execute(self, arguments: dict[str, Any]) -> dict[str, Any]:
        """
        Execute the weather tool with MCP-provided arguments.

        This method adapts MCP arguments to the tool's expected format
        and returns the result.

        Args:
            arguments (dict[str, Any]): Arguments from MCP call

        Returns:
            dict[str, Any]: Weather information

        Raises:
            ValueError: If required arguments are missing
        """
        city = arguments.get("city")
        if not city:
            raise ValueError("Missing required argument: city")

        return await self.tool.get_weather(city)


class EventSearchToolMCPAdapter:
    """
    MCP adapter for the EventSearchTool.

    This adapter wraps an EventSearchTool instance and provides the MCP-specific
    interface, including tool definitions and parameter mapping.

    Attributes:
        tool (EventSearchTool): The underlying events search tool instance
    """

    def __init__(self, tool: EventSearchTool):
        """
        Initialize the adapter with an EventSearchTool instance.

        Args:
            tool (EventSearchTool): The events search tool to adapt for MCP
        """
        self.tool = tool

    def get_tool_definition(self) -> dict[str, Any]:
        """
        Get the MCP tool definition for the events search tool.

        This method defines how the tool appears in the MCP protocol,
        including its name, description, and input schema.

        Returns:
            dict[str, Any]: MCP tool definition
        """
        return {
            "name": "search_events",
            "description": (
                "Search for events happening today in a specified city using DuckDuckGo"
            ),
            "inputSchema": {
                "type": "object",
                "properties": {
                    "city": {
                        "type": "string",
                        "description": "The name of the city to search events for",
                    },
                    "max_results": {
                        "type": "integer",
                        "description": (
                            "Maximum number of results to return (default: 5)"
                        ),
                        "default": 5,
                    },
                },
                "required": ["city"],
            },
        }

    async def execute(self, arguments: dict[str, Any]) -> dict[str, Any]:
        """
        Execute the events search tool with MCP-provided arguments.

        This method adapts MCP arguments to the tool's expected format
        and returns the result.

        Args:
            arguments (dict[str, Any]): Arguments from MCP call

        Returns:
            dict[str, Any]: Event search results

        Raises:
            ValueError: If required arguments are missing
        """
        city = arguments.get("city")
        if not city:
            raise ValueError("Missing required argument: city")

        max_results = arguments.get("max_results", 5)
        return await self.tool.search_events(city, max_results)
