# Agentic - [Docs](https://supercog-ai.github.io/agentic/latest/)

<p align="center"><a href="https://discord.gg/EmPGShjmGu"><img height="60px" src="https://user-images.githubusercontent.com/31022056/158916278-4504b838-7ecb-4ab9-a900-7dc002aade78.png" alt="Join our Discord!"></a></p>

![Screenshot 2025-02-24 at 12 13 31 PM](https://github.com/user-attachments/assets/9aeba0df-82b9-4c75-bb7a-d4fdacddfb29)

[![Release Notes](https://img.shields.io/github/release/supercog-ai/agentic)](https://github.com/supercog-ai/agentic/releases)
[![CI](https://github.com/supercog-ai/agentic/actions/workflows/test-and-lint.yaml/badge.svg)](https://github.com/supercog-ai/agentic/actions/workflows/test-and-lint.yaml)
[![PyPI - License](https://img.shields.io/pypi/l/agentic)](https://opensource.org/licenses/MIT)
[![PyPI - Downloads](https://img.shields.io/pypi/dm/agentic)](https://pypistats.org/packages/agentic)
[![GitHub star chart](https://img.shields.io/github/stars/supercog-ai/agentic)](https://star-history.com/#supercog-ai/agentic)
[![Open Issues](https://img.shields.io/github/issues-raw/supercog-ai/agentic)](https://github.com/supercog-ai/agentic/issues)

Agentic makes it easy to create AI agents - autonomous software programs that understand natural language
and can use tools to do work on your behalf.

Agentic is in the tradition of _opinionated frameworks_. We've tried to encode lots of sensible
defaults and best practices into the design, testing and deployment of agents. 

Agentic is a few different things:

- A lightweight agent framework. Same part of the stack as SmolAgents or PydanticAI.
- A reference implementation of the [agent protocol](https://github.com/supercog-ai/agent-protocol).
- An agent runtime built on [Ray](https://github.com/ray-project/ray)
- An optional "batteries included" set of features to help you get running quickly:
  * Built in FastAPI API for your agent
  * Basic RAG features
  * A set of production-ready [tools](https://github.com/supercog-ai/agentic/tree/main/src/agentic/tools) (extracted from our Supercog product)
  * Agentic Chat UI examples in [NextJS](https://github.com/supercog-ai/agentic/tree/main/src/agentic/dashboard) and [Streamlit](https://github.com/supercog-ai/agentic/tree/main/src/agentic/streamlit)
  * A growing set of working [examples](https://github.com/supercog-ai/agentic/tree/main/examples)

You can pretty much use any of these features and leave the others. There are lots of framework choices but we think we have
embedded some good ideas into ours.

Some of the _framework_ features:

- Approachable and simple to use, but flexible enough to support the most complex agents
- Supports teams of cooperating agents
- Supports Human-in-the-loop
- Easy definition and use of tools (functions, class methods, import LangChain tools, ...)
- Built alongside a set of production-tested tools

Visit the docs: https://supercog-ai.github.io/agentic/latest/

## Pre-built agents you can run today

### [OSS Deep Researcher](https://github.com/supercog-ai/agentic/blob/main/examples/deep_research)

Perform complex research on any topic. Adapted from the LangChain version (but you can actually
understand the code).

### [Agent Operator](https://github.com/supercog-ai/agentic/blob/main/examples/oss_operator.py)

...full browser automation, including using authenticated sessions...

### [Podcast Producer](https://github.com/supercog-ai/agentic/blob/main/examples/podcast)

An agent team which auto-produces and publishes a daily podcast. Customize for your news interests.

### [Meeting Notetaker](https://github.com/supercog-ai/agentic/blob/main/examples/meeting_notetaker.py)

Your own meeting bot agent with meeting summaries stored into RAG.

## Install

At this stage it's probably easiest to run this repo from source. We use `uv` for package management:

> **Note** If you're on Linux or Windows and installing the `rag` extra you will need to add `--extra-index-url https://download.pytorch.org/whl/cpu` to install the CPU version of PyTorch.


```bash
git clone git@github.com:supercog-ai/agentic.git
uv venv  --python 3.12
source .venv/bin/activate

# For MacOS
uv pip install -e "./agentic[all,dev]"

# For Linux or Windows
uv pip install -e "./agentic[all,dev]" --extra-index-url https://download.pytorch.org/whl/cpu --index-strategy unsafe-first-match
```

these commands will install the `agentic` package locally so that you can use the `agentic` CLI command
and so your pythonpath is set correctly.

### Install the package

You can also try installing just the package:

```bash
# For MacOS
uv pip install "agentic-framework[all,dev]"

# For Linux or Windows
uv pip install "agentic-framework[all,dev]" --extra-index-url https://download.pytorch.org/whl/cpu
```

Now setup your folder to hold your agents:

```sh
agentic init .
```

The install will copy examples and a basic file structure into the directory `myagents`. You can name
or rename this folder however you like.

## Intro Tutorial

Visit [the docs](https://supercog-ai.github.io/agentic/latest/) for a tutorial on getting started
with the framework.

## Running Agents

Agentic provides multiple ways to interact with your agents, from command-line interfaces to web applications. This guide covers all available methods.

### Available Interfaces

| Interface | Use Case | Features |
|-----------|----------|----------|
| [Command Line (CLI)](#command-line-interface) | Quick testing, scripting | Simple text I/O, dot commands |
| [REST API](#rest-api) | Integration with other applications | HTTP endpoints, event streaming |
| [Next.js Dashboard](#nextjs-dashboard) | Professional web UI | Real-time updates, thread history, background tasks |
| [Streamlit Dashboard](#streamlit-dashboard) | Quick prototyping | Simple web UI with minimal setup |

### Command Line Interface

The CLI provides a simple REPL interface for direct conversations with your agents.

```bash
agentic thread examples/basic_agent.py
```

[Learn more about the CLI →](https://supercog-ai.github.io/agentic/latest/interacting-with-agents/cli/)

### REST API

The REST API allows integration with web applications, automation systems, or other services.

```bash
agentic serve examples/basic_agent.py
```

[Learn more about the API →](https://supercog-ai.github.io/agentic/latest/interacting-with-agents/rest-api/)

### Next.js Dashboard

The Next.js Dashboard offers a full-featured web interface with:

- Multiple agent management
- Real-time event streaming
- Background task management
- Thread history and logs
- Markdown rendering

```bash
agentic dashboard start --agent-path examples/basic_agent.py
```

[Learn more about the Next.js Dashboard →](https://supercog-ai.github.io/agentic/latest/interacting-with-agents/nextjs-dashboard/)


### Streamlit Dashboard

The Streamlit Dashboard provides a lightweight interface for quick prototyping.

```bash
agentic streamlit --agent-path examples/basic_agent.py
```

[Learn more about the Streamlit Dashboard →](https://supercog-ai.github.io/agentic/latest/interacting-with-agents/streamlit-dashboard/)

### Programmatic Access

You can always interact with agents directly in Python:

```python
from agentic.common import Agent

# Create an agent
agent = Agent(
    name="My Agent",
    instructions="You are a helpful assistant.",
    model="openai/gpt-4o-mini"
)

# Use the << operator for a quick response
response = agent << "Hello, how are you?"
print(response)

# For more control over the conversation
request_id = agent.start_request("Tell me a joke").request_id
for event in agent.get_events(request_id):
    print(event)
```

[Learn more about Programmatic Access →](https://supercog-ai.github.io/agentic/latest/interacting-with-agents/)

## Dependencies

Agentic builds on `Litellm` to enable consistent support for many different LLM models.

Under the covers, Agentic uses [Ray](https://github.com/ray-project/ray) to host and
run your agents. Ray implements an _actor model_ which implements a much better 
architecture for running complex agents than a typical web framework.

## API Keys

Agentic requires API keys for the LLM providers you plan to use. Copy the `.env.example` file to `.env` and set the following environment variables:

```
OPENAI_API_KEY=your_openai_api_key_here
ANTHROPIC_API_KEY=your_anthropic_api_key_here
```

You only need to set the API keys for the models you plan to use. For example, if you're only using OpenAI models, you only need to set `OPENAI_API_KEY`.

## Tests and docs

Run tests:

    pytest

Preview docs locally:

    mike serve

Deploy the docs:

    mike deploy --push dev

## Why does this exist?

Yup, there's a lot of agent frameworks. But many of these are "gen 1" frameworks - designed
before anyone had really built agents and tried to put them into production. Agentic is informed
by our learnings at Supercog from building and running hundreds of agents over the past year.

Some reasons why Agentic is different:

- We have a thin abstraction over the LLM. The "agent loop" code is a 
[couple hundred lines](./src/agentic/actor_agents.py) 
calling directly into the LLM API (the OpenAI _completion_ API via _Litellm_).
- Logging is **built-in** and usable out of the box. Trace agent threads, tool calls, and LLM completions
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

## Contributing

We would love you to contribute! We especially welcome:

- New tools
- Example agents
- New UI apps

but obviously we appreciate bug reports, bug fixes, etc... We encourage **tests** with all contributions,
but especially if you want to modify the core framework please submit tests in the PR.



## Troubleshooting Installation of Supercog AI's Agentic Framework

Note that the directions given here are _not_ the only way to set up agentic and get started with Supercog's Agentic library, instead these are the steps recommened if you’re having issues with the setup.

List of introduction videos, which was put together by Scott Persinger:

*   1) [Terminal basics](https://www.youtube.com/watch?v=aKRYQsKR46I) (Highly recommend)
    
*   2) [Learning Env Variables](https://www.youtube.com/watch?v=aKghi0hI1OA) 
    
*   3) [Virtual Environments](https://www.youtube.com/watch?v=Y21OR1OPC9A) (Highly recommend)
    
*   4) [uv](https://www.youtube.com/watch?v=AMdG7IjgSPM)
    
*   5) [HTTP Protocol and the Web](https://www.youtube.com/watch?v=qcALGDn0zpk&t=160s)
    
*   6) SQL [Vid 1](http://www.apple.com) & [Vid 2](https://www.khanacademy.org/computing/computer-programming/sql)
    

\*Note: While these videos were helpful, they’re very dense. If you're not familiar with these concepts, Start by watching videos 1, 3, and 4 and taking a few notes on them before starting, then going back and watching all of the videos when you’re further along in the process if you’re encountering difficulties not discussed below.


**Explanation of a “Hurdle”**

Each “hurdle” has a section header such as the one above, and contains a roadblock commonly encountered and what can be done to fix it. Sections _not_ under a hurdle header are the basic steps to get your agentic Agents running, and the steps that _are_ within hurdle sections should be executed _in addition to_ the basic steps, if and only if you are running into the same issue as the one described.

PROCESS PT. 1: Github, uv, SQL, and Docker

*   Set up Github:
    
    *   Sign up for an account at [github.com](http://github.com)
        
    *   Set up an SSH key with [these instructions](https://docs.github.com/en/authentication/connecting-to-github-with-ssh/adding-a-new-ssh-key-to-your-github-account)
        
        *   Note: Keep track of your “Passphrase,” you’ll need to use it later. If you lost your passphrase, try following [these instructions](https://docs.github.com/en/authentication/troubleshooting-ssh/recovering-your-ssh-key-passphrase). 
            
        *   Note: Also recommended to take a screenshot of the path to your identification and public key
            
*   Install uv
    
    *   Basic instructions [here](https://docs.astral.sh/uv/getting-started/installation/)
        
    *   Note: If you already have Homebrew installed (not a necessity) [(details on Homebrew here](https://brew.sh/)), use the command:  brew install uv in the Terminal
        
*   Install PostgresQL 
    
    *   Note: If you are using Homebrew, do this by entering this command in the Terminal: brew install postgresql
        
*   [Download Docker](https://www.docker.com/)
    

**Hurdle #1: What your Terminal prompt should look like (vs. what mine looked like, and why)**

When you first open your Terminal, you _should_ see something along the lines of: 

    me@My-MacBook-Air ~ %

(Note that the % may be the symbol $ instead, depending on whether you’re using bash or zsh. Either one is perfectly fine.)

When I opened my Terminal, this is what I saw: 

    (base) me@My-MacBook-Air ~ %

This is due to previously setting up my MacBook with Anaconda (which is a distribution platform for the languages Python and R). Now, my Terminal is set up to automatically be in this virtual environment (base). When initially trying to create a new virtual environment for agentic, I was trying to do so on top of this environment, which likely screwed up the automatic path configurations that the agentic environment was trying to make. 

To successfully install and set up agentic, I manually deactivated this (base) environment before beginning the process. 

Note: while usually you exit a virtual environment by entering the command: deactivate, this particular environment required the command:  conda deactivate

_Moral of the story: Make sure you aren’t already in a virtual environment when you start part 2 of the setup process._

PROCESS PT. 2: Installing & Initializing the Agentic Library

**Hurdle #2: Trying to Set Up the Dashboard**

Note that everything in the dashboard can be done in the Terminal, which means that getting the dashboard set up is not required for anything. I was able to get the Dashboard set up, but it did disorient me in the beginning of this process, and my personal recommendation is to work in the Terminal instead of the Dashboard until you’re more comfortable with the framework.

_Moral of the story: all functions of the Dashboard can be done in Terminal, so if you’re having issues, I recommend skipping setting up the Dashboard until you’ve set everything else up._

(Step A)

Enter into Terminal: 

    mkdir -p ~/agentic

    cd ~/agentic

Note: at this point, that last command should have taken you into your new “agentic” directory. If you’re unsure about this, the way to tell is that if you’re in a directory, your normal “Home” Terminal prompt will be followed by a space, the name of the directory you’re in, another space, and then either the % or $ symbol. So in this case, your normal “Home” Terminal prompt should be followed by a space, then either  agentic %  or agentic $

    Now, enter into Terminal: 

    uv venv --python 3.12

Note: at this point, the Terminal should respond with: 

    Using CPython 3.12.11

    Creating virtual environment at: .venv

    Activate with: source .venv/bin/activate

Now, enter into Terminal: 

    source .venv/bin/activate

You should see (agentic) in all Terminal prompts from now until you run the “deactivate” command later on.

(Step B)

Now, enter into Terminal:

    git clone [git@github.com](mailto:git@github.com):supercog-ai/agentic.git

At this point, the Terminal should respond with:

    Cloning into 'agentic'...

    Enter passphrase for key ‘/YourHomeDirectory/.ssh/id\_ed25519’:

Enter your passphrase for the SSH key you created in Github earlier and hit enter. At this point, the Terminal should respond with:

    remote: Enumerating objects: 7650, done.

    remote: Counting objects: 100% (1442/1442), done.

    remote: Compressing objects: 100% (560/560), done.

    remote: Total 7650 (delta 1077), reused 920 (delta 826), pack-reused 6208 (from 2)

    Receiving objects: 100% (7650/7650), 15.65 MiB | 3.69 MiB/s, done.

    Resolving deltas: 100% (4367/4367), done.

(Step C)

Now enter into Terminal: 

    uv pip install -e “./agentic\[all\]"

To which the Terminal should respond with something along the lines of:

    Resolved 212 packages in 1.71s

        Built agentic-framework @ file:///Users/abby/agentic/agentic

    Prepared 15 packages in 4.58s

    Installed 212 packages in 1.60s

 … followed by a long list of packages and their versions.

*   **Checkpoint: At this point, your Terminal prompts should have (agentic) at the beginning of each prompt and agentic with a space on either side of it at the end of each prompt (with some other stuff in the middle of each prompt).**
    

**If your Terminal prompt does** _**not**_ **contain both of these things:**

1.  **Check to make sure your agentic directory was created: Enter into Terminal:**
    

    cd ~

    ls

To which the Terminal will return a list of the directories in your home directory.

1.  **If “agentic” is in that list of directories, enter into Terminal: cd agentic then proceed to step 2.**
    
2.  **If “agentic” is** _**not**_ **in that list of directories, go back to the very beginning of Pt. 2 and start again from there.**
    
3.  **If your Terminal prompt does not start with (agentic):**
    

*   **Re-enter the virtual environment by entering into the Terminal: source .venv/bin/activate**
    

After making sure that both of the above checkpoint conditions are met, enter into Terminal: 

    agentic init . 

At which point the Terminal will return a message that your project was initialized successfully.

Now enter your openAI API key into Terminal:

    agentic secrets set OPENAI\_API\_KEY=_your\_key\_here_
 

PROCESS PT. 3: Starting to Build Your Own Agents

There are two different practices for building an agent on your own. I recommend going straight to “practice #2”.

*   **Practice #1: Setting up a simple file**
    
    *   Note that this is what is shown on the Supercog website’s “Getting Started” page, found [here](https://supercog-ai.github.io/agentic/latest/getting-started/) under the heading “Creating Your First Agent”. 
        
*   **Practice #2 (RECOMMENDED): Set Up a private Github Repository For Your New Agent**
    
    *   Step A: Create a GitHub repository with the following files:
        
        *   README.md
            
        *   your\_agent\_name.py
            
        *   .gitignore
            
        *   data\_sources.txt
            
        *   requirements.txt
            
    *   Step B: Clone that repository into your “agents” directory by doing the following:
        
        *   Go to your Agent’s Github Repository. 
            
        *   Click the green button “Code”, go to the SSH tab, and copy the url in that tab. It should look something like: [git@github.com](mailto:git@github.com):your\_profile\_name/your\_repository\_name
            
    *   Go into your “agents” directory by entering into the Terminal: cd ~/agentic/agents 
        
        *   Note: this step ensures that you will be running your agent from within your “agents” directory in Terminal. This means that in order to run an agent that you built, you will need to include the path from your “agents” directory to your desired agent’s .py file (this is accounted for in the steps for Pt. 4).
            
    *   Then enter into Terminal: git clone [git@github.com](mailto:git@github.com):your\_profile\_name/your\_repository\_name
        

*   **Checkpoint pt. 1: At this point, your Terminal prompts should have (agentic) at the beginning of each prompt and  agents % or  agents $ with a space before it at the end of each prompt (with some other stuff in the middle of each prompt).** 
    

**If your Terminal prompt does** _**not**_ **end with either agents % or  agents $: Enter into Terminal: cd ~/agentic/agents**

**If your Terminal prompt does** _**not**_ **begin with (agentic) :** 

*   **go to your agentic directory by entering the following command into Terminal: cd ~/agentic** 
    
*   **then enter into Terminal: source .venv/bin/activate**
    
*   **Now your Terminal prompt should start with (agentic). Return back to your agents directory by entering into Terminal: cd agents**
    
*   **Checkpoint pt. 2: Make sure that your new repository was created: enter the command ls into Terminal. It will return the contents of your agents folder. If your\_repository\_name is not listed, restart step B of Practice #2.**
    
*   To run your agent (after passing both checkpoints), enter into Terminal:
    

    python your\_repository\_folder\_name/your\_agent\_python\_file\_name.py

    

**Hurdle #3: Success Running the “Getting Started” Agent (Practice #1), but Not Your Own (Practice #2)**

When I got started, I started with Practice #1 and got that agent working just fine. However, I ran into a bunch of issues when trying to run my agent that I had built using practice #2. The confusion due to discrepancies in the processes are why I recommend just skipping to practice #2, but if you did try both and are having this issue, I’ve added my notes below.

The most likely reason for my second agent not running is that I was attempting to run that second agent from the wrong place, and/or not providing the necessary path the .py file for that agent. 

You should run your agent from within your “agents” directory in Terminal (as described in the instructions above). This means that in order to run an agent that you built, you will need to include the path from your “agents” directory to your desired agent’s .py file (this is accounted for in the steps for Pt. 4).

_Moral of the story: run your agents from inside your “agents” directory in Terminal, and put new agent repositories/directories inside the “agents” directory._

**Hurdle #4: Import Errors:**

*   **ModuleNotFoundError: No module named ‘agentic’**
    
*   **ModuleNotFoundError: No module named ‘rich’**
    
*   **Cannot import name ‘RAGTool’ from ‘agentic.tools’**
    
*   **Import agentic.common, agentic.tools, agentic.models, dotenv could not be resolved**
    

    I got these errors because I was running the agent from inside the wrong directory.

    _Moral of the story: Always be aware of where you’re running your agent from. I suggest running your agent from inside the ‘agents’ directory._

**Hurdle #5: Error in handle\_event callback**

This was because I was using Python 3.13, and was fixed by switching to 3.12.

 _Moral of the story: use Python 3.12_

**Hurdle #6: NameError: name 'openai' is not defined**

I got this error because I hadn’t properly set my OpenAI API Key. See Step C in Pt. 2 for details on how to add an API key to your environment variables.

**Hurdle #7: FileExistsError running AgentRunner(my\_agent).repl\_loop()**

This was due to some file ~/.agentic\_history being a directory, when it should be a file. To fix, first find the path to the file by entering into Terminal: 

    ls -ld ~/.agentic\_history

If this is in fact the cause of the error, Terminal will return something similar to (but with your info):

    drwxr-xr-x 2 abby staff 64 Jul 2 10:00 /Users/abby/.agentic\_history

If that is what Terminal returns, next you should enter into Terminal:

    mv ~/ agentic\_history ~/.agentic\_history\_backup

Now, when you run your agent, this error should be gone.

**Hurdle #8: NameError: name ‘load\_dotenv’ is not defined**

To fix this, I entered into Terminal: uv pip install python-dotenv

**Hurdle #9: ModuleNotFoundError: No module named ‘sqlmodel’**

To fix this, I entered into Terminal: uv pip install sqlmodel

**Hurdle #10 : \[My Agent: tool\_error\] … \\’401 Unauthorized\\’ …**

I got this error because I hadn’t set up the API key for the Tavily web search tool. I got a free API key from Tavily’s website, then entered into the Terminal:

    agentic secrets set TAVILY\_API\_KEY=your\_tavily\_api\_key\_here

_Moral of the story: Make sure you set all the necessary API keys into your environment variables._

PROCESS PT. 4: Shutting Down your Agent

*   To exit out of your agent shell, enter into your Terminal:
    
        ^d  (a.k.a. control d)

*   If that doesn’t work, try hitting ^c (a.k.a. control c) a couple of times.
    

PROCESS PT. 5: Running An Existing Agent

*   Open Terminal, and enter into Terminal: 
    

    cd ~/agentic

    source .venv/bin/activate

    cd agents

*   **Checkpoint: At this point, your Terminal prompts should have (agentic) at the beginning of each prompt and either  agents % or agents $ at the end of each prompt (with some other stuff in the middle of each prompt). If either of these conditions are not met, restart Pt. 4.**
    
*   Now, enter into Terminal:
    

    python your\_agent\_repository\_name/your\_agent\_python\_file\_name.py

This should successfully run your agent.




INDEX OF HURDLES

*   Hurdle #1: What your Terminal prompt should look like (vs. what mine looked like, and why)
    
*   Hurdle #2: Trying to Set Up the Dashboard
    
*   Hurdle #3: Success Running the “Getting Started” Agent (Practice #1), but Not Your Own (Practice #2)
    
*   Hurdle #4: Import Errors:
    
    *   ModuleNotFoundError: No module named ‘agentic’
        
    *   ModuleNotFoundError: No module named ‘rich’
        
    *   Cannot import name ‘RAGTool’ from ‘agentic.tools’
        
    *   Import agentic.common, agentic.tools, agentic.models, dotenv could not be resolved
        
*   Hurdle #5: Error in handle\_event callback
    
*   Hurdle #6: NameError: name 'openai' is not defined
    
*   Hurdle #7: FileExistsError running AgentRunner(my\_agent).repl\_loop()
    
*   Hurdle #8: NameError: name ‘load\_dotenv’ is not defined
    
*   Hurdle #9: ModuleNotFoundError: No module named ‘sqlmodel’
    
*   Hurdle #10 : \[My Agent: tool\_error\] … \\’401 Unauthorized\\’ …


