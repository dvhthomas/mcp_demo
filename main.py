"""
Main entry point for the MCP Tools Server.

This script starts the FastAPI server with uvicorn.
"""

import uvicorn

from server.config import DEFAULT_SERVER_HOST, DEFAULT_SERVER_PORT


def main():
    """Start the MCP Tools Server."""
    uvicorn.run(
        "server.server:app",
        host=DEFAULT_SERVER_HOST,
        port=DEFAULT_SERVER_PORT,
        reload=True,
        log_level="info",
    )


if __name__ == "__main__":
    main()
