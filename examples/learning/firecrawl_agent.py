from agentic.common import Agent, AgentRunner
from agentic.tools import MCPTool

def create_firecrawl_researcher():
    """Create Firecrawl MCP tool with proper error handling"""
    try:
        return MCPTool(
            command="npx",
            args=["-y", "firecrawl-mcp"],
            env={
                "FIRECRAWL_API_KEY": "YOUR_API_KEY_HERE"
            }
        )
    except Exception as e:
        print(f"Error initializing Firecrawl MCP: {e}")
        return None

# Create Firecrawl MCP tool
firecrawl = create_firecrawl_researcher()
if not firecrawl:
    print("Failed to initialize Firecrawl MCP")
    exit(1)

agent = Agent(
    name="Firecrawl Researcher",
    welcome="I am an agent that can help crawl and analyze web content using Firecrawl.",
    instructions="""You are a web research assistant powered by Firecrawl.
    Use the Firecrawl tools to:
    
    1. Crawl and analyze web content
    2. Extract relevant information
    3. Follow links and explore related content
    4. Summarize findings
    5. Respect website terms of service and robots.txt
    
    Guidelines:
    - Always check if a URL is valid before crawling
    - Respect rate limits and crawling policies
    - Provide sources for all information
    - If a website blocks crawling, acknowledge and move on
    - Focus on publicly accessible content only
    """,
    model="openai/gpt-4o",
    tools=[firecrawl]
)

if __name__ == "__main__":
    AgentRunner(agent).repl_loop() 