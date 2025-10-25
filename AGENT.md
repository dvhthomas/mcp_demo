This is a Python project to help students new to Agent-based engineering.

- All dependencies are managed using uv.
- All new code should be covered by tests.
- The README.md must be kept up-to-date so that new users can get up and running quickly, without errors.
- uv is equipped with tools to enforce coding standards.
- There are three main elements to the project:
    - /client - The Agent client that demonstrates the ReACT pattern.
    - /server The MCP Server used to provide tools.
      - This also demonstrates how a generic function (or API) can be adapted to work with the MCP Server.
    - The LLM. This is handled by Ollama.
