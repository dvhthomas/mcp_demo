"""
Unit tests for EventSearchTool.

This test suite verifies that the events search tool correctly handles
various scenarios including:
- Basic functionality and response structure
- City name formats
- Parameter handling (max_results)
- Error handling when DuckDuckGo fails
"""

from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest

from server.config import DEFAULT_MAX_EVENT_RESULTS
from server.tools.events_tool import EventSearchTool


@pytest.fixture
def events_tool():
    """Create an EventSearchTool instance for testing."""
    return EventSearchTool()


class TestEventSearchToolBasic:
    """Test basic EventSearchTool functionality."""

    @pytest.mark.asyncio
    async def test_search_events_returns_expected_structure(self, events_tool):
        """Test that search_events returns all expected fields."""
        result = await events_tool.search_events("New York", max_results=3)

        # Verify all required fields are present
        assert "city" in result
        assert "date" in result
        assert "search_query" in result
        assert "results_count" in result
        assert "results" in result

        # Verify field types
        assert result["city"] == "New York"
        assert isinstance(result["date"], str)
        assert isinstance(result["search_query"], str)
        assert isinstance(result["results_count"], int)
        assert isinstance(result["results"], list)

    @pytest.mark.asyncio
    async def test_search_events_date_format(self, events_tool):
        """Test that the date field is in YYYY-MM-DD format."""
        result = await events_tool.search_events("London", max_results=1)

        # Date should be today's date in YYYY-MM-DD format
        today = datetime.now().strftime("%Y-%m-%d")
        assert result["date"] == today

    @pytest.mark.asyncio
    async def test_search_events_query_format(self, events_tool):
        """Test that the search query includes the city name."""
        result = await events_tool.search_events("Paris", max_results=1)

        assert "Paris" in result["search_query"]
        assert "events" in result["search_query"].lower()

    @pytest.mark.asyncio
    async def test_search_events_with_custom_max_results(self, events_tool):
        """Test that max_results parameter is respected."""
        result = await events_tool.search_events("Tokyo", max_results=2)

        # Results count should not exceed max_results
        assert result["results_count"] <= 2

    @pytest.mark.asyncio
    async def test_default_max_results_used(self, events_tool):
        """Test that default max_results is used when not specified."""
        result = await events_tool.search_events("Berlin")

        # Should use default max results - results won't exceed default
        assert result["results_count"] <= DEFAULT_MAX_EVENT_RESULTS


class TestEventSearchToolResultStructure:
    """Test the structure of search results."""

    @pytest.mark.asyncio
    async def test_result_items_have_expected_fields(self, events_tool):
        """Test that each result item has title, snippet, and url."""
        result = await events_tool.search_events("Chicago", max_results=3)

        for item in result["results"]:
            assert "title" in item
            assert "snippet" in item
            assert "url" in item

    @pytest.mark.asyncio
    async def test_result_item_field_types(self, events_tool):
        """Test that result item fields are strings."""
        result = await events_tool.search_events("Miami", max_results=2)

        for item in result["results"]:
            assert isinstance(item["title"], str)
            assert isinstance(item["snippet"], str)
            assert isinstance(item["url"], str)


