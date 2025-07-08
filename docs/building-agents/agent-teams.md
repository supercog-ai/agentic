# Agent Teams with A2A Communication

Agentic provides powerful **Agent-to-Agent (A2A) communication** capabilities that enable you to build sophisticated teams of specialist agents that can collaborate, delegate tasks, and coordinate complex workflows.

## Overview

The A2A system allows you to:
- **Register specialist agents** with specific capabilities and descriptions
- **Create coordinator agents** that manage and delegate to specialists
- **Enable seamless communication** between agents in the same thread
- **Monitor agent interactions** through unified event streams
- **Handle both delegation and handoffs** between agents

## Setting Up Agent Teams

### 1. Create Specialist Agents

Start by creating agents with specific expertise and tools:

```python
from agentic.tools import WeatherTool, GoogleNewsTool, A2ATool
from agentic.common import Agent
from agentic.models import GPT_4O_MINI

# Weather specialist
weather_specialist = Agent(
    name="Weather Specialist",
    instructions="""You are a weather expert. Provide detailed weather information and forecasts.
    Use the weather tool to get current conditions and explain what they mean for the user.""",
    model=GPT_4O_MINI,
    tools=[WeatherTool()],
)

# News specialist
news_specialist = Agent(
    name="News Specialist", 
    instructions="""You are a news expert. Find and summarize relevant news articles.
    Use the Google News tool to search for current news and provide comprehensive summaries.""",
    model=GPT_4O_MINI,
    tools=[GoogleNewsTool()],
)
```

### 2. Register Agents with A2A Tool

Create an A2A tool instance and register your specialists:

```python
# Create the A2A tool instance
a2a_tool = A2ATool()

# Register specialists with descriptive capabilities
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
```

### 3. Create a Coordinator Agent

Build a coordinator agent that manages the team using the A2A tool:

```python
coordinator = Agent(
    name="Team Coordinator",
    
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
    
    model=GPT_4O_MINI,
    tools=[a2a_tool],
)
```

## A2A Communication Functions

The A2A tool provides several functions for agent coordination:

### `call_agent(target_agent, message)`
Delegates a task to a specialist agent and returns the result. The coordinator remains in control and can process the response.

```python
# Example: Coordinator delegating weather query
result = call_agent("weather_specialist", "What's the weather like in San Francisco today?")
```

### `handoff_to_agent(target_agent, message)`  
Transfers full control to the target agent. The specialist takes over the conversation and interacts directly with the user.

```python
# Example: Handing off to specialist for complex analysis
handoff_to_agent("weather_specialist", "User needs detailed meteorological analysis for farming operations")
```

### `list_available_agents()`
Returns a list of all registered agents and their capabilities.

### `get_agent_info(agent_name)`
Gets detailed information about a specific registered agent.

## Event Monitoring

A2A communications generate special events that appear in the unified event stream:

- **`SubAgentCall`** - When an agent calls another agent
- **`SubAgentResult`** - When a sub-agent returns results

These events include:
- Source and target agent names
- Messages passed between agents
- Results and responses
- Depth information for nested calls

## Advanced Patterns

### Multi-Step Coordination

Coordinators can orchestrate complex workflows involving multiple specialists:

```python
# Example: Planning an outdoor event
# 1. Get weather forecast from weather specialist
# 2. Check news for relevant events/conditions from news specialist  
# 3. Combine information to provide comprehensive planning advice
```

### Conditional Delegation

Use agent capabilities to make intelligent delegation decisions:

```python
# Coordinator can check available agents and their capabilities
agents = list_available_agents()
weather_info = get_agent_info("weather_specialist")

# Then delegate based on request analysis
if "weather" in user_request.lower():
    result = call_agent("weather_specialist", user_request)
```

### Error Handling and Fallbacks

Implement robust error handling for agent communications:

```python
try:
    result = call_agent("weather_specialist", message)
except Exception as e:
    # Handle communication errors
    # Fallback to direct response or alternative agent
```

## When to Use A2A Teams

A2A agent teams are ideal when you need:

- **Specialized expertise**: Different domains requiring domain-specific knowledge and tools
- **Context management**: Breaking complex problems into manageable, focused sub-tasks  
- **Model optimization**: Using different LLMs optimized for specific tasks
- **Scalable delegation**: Dynamic routing of requests to appropriate specialists
- **Workflow coordination**: Multi-step processes requiring multiple agents

## Benefits of A2A Communication

1. **Clear separation of concerns** - Each agent focuses on their specialty
2. **Flexible delegation** - Choose between task delegation and full handoffs
3. **Unified monitoring** - All agent interactions appear in the same event stream
4. **Dynamic team composition** - Register and discover agents at runtime
5. **Cost optimization** - Use appropriate models for each specialist
6. **Enhanced reasoning** - Leverage LLM capabilities for coordination decisions

## Complete Example

See `examples/a2a_team_example.py` for a full working example of an A2A agent team with weather and news specialists coordinated by a team coordinator agent.
