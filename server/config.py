"""
Configuration constants for the MCP Demo server and client.

This module centralizes all configuration values to make them
easy to find and modify. Using named constants instead of magic
numbers makes the code more self-documenting.
"""

# Server Configuration
DEFAULT_SERVER_HOST = "0.0.0.0"
DEFAULT_SERVER_PORT = 8000

# Tool Configuration
DEFAULT_MAX_EVENT_RESULTS = 5

# Agent Configuration
DEFAULT_LLM_TEMPERATURE = 0.0
DEFAULT_MODEL_NAME = "llama3.2:3b"
DEFAULT_MCP_SERVER_URL = "http://localhost:8000"
