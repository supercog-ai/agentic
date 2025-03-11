# Agentic Internals

## Core data model

The base **ReAct** agent is implemented by the `ActorBaseAgent` class in `actor_agents.py`. 
It manages the agent loop and the current LLM context, via its `history` attribute. This
class calls the `completion` API from `Litellm` to generate LLM completions for each
step when running an agent.

External callers operate agents via a _proxy_ class which provides the interface to the agent.
Generally the proxy keeps track of multiple requests, and it creates an instance of `ActorBaseAgent`
to hold the state and process operations for each (parallel) request. The proxy runs the agent
via a separate thread, and dispatches events from a Queue from the caller's thread.

The proxy class manages these concerns:

- creates separate agent instances to manage parallel operations
- dispatches events to the RunManager for persistence
- binds tools properly to the underlying agent instance
- manages an event queue for dispatching agent events to the caller
- parses a JSON string result from the LLM into the requsted result model
- manages running the FastAPI app for the agent

You can implement custom agents by subclassing `BaseAgentProxy`. You should call the base
constructor in your `__init__` method, then implement the `next_turn` method to process
operation requests. That method should `yield` events as your agent runs.

Any instance of `BaseAgentProxy` can be used as a tool by another agent.

## Choosing the runtime engine

There are two agent runtimes: one uses basic threads, and the other runs your agent via the
[Ray] distributed processing system. The thread runtime, implemented via `LocalAgentProxy`,
is chosen by default. Set `AGENTIC_USE_RAY` to enable the Ray runtime:

    AGENTIC_USE_RAY=1 python examples/basic_agent.py

The import `agentic.common.Agent` will reference the active runtime proxy class, either
`LocalAgentProxy` or `RayAgentProxy`.

One big difference when using the `Ray` engine is that all events and data in and out of
your agent must be serializable.

# Agent processing flow

Forward direction processing happens by sending events to agent, which may send
events to sub-agents, and those agents emit events back with results.

### Special tool results:

`PauseForChildResult`  - Put the agent in a paused state, and wait for `TurnEnd` to come
back from a sub-agent call. Assumes the event has **already** been sent to the child.

`PauseForInputResult`  - Put the agent in a paused state, and emit a `WaitForInput`
event back to the caller. Wait for the `ResumeWithInput` event to come back from the caller.

`FinishAgentResult` - Special result to indicate that we have sent a handoff Prompt
to the next agent, and this agent can finish execution (without sending TurnEnd).

When Agent A calls Agent B, it sends a `Prompt` message and then enters a "pause" state
(by having the sub-agent tool call return `PauseForChildResult`).

The pause state is mid-way through an LLM function call. When the `TurnEnd` event is 
received from agent B then Agent A can resume by processing the result as the
result of the tool call.

When Agent A wants to "pause for human", then it needs makes a local tool
call which returns a `PauseForInputResult` result. This puts the agent in a paused
state and its emits a `WaitForInput` event back to the caller. 
The caller should collect input and send a `ResumeWithInput` back to agent A.
Agent A handles this event by _re-calling_ the tool function with the human
input. The tool function can process or return the value as is. Agent A then
processes this as the result of the original tool call.

So Agent A can be paused waiting on _upstream_ or _downstream_, but resuming
processing looks the same: treat the result as the result of a function call
and continue processing.

### Handoff

_Handoff_ is when agent A calls agent B, but then "hands off" its turn to Agent B.
Agent A stops processing. Agent B assumes current context, the original caller,
the original depth, and is expected to emit the `TurnEnd` event back to the original
caller. It should also emit the 


### Case 1: Normal Sub-Agent Call with PauseForChildResult

```mermaid
%% Case 1: Normal Sub-Agent Call with PauseForChildResult
sequenceDiagram
    participant caller
    participant Agent A
    participant Agent B
    
    caller->>Agent A: Event
    Note over Agent A: Process Event
    Agent A->>Agent B: Prompt
    Note over Agent A: Return PauseForChildResult
    Note over Agent A: Enter Paused State
    Agent B->>Agent A: TurnEnd
    Note over Agent A: Resume Processing
    Agent A->>caller: TurnEnd

```

### Case 2: Pause for Human Input

```mermaid
%% Case 2: Pause for Human Input
sequenceDiagram
    participant human
    participant caller
    participant Agent A
    
    caller->>Agent A: Event
    Note over Agent A: Process Event
    Note over Agent A: Tool returns PauseForInputResult
    Agent A->>caller: WaitForInput
    caller->>human: Request Input
    human->>caller: Provide Input
    caller->>Agent A: ResumeWithInput
    Note over Agent A: Re-call tool with input
    Note over Agent A: Continue Processing
    Agent A->>caller: TurnEnd
```

### Case 3: Handoff to Another Agent

```mermaid
%% Case 3: Handoff to Another Agent
sequenceDiagram
    participant caller
    participant Agent A
    participant Agent B
    
    caller->>Agent A: Event
    Note over Agent A: Process Event
    Agent A->>Agent B: Prompt
    Note over Agent A: Return FinishAgentResult
    Note over Agent A: Stop Processing
    Note over Agent B: Assume Context & Depth
    Agent B->>caller: TurnEnd
```

## Ray Actor logic

Each running agent is execute by a _remote_ Ray object. This means that we call its
methods via Ray and they return Promises to get their results. We have to call `ray.get`
to retrieve or wait for the actual result.

Our basic agent execution loop looks like:

```python
user input ->
    remote_gen = agent.receiveMessage.remote(Prompt())
        (agent starts the LLM "turn" loop, calling LLM completions and yielding events)
    for next_ref in remote_gen:
        event = ray.get(next_ref)  # Prompt handling yields events until turn is over
```

If our agent needs to call another agent, it creates the Agent and calls it via
Ray remote:

```python
user input ->
    remote_gen = 
        (agent starts the LLM "turn" loop, calling LLM completions and yielding events)
    for next_ref in agent.receiveMessage.remote(Prompt()):
            # Agent does a function call to a child. 
            agent -> starts sub_agent
                agent -> iterate over Prompt
                    sub_agent yield Event
                agent yield Event
        event = ray.get(next_ref)  # Prompt handling yields events until turn is over
```
If the child call is a `handoff` then the parent agent simply gives the child agent
the same `depth`, and once the child is done then the parent agent finishes without
generating the `TurnEnd` event, since the child already did.

### Pause and Resume

To support "human in the loop", the agent can "pause" execution by saving its state, yielding
a `WaitForInput` event, then returning from its loop. Now the caller should send the `ResumeWithInput`
event to the agent which will continue executing from where it left off.

If a sub agent needs to Pause, then it emits the WaitForInput event, and all parent agents
pause and re-yield that event. They save their context of the child call and restore it
when the Resume event is received.
