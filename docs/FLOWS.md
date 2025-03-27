# ReAct Agent

This is the default form for Agentic agents.

# Pipeline

A pipeline strings together the outputs->inputs of a set of agents in a linear sequence.

```python

from agentic import Agent, Pipeline

pipeline = Pipeline(
    Agent(name="agent 1"),
    Agent(name="agent 2"),
    Agent(name="agent 3"),
)

AgentRunner(pipeline).run()
```
