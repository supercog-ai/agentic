# REST API

Agentic includes built-in support for exposing your agent via a **REST API** using _FastAPI_. This API makes it easy to integrate your agents with web applications, automation tools, or other services.

## Starting the API Server

You can start the API server in three ways:

### 1. Using AgentRunner in code

```python
from agentic.common import Agent, AgentRunner

agent = Agent(name="MyAgent", instructions="You are a helpful assistant.")
AgentRunner(agent).serve()
```

### 2. Using the CLI

The more common approach is to use the command-line interface:

```bash
agentic serve examples/basic_agent.py
```

To enable detailed logging:

```bash
AGENTIC_DEBUG=all agentic serve examples/basic_agent.py
```

### 3. Starting with a custom port

By default, the server runs on port 8086. You can specify a different port:

```bash
agentic serve examples/basic_agent.py --port 9000
```

## API Endpoints

The API server exposes several endpoints for each registered agent. 

### Discovery Endpoint

```
GET /_discovery
```

Returns a list of all available agent paths.

*Example Response:*
```json
["/basic_agent", "/weather_agent"]
```

### Agent Endpoints

Each agent is accessible at its own path, determined by the agent's `safe_name` (lowercased name with special characters replaced by underscores):

```
http://0.0.0.0:8086/<agent_name>
```

#### Describe Agent

```
GET /<agent_name>/describe
```

Returns metadata about the agent, including its name, purpose, tools, and available operations.

*Example Response:*
```json
{
  "name": "Weather Agent",
  "purpose": "I can provide weather information for any location.",
  "tools": ["get_current_weather", "get_forecast"],
  "endpoints": ["/process", "/getevents", "/describe"],
  "operations": ["chat"],
  "prompts": {
    "help": "Here's how to use the Weather Agent..."
  }
}
```

#### Process Request

```
POST /<agent_name>/process
```

Starts a new agent request/conversation turn.

*Request Body:*
```json
{
  "prompt": "What's the weather in New York?",
  "debug": "tools",  // Optional: Enable debug logging
  "run_id": "abc123" // Optional: Specify run ID for tracking
}
```

*Example Response:*
```json
{
  "request_id": "550e8400-e29b-41d4-a716-446655440000",
  "run_id": "abc123"
}
```

#### Get Events

```
GET /<agent_name>/getevents?request_id=550e8400-e29b-41d4-a716-446655440000&stream=true
```

Retrieves events from a running agent request. Can be used in two modes:

- Non-streaming (`stream=false`): Returns all completed events
- Streaming (`stream=true`): Returns a Server-Sent Events (SSE) stream

*Parameters:*

- `request_id`: (Required) The ID returned from the `/process` endpoint
- `stream`: (Optional) Whether to use streaming mode (default: false)

*Example Non-Streaming Response:*
```json
[
  {
    "type": "prompt_started",
    "agent": "Weather Agent",
    "depth": 0,
    "payload": "What's the weather in New York?"
  },
  {
    "type": "chat_output",
    "agent": "Weather Agent",
    "depth": 0,
    "payload": "I'll check the weather for New York."
  },
  {
    "type": "tool_call",
    "agent": "Weather Agent",
    "depth": 0,
    "payload": {
      "name": "get_current_weather",
      "arguments": {
        "location": "New York"
      }
    }
  },
  {
    "type": "tool_result",
    "agent": "Weather Agent",
    "depth": 0,
    "payload": "Temperature: 72°F, Condition: Partly Cloudy"
  },
  {
    "type": "chat_output",
    "agent": "Weather Agent",
    "depth": 0,
    "payload": "The current weather in New York is 72°F and partly cloudy."
  },
  {
    "type": "turn_end",
    "agent": "Weather Agent",
    "depth": 0,
    "payload": "The current weather in New York is 72°F and partly cloudy."
  }
]
```

#### Stream Request

```
POST /<agent_name>/stream_request
```

Combines the process and getevents steps into a single endpoint that returns an SSE stream.

*Request Body:*
```json
{
  "prompt": "What's the weather in New York?",
  "debug": "tools",
  "run_id": "abc123"
}
```

*Example Stream Response:*
A series of SSE events, each containing a serialized Event object.

#### Resume Request

```
POST /<agent_name>/resume
```

Resumes an existing request that was paused waiting for user input.

