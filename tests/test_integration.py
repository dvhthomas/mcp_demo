"""
End-to-end integration test.

This script tests the complete integration:
1. MCP Server (FastMCP with SSE) - runs in background
2. MCP Client - connects via SSE and gets tools
3. LangChain MCP Adapters - official package integration

Run this to verify everything works before starting Ollama.
"""

import asyncio
import multiprocessing
import sys
import time
from pathlib import Path

import httpx
import uvicorn

# Add project root to Python path when running directly
# This allows uvicorn to import "server.server:app"
if __name__ == "__main__":
    project_root = Path(__file__).parent.parent
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))


def run_server():
    """Run MCP server in background process."""
    # Ensure project root is in Python path for this subprocess
    project_root = Path(__file__).parent.parent
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

    uvicorn.run("server.server:app", host="127.0.0.1", port=8000, log_level="error")


async def test_integration():
    """Test the integration."""
    print("=" * 70)
    print("END-TO-END INTEGRATION TEST")
    print("=" * 70)

    # Step 1: Start MCP server in background
    print("\n[1/4] Starting MCP server...")
    server_process = multiprocessing.Process(target=run_server, daemon=True)
    server_process.start()
    time.sleep(2)  # Give server time to start

    try:
        # Step 2: Test MCP server health
        print("[2/4] Testing MCP server health...")
        async with httpx.AsyncClient() as client:
            response = await client.get("http://localhost:8000/health")
            if response.status_code == 200:
                print("      ✓ MCP server is healthy")
            else:
                print("      ✗ MCP server health check failed")
                return False

        # Step 3: Test MCP client via SSE
        print("[3/4] Testing MCP client SSE connection...")
        try:
            from langchain_mcp_adapters.client import MultiServerMCPClient

            # Create client
            client = MultiServerMCPClient(
                {
                    "mcp-tools": {
                        "url": "http://localhost:8000/sse",
                        "transport": "sse",
                    }
                }
            )

            # Get tools
            tools = await client.get_tools()
            print(f"      ✓ Found {len(tools)} tools via langchain-mcp-adapters")
            for tool in tools:
                print(f"        - {tool.name}: {tool.description[:60]}...")

            # Note: MultiServerMCPClient doesn't require explicit cleanup

        except Exception as e:
            print(f"      ✗ MCP client connection failed: {e}")
            import traceback

            traceback.print_exc()
            return False

        # Step 4: Verify tool structure
        print("[4/4] Verifying tool structure...")
        if len(tools) == 2:
            print("      ✓ Expected 2 tools found")
            tool_names = {tool.name for tool in tools}
            expected_names = {"get_weather", "search_events"}
            if tool_names == expected_names:
                print(f"      ✓ Tool names match expected: {expected_names}")
            else:
                print(f"      ✗ Tool names mismatch. Got: {tool_names}")
                return False
        else:
            print(f"      ✗ Expected 2 tools, got {len(tools)}")
            return False

        print("\n" + "=" * 70)
        print("✓ ALL INTEGRATION TESTS PASSED!")
        print("=" * 70)
        print("\nNext steps to run full agent:")
        print("  1. Ensure Ollama is running: ollama serve")
        print("  2. Ensure model is downloaded: ollama pull llama3.2:3b")
        print("  3. Start MCP server: uv run python main.py")
        print("  4. Run agent: uv run python client/agent.py")
        print("=" * 70)
        return True

    finally:
        # Cleanup
        server_process.terminate()
        server_process.join(timeout=1)


if __name__ == "__main__":
    success = asyncio.run(test_integration())
    exit(0 if success else 1)
