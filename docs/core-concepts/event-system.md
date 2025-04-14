# Event System

The agent protocol defines a set of events which are emitted when an agent is
processing an operation.

The most obvious events are `ChatOutput` events which represent text generations
from the LLM. 

To show tool calls, you should show `ToolResult` events.

To understand the lifecycle of processing you can observe `PromptStarted`
and `TurnEnd` events. 

To track usage you should process `FinishCompletion` events which will contain
token usage data.

## Event depth

Events have a `depth` attribute which indicates how deep is the agent that is
generating the event. So the top agent generates `depth=0`, the first level 
sub-agent generates at `depth=1` and so forth. 

Observing depth allows you to build a UI that surfaces the right level of detail
to the user. The simplest UI should only expose ChatOutput events with `depth=0`,
because these are LLM generations from the top-level agent. 


## Event data flow

Agents publish events whenever they are asked to do something. For a single
agent this mechanism is simple:

    caller      --- msg -->     agent
      |                           |
      |         <-- event ---     |

However, once agents start calling other agents, it gets more complicated. Our general
rules is that ALL events published at any level should bubble up back to the original
caller. This is to maximize the caller's visibility into what the system is doing:

    caller      --- msg -->     agent A               agent B
      |                           |                       |
      |         <-- event1 ---    |                       |
      |                           |    --- call B ->      |
      |                           |                       |
      |                           |     <-- event 2 --    |
      |         <-- event 2 ---   |                       |

Each event has an agent `name` property, and `depth` property which indicates how far down 
in the call tree the event originated.

So the caller will get these two events:

    event1 (Agent A, depth=0)
    event2 (Agent B, depth=1)

This allows the caller to ignore sub-agent execution if it prefers.

## Agent execution flow

When you call agent A, it may execute agent B, plus agent C, and they in turn
may call other agents.

If you want to observe all events from the entire execution tree, then you should
implement logic to record the recept of events from each distinct agent, and then
make sure to wait for the `TurnEnd` message from each one. 

## Agent pipeline

To implement "pipeline semantics", agents can "hand off" from one to another. In this
case the sub-agent will assume the original caller of the first agent, and will assume
its `depth` as well:

    caller      --- msg -->     agent A               agent B
      |                           |                       |
      |         <-- event1 ---    |                       |
      |                           |  ---  *handoff* B ->  |
      |         <-- turnend: A -- |                       |                
      |                                                   |
      |         <-- ---------------------- event 2 --     |

So the caller will get events like this:

    event1 (Agent A, depth=0)
    event2 (Agent B, depth=0)

## Chat history

A typical interactive agent is built with _chat history_ which maintains the history
of interactions over the life of a session.