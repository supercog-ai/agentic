from agentic.common import Agent, AgentRunner
from agentic.tools import MCPTool

def create_sequential_thinker():
    """Create Sequential Thinking MCP tool with proper error handling"""
    try:
        return MCPTool(
            command="npx",
            args=["-y", "@modelcontextprotocol/server-sequential-thinking"]
        )
    except Exception as e:
        print(f"Error initializing Sequential Thinking MCP: {e}")
        return None

# Create Sequential Thinking MCP tool
sequential_thinker = create_sequential_thinker()
if not sequential_thinker:
    print("Failed to initialize Sequential Thinking MCP")
    exit(1)

agent = Agent(
    name="Sequential Thinker",
    welcome="I am an agent that can help break down complex problems into steps.",
    instructions="""You are a helpful assistant that breaks down complex problems into 
    manageable steps using sequential thinking. Use the sequential_thinking tool to
    structure your approach to solving problems.
    
    When using sequential thinking:
    1. Break down complex problems into smaller steps
    2. Think through each step carefully
    3. Revise your thinking if needed
    4. Consider alternative approaches
    """,
    model="openai/gpt-4o",
    tools=[sequential_thinker]
)

if __name__ == "__main__":
    AgentRunner(agent).repl_loop() 