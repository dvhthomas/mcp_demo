# Quick Start Guide

Get up and running with the MCP Tools Server in 60 seconds!

## 1. Install Dependencies

```bash
uv sync
```

## 2. Test the Tools

Run the example script to verify everything works:

```bash
uv run python example.py
```

You should see weather data for Paris and event listings for New York.

## 3. Start the Server

```bash
uv run python main.py
```

The server will start on `http://localhost:8000`

## 4. Try the API

Open a new terminal and test the endpoints:

### Get Weather
```bash
curl -X POST http://localhost:8000/mcp/tools/call \
  -H "Content-Type: application/json" \
  -d '{"name": "get_weather", "arguments": {"city": "Tokyo"}}'
```

### Search Events
```bash
curl -X POST http://localhost:8000/mcp/tools/call \
  -H "Content-Type: application/json" \
  -d '{"name": "search_events", "arguments": {"city": "London", "max_results": 3}}'
```

## 5. Explore the Code

- **Weather Tool**: `src/tools/weather_tool.py`
- **Events Tool**: `src/tools/events_tool.py`
- **Server**: `src/server.py`

Each file is well-documented with comprehensive docstrings!

## Next Steps

- Read the full [README.md](README.md) for detailed documentation
- Customize the tools for your needs
- Add your own tools following the same pattern

Happy coding!
