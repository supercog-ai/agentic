# Event Types

## Base Event

All events derive from the base `Event` class, which has these common properties:

- `agent`: The name of the agent that generated the event
- `type`: The type of the event (e.g., "prompt", "chat_output")
- `payload`: The data associated with the event
- `depth`: The nesting level (0 for top-level agent, 1+ for sub-agents)

## Communication Events

### Prompt
Represents a request sent to an agent to perform an operation.
```
Prompt(
    agent="my_agent",
    message="What's the weather like today?",
    debug=DebugLevel.NONE,
    request_context={},  # Optional context data
    depth=0,  # Level in agent hierarchy
    ignore_result=False,  # Whether to ignore the result
    request_id=None  # Optional request ID (auto-generated if None)
)
```

### PromptStarted
Signals that an agent has started processing a prompt.
```
PromptStarted(
    agent="my_agent",
    message="What's the weather like today?",
    depth=0
)
```

### ResetHistory
Indicates that an agent's conversation history has been reset.
```
ResetHistory(agent="my_agent")
```

### ChatOutput
Output containing a chat message.
```
ChatOutput(
    agent="my_agent",
    payload={"content": "This is a response", "role": "assistant"},
    depth=0
)
```

### RunEnd
Signals the completion of an agent's processing for a run.
```
RunEnd(
    agent="my_agent",
    messages=[{"role": "assistant", "content": "Final response"}],
    thread_context=thread_context_obj,
    depth=0
)
```

### RunCancelled
Indicates that an agent's run was cancelled.
```
RunCancelled(agent="my_agent", depth=0)
```

## Tool-Related Events

### ToolCall
Represents an agent calling a tool with arguments.
```
ToolCall(
    agent="my_agent",
    name="weather_tool",
    arguments={"location": "New York"},
    depth=0
)
```

### ToolResult
Contains the result returned from a tool call.
```
ToolResult(
    agent="my_agent",
    name="weather_tool",
    result="It's 75°F and sunny in New York",
    depth=0
)
```

### ToolError
Represents an error that occurred during a tool call.
```
ToolError(
    agent="my_agent",
    name="weather_tool",
    error="Failed to retrieve weather data: API timeout",
    depth=0
)
```

## LLM Completion Events

### StartCompletion
Signals the start of an LLM completion operation.
```
StartCompletion(agent="my_agent", depth=0)
```

### FinishCompletion
Contains information about a completed LLM operation, including token usage and cost.
```
FinishCompletion.create(
    agent="my_agent",
    llm_message="The generated response",
    model="gpt-4",
    cost=0.02,
    input_tokens=150,
    output_tokens=50,
    elapsed_time=1.5,
    depth=0
)
```

## Human-in-the-loop Events

### WaitForInput
Indicates that an agent is waiting for human input to continue.
```
WaitForInput(
    agent="my_agent",
    request_keys={"user_preference": "Please specify your preference"}
)
```

### ResumeWithInput
Sent by the caller with human input to resume an agent's execution.
```
ResumeWithInput(
    agent="my_agent",
    request_keys={"user_preference": "Option A"},
    request_id="abc123"
)
```

## Authentication Events

### OAuthFlow
Emitted when OAuth authentication is required.
```
OAuthFlow(
    agent="my_agent",
    auth_url="https://example.com/oauth",
    tool_name="github_tool",
    depth=0
)
```

## Agent State Events

### SetState
Used to update an agent's internal state.
```
SetState(agent="my_agent", payload={"key": "value"}, depth=0)
```

### AddChild
Adds a child agent to a parent agent.
```
AddChild(agent="parent_agent", remote_ref=child_agent_ref, handoff=False)
```

## Special Result Types

These aren't events, but special return values that affect agent flow:

### PauseForInputResult
Tells the agent to pause and wait for human input.
```
PauseForInputResult(request_keys={"user_preference": "Please specify your preference"})
```

### OAuthFlowResult
Indicates that OAuth flow needs to be initiated.
```
OAuthFlowResult(request_keys={"auth_url": "https://example.com/oauth", "tool_name": "github_tool"})
```

### FinishAgentResult
Tells the agent to stop processing entirely.
```
FinishAgentResult()
```
## Event Flow Example

A typical event flow for a simple agent interaction might look like:

1. `Prompt` - User sends a request to the agent
2. `PromptStarted` - Agent begins processing the request
3. `StartCompletion` - Agent starts an LLM completion
4. `FinishCompletion` - LLM generates a response
5. `ToolCall` - Agent decides to use a tool
6. `ToolResult` - Tool returns a result
7. `StartCompletion` - Agent starts another LLM completion
8. `ChatOutput` - Agent returns a text response
9. `FinishCompletion` - LLM generates final response
10. `RunEnd` - Agent completes processing the request