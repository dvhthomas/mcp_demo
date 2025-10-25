"""
MCP Client - A client for communicating with an MCP server using the official SDK.

This module provides an MCPClient class that uses the official MCP Python SDK
to communicate with an MCP server via SSE (Server-Sent Events).

The client can:
1. Connect to an MCP server via SSE
2. List available tools
3. Call tools with arguments
4. Maintain an active session with the server

This implementation uses the official mcp.client.ClientSession for proper
MCP protocol compliance.
"""

from typing import Any

from mcp import ClientSession
from mcp.client.sse import sse_client


class MCPClient:
    """
    A client for connecting to and interacting with an MCP server
    using the official SDK.

    This class provides methods to list tools and call tools via the MCP protocol
    using SSE (Server-Sent Events) transport.

    Attributes:
        base_url (str): The base URL of the MCP server
        session (ClientSession | None): The active MCP client session
        _read_stream: Internal read stream for MCP messages
        _write_stream: Internal write stream for MCP messages
    """

    def __init__(self, base_url: str = "http://localhost:8000"):
        """
        Initialize the MCP client.

        Args:
            base_url (str): Base URL of the MCP server (default: http://localhost:8000)
        """
        self.base_url = base_url.rstrip("/")
        self.session: ClientSession | None = None
        self._read_stream = None
        self._write_stream = None
        self._sse_context = None

    async def __aenter__(self):
        """Async context manager entry - establishes connection."""
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit - closes connection."""
        await self.close()

    async def connect(self):
        """
        Connect to the MCP server and initialize the session.

        This establishes an SSE connection to the server's /sse endpoint
        and initializes the MCP protocol session.

        Raises:
            Exception: If connection or initialization fails
        """
        # Connect via SSE to the MCP server
        sse_url = f"{self.base_url}/sse"

        # Use sse_client as a context manager to get streams
        self._sse_context = sse_client(sse_url)
        self._read_stream, self._write_stream = await self._sse_context.__aenter__()

        # Create ClientSession with the streams
        self.session = ClientSession(self._read_stream, self._write_stream)

        # Initialize the MCP session
        await self.session.initialize()

    async def close(self):
        """Close the MCP client session and SSE connection."""
        if self.session:
            await self.session.__aexit__(None, None, None)
            self.session = None

        if self._sse_context:
            await self._sse_context.__aexit__(None, None, None)
            self._sse_context = None

    async def health_check(self) -> bool:
        """
        Check if the MCP server is healthy.

        This attempts to connect to the server and list tools as a health check.

        Returns:
            bool: True if server is healthy, False otherwise
        """
        try:
            if self.session is None:
                await self.connect()

            # Type narrowing: after connect(), session is guaranteed to be non-None
            assert self.session is not None

            # Try to list tools as a health check
            await self.session.list_tools()
            return True
        except Exception:
            return False

    async def list_tools(self) -> list[dict[str, Any]]:
        """
        List all available tools from the MCP server.

        Returns:
            list[dict[str, Any]]: List of tool definitions with name,
                description, and inputSchema

        Raises:
            RuntimeError: If session is not connected
            Exception: If the request fails
        """
        if self.session is None:
            raise RuntimeError(
                "Client not connected. Call connect() or use as context manager."
            )

        # Use the official SDK's list_tools method
        result = await self.session.list_tools()

        # Convert Tool objects to dictionaries for compatibility
        tools = []
        for tool in result.tools:
            tools.append(
                {
                    "name": tool.name,
                    "description": tool.description or "",
                    "inputSchema": tool.inputSchema or {},
                }
            )

        return tools

    async def call_tool(
        self, tool_name: str, arguments: dict[str, Any]
    ) -> dict[str, Any]:
        """
        Call a tool on the MCP server with the given arguments.

        Args:
            tool_name (str): Name of the tool to call
            arguments (dict[str, Any]): Arguments to pass to the tool

        Returns:
            dict[str, Any]: Result from the tool execution in MCP format:
                {"content": [{"type": "text", "text": "..."}]}

        Raises:
            RuntimeError: If session is not connected
            Exception: If the request fails
        """
        if self.session is None:
            raise RuntimeError(
                "Client not connected. Call connect() or use as context manager."
            )

        # Use the official SDK's call_tool method
        result = await self.session.call_tool(tool_name, arguments)

        # Convert CallToolResult to dictionary format
        content_items = []
        for content in result.content:
            if hasattr(content, "text"):
                content_items.append(
                    {
                        "type": "text",
                        "text": content.text,
                    }
                )

        return {"content": content_items}
