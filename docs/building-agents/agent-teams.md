# Agent Teams

Agentic makes it very easy to solve a larger problem using a _team of agents_ which
collaborate together.

The easiest mechanism is to employ one agent as a _tool_ for another agent:

```python

producer = Agent(
    name="producer",
    instructions="You are a podcast producer. Call your reporter to get the news report.",
    tools=[
        Agent(
            name="reporter",
            instructions="You are a hard news reporter.",
            tools=[GoogleNewsTool()]
        )
    ]
)
```

The _producer_ agent will receive a tool function like `call_reporter_agent` which it
can call to invoke the _reporter_ agent.

You can attach multiple agents as tools to another agents, and there is no depth limit,
so sub-agents can invoke other sub-agents as needed.

## Using in a workflow agent

You can always write your own code to implement your agent flow (by subclassing `Agent`), and 
in this case you can call sub-agents programatically. The Deep Research example agent 
uses this approach extensively to coordinate a large team of special-purpose agents. 
A good pattern for calling sub-agents looks like this:

```python
    def next_run(self):
        self.sub_agent = Agent(...)
        result = yield from self.sub_agent.final_result(
                "Please query the order system.",
                request_context={
                    "order_id": order_id, 
                },
            )
        # do something with 'result'
```
There are two tricks here. The first is calling `final_result` which waits for the end of the
agent run and returns the final text output. The other trick is the `yield from` which
re-publishes any events that the sub-agent produces before it completes.


## When should I use agent teams?

One obvious use for sub-agents is when you already have an agent which performs some valuable
task, and you just want to leverage that task from another agent. Now you could go look
at the other agent, see what tools it is using, and use those tools directly in _your_ agent.
This is fine, but calling a sub-agent offers some benefits:

- Sub-agents can use their own LLM, which could be a different model than the one powering
the calling agent. This is good if your sub-task requires some capability that your main
model doesn't offer (or to arbitrage model costs).

- Sub-agents can leverage the LLM for reasoning and decision making. As a simple example,
we could give our _reporter_ agent multiple "news feed" tools and let it decide which ones to 
use as appropriate. 

- Sub-agents let you mange your overall _LLM context_. Context windows are limited, tokens
cost money, and LLM decision making gets less reliable as the context size grows. All of these
factors create reasons for wanting to "split your problem" across multiple agents.

## Unified event stream

Note that when Agent A calls Agent B in the agentic framework, both agents are operating within
a shared _Thread_. This means that events published by both agents will appear in the same event
stream to the agent caller. Events identify their source agent and _depth_, so client apps
(like a web interface) can decide how to render "nested" events within the overall thread.
