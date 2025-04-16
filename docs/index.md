# Home

Agentic makes it easy to create AI agents - autonomous software programs that understand natural language
and can use tools to do work on your behalf.

## What is Agentic?

Agentic is an opinionated framework that provides:

- A lightweight agent framework in the same part of the stack as SmolAgents or PydanticAI
- A reference implementation of the [agent protocol](https://github.com/supercog-ai/agent-protocol)
- An agent runtime built on threads with support for [Ray](https://github.com/ray-project/ray)
- A suite of "batteries included" features to help you get running quickly
    - Basic [RAG](./rag-support.md) features
    - Run history and logging
    - Simple UI examples built with [Streamlit](https://github.com/supercog-ai/agentic/tree/main/src/agentic/streamlit){target="_blank"} and [Next.js](https://github.com/supercog-ai/agentic/tree/main/src/agentic/dashboard){target="_blank"}

## Key Features

- **Simple but Powerful**: Approachable and easy to use, yet flexible enough for complex agent systems
- **Team Collaboration**: Support for teams of cooperating agents
- **Human-in-the-Loop**: Built-in support for human intervention and guidance
- **Tool Ecosystem**: Easy definition and use of tools with a growing library of production-ready tools, as well as the ability to create your own
- **Flexible Deployment**: Run agents as standalone applications, API services, or integrated components
- **Framework Interoperability**: Work with agents built using other frameworks

## Quick Install

> **Note**: Agentic requires Python 3.12. It does not work with Python 3.13+ due to [Ray compatibility issues](https://github.com/ray-project/ray/issues/50226).

```bash
# Install from PyPI
pip install agentic-framework

# Or run from source
git clone git@github.com:supercog-ai/agentic.git
cd agentic
uv pip install -e ".[all,dev]"

# Initialize your project
agentic init .
```

## Hello World Example

```python
from agentic.common import Agent, AgentRunner
from agentic.tools import WeatherTool

weather_agent = Agent(
    name="Weather Agent",
    welcome="I can give you some weather reports! Just tell me which city.",
    instructions="You are a helpful assistant.",
    tools=[WeatherTool()],
    model="openai/gpt-4o-mini"
)

if __name__ == "__main__":
    AgentRunner(weather_agent).repl_loop()
```

## Ready-to-Run Agents

Agentic comes with several pre-built agents you can run immediately:

- **[OSS Deep Researcher](https://github.com/supercog-ai/agentic/blob/main/examples/deep_research/oss_deep_research.py){target="_blank"}**: Writes detailed research papers on any topic with references
- **[OSS Operator](https://github.com/supercog-ai/agentic/blob/main/examples/oss_operator.py){target="_blank"}**: Full browser automation with authenticated sessions
- **[Podcast Producer](https://github.com/supercog-ai/agentic/blob/main/examples/podcast){target="_blank"}**: Auto-produces and publishes daily podcasts
- **[Meeting Notetaker](https://github.com/supercog-ai/agentic/blob/main/examples/meeting_notetaker.py){target="_blank"}**: Records and summarizes meetings
- **[Database Agent](https://github.com/supercog-ai/agentic/blob/main/examples/database/database_agent.py){target="_blank"}**: Text-to-SQL for data analysis using natural language

## Next Steps

- [Getting Started Guide](./getting-started.md) - Step-by-step introduction to Agentic
- [Core Concepts](./core-concepts/index.md) - Understand the fundamental ideas behind the framework
- [Examples](./example-agents.md) - Explore real-world agent examples
- [CLI Reference](./interacting-with-agents/cli.md) - Command-line interface documentation
