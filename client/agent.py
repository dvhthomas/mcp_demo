"""
LangGraph ReACT Agent - AI agent that uses MCP tools via ReACT pattern.

This script creates a LangGraph ReACT (Reasoning and Acting) agent that:
1. Connects to an MCP server to discover available tools
2. Uses Ollama with llama3.2:3b for reasoning
3. Executes user queries by reasoning about which tools to use
4. Provides an interactive CLI interface

The ReACT pattern enables the agent to:
- Reason about what actions to take
- Act by using tools
- Observe the results
- Reason again based on observations

This implementation uses LangGraph, the modern framework for building agents,
which works natively with the official langchain-mcp-adapters package.
"""

import asyncio
import sys

from langchain.agents import create_agent
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_ollama import ChatOllama

# Client configuration - independent from server implementation
DEFAULT_LLM_TEMPERATURE = 0.0
DEFAULT_MODEL_NAME = "llama3.2:3b"
DEFAULT_MCP_SERVER_URL = "http://localhost:8000"


class MCPReactAgent:
    """
    ReACT agent that uses MCP tools for answering questions.

    This agent connects to an MCP server, discovers available tools,
    and uses them with a ReACT reasoning loop powered by Ollama.

    Attributes:
        mcp_base_url (str): URL of the MCP server
        model_name (str): Ollama model to use
        mcp_client: MCP client instance
        tools: List of LangChain tools
        agent: LangGraph ReACT agent
    """

    def __init__(
        self,
        mcp_base_url: str = DEFAULT_MCP_SERVER_URL,
        model_name: str = DEFAULT_MODEL_NAME,
        temperature: float = DEFAULT_LLM_TEMPERATURE,
        verbose: bool = True,
    ):
        """
        Initialize the ReACT agent.

        Args:
            mcp_base_url (str): Base URL of the MCP server
            model_name (str): Ollama model name
            temperature (float): LLM temperature (0.0 for deterministic)
            verbose (bool): Whether to print verbose output including prompts
        """
        self.mcp_base_url = mcp_base_url
        self.model_name = model_name
        self.temperature = temperature
        self.verbose = verbose
        self.mcp_client = None
        self.tools = None
        self.agent = None

    async def initialize(self):
        """
        Initialize the agent by connecting to MCP server and setting up tools.

        Raises:
            Exception: If unable to connect to MCP server or Ollama
        """
        print(f"Connecting to MCP server at {self.mcp_base_url}...")

        # Connect to MCP server using official LangChain adapter
        self.mcp_client = MultiServerMCPClient(
            {
                "mcp-tools": {
                    "url": f"{self.mcp_base_url}/sse",
                    "transport": "sse",
                }
            }
        )

        # Get MCP tools as LangChain tools
        self.tools = await self.mcp_client.get_tools()

        print(f"✓ Connected! Found {len(self.tools)} tools:")
        for tool in self.tools:
            print(f"  - {tool.name}: {tool.description}")

        print(f"\nInitializing Ollama with {self.model_name}...")

        # Initialize Ollama LLM
        llm = ChatOllama(
            model=self.model_name,
            temperature=self.temperature,
        )

        # Test Ollama connection
        try:
            await llm.ainvoke("test")
            print("✓ Ollama initialized successfully!")
        except Exception as e:
            raise Exception(
                f"Failed to connect to Ollama. Make sure Ollama is running "
                f"and {self.model_name} is installed.\nError: {e}"
            ) from e

        # Create LangGraph ReACT agent (handles prompt engineering and execution flow)
        self.agent = create_agent(llm, self.tools)

        print("\n" + "=" * 60)
        print("LangGraph ReACT Agent initialized and ready!")
        print("=" * 60)
        if self.verbose:
            print("\nℹ️  Verbose mode is ON - showing reasoning steps in real-time")
            print("   (use --quiet flag to show only final answers)")
        else:
            print("\nℹ️  Quiet mode - showing only final answers")
            print("   (remove --quiet flag to see reasoning steps)")

    async def query(self, question: str) -> str:
        """
        Process a user query using the ReACT agent.

        Args:
            question (str): User's question

        Returns:
            str: Agent's response

        Raises:
            RuntimeError: If agent is not initialized
        """
        if not self.agent:
            raise RuntimeError("Agent not initialized. Call initialize() first.")

        # In verbose mode, stream steps as they happen for real-time visibility
        if self.verbose:
            return await self._query_verbose(question)

        # Non-verbose mode: just get the result
        result = await self.agent.ainvoke({"messages": [("user", question)]})
        return result["messages"][-1].content

    async def _query_verbose(self, question: str) -> str:
        """
        Process query in verbose mode, streaming steps as they happen.

        This shows the ReACT loop in real-time, which is more educational
        than printing everything at the end.

        Args:
            question (str): User's question

        Returns:
            str: Agent's response
        """
        print("\n" + "=" * 60)
        print("REACT LOOP - Agent Reasoning Steps (Real-time)")
        print("=" * 60)

        step_number = 0
        final_messages = None

        # Stream agent execution to show steps as they happen
        async for chunk in self.agent.astream(
            {"messages": [("user", question)]}, stream_mode="values"
        ):
            # Each chunk contains the full state with all messages so far
            messages = chunk.get("messages", [])

            # Print only new messages (messages added since last chunk)
            if final_messages is None:
                # First chunk - print user message
                step_number += 1
                print(f"\n[Step {step_number}] User Question:")
                print("-" * 60)
                print(f"{question}")
            else:
                # Print any new messages
                for message in messages[len(final_messages) :]:
                    step_number += 1
                    self._print_message_step(message, step_number)

            final_messages = messages

        print("\n" + "=" * 60)

        # Return the final answer
        if final_messages:
            return final_messages[-1].content
        return ""

    def _print_message_step(self, message, step_number: int):
        """
        Print a single message step in the ReACT loop.

        Args:
            message: The message object to print
            step_number: Current step number
        """
        message_type = type(message).__name__
        role = (
            getattr(message, "type", None)
            or getattr(message, "role", None)
            or "unknown"
        )

        print(f"\n[Step {step_number}] {message_type} ({role}):")
        print("-" * 60)

        # Print message content
        if hasattr(message, "content"):
            if isinstance(message.content, str):
                print(message.content)
            elif isinstance(message.content, list):
                for item in message.content:
                    print(f"  {item}")
            else:
                print(message.content)

        # Show tool calls if present
        if hasattr(message, "tool_calls") and message.tool_calls:
            print("\n  Tool Calls:")
            for tool_call in message.tool_calls:
                tool_name = tool_call.get("name", "unknown")
                tool_args = tool_call.get("args", {})
                print(f"    - {tool_name}: {tool_args}")

    async def run_interactive(self):
        """
        Run an interactive CLI loop for querying the agent.

        The user can type questions, and the agent will respond using
        the ReACT pattern and available MCP tools.
        """
        print("\nInteractive mode - Type your questions (or 'quit' to exit)")
        print("-" * 60)

        while True:
            try:
                question = input("\nYou: ").strip()

                if not question:
                    continue

                if question.lower() in ["quit", "exit", "q"]:
                    print("\nGoodbye!")
                    break

                print()  # Empty line for readability
                answer = await self.query(question)

                print(f"\n{'=' * 60}")
                print(f"Final Answer: {answer}")
                print("=" * 60)

            except KeyboardInterrupt:
                print("\n\nGoodbye!")
                break
            except Exception as e:
                print(f"\nError: {e}")

    async def cleanup(self):
        """Clean up resources gracefully."""
        # MultiServerMCPClient doesn't require explicit cleanup
        # Connection cleanup happens automatically
        pass


