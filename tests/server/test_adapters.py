"""Unit tests for MCP adapters."""

import pytest

from server.mcp_adapters import EventSearchToolMCPAdapter, WeatherToolMCPAdapter
from server.tools.events_tool import EventSearchTool
from server.tools.weather_tool import WeatherTool


@pytest.fixture
def weather_adapter():
    weather_tool = WeatherTool()
    return WeatherToolMCPAdapter(weather_tool)


@pytest.fixture
def events_adapter():
    events_tool = EventSearchTool()
    return EventSearchToolMCPAdapter(events_tool)


class TestWeatherToolMCPAdapter:
    """Tests for WeatherToolMCPAdapter."""

    def test_get_tool_definition(self, weather_adapter):
        """Test that tool definition is correctly formatted."""
        definition = weather_adapter.get_tool_definition()

        assert definition["name"] == "get_weather"
        assert "description" in definition
        assert "inputSchema" in definition
        assert definition["inputSchema"]["type"] == "object"
        assert "city" in definition["inputSchema"]["properties"]
        assert "city" in definition["inputSchema"]["required"]

    @pytest.mark.asyncio
    async def test_execute_success(self, weather_adapter):
        """Test successful execution with valid city."""
        result = await weather_adapter.execute({"city": "London"})

        assert "city" in result
        assert "country" in result
        assert "temperature" in result
        assert "temperature_unit" in result
        assert "wind_speed" in result
        assert "coordinates" in result

    @pytest.mark.asyncio
    async def test_execute_missing_city(self, weather_adapter):
        """Test execution fails when city argument is missing."""
        with pytest.raises(ValueError, match="Missing required argument: city"):
            await weather_adapter.execute({})


class TestEventSearchToolMCPAdapter:
    """Tests for EventSearchToolMCPAdapter."""

    def test_get_tool_definition(self, events_adapter):
        """Test that tool definition is correctly formatted."""
        definition = events_adapter.get_tool_definition()

        assert definition["name"] == "search_events"
        assert "description" in definition
        assert "inputSchema" in definition
        assert definition["inputSchema"]["type"] == "object"
        assert "city" in definition["inputSchema"]["properties"]
        assert "max_results" in definition["inputSchema"]["properties"]
        assert "city" in definition["inputSchema"]["required"]

    @pytest.mark.asyncio
    async def test_execute_success(self, events_adapter):
        """Test successful execution with valid arguments."""
        result = await events_adapter.execute({"city": "Tokyo", "max_results": 2})

        assert "city" in result
        assert result["city"] == "Tokyo"
        assert "date" in result
        assert "search_query" in result
        assert "results_count" in result
        assert "results" in result

    @pytest.mark.asyncio
    async def test_execute_default_max_results(self, events_adapter):
        """Test execution with default max_results."""
        result = await events_adapter.execute({"city": "Paris"})

        assert "city" in result
        assert "results" in result

    @pytest.mark.asyncio
    async def test_execute_missing_city(self, events_adapter):
        """Test execution fails when city argument is missing."""
        with pytest.raises(ValueError, match="Missing required argument: city"):
            await events_adapter.execute({})
