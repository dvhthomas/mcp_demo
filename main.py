"""
Main entry point for the MCP Tools Server.

This script starts the FastAPI server with uvicorn.
"""

import uvicorn


def main():
    """Start the MCP Tools Server."""
    uvicorn.run(
        "src.server:app", host="0.0.0.0", port=8000, reload=True, log_level="info"
    )


if __name__ == "__main__":
    main()
