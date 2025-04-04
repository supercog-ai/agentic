# Core Concepts

This page explains the fundamental concepts behind Agentic's design and operation.

## Understanding Agents

Agentic agents by default use the LLM **ReAct** pattern. This means:

- The LLM controls the execution flow of your agent
- You specify the tasks and flow of your agent via the LLM system prompt
- The agent gets one or more **tools** that it can use to accomplish its task
- The agent runs in this loop until it decides that it can't go further:
    - plan next step
    - generate text completion or tool call
        (platform executes tool call)
    - observe tool call results

## Components of an Agent

An agent is _defined_ by its behavior - what it does as perceived from the outside. But inside, each agent has these properties:

- **name**: A unique identifier for the agent
- **instructions**: The system prompt that guides the agent's behavior
- **tools**: Functions the agent can use to interact with the world
- **children agents**: Sub-agents that can be called as tools
- **model**: The chosen LLM model
- **welcome** (optional): A message explaining the purpose of the agent
- **memories** (optional): A list of memories the agent uses during execution
- **prompts** (optional): A list of pre-defined prompts that can be called

## Data Model

The Agentic framework uses the following key concepts:

- **Agent**: A named unit of execution that supports operations and maintains state
- **Thread**: A persistent conversation with an agent that maintains history
- **Run**: A single operation request within a thread
- **Event**: Data emitted during a run (output, tool calls, etc.)

## Agents as a Team

Agents can call other agents as tools, allowing you to create teams of cooperating agents.

```python
from agentic.tools import GoogleNewsTool

producer = Agent(
    name="Producer",
    welcome="I am the news producer. Tell me the topic, and I'll get the news from my reporter.",
    instructions="You are a news producer. Call the reporter with the indicated topic.",
    model="gpt-4o-mini",
    tools=[
        Agent(
            name="News Reporter",
            instructions=f"""
        Call Google News to get headlines on the indicated news topic.
        """,
            tools=[GoogleNewsTool()],
        )
    ],
)
```

## Agent Handoff

Sometimes you want to "hand off" execution to another agent rather than waiting for it to return. Use the `handoff` property for this:

```python
from agentic import handoff

agentA = Agent(
    name="Producer",
    welcome="This is the handoff demo.",
    instructions="Print the message 'I am A', then call agent B. Afterwards print 'WARNING!'",
    tools=[
        handoff(Agent(
            name="Agent B",
            instructions="Print the msssage 'and I am B'",
        ))
    ],
)
```

Without using `handoff`, the WARNING message would be printed from the root agent. Handoff is useful if your sub-agent generates a lot of output, because normally that output would be fed back into AgentA as the `observation` step.

## Agent Memory

Agents support multiple types of memory:

- **Short-term memory**: The chat session history in the agent's context window
- **Persistent facts**: Data stored anywhere and applied to the agent context when it runs
- **Run history**: Persistence of chat sessions for later review
- **RAG memory**: Vector storage for larger-than-context retrieval of information

## Event System

As agents run, they emit events that can be observed and processed:

- `ChatOutput`: Text generated by the LLM
- `ToolResult`: Results of tool calls
- `PromptStarted` and `TurnEnd`: Lifecycle events
- `FinishCompletion`: Token usage and tracking data

Events have a `depth` attribute indicating which level of agent generated them, allowing UIs to filter appropriately.

For more information, see the [Events](../core-concepts/event-system.md) documentation.

## Next Steps

- Learn how to [Build Agents](../building-agents/index.md)
- Understand how to use and create [Tools](../tools/index.md)
- Explore [Agent Teams](../building-agents/agent-teams.md)
- See the [CLI Reference](../interacting-with-agents/cli.md)
- Check out [Examples](../example-agents.md)
