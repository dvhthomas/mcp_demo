"""
Example script demonstrating direct usage of the tools.

This script shows how to use the WeatherTool and EventSearchTool
independently, without going through the MCP server.
"""

import asyncio

from src.tools.events_tool import EventSearchTool
from src.tools.weather_tool import WeatherTool


async def main():
    """Run example queries using both tools."""
    print("=" * 60)
    print("MCP Tools Server - Example Usage")
    print("=" * 60)
    print()

    # Initialize tools
    weather_tool = WeatherTool()
    events_tool = EventSearchTool()

    # Example 1: Get weather for Paris
    print("Example 1: Get weather for Paris")
    print("-" * 60)
    try:
        weather = await weather_tool.get_weather("Paris")
        print(f"City: {weather['city']}, {weather['country']}")
        print(f"Temperature: {weather['temperature']}{weather['temperature_unit']}")
        print(f"Wind Speed: {weather['wind_speed']} {weather['wind_speed_unit']}")
        print(f"Coordinates: {weather['coordinates']}")
    except Exception as e:
        print(f"Error: {e}")
    print()

    # Example 2: Search for events in New York
    print("Example 2: Search for events in New York")
    print("-" * 60)
    try:
        events = await events_tool.search_events("New York", max_results=3)
        print(f"City: {events['city']}")
        print(f"Date: {events['date']}")
        print(f"Found {events['results_count']} results:")
        print()
        for i, result in enumerate(events["results"], 1):
            print(f"{i}. {result['title']}")
            print(f"   {result['snippet'][:100]}...")
            print(f"   URL: {result['url']}")
            print()
    except Exception as e:
        print(f"Error: {e}")

    print("=" * 60)
    print("Example completed!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
