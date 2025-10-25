"""
Events Search Tool - Searches for events happening in a city.

This module contains the EventSearchTool class which uses DuckDuckGo
to search for events happening today in a specified city.
"""

from datetime import datetime
from typing import Any

import httpx
from bs4 import BeautifulSoup


class EventSearchTool:
    """
    A tool for searching events happening in cities.

    This class uses DuckDuckGo's search functionality to find events
    happening today in a specified city. It parses the HTML results
    to extract relevant information.

    Attributes:
        search_url (str): Base URL for DuckDuckGo search
    """

    def __init__(self):
        """Initialize the EventSearchTool with the search endpoint."""
        self.search_url = "https://html.duckduckgo.com/html/"

    async def search_events(self, city: str, max_results: int = 5) -> dict[str, Any]:
        """
        Search for events happening today in a specified city.

        This method performs a DuckDuckGo search for events in the city
        and parses the results to extract titles and snippets.

        Args:
            city (str): Name of the city to search events for
            max_results (int): Maximum number of results to return (default: 5)

        Returns:
            Dict[str, Any]: A dictionary containing:
                - city: The city name
                - date: Today's date
                - search_query: The query used for searching
                - results: List of search results, each containing:
                    - title: Result title
                    - snippet: Brief description/snippet
                    - url: Link to the source (if available)

        Raises:
            httpx.HTTPError: If there's an error communicating with DuckDuckGo
        """
        # Build search query for today's events in the city
        today = datetime.now().strftime("%Y-%m-%d")
        search_query = f"events happening today in {city}"

        async with httpx.AsyncClient(follow_redirects=True) as client:
            # Prepare the search request
            # DuckDuckGo HTML requires a POST request with the query parameter
            response = await client.post(
                self.search_url,
                data={"q": search_query},
                headers={
                    "User-Agent": (
                        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
                    )
                },
            )
            response.raise_for_status()

            # Parse the HTML response
            soup = BeautifulSoup(response.text, "html.parser")
            results = []

            # Find all result divs (DuckDuckGo uses class "result")
            search_results = soup.find_all("div", class_="result")

            for result in search_results[:max_results]:
                title_elem = result.find("a", class_="result__a")
                snippet_elem = result.find("a", class_="result__snippet")

                if title_elem:
                    title = title_elem.get_text(strip=True)
                    url = title_elem.get("href", "")
                    snippet = snippet_elem.get_text(strip=True) if snippet_elem else ""

                    results.append({"title": title, "snippet": snippet, "url": url})

            return {
                "city": city,
                "date": today,
                "search_query": search_query,
                "results_count": len(results),
                "results": results,
            }
