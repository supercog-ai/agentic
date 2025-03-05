# Agentic

<p align="center"><a href="https://discord.gg/EmPGShjmGu"><img height="60px" src="https://user-images.githubusercontent.com/31022056/158916278-4504b838-7ecb-4ab9-a900-7dc002aade78.png" alt="Join our Discord!"></a></p>

![Screenshot 2025-02-24 at 12 13 31 PM](https://github.com/user-attachments/assets/9aeba0df-82b9-4c75-bb7a-d4fdacddfb29)

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

### [OSS Deep Researcher](https://github.com/supercog-ai/agentic/blob/main/examples/oss_deep_research.py)

Perform complex research on any topic. Adapted from the LangChain version (but you can actually
understand the code).

### [Agent Operator](https://github.com/supercog-ai/agentic/blob/main/examples/oss_operator.py)

...full browser automation, including using authenticated sessions...

### [Podcast Producer](https://github.com/supercog-ai/agentic/blob/main/examples/podcast.py)

An agent team which auto-produces and publishes a daily podcast. Customize for your news interests.

### [Meeting Notetaker](https://github.com/supercog-ai/agentic/blob/main/examples/meeting_notetaker.py)

[Coming soon] Your own meeting bot agent with meeting summaries stored into RAG.

### Personal Data Analyst

## Install

At this stage it's probably easiest to run this repo from source. We use `uv` for package managment:

```
git clone git@github.com:supercog-ai/agentic.git
cd agentic
uv pip install -e ".[all,dev]"
```

these commands will install the `agentic` package locally so that you can use the `agentic` cli command
and so your pythonpath is set correctly.

### Install the package

You can also try installing just the package:

`pip install agentic-framework`

Now setup your folder to hold your agents:

```sh
agentic init .
```

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

### Tests and docs

Run tests:

    pytest

Preview docs locally:

    mkdocs serve

Deploy the docs:

    mkdocs gh-deploy

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
- Well designed abstractions with just a few nouns: Agent, Tool, Thread, Run. Stop assembling
the _computational graph_ out of toothpicks.
- Rich event system goes beyond text so agents can work with data and media.
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

# Contributing

We would love you to contribute! We especially welcome:

- New tools
- Example agents
- New UI apps

but obviously we appreciate bug reports, bug fixes, etc... We encourage **tests** with all contributions,
but especially if you want to modify the core framework please submit tests in the PR.