*Request Body:*
```json
{
  "continue_result": {
    "location": "New York",
    "request_id": "550e8400-e29b-41d4-a716-446655440000"
  },
  "debug": "tools",
  "run_id": "abc123"
}
```

*Example Response:*
```json
{
  "request_id": "550e8400-e29b-41d4-a716-446655440000",
  "run_id": "abc123"
}
```

#### Get Runs

```
GET /<agent_name>/runs
```

Returns a list of all historical runs for this agent.

*Example Response:*
```json
[
  {
    "id": "abc123",
    "agent_name": "Weather Agent",
    "status": "completed",
    "start_time": "2025-03-25T14:30:22.123456",
    "end_time": "2025-03-25T14:30:25.789012",
    "request": "What's the weather in New York?",
    "response": "The current weather in New York is 72°F and partly cloudy."
  }
]
```

#### Get Run Logs

```
GET /<agent_name>/runs/{run_id}/logs
```

Returns detailed logs for a specific run.

*Example Response:*
```json
[
  {
    "id": "log1",
    "run_id": "abc123",
    "timestamp": "2025-03-25T14:30:22.123456",
    "event_type": "prompt_started",
    "content": "What's the weather in New York?"
  },
  {
    "id": "log2",
    "run_id": "abc123",
    "timestamp": "2025-03-25T14:30:23.456789",
    "event_type": "tool_call",
    "content": "{\"name\": \"get_current_weather\", \"arguments\": {\"location\": \"New York\"}}"
  }
]
```

#### Webhook

```
POST /<agent_name>/webhook/{run_id}/{callback_name}
```

Handles webhook callbacks for asynchronous tool operations.

*Path Parameters:*

- `run_id`: The ID of the agent run
- `callback_name`: Name of the tool function to call

*Request Body:*
The request body can include any parameters needed by the callback function. These are passed to the tool as arguments.

*Example Response:*
```json
{
  "status": "success",
  "result": "Webhook processed successfully"
}
```

## Working with Events

When building a client for the Agentic API, you'll need to process various events returned by the agent. Here are the key event types:

- `prompt_started`: Indicates the agent has started processing a prompt
- `chat_output`: Text generated by the agent's LLM
- `tool_call`: Agent is calling a tool with specific arguments
- `tool_result`: Result returned from a tool call
- `tool_error`: Error that occurred during a tool call
- `turn_end`: Final result of the request
- `wait_for_input`: Agent is waiting for user input to continue

Each event includes:

- `type`: The event type
- `agent`: Name of the agent that generated the event
- `depth`: Nesting level (0 for top-level agent, 1+ for sub-agents)
- `payload`: Event-specific data

## Client Implementation Example

Below is a simple JavaScript client example that processes a request and handles the event stream. See the Next.js Dashboard [Docs](./nextjs-dashboard.md) and [Implementation](https://github.com/supercog-ai/agentic/tree/main/src/agentic/dashboard) for a more complete implementation example.

```javascript
async function chatWithAgent(agentName, message) {
  // Start a request
  const response = await fetch(`http://localhost:8086/${agentName}/process`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ prompt: message })
  });
  
  const { request_id } = await response.json();
  
  // Create event source to receive events
  const eventSource = new EventSource(`http://localhost:8086/${agentName}/getevents?request_id=${request_id}&stream=true`);
  
  eventSource.onmessage = (event) => {
    const agentEvent = JSON.parse(event.data);
    
    switch(agentEvent.type) {
      case 'chat_output':
        console.log(`Agent: ${agentEvent.payload}`);
        break;
      case 'tool_call':
        console.log(`Using tool: ${agentEvent.payload.name}`);
        break;
      case 'wait_for_input':
        // Handle user input required
        eventSource.close();
        const userInput = prompt(agentEvent.payload.message);
        resumeConversation(agentName, request_id, agentEvent.payload.key, userInput);
        break;
      case 'turn_end':
        console.log('Conversation turn complete');
        eventSource.close();
        break;
    }
  };
}

async function resumeConversation(agentName, requestId, key, value) {
  const response = await fetch(`http://localhost:8086/${agentName}/resume`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      continue_result: {
        [key]: value,
        request_id: requestId
      }
    })
  });
  
  // Continue handling events...
}
```

## API Documentation

You can access the FastAPI-generated OpenAPI documentation at:

```
http://0.0.0.0:8086/<agent_name>/docs
```

This interactive documentation allows you to test endpoints directly in your browser.
