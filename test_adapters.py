"""
Quick test script to verify MCP adapters work correctly.
"""

import asyncio

from src.mcp_adapters import EventSearchToolMCPAdapter, WeatherToolMCPAdapter
from src.tools.events_tool import EventSearchTool
from src.tools.weather_tool import WeatherTool


async def main():
    """Test the MCP adapters."""
    print("Testing MCP Adapters...")
    print("=" * 60)

    # Test WeatherToolMCPAdapter
    print("\n1. Testing WeatherToolMCPAdapter")
    print("-" * 60)
    weather_tool = WeatherTool()
    weather_adapter = WeatherToolMCPAdapter(weather_tool)

    # Get tool definition
    definition = weather_adapter.get_tool_definition()
    print(f"Tool name: {definition['name']}")
    print(f"Description: {definition['description']}")

    # Execute with arguments
    result = await weather_adapter.execute({"city": "London"})
    print(f"Result: {result['city']}, {result['country']}")
    print(f"Temperature: {result['temperature']}{result['temperature_unit']}")

    # Test EventSearchToolMCPAdapter
    print("\n2. Testing EventSearchToolMCPAdapter")
    print("-" * 60)
    events_tool = EventSearchTool()
    events_adapter = EventSearchToolMCPAdapter(events_tool)

    # Get tool definition
    definition = events_adapter.get_tool_definition()
    print(f"Tool name: {definition['name']}")
    print(f"Description: {definition['description']}")

    # Execute with arguments
    result = await events_adapter.execute({"city": "Tokyo", "max_results": 2})
    print(f"Result: {result['city']}")
    print(f"Found {result['results_count']} events")

    print("\n" + "=" * 60)
    print("All adapter tests passed!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
