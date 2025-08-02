# Web Search Support

Agentic framework provides built-in web search support that allows agents to automatically search the web for current information when needed. This feature integrates with LiteLLM's web search capabilities.

## Overview

Web search can be enabled at the agent level using the `reasoning_tools` parameter. When enabled, the agent can automatically perform web searches to answer questions requiring current information.

## Supported Models

The following models support web search through LiteLLM:

- **OpenAI**: `gpt-4o-search-preview`
- **xAI**: `grok-3`
- **VertexAI**: `gemini-2.0-flash`
- **Google AI Studio**: `gemini/gemini-2.0-flash`
- **Perplexity**: Various models

## Basic Usage

### Enable Web Search

```python
from agentic.common import Agent

agent = Agent(
    name="Web Search Agent",
    instructions="You can search the web for current information.",
    model="openai/gpt-4o-search-preview",
    reasoning_tools=["websearch"],  # Enable web search
    web_search_context_size="medium",  # Options: "low", "medium", "high"
)
```

### Example Agent

```python
from agentic.common import Agent, AgentRunner

agent = Agent(
    name="News Assistant",
    welcome="I can help you find current news and information from the web.",
    instructions="""You are a helpful assistant that can access current information 
    through web search. When users ask about recent events, news, or current data, 
    use web search to provide accurate, up-to-date information.""",
    model="openai/gpt-4o-search-preview",
    reasoning_tools=["websearch"],
)

if __name__ == "__main__":
    AgentRunner(agent).repl_loop()
```

## How It Works

1. **Agent Level Configuration**: Web search is enabled by adding `"websearch"` to the `reasoning_tools` list
2. **Automatic Detection**: The framework automatically detects if the model supports web search
3. **Parameter Injection**: When supported, `web_search_options` are automatically added to LiteLLM completion calls

## Implementation Details

The web search feature:

- Checks model compatibility using `litellm.supports_web_search()` (if available)
- Adds `web_search_options` parameter to completion calls
- Uses `"medium"` search context size by default
- Gracefully falls back if web search is not supported

## Configuration Options

You can customize the web search context size when creating an agent:

```python
# Low context - faster but less comprehensive
agent = Agent(
    name="Quick Search Agent",
    model="openai/gpt-4o-search-preview",
    reasoning_tools=["websearch"],
    web_search_context_size="low"
)

# Medium context - balanced (default)
agent = Agent(
    name="Balanced Search Agent", 
    model="openai/gpt-4o-search-preview",
    reasoning_tools=["websearch"],
    web_search_context_size="medium"
)

# High context - comprehensive but slower
agent = Agent(
    name="Thorough Search Agent",
    model="openai/gpt-4o-search-preview", 
    reasoning_tools=["websearch"],
    web_search_context_size="high"
)
```

### Context Size Options

The `web_search_context_size` parameter controls how much information the search returns:

- **"low"**: Fast search with minimal context. Good for quick facts or simple queries.
- **"medium"**: Balanced search context (default). Good for most use cases.
- **"high"**: Comprehensive search with maximum context. Best for research and detailed analysis.

**Note**: If an invalid context size is provided, LiteLLM will use its default behavior.

## Debugging

Enable debug mode to see web search activity:

```python
from agentic.actor_agents import DebugLevel

agent = Agent(
    name="Debug Web Agent",
    model="openai/gpt-4o-search-preview",
    reasoning_tools=["websearch"],
    debug=DebugLevel("all"),  # Enable debug logging
)
```

This will show:
- Model web search support detection
- Web search options being added
- Debug information about completion parameters

## Migration from Web Search Tools

If you were previously using the `OpenAIWebSearchTool`, you can migrate to the built-in support:

**Before (using tool):**
```python
from agentic.tools import OpenAIWebSearchTool

agent = Agent(
    name="Agent",
    tools=[OpenAIWebSearchTool()],
)
```

**After (built-in support):**
```python
agent = Agent(
    name="Agent", 
    model="openai/gpt-4o-search-preview",
    reasoning_tools=["websearch"],
)
```

The built-in approach is more efficient as it integrates directly with the model's completion rather than requiring separate tool calls.