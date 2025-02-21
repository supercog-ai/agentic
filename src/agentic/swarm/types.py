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
    ):
        self._context = context
        self.agent_name = agent_name
        self.agent = agent
        self.debug_level = debug_level
        self.run_id = run_id

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
        """Generate a webhook endpoint URL for this agent and run.
        
        Args:
            callback_name: Name of the callback function to invoke 
            args: Optional query parameters to include
            host: Host address (default: localhost)
            port: Port number (default: 8086)

        Returns:
            str: Complete webhook URL with run_id and query parameters
        """
        host: str = "localhost" 
        port: int = 8086
        
        if not self.run_id:
            raise ValueError("No active run_id. Webhook endpoints require an active agent run.")
            
        # Use agent's safe_name (convert spaces/special chars to underscores)
        safe_name = "".join(c if c.isalnum() else "_" for c in self.agent_name).lower()
        
        # Build base URL
        base_url = f"http://{host}:{port}/{safe_name}/webhook/{self.run_id}/{callback_name}"
        
        # Add query parameters if provided
        if args:
            query_params = "&".join(f"{k}={v}" for k, v in args.items())
            return f"{base_url}?{query_params}"
        
        return base_url

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
