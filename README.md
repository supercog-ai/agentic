# Agentic

Agentic makes it easy to create AI agents - autonomous software programs that understand natural language
and can use tools to do work on your behalf.

Agentic is in the tradition of _opinionated frameworks_. We've tried to encode lots of sensisible
defaults and best practices into the design, testing and deployment of agents. 

Agentic is a few different things:

- A lightweight agent framework. Same part of the stack as SmolAgents or PydanticAI.
- A referenece implementation of the [agent protocol](https://github.com/supercog-ai/agent-protocol).
- An agent runtime built on [Ray](https://github.com/ray-project/ray)
- An optional "batteries included" set of features to help you get running quickly:
  * Built in FastAPI API for your agent
  * Basic RAG features
  * A set of production-ready [tools](https://github.com/supercog-ai/agentic/tree/main/src/agentic/tools) (extracted from our Supercog product)
  * Agentic Chat UI examples in [NextJS](https://github.com/supercog-ai/agentic/tree/main/src/agentic/ui/next-js) and [Streamlit](https://github.com/supercog-ai/agentic/tree/main/src/agentic/ui)
  * A growing set of working [examples](https://github.com/supercog-ai/agentic/tree/main/examples)

You can pretty much use any of these features and leave the others. There are lots of framework choices but we think we have
embedded some good ideas into ours.

Some of the _framework_ features:

- Approachable and simple to use, but flexible enough to support the most complex agents
- Supports teams of cooperating agents
- Supports Human-in-the-loop
- Easy definition and use of tools (functions, class methods, import LangChain tools, ...)
- Built alongside a set of production-tested tools

Visits the docs: https://supercog-ai.github.io/agentic/

## Pre-built agents you can run today

### [Agent Operator](https://github.com/supercog-ai/agentic/blob/main/examples/operator_agent.py)

...full browser automation, including using authenticated sessions...

### [Podcast Producer](https://github.com/supercog-ai/agentic/blob/main/examples/podcast.py)

An agent team which auto-produces and publishes a daily podcast. Customize for your news interests.

### [Meeting Notetaker](https://github.com/supercog-ai/agentic/blob/main/examples/meeting_notetaker.py)

[Coming soon] Your own meeting bot agent with meeting summaries stored into RAG.

### Personal Data Analyst

## Install

The easiest thing is to install the package from pypi:

`pip install agentic-framework`

For the latest and greatest you can install directly from the repo:

`pip install git+ssh://git@github.com/supercog-ai/agentic.git`

We recommend installing into a virtual env.

After you install, setup a folder to hold your agents, like "myagents", and then run:

`agentic init .`

This will initialize the directory that you are in and create these folders:

    examples/   - The example agents from this repo
    agents/     - A folder to put your own agents
    runtime/    - Agents execute in here by default, and will store files here

The CLI will setup the current directory to contain your agents.

The install will copy examples and a basic file structure into the directory `myagents`. You can name
or rename this folder however you like.

## Intro Tutorial

Visit [the docs](https://supercog-ai.github.io/agentic/) for a tutorial on getting started
with the framework.

## Dependencies

Agentic builds on `Litellm` to enable consistent support for many different LLM models.

Under the covers, Agentic uses [Ray](https://github.com/ray-project/ray) to host and
run your agents. Ray implements an _actor model_ which implements a much better 
architecture for running complex agents than a typical web framework.

### API Keys

Agentic requires API keys for the LLM providers you plan to use. Copy the `.env.example` file to `.env` and set the following environment variables:

```
OPENAI_API_KEY=your_openai_api_key_here
ANTHROPIC_API_KEY=your_anthropic_api_key_here
```

You only need to set the API keys for the models you plan to use. For example, if you're only using OpenAI models, you only need to set `OPENAI_API_KEY`.

## Why does this exist?

Yup, there's a lot of agent frameworks. But many of these are "gen 1" frameworks - designed
before anyone had really built agents and tried to put them into production. Agentic is informed
by our learnings at Supercog from building and running hundreds of agents over the past year.

Some reasons why Agentic is different:

- We have a thin abstraction over the LLM. The "agent loop" code is a 
[couple hundred lines](./src/agentic/actor_agents.py) 
calling directly into the LLM API (the OpenAI _completion_ API via _Litellm_).
- Logging is **built-in** and usable out of the box. Trace agent runs, tool calls, and LLM completions
with ability to control the right level of detail.
- Very simple and well designed abstractions with just a few nouns: Agent, Tool, Run, Pipeline. You can easily
build complex agent teams and flows, but don't have to assemble the _computational graph_ by hand.
- Agents are asynchronous and generate typed events, not just text. Consuming an event stream
allows lots of rich interactions and different media types.
- Event streams can have _multiple channels_, so your agent can "run in the background" and
still notify you of what is happening.
- Human-in-the-loop is built into the framework, not hacked in. An agent can wait indefinitely,
or get notification from any channel like an email or webhook.
- Context length, token usage, and timing usage data is emitted in a standard form.
- Tools are designed to support configuration and authentication, not just run on a sea of random env vars.
- Use tools from almost any framework, including MCP and Composio.
- "Tools are agents". You can use tools and agents interchangeably. This is where the world is heading, that 
whatever "service" your agent uses it will be indistinguishable whether that service is "hard-coded" or
implemented by another agent.
- Agents can add or remove tools dynamically while they are running.
(coming soon...)
- "Batteries included". Easy RAG support. Every agent has an API interface. UI tools for quickly
building a UI for your agents. "Agent contracts" for testing.
- Automatic context management keeps your agent within context length limits.



