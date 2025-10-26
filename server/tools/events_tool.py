"""
Events Search Tool - Searches for events happening in a city.

This module contains the EventSearchTool class which uses the official
DuckDuckGo Search library to find events happening today in a specified city.
"""

from datetime import datetime
from typing import Any

from ddgs import DDGS

from server.config import DEFAULT_MAX_EVENT_RESULTS


class EventSearchTool:
    """
    A tool for searching events happening in cities.

    This class uses the official DuckDuckGo Search library to find events
    happening today in a specified city.

    The library provides a clean, official API instead of HTML scraping.
    """

    def __init__(self):
        """Initialize the EventSearchTool."""
        pass  # No initialization needed for duckduckgo-search

    async def search_events(
        self, city: str, max_results: int = DEFAULT_MAX_EVENT_RESULTS
    ) -> dict[str, Any]:
        """
        Search for events happening today in a specified city.

        This method uses the official DuckDuckGo Search library to find
        events and returns formatted results.

        Args:
            city (str): Name of the city to search events for
            max_results (int): Maximum number of results to return (default: 5)

        Returns:
            dict[str, Any]: A dictionary containing:
                - city: The city name
                - date: Today's date
                - search_query: The query used for searching
                - results_count: Number of results found
                - results: List of search results, each containing:
                    - title: Result title
                    - snippet: Brief description/snippet
                    - url: Link to the source

        Raises:
            Exception: If there's an error searching DuckDuckGo
        """
        # Build search query for today's events in the city
        today = datetime.now().strftime("%Y-%m-%d")
        search_query = f"events happening today in {city}"

        try:
            # Use DuckDuckGo Search library
            # The library handles the async internally, but we wrap it
            # for consistency with the rest of our async API
            search_client = DDGS()
            raw_results = search_client.text(
                query=search_query,
                max_results=max_results,
            )

            # Format results
            results = []
            for result in raw_results:
                results.append(
                    {
                        "title": result.get("title", ""),
                        "snippet": result.get("body", ""),
                        "url": result.get("href", ""),
                    }
                )

            return {
                "city": city,
                "date": today,
                "search_query": search_query,
                "results_count": len(results),
                "results": results,
            }

        except Exception as e:
            # Return error information in a structured way
            return {
                "city": city,
                "date": today,
                "search_query": search_query,
                "results_count": 0,
                "results": [],
                "error": f"DuckDuckGo search failed: {str(e)}",
            }