async def main():
    """Main entry point for the agent."""
    import argparse

    parser = argparse.ArgumentParser(
        description="LangChain ReACT agent using MCP tools"
    )
    parser.add_argument(
        "--mcp-url",
        default=DEFAULT_MCP_SERVER_URL,
        help=f"MCP server URL (default: {DEFAULT_MCP_SERVER_URL})",
    )
    parser.add_argument(
        "--model",
        default=DEFAULT_MODEL_NAME,
        help=f"Ollama model name (default: {DEFAULT_MODEL_NAME})",
    )
    parser.add_argument(
        "--query",
        help="Single query to execute (instead of interactive mode)",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help=(
            "Disable verbose output - only show final answer "
            "(by default, shows the ReACT reasoning loop in real-time)"
        ),
    )

    args = parser.parse_args()

    # Create and initialize agent
    agent = MCPReactAgent(
        mcp_base_url=args.mcp_url, model_name=args.model, verbose=not args.quiet
    )

    try:
        await agent.initialize()

        if args.query:
            # Single query mode
            print(f"\nQuestion: {args.query}\n")
            answer = await agent.query(args.query)
            print(f"\n{'=' * 60}")
            print(f"Final Answer: {answer}")
            print("=" * 60)
        else:
            # Interactive mode
            await agent.run_interactive()

    except KeyboardInterrupt:
        # Handle Ctrl+C gracefully without traceback
        print("\n\nInterrupted. Cleaning up...")
    except Exception as e:
        print(f"\nError: {e}", file=sys.stderr)
        return 1
    finally:
        try:
            await agent.cleanup()
        except Exception:
            # Suppress cleanup errors for clean exit
            pass

    return 0


if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        # Final safety net for Ctrl+C during asyncio.run
        sys.exit(0)
