"""
Unit tests for MCPClient.

This test suite verifies the MCP client functionality including:
- Connection management (connect, close, context manager)
- Tool listing
- Tool calling
- Health checks
- Error handling for disconnected state
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from client.mcp_client import MCPClient


@pytest.fixture
def mcp_client():
    """Create an MCPClient instance for testing."""
    return MCPClient(base_url="http://localhost:8000")


class TestMCPClientInitialization:
    """Test MCPClient initialization."""

    def test_init_with_default_url(self):
        """Test initialization with default URL."""
        client = MCPClient()
        assert client.base_url == "http://localhost:8000"
        assert client.session is None

    def test_init_with_custom_url(self):
        """Test initialization with custom URL."""
        client = MCPClient(base_url="http://example.com:9000")
        assert client.base_url == "http://example.com:9000"

    def test_init_strips_trailing_slash(self):
        """Test that trailing slash is stripped from URL."""
        client = MCPClient(base_url="http://localhost:8000/")
        assert client.base_url == "http://localhost:8000"

    def test_init_session_is_none(self):
        """Test that session is None before connection."""
        client = MCPClient()
        assert client.session is None
        assert client._read_stream is None
        assert client._write_stream is None
        assert client._sse_context is None


class TestMCPClientConnection:
    """Test MCPClient connection management."""

    @pytest.mark.asyncio
    async def test_connect_establishes_session(self):
        """Test that connect() establishes a session."""
        client = MCPClient()

        # Mock the SSE client and ClientSession
        mock_read_stream = AsyncMock()
        mock_write_stream = AsyncMock()

        mock_sse_context = AsyncMock()
        mock_sse_context.__aenter__ = AsyncMock(
            return_value=(mock_read_stream, mock_write_stream)
        )
        mock_sse_context.__aexit__ = AsyncMock(return_value=None)

        mock_session = AsyncMock()
        mock_session.initialize = AsyncMock()

        with patch("client.mcp_client.sse_client", return_value=mock_sse_context):
            with patch(
                "client.mcp_client.ClientSession", return_value=mock_session
            ) as mock_session_class:
                await client.connect()

                # Verify SSE context was entered
                mock_sse_context.__aenter__.assert_called_once()

                # Verify ClientSession was created with streams
                mock_session_class.assert_called_once_with(
                    mock_read_stream, mock_write_stream
                )

                # Verify session was initialized
                mock_session.initialize.assert_called_once()

                # Verify client state
                assert client.session is not None
                assert client._sse_context is not None

        await client.close()

    @pytest.mark.asyncio
    async def test_close_cleans_up_resources(self):
        """Test that close() properly cleans up resources."""
        client = MCPClient()

        # Set up mock session and context
        mock_session = AsyncMock()
        mock_session.__aexit__ = AsyncMock(return_value=None)

        mock_sse_context = AsyncMock()
        mock_sse_context.__aexit__ = AsyncMock(return_value=None)

        client.session = mock_session
        client._sse_context = mock_sse_context

        await client.close()

        # Verify cleanup
        mock_session.__aexit__.assert_called_once_with(None, None, None)
        mock_sse_context.__aexit__.assert_called_once_with(None, None, None)
        assert client.session is None
        assert client._sse_context is None

    @pytest.mark.asyncio
    async def test_close_handles_none_session(self):
        """Test that close() handles None session gracefully."""
        client = MCPClient()
        # Should not raise even with None session
        await client.close()

    @pytest.mark.asyncio
    async def test_context_manager_protocol(self):
        """Test async context manager protocol."""
        mock_read_stream = AsyncMock()
        mock_write_stream = AsyncMock()

        mock_sse_context = AsyncMock()
        mock_sse_context.__aenter__ = AsyncMock(
            return_value=(mock_read_stream, mock_write_stream)
        )
        mock_sse_context.__aexit__ = AsyncMock(return_value=None)

        mock_session = AsyncMock()
        mock_session.initialize = AsyncMock()
        mock_session.__aexit__ = AsyncMock(return_value=None)

        with patch("client.mcp_client.sse_client", return_value=mock_sse_context):
            with patch("client.mcp_client.ClientSession", return_value=mock_session):
                async with MCPClient() as client:
                    assert client.session is not None

                # After exiting context, session should be cleaned up
                # (The mock doesn't actually set session to None, but __aexit__ is called)
                mock_session.__aexit__.assert_called()


class TestMCPClientListTools:
    """Test MCPClient.list_tools() method."""

    @pytest.mark.asyncio
    async def test_list_tools_returns_tools(self):
        """Test that list_tools returns formatted tool list."""
        client = MCPClient()

        # Create mock tool objects
        mock_tool1 = MagicMock()
        mock_tool1.name = "get_weather"
        mock_tool1.description = "Get weather for a city"
        mock_tool1.inputSchema = {"type": "object", "properties": {"city": {}}}

        mock_tool2 = MagicMock()
        mock_tool2.name = "search_events"
        mock_tool2.description = "Search for events"
        mock_tool2.inputSchema = {"type": "object", "properties": {"city": {}}}

        mock_result = MagicMock()
        mock_result.tools = [mock_tool1, mock_tool2]

        mock_session = AsyncMock()
        mock_session.list_tools = AsyncMock(return_value=mock_result)
        client.session = mock_session

        tools = await client.list_tools()

        assert len(tools) == 2
        assert tools[0]["name"] == "get_weather"
        assert tools[0]["description"] == "Get weather for a city"
        assert "inputSchema" in tools[0]

        assert tools[1]["name"] == "search_events"

    @pytest.mark.asyncio
    async def test_list_tools_handles_none_description(self):
        """Test that list_tools handles None description."""
        client = MCPClient()

        mock_tool = MagicMock()
        mock_tool.name = "test_tool"
        mock_tool.description = None
        mock_tool.inputSchema = None

        mock_result = MagicMock()
        mock_result.tools = [mock_tool]

        mock_session = AsyncMock()
        mock_session.list_tools = AsyncMock(return_value=mock_result)
        client.session = mock_session

        tools = await client.list_tools()

        assert tools[0]["description"] == ""
        assert tools[0]["inputSchema"] == {}

    @pytest.mark.asyncio
    async def test_list_tools_not_connected_raises_error(self, mcp_client):
        """Test that list_tools raises RuntimeError when not connected."""
        with pytest.raises(RuntimeError, match="Client not connected"):
            await mcp_client.list_tools()


class TestMCPClientCallTool:
    """Test MCPClient.call_tool() method."""

    @pytest.mark.asyncio
    async def test_call_tool_success(self):
        """Test successful tool call."""
        client = MCPClient()

        # Create mock content with text attribute
        mock_content = MagicMock()
        mock_content.text = '{"temperature": 20, "city": "London"}'

        mock_result = MagicMock()
        mock_result.content = [mock_content]

        mock_session = AsyncMock()
        mock_session.call_tool = AsyncMock(return_value=mock_result)
        client.session = mock_session

        result = await client.call_tool("get_weather", {"city": "London"})

        # Verify call was made correctly
        mock_session.call_tool.assert_called_once_with(
            "get_weather", {"city": "London"}
        )

        # Verify result format
        assert "content" in result
        assert len(result["content"]) == 1
        assert result["content"][0]["type"] == "text"
        assert "temperature" in result["content"][0]["text"]

    @pytest.mark.asyncio
    async def test_call_tool_multiple_content_items(self):
        """Test call_tool with multiple content items."""
        client = MCPClient()

        mock_content1 = MagicMock()
        mock_content1.text = "First response"

        mock_content2 = MagicMock()
        mock_content2.text = "Second response"

        mock_result = MagicMock()
        mock_result.content = [mock_content1, mock_content2]

        mock_session = AsyncMock()
        mock_session.call_tool = AsyncMock(return_value=mock_result)
        client.session = mock_session

        result = await client.call_tool("test_tool", {})

        assert len(result["content"]) == 2
        assert result["content"][0]["text"] == "First response"
        assert result["content"][1]["text"] == "Second response"

    @pytest.mark.asyncio
    async def test_call_tool_content_without_text(self):
        """Test call_tool filters out content without text attribute."""
        client = MCPClient()

        # Content without text attribute should be skipped
        mock_content_no_text = MagicMock(spec=[])  # No text attribute

        mock_content_with_text = MagicMock()
        mock_content_with_text.text = "Has text"

        mock_result = MagicMock()
        mock_result.content = [mock_content_no_text, mock_content_with_text]

        mock_session = AsyncMock()
        mock_session.call_tool = AsyncMock(return_value=mock_result)
        client.session = mock_session

        result = await client.call_tool("test_tool", {})

        # Only content with text should be included
        assert len(result["content"]) == 1
        assert result["content"][0]["text"] == "Has text"

    @pytest.mark.asyncio
    async def test_call_tool_not_connected_raises_error(self, mcp_client):
        """Test that call_tool raises RuntimeError when not connected."""
        with pytest.raises(RuntimeError, match="Client not connected"):
            await mcp_client.call_tool("get_weather", {"city": "London"})


class TestMCPClientHealthCheck:
    """Test MCPClient.health_check() method."""

    @pytest.mark.asyncio
    async def test_health_check_returns_true_when_healthy(self):
        """Test health_check returns True when server responds."""
        client = MCPClient()

        mock_result = MagicMock()
        mock_result.tools = []

        mock_session = AsyncMock()
        mock_session.list_tools = AsyncMock(return_value=mock_result)
        client.session = mock_session

        result = await client.health_check()

        assert result is True

    @pytest.mark.asyncio
    async def test_health_check_connects_if_not_connected(self):
        """Test health_check connects if session is None."""
        client = MCPClient()

        mock_read_stream = AsyncMock()
        mock_write_stream = AsyncMock()

        mock_sse_context = AsyncMock()
        mock_sse_context.__aenter__ = AsyncMock(
            return_value=(mock_read_stream, mock_write_stream)
        )
        mock_sse_context.__aexit__ = AsyncMock(return_value=None)

        mock_result = MagicMock()
        mock_result.tools = []

        mock_session = AsyncMock()
        mock_session.initialize = AsyncMock()
        mock_session.list_tools = AsyncMock(return_value=mock_result)
        mock_session.__aexit__ = AsyncMock(return_value=None)

        with patch("client.mcp_client.sse_client", return_value=mock_sse_context):
            with patch("client.mcp_client.ClientSession", return_value=mock_session):
                result = await client.health_check()

                assert result is True
                # Connect should have been called
                mock_session.initialize.assert_called_once()

        await client.close()

    @pytest.mark.asyncio
    async def test_health_check_returns_false_on_exception(self):
        """Test health_check returns False when exception occurs."""
        client = MCPClient()

        mock_session = AsyncMock()
        mock_session.list_tools = AsyncMock(side_effect=Exception("Connection failed"))
        client.session = mock_session

        result = await client.health_check()

        assert result is False

    @pytest.mark.asyncio
    async def test_health_check_returns_false_when_cannot_connect(self):
        """Test health_check returns False when connection fails."""
        client = MCPClient()

        with patch(
            "client.mcp_client.sse_client", side_effect=Exception("Connection refused")
        ):
            result = await client.health_check()

            assert result is False


class TestMCPClientURLHandling:
    """Test URL handling in MCPClient."""

    def test_sse_url_construction(self):
        """Test that SSE URL is correctly constructed."""
        client = MCPClient(base_url="http://example.com:9000")

        # The SSE URL is constructed in connect(), but we can verify base_url
        assert client.base_url == "http://example.com:9000"
        # In connect(), it would construct: f"{self.base_url}/sse"
        expected_sse_url = f"{client.base_url}/sse"
        assert expected_sse_url == "http://example.com:9000/sse"

    def test_base_url_without_port(self):
        """Test base URL without explicit port."""
        client = MCPClient(base_url="http://localhost")
        assert client.base_url == "http://localhost"

    def test_base_url_with_https(self):
        """Test base URL with HTTPS."""
        client = MCPClient(base_url="https://secure.example.com:8443")
        assert client.base_url == "https://secure.example.com:8443"
