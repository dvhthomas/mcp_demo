"""
Weather Tool - Provides weather information for any city in the world.

This module contains the WeatherTool class which uses the Open-Meteo API
to fetch current weather conditions for a specified city.
"""

from typing import Any

import httpx


class WeatherTool:
    """
    A tool for fetching weather information for cities worldwide.

    This class uses the Open-Meteo API, which is free and doesn't require
    an API key. It first geocodes the city name to get coordinates, then
    fetches current weather data.

    Attributes:
        geocoding_url (str): Base URL for the geocoding API
        weather_url (str): Base URL for the weather API
    """

    def __init__(self):
        """Initialize the WeatherTool with API endpoints."""
        self.geocoding_url = "https://geocoding-api.open-meteo.com/v1/search"
        self.weather_url = "https://api.open-meteo.com/v1/forecast"

    async def get_weather(self, city: str) -> dict[str, Any]:
        """
        Get current weather information for a specified city.

        This method performs two API calls:
        1. Geocode the city name to get latitude and longitude
        2. Fetch current weather data for those coordinates

        Args:
            city (str): Name of the city to get weather for

        Returns:
            Dict[str, Any]: A dictionary containing weather information including:
                - city: The city name
                - country: Country code
                - temperature: Current temperature in Celsius
                - wind_speed: Current wind speed in km/h
                - weather_code: WMO weather code
                - coordinates: Dict with latitude and longitude

        Raises:
            ValueError: If the city cannot be found
            httpx.HTTPError: If there's an error communicating with the API
        """
        async with httpx.AsyncClient() as client:
            # Step 1: Geocode the city name
            geocode_response = await client.get(
                self.geocoding_url, params={"name": city, "count": 1, "format": "json"}
            )
            geocode_response.raise_for_status()
            geocode_data = geocode_response.json()

            if not geocode_data.get("results"):
                raise ValueError(f"City '{city}' not found")

            location = geocode_data["results"][0]
            latitude = location["latitude"]
            longitude = location["longitude"]
            city_name = location["name"]
            country = location.get("country", "Unknown")

            # Step 2: Get weather data for the coordinates
            weather_response = await client.get(
                self.weather_url,
                params={
                    "latitude": latitude,
                    "longitude": longitude,
                    "current": "temperature_2m,wind_speed_10m,weather_code",
                },
            )
            weather_response.raise_for_status()
            weather_data = weather_response.json()

            current = weather_data["current"]

            # Format and return the weather information
            return {
                "city": city_name,
                "country": country,
                "temperature": current["temperature_2m"],
                "temperature_unit": weather_data["current_units"]["temperature_2m"],
                "wind_speed": current["wind_speed_10m"],
                "wind_speed_unit": weather_data["current_units"]["wind_speed_10m"],
                "weather_code": current["weather_code"],
                "coordinates": {"latitude": latitude, "longitude": longitude},
            }
