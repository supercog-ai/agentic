from agentic.tools import WeatherTool, GoogleNewsTool, A2ATool

from agentic.common import Agent, AgentRunner
from agentic.models import GPT_4O_MINI


MODEL = GPT_4O_MINI

# Create specialist agents
weather_specialist = Agent(
    name="Weather Specialist",
    instructions="""You are a weather expert. Provide detailed weather information and forecasts.
    Use the weather tool to get current conditions and explain what they mean for the user.""",
    model=MODEL,
    tools=[WeatherTool()],
)

news_specialist = Agent(
    name="News Specialist", 
    instructions="""You are a news expert. Find and summarize relevant news articles.
    Use the Google News tool to search for current news and provide comprehensive summaries.""",
    model=MODEL,
    tools=[GoogleNewsTool()],
)

# Create the A2A tool instance
a2a_tool = A2ATool()

# Register specialists with the A2A tool
a2a_tool.register_agent(
    "weather_specialist", 
    weather_specialist,
    "Expert in weather conditions, forecasts, and meteorological analysis"
)

a2a_tool.register_agent(
    "news_specialist",
    news_specialist, 
    "Expert in current events, news analysis, and information gathering"
)

# Create the coordinator agent that manages the team
coordinator = Agent(
    name="Team Coordinator",
    welcome="""Hello! I'm the Team Coordinator. I manage a team of specialist agents including:
    
🌤️  Weather Specialist - For weather information and forecasts
📰 News Specialist - For current events and news analysis

I can help you by:
- Delegating tasks to the appropriate specialist
- Coordinating multi-step tasks that require multiple specialists
- Providing direct assistance when no specialist is needed

What can I help you with today?""",
    
    instructions="""You are a team coordinator managing specialist agents. Your role is to:

1. **Analyze user requests** and determine if they need specialist help
2. **Delegate appropriately** using these guidelines:
   - Weather-related questions → call weather_specialist
   - News/current events questions → call news_specialist  
   - Complex tasks → coordinate between multiple specialists
   - Simple questions → handle directly

3. **Use A2A communication** via these functions:
   - call_agent(target_agent, message) - for delegation and collaboration
   - handoff_to_agent(target_agent, message) - when specialist should take full control
   - list_available_agents() - to see available team members
   - get_agent_info(agent_name) - for specialist details

4. **Coordinate responses** by combining specialist inputs when needed

Remember: Always explain your coordination decisions to the user.""",
    
    model=MODEL,
    tools=[a2a_tool],
    
    prompts={
        "weather": "What's the weather like in San Francisco today?",
        "news": "What are the top tech news stories today?",
        "team": "Who are my team members and what do they specialize in?",
        "complex": "I'm planning a outdoor event in New York next weekend. I need weather forecast and any relevant news about events or conditions.",
        "handoff_weather": "I need detailed weather analysis for my farming operation. Please connect me directly with your weather expert.",
        "handoff_news": "I'm a journalist working on a breaking story. Please connect me directly with your news specialist.",
    }
)

if __name__ == "__main__":
    AgentRunner(coordinator).repl_loop() 