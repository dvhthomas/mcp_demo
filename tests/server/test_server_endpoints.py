"""
Unit tests for Server REST endpoints.

This test suite verifies the HTTP REST API endpoints including:
- Root endpoint (/)
- Health check (/health)
- MCP info (/mcp/info)
- Tools list (/mcp/tools/list)
- Tool call (/mcp/tools/call)
- Error handling for invalid requests
"""

from unittest.mock import AsyncMock, patch

import pytest
from starlette.testclient import TestClient

from server.server import app


@pytest.fixture
def client():
    """Create a test client for the server."""
    return TestClient(app)


class TestRootEndpoint:
    """Test the root (/) endpoint."""

    def test_root_returns_server_info(self, client):
        """Test that root endpoint returns server information."""
        response = client.get("/")

        assert response.status_code == 200
        data = response.json()

        assert data["name"] == "MCP Tools Server"
        assert data["version"] == "0.1.0"
        assert data["protocol"] == "MCP"
        assert "description" in data

    def test_root_returns_endpoints_list(self, client):
        """Test that root endpoint lists available endpoints."""
        response = client.get("/")

        assert response.status_code == 200
        data = response.json()

        assert "endpoints" in data
        endpoints = data["endpoints"]

        assert endpoints["info"] == "/mcp/info"
        assert endpoints["tools"] == "/mcp/tools/list"
        assert endpoints["call"] == "/mcp/tools/call"
        assert endpoints["mcp_sse"] == "/sse"
        assert endpoints["health"] == "/health"


class TestHealthEndpoint:
    """Test the health check (/health) endpoint."""

    def test_health_returns_healthy(self, client):
        """Test that health endpoint returns healthy status."""
        response = client.get("/health")

        assert response.status_code == 200
        data = response.json()

        assert data["status"] == "healthy"


class TestMCPInfoEndpoint:
    """Test the MCP info (/mcp/info) endpoint."""

    def test_mcp_info_returns_protocol_version(self, client):
        """Test that MCP info returns protocol version."""
        response = client.get("/mcp/info")

        assert response.status_code == 200
        data = response.json()

        assert data["protocolVersion"] == "2024-11-05"

    def test_mcp_info_returns_server_info(self, client):
        """Test that MCP info returns server information."""
        response = client.get("/mcp/info")

        assert response.status_code == 200
        data = response.json()

        assert "serverInfo" in data
        assert data["serverInfo"]["name"] == "mcp-tools-server"
        assert data["serverInfo"]["version"] == "0.1.0"

    def test_mcp_info_returns_capabilities(self, client):
        """Test that MCP info returns capabilities."""
        response = client.get("/mcp/info")

        assert response.status_code == 200
        data = response.json()

        assert "capabilities" in data
        assert data["capabilities"]["tools"] is True


class TestToolsListEndpoint:
    """Test the tools list (/mcp/tools/list) endpoint."""

    def test_list_tools_returns_both_tools(self, client):
        """Test that tools list returns both registered tools."""
        response = client.get("/mcp/tools/list")

        assert response.status_code == 200
        data = response.json()

        assert "tools" in data
        tools = data["tools"]

        assert len(tools) == 2

        tool_names = {tool["name"] for tool in tools}
        assert "get_weather" in tool_names
        assert "search_events" in tool_names

    def test_list_tools_returns_tool_definitions(self, client):
        """Test that tools list returns complete tool definitions."""
        response = client.get("/mcp/tools/list")

        assert response.status_code == 200
        data = response.json()

        for tool in data["tools"]:
            assert "name" in tool
            assert "description" in tool
            assert "inputSchema" in tool

    def test_weather_tool_definition_structure(self, client):
        """Test weather tool definition has correct structure."""
        response = client.get("/mcp/tools/list")

        assert response.status_code == 200
        tools = response.json()["tools"]

        weather_tool = next(t for t in tools if t["name"] == "get_weather")

        assert "city" in weather_tool["description"].lower()
        assert weather_tool["inputSchema"]["type"] == "object"
        assert "city" in weather_tool["inputSchema"]["properties"]
        assert "city" in weather_tool["inputSchema"]["required"]

    def test_events_tool_definition_structure(self, client):
        """Test events tool definition has correct structure."""
        response = client.get("/mcp/tools/list")

        assert response.status_code == 200
        tools = response.json()["tools"]

        events_tool = next(t for t in tools if t["name"] == "search_events")

        assert "event" in events_tool["description"].lower()
        assert events_tool["inputSchema"]["type"] == "object"
        assert "city" in events_tool["inputSchema"]["properties"]
        assert "max_results" in events_tool["inputSchema"]["properties"]
        assert "city" in events_tool["inputSchema"]["required"]


