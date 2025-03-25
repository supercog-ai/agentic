Agentic makes it easy to create AI agents - autonomous software programs that understand natural language
and can use tools to do work on your behalf.

Agentic is in the tradition of _opinionated_ frameworks_. We've tried to encode lots of sensisible
defaults and best practices into the design, testing and deployment of agents. 

Agentic is a few different things:

- A lightweight agent framework. Same part of the stack as SmolAgents or PydanticAI.
- A reference implementation of the [agent protocol](https://github.com/supercog-ai/agent-protocol).
- An agent runtime built on [Ray](https://github.com/ray-project/ray)
- An optional "batteries included" set of features to help you get running quickly:
    * Built in FastAPI [API](./rest-api.md) for your agent
    * Basic [RAG](./rag.md) features
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
- Interoperate with agents built with other frameworks

## Pre-built agents you can run today

### [OSS Operator](https://github.com/supercog-ai/agentic/blob/main/examples/oss_operator.py)

...full browser automation, including using authenticated sessions...

### [Podcast Producer](https://github.com/supercog-ai/agentic/blob/main/examples/podcast.py)

An agent team which auto-produces and publishes a daily podcast. Customize for your news interests.

### [Meeting Notetaker](https://github.com/supercog-ai/agentic/blob/main/examples/meeting_notetaker.py)

[Coming soon] Your own meeting bot agent with meeting summaries stored into RAG.

### Personal Data Analyst

[Coming soon]

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

Let's build our first agent. We'll start with the "Hello World" of agents, an agent which can
give us a weather report.

Create a new file `./agents/weather.py`, and add this code:

```python
from agentic.common import Agent, AgentRunner
from agentic.tools.weather_tool import WeatherTool

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

Now let's run our agent. Note that you will need to configure your OpenAI API key. If you
want to use a different LLM, including running a model locally, see the intstructions
at [models](./models.md).

```sh
    agentic set-secret OPENAI_API_KEY=<your key>
```

```sh
(.venv) % python agents/weather.py 
I can give you some weather reports! Just tell me which city.
press <ctrl-d> to quit
[Weather Agent]> what is the weather like in NYC?
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

That's it. We've created an agent, powered by the GPT-4o-mini LLM, and given it a tool which
it can use to retrieve weather reports. (The weather info is provided by https://open-meteo.com.)

Try running some of the other example agents to get a feel for the framework.

Try `examples/database/database_agent.py` for a basic Text-to-SQL agent.


# Understanding Agents

Agentic agents by default use the LLM **ReAct** pattern. This means:

- The LLM controls the execution flow of your agent
- You specify the tasks and flow of your agent via the LLM system prompt
- The agent gets one or more **tools** that it can use to accomplish its task
- The agent runs in this loop until it decides that it can't go further:
    - plan next step
    - generate text completion or tool call
        (platform executes tool call)
    - observe tool call results

## Components of an agent

An agent is _defined_ by its behavior - what is does as perceived from the outside. But
inside each agent has these properties:

- name
- instructions
- list of tools
- list of children agents
- chosen LLM model
- a 'welcome' message explaining the purpose of the agent

Notice that agents can call both `tools`, which are regular code functions, or
other agents, in the same way. 

Calling "sub agents" allows us to organize a set of multiple agents to solve
a single problem. The simplest example looks like this:

```python
from agentic.tools import GoogleNewsTool

producer = Agent(
    name="Producer",
    welcome="I am the news producer. Tell me the topic, and I'll get the news from my reporter.",
    instructions="You are a news producer. Call the reporter with the indicated topic.",
    model="gpt-4o-mini",
    tools=[
        Agent(
            name="News Reporter",
            instructions=f"""
        Call Google News to get headlines on the indicated news topic.
        """,
            tools=[GoogleNewsTool()],
        )
    ],
)
```
### Calling agents in sequence

Treating agents as a `subroutine` is useful, but sometimes we want `pipeline` semantics
where we want to invoke the next agent by "handing off" execution to that agent and
not waiting for it to return. We can just use the `handoff` property to do so:


```python
from agentic import handoff

agentA = Agent(
    name="Producer",
    welcome="This is the handoff demo.",
    instructions="Print the message 'I am A', then call agent B. Afterwards print 'WARNING!'",
    tools=[
        handoff(Agent(
            name="Agent B",
            instructions="Print the msssage 'and I am B'",
        ))
    ],
)

python examples/handoff_demo.py
This is the handoff demo.
> run
I am A
and I am B
> 
```
Without using `handoff` we would have seen the WARNING message printed from the root agent.
Handoff can be useful if your sub-agent generates a lot of output, because normally that
output when be fed back into AgentA as the `observation` step, which means both another
inference call to pay for, and means that AgentA may summarize or alter the results.


## The problem with function calling

Since the introduction of "function calling" by OpenAI, most frameworks have built around
the idea of agent "tools" as functions. Many have extended this idea to include calling
agents calling other _agents as tools_. 

The problem is that function calling generally assumes synchronous semantics and strictly 
typed parameters and return values. Both of these make poor assumptions when dealing with
AI agents. Since agents can easily be long-running, it is much better assume an event-driven
model (sending messages, and waiting for events) than a synchronous one. Strict typing
is useful in compiled code, but LLMs are really best with text and language, not strict
compiler types.

As you start building more complex agents, you want them to run longer, be decomposable
into multiple units, and have flexible behavior like stopping for human input. Agentic
is designed to make these more complex use cases easy.

## Tools as Agents

Agentic assumes an event driven model for agents. We send events to agents when we want
them to do something, and the agent publishes events back to us with the results. Because
event driven is so key, _tool calling_ is also event driven. Although the framework
hides most of the details, every tool (function) call happens asynchronously. One of
the implications of this design is that tools can "interrupt" the agent, and wait for
human input. When your agent is waiting for input it is effectively paused, consuming
no resources. This means that complex patterns like "send an email for clarification,
and wait for the reply" are easy and low-cost to build.

## Complete example

```python
from agentic import Agent, AgentRunner
from agentic.tools import LinkedinTool, HumanInterruptTool

researcher = Agent(
    name="Person Researcher",
    welcome="I am your People Researcher. Who would you like to know more about?",
    instructions="""
You do research on people. Given a name and a company:
1. Search for matching profiles on linkedin.
2. If you find a single strong match, then prepare a background report on that person. Make sure
to print the full report.
3. If you find multiple matches, then ask stop and ask the user for clarification. Then go back to step 1.
If you are missing info, then seek clarification from the user.
""",
    model="openai://gpt-4o-mini",
    tools=[
        LinkedinTool(), 
        HumanInterruptTool(),
        Agent(
            name = "Person Report Writer",
            instructions="""
        You will receive the URL to a linkedin profile. Retrieve the profile and
        write a background report on the person, focusing on their career progression
        and current role.
            """,
            tools=[LinkedinTool()],
            model="anthropic://claude-sonnet-3.5",
        )
    ]
)

runner = AgentRunner(agent)
runner.repl_loop()
```

**Breaking down our example**

First we define our top-level agent, the "Person Researcher", give it a goal
and a task list, an LLM model, and some tools:

- A linkedin tool for searching for linkedin profiles
- A "Human interrupt" tool which the agent can call to ask for human help

Now, we define a "sub agent" for this agent to use as another tool. This
is the "Person Report Writer" agent, with its own instruction and a 
different LLM model. We include this agent in the list of tools for the Researcher.

**Running our agent**

To run our agent, we construct an `AgentRunner`. This object manages
a single multi-turn session interacting with our agent.

Here is the complete (condensed) run output:

```markdown
(agentic) scottp@MacBook-Air agentic % python examples/people_researcher.py 
I am the People Researcher. Tell me who you want to know about.
> marc benioff
--> search_profiles({"name":"marc benioff"})
--> get_human_input({"request_message":"I found multiple profiles for Marc..."})
I found multiple LinkedIn profiles for Marc Benioff. Here are the details:

1. **Marc Benioff**  
   - **Headline:** Chair & CEO at Salesforce  
   ...

2. **Marc Benioff**  
   - **Headline:** Bachelor's degree at Brunel University London  
   ...
...
Please let me know which profile you would like to know more about. 
> 1
call_person_report_writer({"message":"Please prepare a background report on Marc Benioff..."})
--> get_profile({"url":"https://www.linkedin.com/in/marcbenioff"})
### Background Report on Marc Benioff
**Current Role:**
Marc Benioff is the Chair and CEO of Salesforce, a leading cloud-based software company headquartered in San Francisco, California. Under his leadership, Salesforce has become a pioneer in customer relationship management (CRM) software and has significantly influenced the tech industry with its innovative solutions and commitment to social responsibility.

**Career Progression:**
- **Early Career:** Marc Benioff began his career at Oracle Corporation, where he worked for 13 years. During his time at Oracle, he held various positions, gaining valuable experience in software development and sales.
...
```

We call `start` to start our agent.
Now we iteratively grab events from the agent until the turn is finished.

- The initial user prompt is passed to our Researcher agent. It considers
its instructions and the user input. Based on this it generates 
a tool call to `LinkedinTool.search_profiles`. 
- The `search_profiles` function is called, and the result is returned
to the agent, which "observes" this result and generates the next
event (the "observation" event.)
- The agent "loops" and determines that multiple profiles were returned,
so it prints the list (emits output events with the text), and then
creates a tool call to `get_human_input`.
- The runner returns the interrupt event, return True from `event.requests_input()`
to be the agent request. We print that request message, collect input from the user,
and then call `continue_with` on the runner with the response. The human response
will be returned as the value of the `get_human_input` tool call.
- On `runner.next` the agent considers that we specified to check the first
returned profile, so it generates
a tool call to `call_person_report_writer` to create the report. If the user had
responded "I don't know", then the agent could decide it can't go any further
and just finish the turn.
- The `call_person_report_writer` function now activates our "Person Report Writer"
agent, with the profile URL as input, but in a new LLM context. This agent calls
`get_profile` to get the full Linkedin profile, then writes the research report.
- Finally the report is returned to the parent agent, which prints the results.

### Things to note

We have used the convenience `repl_loop` in `AgentRunner` to interface to our agent.
But we can write our own loop (or API or whatever) to run our agent:

```python

runner.start(command)
for event in self.next_turn(request: str):
    print("Agent event: ", event)
```

The `next_turn` function will keep emitting events until the current turn of the agent is
complete. Because you are getting fine-grained events as the agent runs, you can
choose to do other things in the middle, including things like modifying the agent
by giving it more tools. Even though this interface looks like the agent is
"running" some thread (like in Langchain), in fact the agent runs step by step, generating
events along the way, but it can stop at any time.

Events have a `depth` attribute which indicates how deep is the agent that is
generating the event. So the top agent generates `depth=0`, the first level 
sub-agent generates at `depth=1` and so forth. 

The list of tools on an agent should be modifiable at any time:

    agent.add_tool(tool)
    agent.remove_tool(tool)

However, tools probably shouldn't modify the running agent directly. Safer that
they publish events like `EnableTool` which can be handled properly by the
framework (there might be security controls or what not).

**RunContext**

The state for your agent is kept and transmitted between turns via the `RunContext`
object. One is created each time a turn starts.
 
### Examples

Read [Examples](./examples.md) or look at the github repo [examples](https://github.com/supercog-ai/agentic/tree/main/examples) folder.

## Try the web UI (using streamlit)

    agentic ui




