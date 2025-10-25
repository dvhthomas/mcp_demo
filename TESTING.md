# Testing Guide - End-to-End Verification

## Quick Verification (No Ollama Required)

Run the integration test to verify everything works:

```bash
uv run python test_end_to_end.py
```

This tests:
- ✅ MCP Server (FastAPI) starts and responds
- ✅ MCP Client can connect and list tools
- ✅ LangChain tool conversion works
- ✅ ZeroShotAgent.create_prompt() works

## Full End-to-End Test (With Ollama)

### Prerequisites

1. **Install Ollama** (if not already installed):
   - Visit https://ollama.ai
   - Download and install for your platform
   - Verify: `ollama --version`

2. **Start Ollama server**:
   ```bash
   ollama serve
   ```
   Keep this running in a terminal.

3. **Download the model** (in a new terminal):
   ```bash
   ollama pull llama3.2:3b
   ```
   This downloads ~2GB. Wait for completion.

4. **Verify model is available**:
   ```bash
   ollama list
   ```
   You should see `llama3.2:3b` in the list.

### Step-by-Step Test

**Terminal 1: Start MCP Server**
```bash
cd mcp_demo
uv run python main.py
```

You should see:
```
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000
```

**Terminal 2: Test Agent (Interactive Mode)**
```bash
cd mcp_demo
uv run python agent.py
```

You should see:
```
Connecting to MCP server at http://localhost:8000...
✓ Connected! Found 2 tools:
  - get_weather: Get current weather information for any city in the world
  - search_events: Search for events happening today in a specified city using DuckDuckGo

Initializing Ollama with llama3.2:3b...
✓ Ollama initialized successfully!

============================================================
ZeroShotAgent (MRKL) initialized and ready!
============================================================

Interactive mode - Type your questions (or 'quit' to exit)
------------------------------------------------------------

You:
```

**Test Queries:**

1. Simple weather query:
   ```
   You: What's the weather in Paris?
   ```

2. Events query:
   ```
   You: What events are happening in New York today?
   ```

3. Combined query (tests multi-tool reasoning):
   ```
   You: What's the weather in London and what events are happening there today?
   ```

**Terminal 3: Test Single Query Mode**
```bash
uv run python agent.py --query "What's the temperature in Tokyo?"
```

**Terminal 4: Test Verbose Mode**
```bash
uv run python agent.py --verbose
```

This shows the ZeroShotAgent system prompt.

## Expected Behavior

### Successful Weather Query

```
You: What's the weather in Paris?

> Entering new AgentExecutor chain...
Thought: I need to get weather information for Paris
Action: get_weather
Action Input: {"city": "Paris"}
Observation: {'city': 'Paris', 'country': 'France', 'temperature': 12.0, ...}
Thought: I now know the final answer
Final Answer: The current weather in Paris, France is 12.0°C with wind speed of 13.8 km/h.

============================================================
Final Answer: The current weather in Paris, France is 12.0°C with wind speed of 13.8 km/h.
============================================================
```

### Successful Events Query

```
You: Find events in Berlin today

> Entering new AgentExecutor chain...
Thought: I should search for events happening in Berlin today
Action: search_events
Action Input: {"city": "Berlin", "max_results": 5}
Observation: {'city': 'Berlin', 'date': '2025-10-25', 'results_count': 5, ...}
Thought: I now know the final answer
Final Answer: Here are events happening in Berlin today: [list of events]

============================================================
Final Answer: Here are events happening in Berlin today: ...
============================================================
```

## Troubleshooting

### Error: "Failed to connect to Ollama"

**Cause**: Ollama server is not running or model not installed.

**Solution**:
```bash
# Terminal 1: Start Ollama
ollama serve

# Terminal 2: Verify model
ollama list

# If model not listed:
ollama pull llama3.2:3b
```

### Error: "MCP server at http://localhost:8000 is not healthy"

**Cause**: MCP server not running.

**Solution**:
```bash
# Start MCP server
uv run python main.py
```

### Agent gets stuck or times out

**Possible causes**:
- Ollama model too slow (try smaller model: `--model llama3.2:1b`)
- Network issues with API calls
- Max iterations reached

**Solutions**:
```bash
# Use smaller/faster model
uv run python agent.py --model llama3.2:1b

# Check MCP server logs for API errors
# Check agent verbose output
uv run python agent.py --verbose
```

### Tools return errors

**Weather Tool**: "City not found"
- Try including country: "Paris, France"
- Check spelling

**Events Tool**: No results
- DuckDuckGo might be rate limiting
- Try different city
- Check internet connection

## Component-Level Testing

### Test 1: MCP Server Only

```bash
# Start server
uv run python main.py

# In another terminal, test with curl
curl http://localhost:8000/health
curl http://localhost:8000/mcp/tools/list
curl -X POST http://localhost:8000/mcp/tools/call \
  -H "Content-Type: application/json" \
  -d '{"name": "get_weather", "arguments": {"city": "Paris"}}'
```

### Test 2: Tools Directly (No MCP, No Agent)

```bash
uv run python example.py
```

This tests the business logic tools without any MCP or agent overhead.

### Test 3: MCP Client Only

```bash
uv run python << 'EOF'
import asyncio
from mcp_client import MCPClient

async def test():
    async with MCPClient("http://localhost:8000") as client:
        tools = await client.list_tools()
        print(f"Found {len(tools)} tools")

        result = await client.call_tool("get_weather", {"city": "London"})
        print("Weather result:", result)

asyncio.run(test())
EOF
```

### Test 4: LangChain Tools Only

```bash
uv run python << 'EOF'
import asyncio
from langchain_mcp_tools import get_mcp_tools_for_langchain

async def test():
    client, tools = await get_mcp_tools_for_langchain("http://localhost:8000")
    print(f"Converted {len(tools)} tools to LangChain format")
    for tool in tools:
        print(f"  - {tool.name}: {tool.description}")
    await client.close()

asyncio.run(test())
EOF
```

## Performance Expectations

**First query (cold start)**: 5-15 seconds
- LLM needs to load and reason
- API calls to weather/events services

**Subsequent queries**: 3-8 seconds
- LLM already loaded
- Faster reasoning

**Model sizes**:
- `llama3.2:1b` - Fastest, less accurate (~1-2s per query)
- `llama3.2:3b` - Balanced (~3-5s per query) ← **Recommended**
- `llama3:8b` - Most accurate, slower (~8-15s per query)

## Success Criteria

✅ MCP server starts without errors
✅ Agent connects to MCP server
✅ Agent discovers 2 tools (get_weather, search_events)
✅ Ollama initializes successfully
✅ Agent can answer weather questions
✅ Agent can answer events questions
✅ Agent can handle multi-tool questions
✅ Agent returns proper "Final Answer" format
✅ No crashes or hangs

## Clean Shutdown

1. In agent terminal: Type `quit` or press Ctrl+C
2. In MCP server terminal: Press Ctrl+C
3. Ollama can keep running (or: `killall ollama` on macOS/Linux)

## Next Steps After Testing

- Try different cities and queries
- Experiment with `--verbose` to see reasoning
- Try different Ollama models
- Add your own custom tools to the MCP server
- Modify the agent's behavior
