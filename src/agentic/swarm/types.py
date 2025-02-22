from openai.types.chat import ChatCompletionMessage
from openai.types.chat.chat_completion_message_tool_call import (
    ChatCompletionMessageToolCall,
    Function,
)
from typing import List, Callable, Union, Optional
from agentic.agentic_secrets import agentic_secrets
from agentic.settings import settings

# Third-party imports
from pydantic import BaseModel

AgentFunction = Callable[[], Union[str, "SwarmAgent", dict]] | dict


def agent_secret_key(agent_name: str, key: str) -> str:
    return f"{agent_name}/{key}"


def tool_name(tool) -> str:
    if hasattr(tool, "__name__"):
        return tool.__name__
    elif hasattr(tool, "__class__"):
        return tool.__class__.__name__
    else:
        return str(tool)


class DebugLevel:
    OFF: str = ""

    def __init__(self, level: str | bool):
        if isinstance(level, bool):
            if level == True:
                level = "tools,llm"
            else:
                level = ""
        self.level = str(level)

    def debug_tools(self):
        return self.level == "all" or "tools" in self.level

    def debug_llm(self):
        return self.level == "all" or "llm" in self.level

    def debug_agents(self):
        return self.level == "all" or "agents" in self.level

    def debug_all(self):
        return self.level == "all"

    def is_off(self):
        return self.level == ""

    def __str__(self) -> str:
        return str(self.level)


class RunContext:
    def __init__(
        self,
        agent,
        context: dict = {},
        agent_name: str = "",
        debug_level: DebugLevel = DebugLevel(DebugLevel.OFF),
        run_id: str = None,
        api_endpoint: str = None,
    ):
        self._context = context
        self.agent_name = agent_name
        self.agent = agent
        self.debug_level = debug_level
        self.run_id = run_id
        self.api_endpoint = api_endpoint

    def __getitem__(self, key):
        return self._context.get(key, None)

    def get(self, key, default=None):
        return self._context.get(key, default)

    def __setitem__(self, key, value):
        self._context[key] = value

    def update(self, context: dict):
        self._context.update(context)

    def get_agent(self) -> "Agent":
        return self.agent

    def get_setting(self, key, default=None):
        return settings.get(
            self.agent_name + "/" + key, settings.get(key, self.get(key, default))
        )

    def set_setting(self, key, value):
        settings.set(self.agent_name + "/" + key, value)

    def get_secret(self, key, default=None):
        return agentic_secrets.get_secret(
            agent_secret_key(self.agent_name, key),
            agentic_secrets.get_secret(key, self.get(key, default)),
        )

    def set_secret(self, key, value):
        return agentic_secrets.set_secret(
            self.agent_name + "/" + key,
            value,
        )

    def get_context(self) -> dict:
        return self._context

    def error(self, *args):
        print("ERROR:", *args)

    def info(self, *args):
        print("INFO:", *args)

    def debug(self, *args):
        if self.debug_level.debug_all():
            print("DEBUG:", *args)

    def warn(self, *args):
        print("WARNING:", *args)

    def get_webhook_endpoint(self, callback_name: str, args: dict = None) -> str:
        if not self.run_id:
            raise ValueError("No active run_id. Webhook endpoints require an active agent run.")
        
        if not self.api_endpoint:
            # Fallback to default if not set
            host = "localhost"
            port = 8086
            base_url = f"http://{host}:{port}/{self.agent_name}" 
        else:
            base_url = self.api_endpoint

        # Build webhook URL
        webhook_url = f"{base_url}/webhook/{self.run_id}/{callback_name}"
        
        if args:
            query_params = "&".join(f"{k}={v}" for k, v in args.items())
            return f"{webhook_url}?{query_params}"
        
        return webhook_url

    def __repr__(self):
        return f"RunContext({self._context})"


class SwarmAgent(BaseModel):
    name: str = "Agent"
    model: str = "gpt-4o"
    instructions_str: str = "You are a helpful agent."
    tool_choice: str = "auto"
    parallel_tool_calls: bool = True
    trim_context: bool = True
    max_tokens: bool = None

    def get_instructions(self, context: RunContext) -> str:
        return self.instructions_str


class Result(BaseModel):
    """
    Encapsulates the possible return values for an agent function.

    Attributes:
        value (str): The result value as a string.
        agent (Agent): The agent instance, if applicable.
    """

    value: str = ""
    agent: Optional[SwarmAgent] = None
    tool_function: Optional[Function] = None


class Response(BaseModel):
    messages: List = []
    agent: Optional[SwarmAgent] = None
    # These are meant to be updates to Run Context variables. But I think it's easier for
    # tools to just update RunContext directly.
    # Swarm used this dict to pass around state, but we are using RunContext instead.
    last_tool_result: Optional[Result] = None
