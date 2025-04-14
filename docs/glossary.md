# Glossary

## A

### Agentic
Our opinionated framework for creating AI agents! Agentic is an easy-to-use, developer-first framework with the goal of mass agent development for everyone from hobbiests to professionals.

### Agent
A named unit of execution powered by an LLM that supports operations, maintains state, and uses tools to interact with the world. An agent has instructions, tools, and context which it uses to perform tasks.

### Agent Protocol
A reference implementation built by us that standardizes how agents communicate and operate, enabling interoperability between different agent frameworks.

### Agent Teams
A group of specialized agents working together to solve a larger problem. Agents on the team have distinct functions and capabilities. This is usually constructed with an orchestrator agent that calls other agents as tools. [Deep Researcher Example](https://github.com/supercog-ai/agentic/blob/main/examples/deep_research/oss_deep_research.py)

### `AgentRunner`
A utility class that provides a REPL interface for interacting with agents via the CLI. Running one of our example agent files with start the agent runner: e.g. `python examples/basic_agent.py`.

## B

### `BaseAgentProxy`
A base class for implementing custom agents. Handles concerns like event dispatching, tool binding, and parallel operations.

## C

### Chat History
The running record of turns between the agent and user in the current [thread](#thread). Consumes part of the LLM context window.

### Context Window
The number of [tokens](#token) an agent can utilize when executing in a thread. Each LLM has a different context window. Smaller context windows lower execution costs but also limit ability.

## D

### Depth
An attribute of events that indicates how deep in the agent call tree the event originated. Depth is increased by one for each level down the agent tree an event is emitted from. An event emmited by the orchestrating agent has a depth of 0, an event emitted by a child agent would have a depth of 1, etc.

## E

### Event
Data emitted during agent execution, such as chat output, tool calls and results, or completion events. Events are keyed to specific [runs](#run) and [threads](#thread). See [Event System](./core-concepts/event-system.md) and [Event Types](./core-concepts/event-types.md) for more information.

## F

### Function Calling
The protocol where an LLM generates a structured text block that is parsed into a tool's function call, allowing agents to use tools.

## H

### Handoff
When one agent transfers control to another agent, stopping its own processing. The second agent assumes the context, caller relationship, and depth of the first agent.

### Human-in-the-Loop
A design pattern where agents pause execution to request input from human operators, then resume processing with that input.

## I

### Instructions
The system guidelines provided to an agent that define its purpose, behavior, and approach to tasks. Instructions can range from general guidance ("You are a helpful assistant") to specific step-by-step procedures for completing complex tasks. They essentially program the agent's behavior by steering the underlying LLM in a particular direction. Good instructions are clear, specific about the agent's role, and provide appropriate guardrails for the desired behavior.

## L

### Litellm
An [open source](https://github.com/BerriAI/litellm) package that Agentic uses to make calls to LLMs.

### LLM (Large Language Model)
The AI model powering an agent's reasoning and text generation capabilities. Agentic supports various LLMs through Litellm.

### `LocalAgentProxy`
An implementation of the agent runtime that uses basic threads for execution. This is the runtime that is used by default.

## M

### MCP (Model Context Protocol)
A [protocol](https://modelcontextprotocol.io/introduction) developed by Anthropic for tools that extends the capabilities of LLMs. It allows for easy tool integration into Agentic.

### Memory
The various ways agents store and retrieve information, including short-term (run history), persistent facts, and RAG-based vector storage. With Agentic you can implement long-term memory by adding `memories (list[str])` to your agent declaration.

## O

### Ollama
A system for running local LLM models that Agentic supports for agent operation.

## P

### Pipeline
A pattern for connecting multiple agents in sequence, where the output of one agent is used as input for the next.

### Prompt
A message sent to an agent to request it to perform an operation. This initiates a [run](#run).

## R

### RAG (Retrieval Augmented Generation)
A local knowledge base that indexes documents and media into a vector database. This information can then be queried by the agent at runtime to help it complete its task.

### `RayAgentProxy`
A distributed processing system that can be used as an alternative runtime engine for agents.

### ReAct Agent
The default pattern for Agentic agents, which follows a cycle of Reasoning, taking Action, and observing the result.

### `ResumeWithInput`
An event sent to an agent to continue processing after a pause for human input.

### Run
A single operation request within a [thread](#thread), representing one full interaction cycle from user prompt to agent response.

### RunContext
An object that holds state during agent execution and provides access to system services, configuration, and secrets.

## S

### Secrets
Encrypted credentials stored in a local database that agents can use to access external services.

### Sequential Thinking
A mode where an agent breaks down complex reasoning into explicit steps.

### SQLite
A lightweight, serverless, self-contained database engine that Agentic uses for various storage needs. In the Agentic framework, SQLite is used to store encrypted secrets (in ~/.agentic) and run logs (in ./runtime). Unlike client-server database systems, SQLite reads and writes directly to ordinary disk files without requiring a separate server process. [SQLite docs](https://sqlite.org/about.html)

### System Prompt
The instructions provided to the LLM that guide the agent's behavior and purpose, set through the [instructions](#instructions) parameter.

## T

### Thread
A persistent conversation with an agent that maintains a history of runs. They can be thought of as a conversation, with multiple user / agent interactions.

### Token
The basic unit of text processing in LLMs. Tokens are fragments of words or characters that the model processes - typically a token is about 4 characters or 3/4 of a word in English. The number of tokens affects both the cost of using LLMs (as providers typically charge per token) and the context window size (maximum input+output length). In Agentic, token usage is tracked and displayed during agent runs to help monitor costs and performance.

### Tool
A function or capability that allows an agent to interact with the world, query data, or take actions. Tools are the AI-to-computer interface and are the core value added to agents along with [instructions](#instructions).

### Tool Library
A collection of pre-built tools provided by Agentic that agents can use for common tasks like web browsing, database access, API calls, etc.

### TurnEnd
An event marking the completion of an agent's processing for a particular [run](#run).

## V

### Vector Database
A database optimized for storing and retrieving vector embeddings, used in RAG systems to match queries with relevant document chunks.

## W

### `WaitForInput`
An event emitted when an agent needs human input to continue processing.

### Weaviate
The vector database used by Agentic for implementing RAG features.  [Weaviate docs](https://weaviate.io/developers/weaviate)

### Welcome Message
A string displayed to end users when they first interact with an agent, helping them understand its purpose.