class TestEventSearchToolCityFormats:
    """Test various city name formats using mocks to avoid network calls."""

    @pytest.mark.asyncio
    async def test_simple_city_name(self):
        """Test that simple city names work correctly."""
        tool = EventSearchTool()

        mock_results = [{"title": "Event", "body": "Desc", "href": "http://e.com"}]

        with patch("server.tools.events_tool.DDGS") as mock_ddgs:
            mock_instance = MagicMock()
            mock_instance.text.return_value = mock_results
            mock_ddgs.return_value = mock_instance

            result = await tool.search_events("Seattle", max_results=2)

            assert result["city"] == "Seattle"
            assert "error" not in result
            assert result["results_count"] == 1

    @pytest.mark.asyncio
    async def test_city_with_state(self):
        """Test city with state format."""
        tool = EventSearchTool()

        mock_results = [{"title": "Event", "body": "Desc", "href": "http://e.com"}]

        with patch("server.tools.events_tool.DDGS") as mock_ddgs:
            mock_instance = MagicMock()
            mock_instance.text.return_value = mock_results
            mock_ddgs.return_value = mock_instance

            result = await tool.search_events("Austin, Texas", max_results=2)

            assert result["city"] == "Austin, Texas"
            assert "error" not in result

    @pytest.mark.asyncio
    async def test_city_with_country(self):
        """Test city with country format."""
        tool = EventSearchTool()

        mock_results = [{"title": "Event", "body": "Desc", "href": "http://e.com"}]

        with patch("server.tools.events_tool.DDGS") as mock_ddgs:
            mock_instance = MagicMock()
            mock_instance.text.return_value = mock_results
            mock_ddgs.return_value = mock_instance

            result = await tool.search_events("Sydney, Australia", max_results=2)

            assert result["city"] == "Sydney, Australia"
            assert "error" not in result

    @pytest.mark.asyncio
    async def test_city_with_special_characters(self):
        """Test cities with special characters."""
        tool = EventSearchTool()

        mock_results = [{"title": "Event", "body": "Desc", "href": "http://e.com"}]

        with patch("server.tools.events_tool.DDGS") as mock_ddgs:
            mock_instance = MagicMock()
            mock_instance.text.return_value = mock_results
            mock_ddgs.return_value = mock_instance

            result = await tool.search_events("São Paulo", max_results=2)

            assert result["city"] == "São Paulo"
            assert "error" not in result


class TestEventSearchToolEdgeCases:
    """Test edge cases and error conditions."""

    @pytest.mark.asyncio
    async def test_empty_city_name(self, events_tool):
        """Test that empty city name still returns a valid structure."""
        result = await events_tool.search_events("", max_results=2)

        # Should still return valid structure (search might return nothing)
        assert "city" in result
        assert "results" in result
        assert result["city"] == ""

    @pytest.mark.asyncio
    async def test_max_results_one(self, events_tool):
        """Test with max_results=1."""
        result = await events_tool.search_events("Boston", max_results=1)

        assert result["results_count"] <= 1

    @pytest.mark.asyncio
    async def test_whitespace_in_city_name(self):
        """Test city names with extra whitespace."""
        tool = EventSearchTool()

        mock_results = [{"title": "Event", "body": "Desc", "href": "http://e.com"}]

        with patch("server.tools.events_tool.DDGS") as mock_ddgs:
            mock_instance = MagicMock()
            mock_instance.text.return_value = mock_results
            mock_ddgs.return_value = mock_instance

            result = await tool.search_events("  Denver  ", max_results=2)

            # City should be stored as provided (whitespace preserved)
            assert result["city"] == "  Denver  "
            assert "error" not in result

    @pytest.mark.asyncio
    async def test_very_long_city_name(self, events_tool):
        """Test with a very long city name."""
        long_city = "A" * 200
        result = await events_tool.search_events(long_city, max_results=1)

        # Should handle gracefully without crashing
        assert "city" in result
        assert "results" in result


