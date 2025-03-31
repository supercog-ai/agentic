# Getting Started

This guide will walk you through installing Agentic, setting up your first agent, and understanding how it works.

## Installation

> **Note**: Agentic requires Python 3.12. It does not work with Python 3.13+ due to [Ray compatibility issues](https://github.com/ray-project/ray/issues/50226).

At this stage it's probably easiest to run this repo from source. We use `uv` for package management:

```bash
git clone git@github.com:supercog-ai/agentic.git
cd agentic
uv pip install -e ".[all,dev]"
```

These commands will install the `agentic` package locally so that you can use the `agentic` CLI command and your Python path is set correctly.

### Alternative: Install from PyPI

You can also install just the package from PyPI:

```bash
pip install agentic-framework
```

## Setting Up Your Project

Now set up your folder to hold your agents:

```bash
agentic init .
```

The install will copy examples and a basic file structure into the directory `agents`. You can name or rename this folder however you like.

## Creating Your First Agent

Let's build our first agent - a simple weather reporting agent.

Create a new file `./agents/weather.py`, and add this code:

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

## Configuring API Access

Before running your agent, you need to configure your OpenAI API key:

```bash
agentic set-secret OPENAI_API_KEY=<your key>
```

If you want to use a different LLM, including running a model locally, see the instructions at [models](./core-concepts/models.md).

## Running Your Agent

Now let's run our weather agent:

```bash
python agents/weather.py
```

You should see output like:

```
I can give you some weather reports! Just tell me which city.
press <ctrl-d> to quit
[Weather Agent]> What does the weather look like in NYC?
The current weather in New York City is as follows:

- **Temperature:** 0.5°C
- **Feels Like:** -4.9°C
- **Wind Speed:** 22.9 km/h
- **Wind Direction:** 278° (from the west)
- **Wind Gusts:** 45.0 km/h
- **Precipitation:** 0.0 mm
- **Cloud Cover:** 0%
- **Relative Humidity:** 53%
- **Visibility:** 37,000 m
- **UV Index:** 0.0
- **Daylight:** No (its currently dark)

It seems to be quite cold with a significant wind chill factor.
[openai/gpt-4o-mini: 2 calls, tokens: 162 -> 144, 0.02 cents, time: 3.81s tc: 0.02 c, ctx: 306]
[Weather Agent]> 
```

Congratulations! You've created an agent powered by the GPT-4o-mini LLM, and given it a tool which it can use to retrieve weather reports (provided by [Open-meteo](https://open-meteo.com)).

## Next Steps

- Learn more about [Agent Concepts](./core-concepts/index.md)
- Learn how to create your own [Tools](./tools/index.md)
- Explore the [Database Agent](https://github.com/supercog-ai/agentic/blob/main/examples/database/database_agent.py){target="_blank"} for a basic Text-to-SQL agent
- Discover how to build [Agent Teams](./building-agents/agent-teams.md)
