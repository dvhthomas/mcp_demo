"""
MCP Adapters - Protocol translation layer between business tools and MCP server.

Adapters translate tool functions into MCP tool definitions and handle
parameter validation and mapping. This separation allows business tools
to remain protocol-agnostic and reusable.
"""

from typing import Any

from server.config import DEFAULT_MAX_EVENT_RESULTS
from server.tools.events_tool import EventSearchTool
from server.tools.weather_tool import WeatherTool


class WeatherToolMCPAdapter:
    """Adapts WeatherTool for MCP protocol."""

    def __init__(self, tool: WeatherTool):
        """Initialize adapter with a WeatherTool instance."""
        self.tool = tool

    def get_tool_definition(self) -> dict[str, Any]:
        """Return MCP tool definition with name, description, and input schema."""
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
        """Execute weather tool with validated arguments."""
        city = arguments.get("city")
        if not city:
            raise ValueError("Missing required argument: city")

        return await self.tool.get_weather(city)


class EventSearchToolMCPAdapter:
    """Adapts EventSearchTool for MCP protocol."""

    def __init__(self, tool: EventSearchTool):
        """Initialize adapter with an EventSearchTool instance."""
        self.tool = tool

    def get_tool_definition(self) -> dict[str, Any]:
        """Return MCP tool definition with name, description, and input schema."""
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
                            f"Maximum number of results to return "
                            f"(default: {DEFAULT_MAX_EVENT_RESULTS})"
                        ),
                        "default": DEFAULT_MAX_EVENT_RESULTS,
                    },
                },
                "required": ["city"],
            },
        }

    async def execute(self, arguments: dict[str, Any]) -> dict[str, Any]:
        """Execute events search tool with validated arguments."""
        city = arguments.get("city")
        if not city:
            raise ValueError("Missing required argument: city")

        max_results = arguments.get("max_results", DEFAULT_MAX_EVENT_RESULTS)
        return await self.tool.search_events(city, max_results)