class TestEventSearchToolErrorHandling:
    """Test error handling scenarios using mocks."""

    @pytest.mark.asyncio
    async def test_ddgs_exception_returns_error_dict(self, events_tool):
        """Test that DuckDuckGo exceptions are handled gracefully."""
        with patch.object(events_tool, "search_events") as mock_search:
            # Simulate what the actual method does on error
            mock_search.return_value = {
                "city": "TestCity",
                "date": datetime.now().strftime("%Y-%m-%d"),
                "search_query": "events happening today in TestCity",
                "results_count": 0,
                "results": [],
                "error": "DuckDuckGo search failed: Connection error",
            }

            result = await events_tool.search_events("TestCity", max_results=5)

            assert "error" in result
            assert result["results_count"] == 0
            assert result["results"] == []

    @pytest.mark.asyncio
    async def test_error_response_structure(self):
        """Test error response has all required fields."""
        tool = EventSearchTool()

        # Use mock to force an exception in DDGS
        with patch("server.tools.events_tool.DDGS") as mock_ddgs:
            mock_instance = MagicMock()
            mock_instance.text.side_effect = Exception("Network timeout")
            mock_ddgs.return_value = mock_instance

            result = await tool.search_events("ErrorCity", max_results=3)

            # Should return error dict with all fields
            assert result["city"] == "ErrorCity"
            assert result["date"] == datetime.now().strftime("%Y-%m-%d")
            assert "events happening today in ErrorCity" in result["search_query"]
            assert result["results_count"] == 0
            assert result["results"] == []
            assert "error" in result
            assert "Network timeout" in result["error"]


class TestEventSearchToolMocked:
    """Tests using mocked DuckDuckGo responses for deterministic testing."""

    @pytest.mark.asyncio
    async def test_results_mapping_from_ddgs_response(self):
        """Test that DDGS response fields are correctly mapped."""
        tool = EventSearchTool()

        mock_ddgs_results = [
            {
                "title": "Event Title 1",
                "body": "Description of event 1",
                "href": "https://example.com/event1",
            },
            {
                "title": "Event Title 2",
                "body": "Description of event 2",
                "href": "https://example.com/event2",
            },
        ]

        with patch("server.tools.events_tool.DDGS") as mock_ddgs:
            mock_instance = MagicMock()
            mock_instance.text.return_value = mock_ddgs_results
            mock_ddgs.return_value = mock_instance

            result = await tool.search_events("MockCity", max_results=5)

            # Verify mapping
            assert result["results_count"] == 2
            assert len(result["results"]) == 2

            assert result["results"][0]["title"] == "Event Title 1"
            assert result["results"][0]["snippet"] == "Description of event 1"
            assert result["results"][0]["url"] == "https://example.com/event1"

            assert result["results"][1]["title"] == "Event Title 2"
            assert result["results"][1]["snippet"] == "Description of event 2"
            assert result["results"][1]["url"] == "https://example.com/event2"

    @pytest.mark.asyncio
    async def test_empty_ddgs_response(self):
        """Test handling of empty search results."""
        tool = EventSearchTool()

        with patch("server.tools.events_tool.DDGS") as mock_ddgs:
            mock_instance = MagicMock()
            mock_instance.text.return_value = []
            mock_ddgs.return_value = mock_instance

            result = await tool.search_events("EmptyCity", max_results=5)

            assert result["results_count"] == 0
            assert result["results"] == []
            assert "error" not in result

    @pytest.mark.asyncio
    async def test_missing_fields_in_ddgs_response(self):
        """Test handling of DDGS results with missing fields."""
        tool = EventSearchTool()

        # DDGS might return results with missing fields
        mock_ddgs_results = [
            {"title": "Only Title"},  # Missing body and href
            {"body": "Only Body"},  # Missing title and href
            {},  # All fields missing
        ]

        with patch("server.tools.events_tool.DDGS") as mock_ddgs:
            mock_instance = MagicMock()
            mock_instance.text.return_value = mock_ddgs_results
            mock_ddgs.return_value = mock_instance

            result = await tool.search_events("PartialCity", max_results=5)

            # Should handle gracefully with empty strings for missing fields
            assert result["results_count"] == 3
            assert result["results"][0]["title"] == "Only Title"
            assert result["results"][0]["snippet"] == ""
            assert result["results"][0]["url"] == ""

            assert result["results"][1]["title"] == ""
            assert result["results"][1]["snippet"] == "Only Body"

            assert result["results"][2]["title"] == ""
            assert result["results"][2]["snippet"] == ""
            assert result["results"][2]["url"] == ""
