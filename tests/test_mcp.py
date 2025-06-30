import pytest
import json
from agentic.common import Agent, AgentRunner
from agentic.tools.mcp_tool import MCPTool

"""
A note on this testing approach:

The Sequential Thinking MCP displays its "Thought" steps directly to stderr in a formatted way,
but doesn't actually return them as part of the response or include them in the final agent output.

2. Standard pytest stderr/stdout capturing doesn't work well with the MCP server's output because
   it's coming from a subprocess that uses its own piping mechanism.

A "TrackedMCPTool" class that monitors the actual API calls to the
Sequential Thinking MCP is used rather than trying to capture the stderr output. This lets us verify:
   - The tool is actually being called
   - It's receiving proper arguments (thoughts, thoughtNumber, etc.)
   - The thinking process is happening correctly
"""

class TrackedMCPTool(MCPTool):
    """A wrapper around MCPTool that tracks tool calls and their results for testing"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.tool_calls = []
        self.tool_results = []
        self._original_call_tool = self.call_tool
        
        # Override the call_tool method to track what's happening
        async def tracked_call_tool(openai_tool):
            # Keep track of what tools are being called and with what arguments
            func_name = openai_tool["function"]["name"]
            args = json.loads(openai_tool["function"]["arguments"])
            self.tool_calls.append({
                "function": func_name,
                "arguments": args
            })
            
            # Let the original method do its thing
            result = await self._original_call_tool(openai_tool)
            
            # Save the result for later analysis
            self.tool_results.append(result)
            
            # Show what's happening for easier debugging
            print(f"Tool call: {func_name} with args {args}")
            print(f"Tool result (first 100 chars): {str(result)[:100]}")
            
            return result
            
        self.call_tool = tracked_call_tool
    
    def get_tracked_calls(self):
        """Returns the history of tools that were called"""
        return self.tool_calls
    
    def get_tool_results(self):
        """Returns the results that came back from the tool calls"""
        return self.tool_results
    
    def was_sequential_thinking_used(self):
        """Checks if the agent actually used sequential thinking with proper arguments"""
        for call in self.tool_calls:
            if (call["function"] == "sequentialthinking" and
                "thought" in call["arguments"] and
                "thoughtNumber" in call["arguments"]):
                return True
        return False
    
    def was_fetch_used(self):
        """Checks if the fetch tool was used with proper arguments"""
        for call in self.tool_calls:
            if call["function"] == "fetch" and "url" in call["arguments"]:
                return True
        return False
    
    def get_final_thoughts(self):
        """Extracts the thinking steps from the tool call history"""
        thoughts = []
        for call in self.tool_calls:
            if call["function"] == "sequentialthinking":
                thought_text = call["arguments"].get("thought", "")
                thought_num = call["arguments"].get("thoughtNumber", "")
                thoughts.append(f"Thought {thought_num}: {thought_text}")
        return thoughts

def create_sequential_thinker():
    """Creates our special tracking version of the Sequential Thinking tool"""
    try:
        return TrackedMCPTool(
            command="npx",
            args=["-y", "@modelcontextprotocol/server-sequential-thinking"]
        )
    except Exception as e:
        print(f"Error initializing Sequential Thinking MCP: {e}")
        return None

def create_fetch_tool():
    """Creates a fetch tool for web content retrieval testing"""
    try:
        return TrackedMCPTool(
            command="uvx",
            args=["mcp-server-fetch"]
        )
    except Exception as e:
        print(f"Error initializing Fetch MCP: {e}")
        return None

@pytest.mark.requires_llm
def test_sequential_thinking_mpc():
    """
    Tests the Sequential Thinking MCP tool to verify it works correctly.
    
    This test checks that:
    1. The tool is called with proper arguments
    2. The thinking process completes with multiple steps
    3. The final answer/calculation is correct
    """
    # Create our tracking version of the sequential thinking tool
    sequential_thinker = create_sequential_thinker()
    
    # Set up an agent that uses sequential thinking
    agent = Agent(
        name="Sequential Thinker",
        welcome="I am an agent that can help break down complex problems into steps.",
        instructions="""You are a helpful assistant that breaks down complex problems into 
        manageable steps using sequential thinking. Use the sequential_thinking tool to
        structure your approach to solving problems.
        
        After using sequential thinking, make sure to provide a final answer that includes
        the result of the calculation. Even if the sequential_thinking tool doesn't return a final result,
        YOU must explicitly state the final answer.""",
        model="openai/gpt-4o",
        tools=[sequential_thinker],
    )
    
    # Ask the agent to solve a simple multiplication problem using sequential thinking
    agent_runner = AgentRunner(agent)
    response = agent_runner.run("What is 25 * 4? use sequential thinking to solve this and provide the final answer")
    

    
    # Show the thinking steps for easier debugging
    final_thoughts = sequential_thinker.get_final_thoughts()
    print("\nThoughts from sequential thinking:")
    for thought in final_thoughts:
        print(f"- {thought}")
    
    # Make sure sequential thinking was actually used
    assert sequential_thinker.was_sequential_thinking_used(), "The agent didn't use sequential thinking properly"
    assert len(sequential_thinker.get_tracked_calls()) > 0, "The sequential thinking tool wasn't called at all"
    
    # Show all the tool calls for debugging
    for i, call in enumerate(sequential_thinker.get_tracked_calls()):
        print(f"Call {i+1}: {call['function']} with args: {call['arguments']}")
    
    # The response might be empty, but we can still verify sequential thinking worked
    # We'll check either the response OR the thoughts themselves
    if not any(term in response.lower() for term in ["100", "one hundred"]):
        # If the response is empty, make sure enough thinking happened
        assert len(final_thoughts) >= 3, "Not enough thinking steps were completed"
        
        # And check if the final thought has the answer
        final_thought = final_thoughts[-1] if final_thoughts else ""
        assert any(term in final_thought.lower() for term in ["80 + 20", "100"]), \
            f"The final thought doesn't contain the right answer: {final_thought}"
    
    # Make sure we didn't get any tool errors
    assert "tool_error" not in response.lower(), "Tool error found in the response"

@pytest.mark.requires_llm
def test_fetch_mcp():
    """Tests the Fetch MCP tool for retrieving web content"""
    # Create a regular fetch tool
    fetch_tool = create_fetch_tool()
    
    # Set up an agent that can fetch web content
    agent = Agent(
        name="Web Content Assistant",
        welcome="I am an agent that can retrieve and summarize web content for you.",
        instructions="""You are a helpful assistant that can fetch web content.
        Use the fetch tool to retrieve the content from the given URL and provide a brief summary.""",
        model="openai/gpt-4o",
        tools=[fetch_tool],
    )
    
    # Ask the agent to fetch a simple, stable webpage
    agent_runner = AgentRunner(agent)
    response = agent_runner.run("Fetch https://www.york.ac.uk/teaching/cws/wws/webpage1.html")
    
    # Check that we got something relevant back
    assert any(term in response.lower() for term in ["html", "web", "page"]), response

@pytest.mark.requires_llm
def test_multiple_mcp_tools():
    """
    Tests the combination of Fetch and Sequential Thinking tools.
    
    This test verifies that an agent can:
    1. Use the fetch tool to retrieve web content
    2. Use sequential thinking to analyze the content
    3. Provide an answer that combines both tool outputs
    """
    # Create tracking versions of both tools
    sequential_thinker = create_sequential_thinker()
    fetch_tool = create_fetch_tool()
    
    # Create an agent with both tools
    agent = Agent(
        name="Combined Tools Agent",
        welcome="I can analyze web content using sequential thinking.",
        instructions="""You are a helpful assistant that can fetch web content and analyze it
        using sequential thinking.
        
        First, use the fetch tool to retrieve content from URLs.
        Then, use sequential_thinking to break down your analysis into clear steps.
        
        Make sure to provide a final answer based on your analysis.""",
        model="openai/gpt-4o",
        tools=[sequential_thinker, fetch_tool],
    )
    
    # Ask a question that requires both tools
    agent_runner = AgentRunner(agent)
    response = agent_runner.run("Fetch https://www.york.ac.uk/teaching/cws/wws/webpage1.html and answer what are the ways to create web pages? Use sequential thinking")
    
    # Check that fetch was used
    assert fetch_tool.was_fetch_used(), "The fetch tool wasn't used"
    
    # Check that sequential thinking was used
    assert sequential_thinker.was_sequential_thinking_used(), "Sequential thinking wasn't used"