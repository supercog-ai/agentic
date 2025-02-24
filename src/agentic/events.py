# Shutup stupid pydantic warnings
import warnings
import typing
import uuid

warnings.filterwarnings("ignore", message="Valid config keys have changed in V2:*")

from dataclasses import dataclass
from typing import Any
from pydantic import BaseModel, ConfigDict
from .swarm.types import Result, DebugLevel, RunContext

from litellm.types.utils import ModelResponse, Message


class Event(BaseModel):
    agent: str
    type: str
    payload: Any
    depth: int = 0

    model_config = ConfigDict(
        arbitrary_types_allowed=True
    )

    def __str__(self) -> str:
        return str(f"[{self.agent}: {self.type}] {self.payload}\n")

    def print(self, debug_level: str):
        return str(self)

    def _indent(self, msg: str):
        return "\n" + "  " * self.depth + msg + "\n"

    def _safe(self, d, keys: list[str], default_val=None):
        for k in keys:
            if k in d:
                d = d[k]
            else:
                return default_val
        return d or default_val

    @property
    def is_output(self):
        return False


class Prompt(Event):
    # The 'originator' is meant to be the address of the top-level caller (the user's loop) into the
    # agent. This gets passed around into the agent call chain in case sub-agents need to communicate
    # back to the top. Note that in Thespian, we don't have this address until the first receiveMessage
    # is called, so we set it then.
    debug: DebugLevel
    request_id: str
    
    def __init__(
        self,
        agent: str,
        message: str,
        debug: DebugLevel,
        depth: int = 0,
        ignore_result: bool = False,
        request_id: str = None,
    ):
        data = {
            "agent": agent,
            "type": "prompt",
            "payload": message,
            "depth": depth,
            "debug": debug,
            "ignore_result": ignore_result,
        }
        data["request_id"] = request_id if request_id else uuid.uuid4().hex
        
        # Use Pydantic's model initialization directly
        BaseModel.__init__(self, **data)

    # Make a set method for 'message'
    def set_message(self, message: str):
        self.payload = message

class PromptStarted(Event):
    def __init__(self, agent: str, message: str, depth: int = 0):
        super().__init__(agent=agent, type="prompt_started", payload=message, depth=depth)

    def print(self, debug_level: str):
        return self._indent(str(self))

class ResetHistory(Event):
    def __init__(self, agent: str):
        super().__init__(agent=agent, type="reset_history", payload={})

class Output(Event):
    def __init__(self, agent: str, message: Any, depth: int = 0):
        super().__init__(agent=agent, type="output", payload=message, depth=depth)

    def __str__(self) -> str:
        return str(self.payload or "")

    def __repr__(self) -> str:
        return repr(self.__dict__)

    @property
    def is_output(self):
        return True


class ChatOutput(Output):
    def __init__(self, agent: str, payload: dict, depth: int = 0):
        super().__init__(agent=agent, message=payload, depth=depth)
        self.type = "chat_output"

    def __str__(self) -> str:
        return str(self.payload.get("content") or "")

    def __repr__(self) -> str:
        return repr(self.__dict__)


class ToolCall(Event):
    args: dict = {}

    def __init__(self, agent: str, name: str, args: dict, depth: int = 0):
        super().__init__(agent=agent, type="tool_call", payload=name, depth=depth)
        self.args = args

    def __str__(self):
        name = self.payload
        return "  " * (self.depth + 1) + f"[TOOL: {name} >> ({self.args})]\n"


class ToolResult(Event):
    result: Any = None

    def __init__(self, agent: str, name: str, result: Any, depth: int = 0):
        super().__init__(agent=agent, type="tool_result", payload=name, depth=depth)
        self.result = result

    def __str__(self):
        name = self.payload
        return "  " * (self.depth + 1) + f"[TOOL: {name}] <<\n{self.result}]\n"


class ToolOutput(Event):
    result: Any

    def __init__(self, agent: str, name: str, result: Any, depth: int = 0):
        super().__init__(agent=agent, type="tool_result", payload=name, depth=depth)
        self.result = result

    def __str__(self):
        name = self.payload
        return "  " * (self.depth + 1) + f"[TOOL: {name}] <<\n{self.result}]\n"

class ToolError(Event):
    _error: str

    def __init__(self, agent: str, func_name: str, error: str, depth: int = 0):
        super().__init__(agent=agent, type="tool_error", payload=func_name, depth=depth)
        self._error = error

    @property
    def error(self):
        return self._error

    def print(self, debug_level: str):
        return str(self._error)


