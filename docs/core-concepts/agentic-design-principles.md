# Agentic Design Principles

## 1. An agentic system should leverage the LLM as much as possible.

As much as possible an agentic app leverages the planning and reasoning of the LLM.
Most logic should happen at inference-time rather than compile-time.

## 2. The probabilistic nature of LLM inference is a feature

Traditional software strives for perfectly deterministic behavior. But the probabilitic
nature of the LLM gives us the ability to write software which is creative, reflective and
self-improving. Many systems will need guardrails and self-healing logic to ensure
reliable operation, but trying to get perfect determinism from an agent is misguided.

## 3. Agents follow the actor model

Agents should follow the _actor model_ from computer science, which means:
- They are encapsulated programs which can only manipulate their own private state
- They are event driven, responding to messages and generating messages

## 4. Tools as agents

It is common to want to apply _function calling_ semantics to LLM programs, which
is encouraged by OpenAI's function calling API. But function calling is the wrong
paradigm for agents since it generally implies synchronous execution and strictly
typed parameters. Both of these are poor assumptions when building AI agents.

Rather than generalize everything as a function call, it is better to generalize
_everything_ as an _actor_ (agent). So doing a "web search" call means sending
a message event to the "web search agent", which will reply with events containing
the results. We can easily implement this as a compile-time tool, but it also
means that our "web search tool" could just as easily be another full agent.

## 5. The best tool protocols are languages

LLMs are _really good_ at language, which implies that the best way to interface them
into traditional systems is via some _protocol language_, rather than describing
some huge set of REST endpoints. Wherever possible try to build tools on top of
language protocols like SQL or GraphQL, where the LLM can express complex operations
very efficiently. If your system doesn't support a language already known to your
model, you can define a new language and teach it to your agent. 

## **Agent Trust**

## 6. An agent must be trusted by humans, or it will have no value

AI agents will not, and should not, be trusted by default. They have to earn trust.
These guidelines are a starting point for building trustworthy agents. The
key elements of trust include:
    - the agent will only perform expected operations
    - the behavior of the agent is explainable
    - the agent will rely only on knowledge we expect it to use, and it will
        explain its knowledge sources when it makes a decision
    - the agent stays aligned with its operator's values, and the values of
        human safety

## 7. Agents must only run under the authority of a named human user

Agents always inherit their authority to access information or resources
from their human creators and operators.  Agents must never run _autonomously_ 
without any human being named as responsible for their operation. 
Allowing anonymous (or "AI identity") operation is a dangerous anti-pattern. 

*Human in the loop* is a key feature that agents should rely on until they can
prove that they can operate autonomously.

## 8. Agent behavior must be _explainable_

We cannot necessarily predict agent behavior, but agentic systems must explain
what they are doing and why as much as possible. Unexplainable behavior is
a system bug to be fixed, and should not be tolerated. Part of explainability is
transparency about the operations executed and resources used by the agent.

Agent User Interface should always promote and provide explainability - they
should never hide the actions of the agent.

## 9. Agents should come with _test contracts_

Test Contracts are a way of automatically testing for the correct behavior of your agent.
These are critical to building reliable agentic systems, especially ones that run
