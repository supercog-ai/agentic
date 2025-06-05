# Tools

**Tools** are the fundamental way that your agent gets access to the world around it.
Tools can literally do anything - query any data or take any action - that you can think of.

It is tempting to think of tools the way we think about libraries that we use in traditional code,
but this is a mistake. In fact tools are the key component in the **AI to computer** interface. 
They determine how well the LLM can interact with the world, and the fidelity with which your
agent can perceive the world around it. Tools have a huge impact on the efficacy of agents,
and building agents often involves a lot of time working on tools (although we are getting
better "off the shelf" tools all the time.)

At root, tools are exposing _functions_ to your Agent. Using the _tool calling_ protocol developed
by OpenAI, your agent elects to call tools by generating a text block in its output, and this
output is parsed by the framework and turned into the actual function call.

> Side node: The _smolagents_ library from Huggingface promotes the idea of using 
> [CodeAgents](https://huggingface.co/blog/smolagents#code-agents) instead of tool calling. Some
> researchers have found that having your agent write _code_ - on demand - to call functions elicits
> superior results than traditional tool calling. It's certainly an intriguing notion, and one that
> we are testing presently.

Agentic supports providing tool functions as:

- Simple functions
- Class instance methods
- Langchain tools
- Model Context Protocol (from Anthropic) tools
- Other Agents

Here are a few examples:

``` python

def simple_function(arg1: int, arg2: int) ->:
    """ Multiplies two numbers by a mystery factor """
    
    return arg1 * arg2 * 23

class FileReaderTool:
    def get_tools(self) -> list[Callable]:
        return [
            self.read_file,
            self.write_file,
        ]

    def read_file(self, path: str) -> str:
        """ Returns the file at the given path """
        return open(path).read()

    def write_file(self, path: str, content: str) -> str:
        """ Writes the provided content to the indicated path """
        with open(path, "w") as f:
            f.write(content)
        return "The file was written"

agent = Agent(
    ...
    tools = [simple_function, FileReaderTool()]
)
```

Note that the _docstring_ is required to describe each function.

Here are some rules/guidelines for writing good tools:

- Generally we find classes and methods are a more useful form than bare functions. There
aren't a lot of bare functions that are super helpful tools.
- Using classes and methods means that you can keep state in your tool (via `self`) and
share it between function calls.
- The name of the function, the docstring, and the parameter names are all passed to the LLM.
Function names should very clearly explain the purpose of the function.
- You can describe parameter usage (possible values, etc...) in the docstring, but often
its enough to just have good parameter names.
- Try to avoid super generic function names like `read_file`, and consider prefixing 
functions with a namespace, like `github_read_file`.

Although you can always use "plain functions" for tools, Agentic has some special support
for particular tool patterns.

**ThreadContext**

When your agent is started, a `ThreadContext` object is created and preserved through the lifetime
of the run session. This object can hold arbitrary state that your agent can use
during the run. Tool functions just need to define a parameter called `thread_context` to receive
the object when they are invoked:

```
    def hello_func(self, thread_context: ThreadContext, message):
        print(message)
        print("I am running in agent: ", thread_context.agent.name)
```

ThreadContext also offers various utility methods for getting access to system services.

## Tool return types

The most common tool simply returns a _string_ which is provided to the LLM as the "anwer"
to the tool call.

However, tools can generally return any kind of object as long as it can be serialized into
a string. In particular dicts and lists of dicts will be automatically serialized as JSON
which most LLMs understand quite well.

## Configuration and Secrets

It is very common for tools to need some configuration or credentials in order to operate.
Agentic tries to provide some framework support to cover the most common cases:

    - For config, take parameters to the `__init__` function for your tool class
    - Configure secrets in the environment, but use `thread_context` to access them
    - Described required secrets by implementing the `required_secrets` method

Here is an example from the TavilyTool (for web search):

```python
class TavilySearchTool:
    def __init__(self, api_key: str = None):
        self.api_key = api_key

    def required_secrets(self) -> dict[str, str]:
        return {"TAVILY_API_KEY": "Tavily API key"}

    async def query_for_news(
        self, thread_context: ThreadContext, query: str, days_back: int = 1
    ) -> pd.DataFrame | PauseForInputResult:
        """Returns the latest headlines on the given topic."""

        api_key = thread_context.get_secret("TAVILY_API_KEY", self.api_key)
        ...
```
You can pass the API key to the init function, but more likely you want to configure that 
key in your environment. By implementing `required_secrets` you tell the framework
that your tool needs some credentials, and the framework will check that they are set, or
prompt the user to supply them.

Once your tool function is called (like 'query_for_news') then you can retrieve the
secrets from the ThreadContext. Look at Agentic's [secrets](../building-agents/index.md#secrets) system for a description
of how secrets are managed.

### Using environment configuration

In addition to secrets, you can store plaintext settings in your enviroment as well. Add
a setting with the CLI:

    agentic set <setting1> <value1>

and access it in your tool via `thread_context.get`.


## Implementing Human-in-the-Loop

Sometimes your tool will need some info from the human operator, and so your agent will need
to pause to wait for that input. You can achieve this with the `PauseForInputResult` class:

```
from agentic.events import PauseForInputResult

    def get_favorite_tv_show(self, thread_context):
        fave_tv = thread_context.get_setting("tv_show")
        if fave_tv is None:
            return PauseForInputResult({"tv_show": "Please indicate your favorite TV Show"})
        else:
            thread_context.set_setting("tv_show", fave_tv) # remember persistently
        return f"Ok, getting your favorite espiodes from {fave_tv}"
```
The first time your function is called it determines that the required
value is missing, so it returns the `PauseForInputResult` with the missing key and a message
describing what it needs. The message will be shown to the user, and their response will
be automatically set in the `thread_context` using the indicated key. Then your function will
be invoked **again**, but this time the setting should be available. You can choose to persist
the value so that the human doesn't get interrupted again on the next run, via `thread_context.set_setting`. 

If you want your agent to request "human input" directly, there is a convenience `HumanInterruptTool`
available.

### Generating Events / Logging

Remember that when you agent is running, it emits a stream of well-typed [events](../core-concepts/event-system.md).
It is possible for tool functions to also generate events. In this case these events will be
emitted by your agent, but they won't be revealed to the LLM. Only the actual return value
from your function is returned to the LLM.

A classic use case is generating logging events from a function:

```
    def long_running_function(self, thread_context) -> str:
        """ Runs a long operation and returns the result. """
        for x in range():
            yield ToolResult(thread_context.agent_name, "long_running_function", f"working on row {x})
            ... do some work

        return "The work is done! Thanks for waiting."
```

Building the event is toilsome, so `thread_context` has a convenience method:

    yield thread_context.log("Something interesting happened: ", param2, param2)

This builds and returns the `ToolResult` event for you.

Note that this style works for synchronous functions, but not async. In the async
case you need to yield the return value:

```
    async def long_running_function(self) -> str:
        """ Runs a long operation and returns the result. """
        for x in range():
            yield thread_context.log(f"working on row {x})
            ... do some work

        yield "The work is done! Thanks for waiting."
```

The generator is the right approach for true long-running tools, because otherwise your agent
cannot emit any status info while the function is running. However, for short-running functions
that still want to do logging, it is annoying to have to implement a generator.

So for convenience, you can log into the `thread_context` instead:

```
    def my_func_with_logging(self, thread_context: ThreadContext) -> str:
        """ An interesting functions. """
        for x in range():
            thread_context.log(f"working on row {x})
            ... do some work

        return "The work is done! Thanks for waiting."
```
Note that we didn't `yield` the log object. After your function returns, the system will 
automatically publish the `ToolResult` events from any messages logged by your function, 
and then proceed to process the function result.


**Adding tools dynamically**

You can add a tool to an agent at any time:


    agent.add_tool(tool)

and it will be availabe to the agent the next time it runs.
