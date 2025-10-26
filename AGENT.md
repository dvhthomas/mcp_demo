# AI Agent Development Guide

This document provides guidance for AI coding agents working on this Python project. The project is designed to help students new to Agent-based engineering.

## Project Overview

This project demonstrates the integration of:
- **`/client`** - The Agent client that demonstrates the ReACT pattern
- **`/server`** - The MCP Server that provides tools to the agent
  - Also demonstrates how generic functions/APIs can be adapted to work with the MCP Server
- **LLM** - Handled by Ollama (llama3.2:3b model)

## Development Standards

### Dependency Management
- All dependencies are managed using **uv**
- Add new dependencies via `uv add <package>`
- Dev dependencies via `uv add --dev <package>`
- Never manually edit `pyproject.toml` dependencies

### Code Quality
- **All new code must be covered by tests**
- Use `uv run ruff check .` to enforce coding standards
- Use `uv run ruff format .` to format code consistently

### Documentation
- The **README.md must be kept up-to-date** so new users can get up and running quickly without errors
- Update TESTING.md when adding new tests
- Update ARCHITECTURE.md when making architectural changes

## Testing Requirements

### CRITICAL: Tests Must Pass Before Committing

**ALL tests must be run and pass before any git commit.**

This is non-negotiable because:
- Broken tests in the repo block other developers
- They create confusion about what actually works
- They undermine confidence in the codebase

### How to Run Tests

```bash
# Run all tests (required before every commit)
uv run pytest

# Run specific test suites
uv run pytest tests/server/          # Unit tests only
uv run python tests/test_integration.py  # Integration test only

# Run with verbose output for debugging
uv run pytest -v
```

### What Must Pass

Before committing, verify:
1. ✅ All unit tests pass: `uv run pytest tests/server/`
2. ✅ Integration test passes: `uv run python tests/test_integration.py`
3. ✅ Full test suite passes: `uv run pytest`
4. ✅ No ruff errors: `uv run ruff check .`

### Test Writing Guidelines

When adding new functionality:
1. **Write tests first** (TDD approach recommended)
2. **Test both success and failure cases**
3. **Use pytest fixtures** for common test setup
4. **Mark slow tests** with `@pytest.mark.slow`
5. **Mark integration tests** with `@pytest.mark.integration`

Example:
```python
@pytest.mark.asyncio
async def test_new_feature_success():
    """Test that new feature works correctly."""
    # Arrange
    tool = NewTool()

    # Act
    result = await tool.execute({"param": "value"})

    # Assert
    assert "expected_key" in result
```

## Git Workflow

### Before Committing

1. **Run all tests**: `uv run pytest`
2. **Check for linting errors**: `uv run ruff check .`
3. **Verify integration test**: `uv run python tests/test_integration.py`
4. **Review changed files**: `git status` and `git diff`

### Commit Message Format

Follow conventional commit style:
```
<type>: <short description>

<detailed description>

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>
```

Types: `feat`, `fix`, `docs`, `test`, `refactor`, `chore`

## Common Tasks

### Adding a New MCP Tool

1. Create tool in `/server/tools/`
2. Create adapter in `/server/mcp_adapters.py`
3. Register in `/server/server.py`
4. Write unit tests in `/tests/server/`
5. Run tests: `uv run pytest`
6. Update ARCHITECTURE.md

### Modifying the Agent

1. Edit `/client/agent.py`
2. Test manually with: `uv run python client/agent.py`
3. Ensure integration test still passes
4. Update AGENT_README.md if behavior changes

### Updating Dependencies

1. Add: `uv add <package>` or `uv add --dev <package>`
2. Remove: `uv remove <package>`
3. Update: `uv sync`
4. Test: `uv run pytest`
5. Commit `pyproject.toml` and `uv.lock`

## Troubleshooting

### Tests Failing After Changes

1. Check import errors: Ensure Python path is correct
2. Check for port conflicts: Kill processes on port 8000
3. Review test output: `uv run pytest -v`
4. Run individual test: `uv run pytest tests/server/test_adapters.py::TestWeatherToolMCPAdapter::test_execute_success`

### Integration Test Fails

Common causes:
- Server can't start (port 8000 in use): `lsof -ti :8000 | xargs kill -9`
- Import errors (missing dependencies): `uv sync`
- Network issues (weather/events APIs down): Check internet connection

## Resources

- **MCP SDK**: https://github.com/anthropics/anthropic-sdk-python
- **LangGraph**: https://langchain-ai.github.io/langgraph/
- **uv Documentation**: https://github.com/astral-sh/uv
- **pytest Documentation**: https://docs.pytest.org/
