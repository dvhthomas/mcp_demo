"""
Test edge cases for WeatherTool, especially city name format handling.

This test suite verifies that the weather tool correctly handles various
city name formats, including:
- Simple city names: "Paris"
- City with state: "Aspen, Colorado"
- City with country: "Paris, France"
- Invalid city names
"""

import pytest

from server.tools.weather_tool import WeatherTool


@pytest.fixture
def weather_tool():
    """Create a WeatherTool instance for testing."""
    return WeatherTool()


class TestWeatherToolCityFormats:
    """Test various city name formats."""

    @pytest.mark.asyncio
    async def test_simple_city_name(self, weather_tool):
        """Test that simple city names work correctly."""
        result = await weather_tool.get_weather("Paris")

        assert "city" in result
        assert "temperature" in result
        assert "country" in result
        # Should find Paris, France
        assert result["city"] == "Paris"

    @pytest.mark.asyncio
    async def test_city_with_state_comma_format(self, weather_tool):
        """Test city with state in comma format (e.g., 'Aspen, Colorado')."""
        # This format often fails in geocoding APIs but should work
        # with our fallback mechanism
        result = await weather_tool.get_weather("Aspen, Colorado")

        assert "city" in result
        assert "temperature" in result
        # Should find Aspen (the fallback strips ", Colorado")
        assert result["city"] == "Aspen"

    @pytest.mark.asyncio
    async def test_city_with_state_abbreviation(self, weather_tool):
        """Test city with state abbreviation (e.g., 'New York, NY')."""
        result = await weather_tool.get_weather("New York, NY")

        assert "city" in result
        assert "temperature" in result
        # Should find New York via fallback
        assert result["city"] == "New York"

    @pytest.mark.asyncio
    async def test_city_with_country(self, weather_tool):
        """Test city with country (e.g., 'Paris, France')."""
        # Some city+country formats work directly with the API
        result = await weather_tool.get_weather("Paris, France")

        assert "city" in result
        assert result["city"] == "Paris"
        assert result["country"] == "France"

    @pytest.mark.asyncio
    async def test_invalid_city_raises_error(self, weather_tool):
        """Test that invalid city names raise ValueError."""
        with pytest.raises(ValueError, match="not found"):
            await weather_tool.get_weather("XYZ123NotARealCity")

    @pytest.mark.asyncio
    async def test_city_with_extra_spaces(self, weather_tool):
        """Test city names with extra spaces are handled."""
        # Should work because we strip() the city name after split
        result = await weather_tool.get_weather("Aspen  ,   Colorado")

        assert "city" in result
        assert result["city"] == "Aspen"

    @pytest.mark.asyncio
    async def test_weather_data_structure(self, weather_tool):
        """Test that weather data has all expected fields."""
        result = await weather_tool.get_weather("London")

        # Verify all required fields are present
        assert "city" in result
        assert "country" in result
        assert "temperature" in result
        assert "temperature_unit" in result
        assert "wind_speed" in result
        assert "wind_speed_unit" in result
        assert "weather_code" in result
        assert "coordinates" in result

        # Verify coordinates structure
        assert "latitude" in result["coordinates"]
        assert "longitude" in result["coordinates"]

        # Verify data types
        assert isinstance(result["temperature"], (int, float))
        assert isinstance(result["wind_speed"], (int, float))
        assert isinstance(result["weather_code"], (int, float))

    @pytest.mark.asyncio
    async def test_case_insensitive_city_names(self, weather_tool):
        """Test that city names are case-insensitive."""
        # The API should handle case variations
        result1 = await weather_tool.get_weather("paris")
        result2 = await weather_tool.get_weather("PARIS")
        result3 = await weather_tool.get_weather("Paris")

        # All should find Paris
        assert result1["city"] == "Paris"
        assert result2["city"] == "Paris"
        assert result3["city"] == "Paris"


class TestWeatherToolEdgeCases:
    """Test edge cases and error conditions."""

    @pytest.mark.asyncio
    async def test_empty_string_raises_error(self, weather_tool):
        """Test that empty city name raises appropriate error."""
        with pytest.raises(ValueError, match="not found"):
            await weather_tool.get_weather("")

    @pytest.mark.asyncio
    async def test_only_comma_raises_error(self, weather_tool):
        """Test that just a comma raises appropriate error."""
        with pytest.raises(ValueError, match="not found"):
            await weather_tool.get_weather(",")

    @pytest.mark.asyncio
    async def test_multiple_commas_uses_first_part(self, weather_tool):
        """Test that multiple commas use the first part."""
        # "Denver, Colorado, USA" should fallback to "Denver"
        result = await weather_tool.get_weather("Denver, Colorado, USA")

        assert "city" in result
        assert result["city"] == "Denver"

    @pytest.mark.asyncio
    async def test_special_characters_in_city_name(self, weather_tool):
        """Test cities with special characters."""
        # Test a city with special characters that actually exists
        result = await weather_tool.get_weather("São Paulo")

        assert "city" in result
        # The API might return it as "Sao Paulo" or "São Paulo"
        assert "Paulo" in result["city"]
