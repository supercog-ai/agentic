# Interacting with Agents

Agentic provides several ways to interact with your agents, ranging from simple CLI interfaces to full-featured web applications. This section covers the different methods available.

## Available Interfaces

| Interface | Use Case | Features |
|-----------|----------|----------|
| [Command Line (CLI)](#command-line-interface) | Quick testing, scripting | Simple text I/O, dot commands |
| [REST API](#rest-api) | Integration with other applications | HTTP endpoints, event streaming |
| [Next.js Dashboard](#nextjs-dashboard) | Professional web UI | Real-time updates, run history, background tasks |
| [Streamlit Dashboard](#streamlit-dashboard) | Quick prototyping | Simple web UI with minimal setup |

## Command Line Interface

The CLI is the simplest way to interact with your agents. It provides a REPL (Read-Eval-Print Loop) interface for direct conversations.

```bash
agentic thread examples/basic_agent.py
```

Special "dot commands" give you access to debugging features and agent controls:

```
.debug tools      # Show tool calls
.model claude-3   # Switch models
.history          # Show conversation history
.help             # See all available commands
```

[Learn more about the CLI →](./cli.md)

## REST API

The REST API allows you to integrate agents with web applications, automation systems, or other services. It exposes endpoints for starting conversations, getting events, managing runs, and more.

```bash
agentic serve examples/basic_agent.py
```

This starts a FastAPI server that provides:
- Agent discovery
- Process requests
- Event streaming
- Run history and logs

[Learn more about the REST API →](./rest-api.md)

## Next.js Dashboard

The Next.js Dashboard provides a full-featured web interface for interacting with your agents, with support for:

- Multiple agent management
- Real-time event streaming
- Background task management
- Run history and logs
- Markdown rendering

```bash
agentic dashboard start --agent-path examples/basic_agent.py
```

[Learn more about the Next.js Dashboard →](./nextjs-dashboard.md)

## Streamlit Dashboard

The Streamlit Dashboard offers a lightweight web interface for quick prototyping and visualization.

```bash
agentic streamlit
```

[Learn more about the Streamlit Dashboard →](./streamlit-dashboard.md)

## Programmatic Access

In addition to these interfaces, you can always interact with agents programmatically in your Python code:

```python
from agentic.common import Agent

# Create an agent
agent = Agent(
    name="My Agent",
    instructions="You are a helpful assistant.",
    model="openai/gpt-4o-mini"
)

# Use the << operator for a quick response
response = agent << "Hello, how are you?"
print(response)

# For more control over the conversation
request_id = agent.start_request("Tell me a joke").request_id
for event in agent.get_events(request_id):
    print(event)
```

## Next Steps

- Learn about the [CLI options and features](./cli.md)
- Set up the [REST API](./rest-api.md) for integration with other applications
- Explore the [Next.js Dashboard](./nextjs-dashboard.md) for a full-featured web interface
- Try the [Streamlit Dashboard](./streamlit-dashboard.md) for quick prototyping
