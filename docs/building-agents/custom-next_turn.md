# Building a Custom `next_turn` Agent in Agentic

This document explains how to implement your own agent using a custom `next_turn` method in the Agentic framework. It covers the use cases, benefits, tradeoffs, and best practices to follow.

---

## Why Customize `next_turn`?

The `next_turn` method is the **core orchestration loop** for an agent in Agentic. Overriding it gives you control over:

- How your agent interacts with subagents.
- How tools are invoked.
- The logic for multi-step workflows (e.g., retries, research-plan-execute loops).
- Waiting for user feedback or pausing between steps.

**Example Use Case:**  
(in examples/deep-research/oss_deep_research.py)
Research planning → web queries → content writing → final report revision.
---

## Pros of Writing a Custom `next_turn`

| Benefit                       | Explanation                           |
|------------------------------------|-------------------------------------------|
| Full control over agent logic      | Define exactly how the workflow runs step-by-step. |
| Conditional logic                 | Branch based on intermediate results (e.g., "if feedback is bad, retry"). |
| Hierarchical coordination         | Easily manage subagents and tools.        |
| Support for pause/resume flows     | Use `WaitForInput`, `PauseForInputResult`, and handle feedback gracefully. |
| Better observability              | Yield `Event`s at each stage for clean logging and monitoring. |

---

## Cons and Tradeoffs

| Challenge                      | Impact                                |
|------------------------------------|-------------------------------------------|
| More boilerplate                   | You'll have to manage event yielding manually and accurately for the agent to run correctly |
| Less plug-and-play                 | Higher learning curve than basic function-based tools. |
| Error-prone in async contexts      | Use generators properly and be careful with subagent calls that are also generators. |

---

## Best Practices

### 1. **Always Yield `PromptStarted` First**
```python
yield PromptStarted(self.name, {"content": self.topic})
```

### 2. **Use `WaitForInput` for Pauses (Don’t `return` Early)**
```python
yield WaitForInput(self.name, {"feedback": "Please provide feedback on the plan."})
return  # Safely exit the generator after yielding pause
```

### 3. **Subagent Calls Should Use `yield from`**
```python
queries = yield from self.query_planner.final_result("Generate queries", request_context={...})
```

This ensures that:
- Events from the subagent are streamed up properly.
- Subagent run tracking remains isolated.

---

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
        "Make a plan", request_context={"topic": topic}
    )

    yield ChatOutput(self.name, {"content": f"Plan: {plan}"})

    yield WaitForInput(self.name, {"feedback": "Approve the plan or provide feedback."})
```

---

## Key Things to Avoid

- Don’t return early without yielding `TurnEnd`.
- Don’t mix sync calls and generator calls (`yield from`) improperly.
- Don’t directly call subagent methods like `.next_turn()` — use the proxy API (`final_result`, etc.).
- Avoid sharing `RunContext` objects across agents.

---

## API Expectations

| Concept        | Expectation                             |
|----------------|------------------------------------------|
| `run_id`       | Must be consistent per top-level request. |
| Subagents      | Should not share history directly with parent. |
| Logging        | Only log events for the current agent, not subagent events. |
| History        | Cleanly reset between runs if your agent doesn't need memory. |

---

## Example Use Cases

- **Multi-agent research assistants** (planner → researcher → writer).
- **Interactive approval workflows** (wait for feedback before proceeding).
- **Agents that retry based on intermediate results.**

---