class StartCompletion(Event):
    def __init__(self, agent: str, depth: int = 0):
        super().__init__(agent=agent, type="completion_start", payload={}, depth=depth)


class FinishCompletion(Event):
    MODEL_KEY: typing.ClassVar[str] = "model"
    COST_KEY: typing.ClassVar[str]  = "cost"
    INPUT_TOKENS_KEY: typing.ClassVar[str] = "input_tokens"
    OUTPUT_TOKENS_KEY: typing.ClassVar[str] = "output_tokens"
    ELAPSED_TIME_KEY: typing.ClassVar[str] = "elapsed_time"
    metadata: dict = {}

    model_config = ConfigDict(
        arbitrary_types_allowed=True
    )

    def __init__(
        self, agent: str, llm_message: Message, metadata: dict = {}, depth: int = 0
    ):
        super().__init__(agent=agent, type="completion_end", payload=llm_message, depth=depth)
        self.metadata = metadata

    @classmethod
    def create(
        cls,
        agent: str,
        llm_message: Message|str,
        model: str,
        cost: float,
        input_tokens: int | None,
        output_tokens: int | None,
        elapsed_time: float | None,
        depth: int = 0,
    ):
        meta = {
            cls.MODEL_KEY: model,
            cls.COST_KEY: cost or 0,
            cls.INPUT_TOKENS_KEY: input_tokens or 0,
            cls.OUTPUT_TOKENS_KEY: output_tokens or 0,
            cls.ELAPSED_TIME_KEY: elapsed_time or 0,
        }

        if isinstance(llm_message, str):
            llm_message = Message(content=llm_message, role="assistant")

        return cls(agent, llm_message, meta, depth)

    @property
    def response(self) -> Message:
        return self.payload


class TurnEnd(Event):
    def __init__(
        self, agent: str, messages: list, run_context: RunContext, depth: int = 0
    ):
        super().__init__(
            agent=agent, type="turn_end", payload={"messages": messages, "run_context": run_context}, depth=depth
        )

    @property
    def messages(self):
        return self.payload["messages"]

    @property
    def result(self):
        return self.messages[-1]["content"]

    @property
    def run_context(self):
        return self.payload["run_context"]

    def print(self, debug_level: str):
        if debug_level == "agents":
            return self._indent(f"[{self.agent}: finished turn]")
        return super().print(debug_level)


class SetState(Event):
    def __init__(self, agent: str, payload: Any, depth: int = 0):
        super().__init__(agent=agent, type="set_state", payload=payload, depth=depth)

class AddChild(Event):
    handoff: Any = None

    def __init__(self, agent, remote_ref, handoff: bool = False):
        super().__init__(agent=agent, type="add_child", payload=remote_ref)
        self.handoff = handoff

    @property
    def remote_ref(self):
        return self.payload


PAUSE_FOR_INPUT_SENTINEL = "__PAUSE4INPUT__"
PAUSE_FOR_CHILD_SENTINEL = "__PAUSE__CHILD"
FINISH_AGENT_SENTINEL = "__FINISH__"


class WaitForInput(Event):
    # Whenenever the agent needs to pause, either to wait for human input or a response from
    # another agent, we emit this event.
    def __init__(self, agent: str, request_keys: dict):
        super().__init__(agent=agent, type="wait_for_input", payload=request_keys)

    @property
    def request_keys(self) -> dict:
        return self.payload


# Sent by the caller with human input
class ResumeWithInput(Event):
    def __init__(self, agent, request_keys: dict):
        super().__init__(agent=agent, type="resume_with_input", payload=request_keys)

    @property
    def request_keys(self):
        return self.payload


class PauseForInputResult(Result):
    request_keys: dict = {}

    def __init__(self, request_keys: dict):
        super().__init__(value=PAUSE_FOR_INPUT_SENTINEL)
        self.request_keys=request_keys

    @staticmethod
    def matches_sentinel(value) -> bool:
        return value == PAUSE_FOR_INPUT_SENTINEL

# Special result which aborts any further processing by the agent.
class FinishAgentResult(Result):
    def __init__(self):
        super().__init__(value=FINISH_AGENT_SENTINEL)

    @staticmethod
    def matches_sentinel(value) -> bool:
        return value == FINISH_AGENT_SENTINEL

class AgentDescriptor(BaseModel):
    name: str
    purpose: str
    endpoints: list[str]
    operations: list[str] = ["chat"]
    tools: list[str] = []