class TestToolCallEndpoint:
    """Test the tool call (/mcp/tools/call) endpoint."""

    def test_call_weather_tool_success(self, client):
        """Test successful weather tool call."""
        # Mock the weather adapter to avoid real API calls
        with patch("server.server.weather_adapter.execute") as mock_execute:
            mock_execute.return_value = {
                "city": "London",
                "country": "United Kingdom",
                "temperature": 15.5,
                "temperature_unit": "celsius",
                "wind_speed": 10.2,
                "wind_speed_unit": "km/h",
                "weather_code": 1,
                "coordinates": {"latitude": 51.5, "longitude": -0.1},
            }

            response = client.post(
                "/mcp/tools/call",
                json={"name": "get_weather", "arguments": {"city": "London"}},
            )

            assert response.status_code == 200
            data = response.json()

            assert "content" in data
            assert len(data["content"]) == 1
            assert data["content"][0]["type"] == "text"
            assert "London" in data["content"][0]["text"]

    def test_call_events_tool_success(self, client):
        """Test successful events tool call."""
        with patch("server.server.events_adapter.execute") as mock_execute:
            mock_execute.return_value = {
                "city": "Tokyo",
                "date": "2024-01-15",
                "search_query": "events happening today in Tokyo",
                "results_count": 2,
                "results": [
                    {"title": "Event 1", "snippet": "Desc 1", "url": "http://e1.com"}
                ],
            }

            response = client.post(
                "/mcp/tools/call",
                json={
                    "name": "search_events",
                    "arguments": {"city": "Tokyo", "max_results": 5},
                },
            )

            assert response.status_code == 200
            data = response.json()

            assert "content" in data
            assert "Tokyo" in data["content"][0]["text"]

    def test_call_unknown_tool_returns_404(self, client):
        """Test that calling unknown tool returns 404."""
        response = client.post(
            "/mcp/tools/call",
            json={"name": "unknown_tool", "arguments": {}},
        )

        assert response.status_code == 404
        data = response.json()

        assert "error" in data
        assert "unknown_tool" in data["error"]
        assert "not found" in data["error"].lower()

    def test_call_tool_missing_required_argument_returns_400(self, client):
        """Test that missing required argument returns 400."""
        response = client.post(
            "/mcp/tools/call",
            json={"name": "get_weather", "arguments": {}},
        )

        assert response.status_code == 400
        data = response.json()

        assert "error" in data
        assert "city" in data["error"].lower()

    def test_call_tool_with_empty_arguments(self, client):
        """Test tool call with empty arguments object."""
        response = client.post(
            "/mcp/tools/call",
            json={"name": "get_weather", "arguments": {}},
        )

        # Should return 400 for missing required argument
        assert response.status_code == 400

    def test_call_tool_without_arguments_key(self, client):
        """Test tool call without arguments key uses empty dict."""
        response = client.post(
            "/mcp/tools/call",
            json={"name": "get_weather"},
        )

        # Should still return 400 for missing required argument
        assert response.status_code == 400

    def test_call_tool_server_error_returns_500(self, client):
        """Test that server errors return 500."""
        with patch("server.server.weather_adapter.execute") as mock_execute:
            mock_execute.side_effect = Exception("Internal server error")

            response = client.post(
                "/mcp/tools/call",
                json={"name": "get_weather", "arguments": {"city": "London"}},
            )

            assert response.status_code == 500
            data = response.json()

            assert "error" in data
            assert "Error executing tool" in data["error"]


class TestToolCallEndpointEdgeCases:
    """Test edge cases for tool call endpoint."""

    def test_call_tool_with_extra_arguments(self, client):
        """Test that extra arguments are passed through."""
        with patch("server.server.weather_adapter.execute") as mock_execute:
            mock_execute.return_value = {"city": "Paris", "temperature": 20}

            response = client.post(
                "/mcp/tools/call",
                json={
                    "name": "get_weather",
                    "arguments": {"city": "Paris", "extra_arg": "ignored"},
                },
            )

            assert response.status_code == 200
            # The adapter should have been called with all arguments
            mock_execute.assert_called_once()
            call_args = mock_execute.call_args[0][0]
            assert call_args["city"] == "Paris"
            assert call_args["extra_arg"] == "ignored"

    def test_call_events_with_default_max_results(self, client):
        """Test events tool call without max_results uses default."""
        with patch("server.server.events_adapter.execute") as mock_execute:
            mock_execute.return_value = {
                "city": "Berlin",
                "date": "2024-01-15",
                "search_query": "events",
                "results_count": 0,
                "results": [],
            }

            response = client.post(
                "/mcp/tools/call",
                json={"name": "search_events", "arguments": {"city": "Berlin"}},
            )

            assert response.status_code == 200

    def test_call_tool_with_special_characters_in_city(self, client):
        """Test tool call with special characters in city name."""
        with patch("server.server.weather_adapter.execute") as mock_execute:
            mock_execute.return_value = {"city": "São Paulo", "temperature": 25}

            response = client.post(
                "/mcp/tools/call",
                json={"name": "get_weather", "arguments": {"city": "São Paulo"}},
            )

            assert response.status_code == 200
            mock_execute.assert_called_once_with({"city": "São Paulo"})


class TestToolCallValidationErrors:
    """Test validation error handling in tool calls."""

    def test_validation_error_returns_400(self, client):
        """Test that ValueError from adapter returns 400."""
        with patch("server.server.weather_adapter.execute") as mock_execute:
            mock_execute.side_effect = ValueError("Invalid city format")

            response = client.post(
                "/mcp/tools/call",
                json={"name": "get_weather", "arguments": {"city": ""}},
            )

            assert response.status_code == 400
            data = response.json()
            assert "error" in data


class TestHTTPMethods:
    """Test HTTP method handling."""

    def test_root_only_accepts_get(self, client):
        """Test that root endpoint only accepts GET."""
        response = client.get("/")
        assert response.status_code == 200

        response = client.post("/")
        assert response.status_code == 405

    def test_health_only_accepts_get(self, client):
        """Test that health endpoint only accepts GET."""
        response = client.get("/health")
        assert response.status_code == 200

        response = client.post("/health")
        assert response.status_code == 405

    def test_tools_list_only_accepts_get(self, client):
        """Test that tools list endpoint only accepts GET."""
        response = client.get("/mcp/tools/list")
        assert response.status_code == 200

        response = client.post("/mcp/tools/list")
        assert response.status_code == 405

    def test_tools_call_only_accepts_post(self, client):
        """Test that tools call endpoint only accepts POST."""
        response = client.post(
            "/mcp/tools/call",
            json={"name": "get_weather", "arguments": {"city": "London"}},
        )
        # Will be 200 or 4xx depending on mock, but not 405
        assert response.status_code != 405

        response = client.get("/mcp/tools/call")
        assert response.status_code == 405
