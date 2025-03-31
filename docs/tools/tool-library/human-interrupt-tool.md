# HumanInterruptTool

The `HumanInterruptTool` provides a simple mechanism for agents to pause execution and request input from a human. This tool is essential for implementing human-in-the-loop workflows where an agent needs to gather information or approval before proceeding.

## Features

- Pause agent execution to request human input
- Display custom messages to guide human input
- Seamlessly resume execution with the provided input
- Maintain context across the interruption

## Methods

### stop_for_input

```python
def stop_for_input(request_message: str, run_context: RunContext)
```

Stop and ask the user for input.

**Parameters:**

- `request_message (str)`: The message to display to the human
- `run_context (RunContext)`: The execution context

**Returns:**
Either the human input (if already provided) or a `PauseForInputResult` that will pause execution and request input.

## How It Works

1. When the `stop_for_input` method is called, it first checks if input already exists in the run context
2. If input exists, it returns that input immediately
3. If no input exists, it returns a `PauseForInputResult` which signals the agent framework to:
   - Pause the current execution
   - Display the request message to the human
   - Wait for input
   - Resume execution with the provided input

## Example Usage

```python
from agentic.common import Agent
from agentic.tools import HumanInterruptTool

# Create an agent with human interruption capability
interactive_agent = Agent(
    name="Interactive Assistant",
    instructions="You help users by gathering necessary information before proceeding.",
    tools=[HumanInterruptTool()]
)

# Use the agent in a conversation requiring human input
response = interactive_agent << "Plan a trip to Japan for me"
print(response)

# In this example, the agent might interrupt to ask:
# "What is your budget for this trip to Japan?"
# After the human provides an answer, the agent continues planning
```

## Integration with Other Tools

The `HumanInterruptTool` works well when combined with other tools that might need additional information:

```python
from agentic.common import Agent
from agentic.tools import HumanInterruptTool, WeatherTool

# Create an agent with multiple tools
travel_agent = Agent(
    name="Travel Planner",
    instructions="You help plan trips based on weather and user preferences.",
    tools=[HumanInterruptTool(), WeatherTool()]
)

# The agent can get weather data but might need to interrupt for location details
response = travel_agent << "What clothes should I pack for my trip next week?"
# Agent might pause and ask: "Where are you traveling to next week?"
print(response)
```

## Best Practices

- Use clear, specific request messages to guide the human on what information is needed
- Keep interruptions to a minimum to maintain conversation flow
- Consider whether information could be obtained through other tools before interrupting
- Store frequently requested information in the agent's memory to avoid repeated interruptions

## Technical Details

- The tool uses the `PauseForInputResult` class from the Agentic framework
- Input data is stored in the run context with the key "input"
- The tool is stateless - it doesn't maintain any internal state between calls
