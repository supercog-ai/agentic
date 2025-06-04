# Advanced Agent Configuration

This document explains how to implement your own agent using a custom `next_turn` method in the Agentic framework. It covers the use cases, benefits, tradeoffs, and best practices to follow.

---

## Why Customize `next_turn`?

The `next_turn` method is the **core orchestration loop** for an agent in Agentic. Overriding it gives you control over:

- How your agent interacts with subagents.
- How tools are invoked.
- The logic for multi-step workflows (e.g., retries, research-plan-execute loops).
- Waiting for user feedback or pausing between steps.

### Example Use Case 
Our [Open Source Deep Research](https://github.com/supercog-ai/agentic/blob/main/examples/deep_research/oss_deep_research.py) agent uses a custom `next_turn` to orchestrate a multi-step workflow:

Research planning → Human validation → Knowledge accumulation → Section writing → Final report assembly.

This approach allows for iterative refinement and human-in-the-loop validation, making it suitable for complex research tasks. Each step along the way has its own subagent. The custom `next_turn` method calls the subagents and orchestrates the overall workflow.

> **Note**: This workflow supports human-in-the-loop validation, where the agent pauses after an initial plan generation to wait for user feedback before continuing to allow for iterative refinement.

---

## Pros of Writing a Custom `next_turn`

| Benefit                            | Explanation                           |
|------------------------------------|-------------------------------------------|
| Full control over agent logic      | Define exactly how the workflow runs step-by-step. |
| Conditional logic                  | Branch based on intermediate results (e.g., "if feedback is bad, retry"). |
| Hierarchical coordination          | Easily manage subagents and tools.        |
| Better custom observability        | Yield concise `Event`s for custom logging and monitoring. |

---

## Cons and Tradeoffs

| Challenge                          | Impact                                |
|------------------------------------|-------------------------------------------|
| More boilerplate                   | You'll have to manage event yielding manually and accurately for the agent to run correctly |
| Less plug-and-play                 | Higher learning curve than basic function-based tools. |
| Error-prone in async contexts      | Use generators properly and be careful with subagent calls that are also generators. |

---

## Best Practices

### 1. Always Yield `PromptStarted` First
```python
yield PromptStarted(self.name, {"content": self.topic})
```

### 2. Use `WaitForInput` for Pauses
```python
yield WaitForInput(self.name, {"feedback": "Please provide feedback on the plan."})
return  # Safely exit the generator after yielding pause
```

### 3. Subagent Calls Should Use `yield from`
```python
queries = yield from self.query_planner.final_result("Generate queries", request_context={...})
```

### 4. Always finish with a `TurnEnd` event
```python
yield TurnEnd(self.name, {"status": "Turn completed."})
```

This ensures that:

- Events from the subagent are streamed properly.
- Subagent run tracking remains isolated.
- The turn is ended properly.

---
## Subagent `thread_id` Propagation for Subagents
To ensure events from subagents (like planners or tools) are grouped with the top-level agent in the event-logs, you must pass thread_id in request_context and ensure it is picked up by the subagent. 

### What to do
pass `thread_id` in every subagent request:
```python
result = yield from self.section_planner.final_result(
    "Plan sections",
    request_context={
        "topic": self.topic,
        "thread_id": thread_context.thread_id  # Required for shared logging
    }
)
```


## Event Flow Cheat Sheet

| Event Type          | Purpose                        |
|----------------------|--------------------------------|
| `PromptStarted`      | Start of a turn, log the prompt. |
| `ChatOutput`         | Message from agent or subagent. |
| `ToolCall` / `ToolResult` | Tool usage events.         |
| `WaitForInput`       | Pauses until user input.       |
| `TurnEnd`            | Signals end of a turn + final result. |

---

## Minimal Example of Custom `next_turn`

```python
def next_turn(self, request: str | Prompt, request_context: dict = {}, **kwargs):
    topic = request.payload if isinstance(request, Prompt) else request
    yield PromptStarted(self.name, {"content": topic})

    # Example: Plan → Research → Write
    plan = yield from self.planner_agent.final_result(
        "Make a plan", 
        request_context={"topic": topic, "thread_id": request_context.get("thread_id")}
    )

    yield ChatOutput(self.name, {"content": f"Plan: {plan}"})

    yield WaitForInput(self.name, {"feedback": "Approve the plan or provide feedback."})
    yield TurnEnd(self.name, {"status": "Turn completed after waiting for input."})
```

---

## Key Things to Avoid

- Don’t return early without yielding `TurnEnd`.
- Don’t mix sync calls and generator calls (`yield from`) improperly.
- Don’t directly call subagent methods like `.next_turn()` — use the proxy API (`final_result`, etc.).

---

## API Expectations

| Concept        | Expectation                             |
|----------------|------------------------------------------|
| `thread_id`       | Must be consistent per top-level request. |
| Logging        | Only logs events for current agent, unless propagating via shared `thread_id` |
| History        | Cleanly reset between runs if your agent doesn't need memory. |

---

## Example Use Cases

- **Multi-agent research assistants** (planner → researcher → writer).
- **Interactive approval workflows** (wait for feedback before proceeding).
- **Branching agents for complex tasks** (e.g., "if else logic").

---

