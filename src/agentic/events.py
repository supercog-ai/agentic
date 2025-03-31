# Shutup stupid pydantic warnings
import warnings
import typing
import uuid
from typing import Dict

warnings.filterwarnings("ignore", message="Valid config keys have changed in V2:*")

from dataclasses import dataclass
from typing import Any, Optional
from typing_extensions import override
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
    request_context: dict = {}

    def __init__(
        self,
        agent: str,
        message: str,
        debug: DebugLevel,
        request_context: dict = {},
        depth: int = 0,
        ignore_result: bool = False,
        request_id: str|None = None,
    ):
        data = {
            "agent": agent,
            "type": "prompt",
            "payload": message,
            "depth": depth,
            "debug": debug,
            "ignore_result": ignore_result,
            "request_context": request_context,
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

    @classmethod
    def assistant_message(cls, agent: str, content: str, depth: int = 0):
        return cls(agent, {"content": content, "role": "assistant"}, depth)

    def __str__(self) -> str:
        return str(self.payload.get("content") or "")

    def __repr__(self) -> str:
        return repr(self.__dict__)


class ToolCall(Event):
    arguments: dict = {}

    def __init__(self, agent: str, name: str, arguments: dict, depth: int = 0):
        super().__init__(
            agent=agent,
            type="tool_call",
            payload={
                "name": name,
                "arguments": arguments
            },
            depth=depth
        )
        self.arguments = arguments

    def __str__(self):
        name = self.payload
        return "  " * (self.depth + 1) + f"[TOOL: {name} >> ({self.arguments})]\n"


class ToolResult(Event):
    result: Any = None

    def __init__(self, agent: str, name: str, result: Any, depth: int = 0):
        super().__init__(
            agent=agent,
            type="tool_result",
            payload={
                "name": name,
                "result": result
            },
            depth=depth
        )
        self.result = result

    def __str__(self):
        name = self.payload
        return "  " * (self.depth + 1) + f"[TOOL: {name}] <<\n{self.result}]\n"

class ToolError(Event):
    _error: str

    def __init__(self, agent: str, name: str, error: str, depth: int = 0):
        super().__init__(
            agent=agent,
            type="tool_error",
            payload={
                "name": name,
                "error": error
            },
            depth=depth
        )
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

    def __str__(self):
        return f"[{self.agent}] {self.payload}, tokens: {self.metadata}"

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
        """Safe result access with fallback"""
        try:
            return self.messages[-1]["content"] if self.messages else "No response generated"
        except (IndexError, KeyError):
            return "Error: Malformed response"

    def set_result(self, result: Any):
        self.messages[-1]['content'] = result

    @property
    def run_context(self):
        return self.payload["run_context"]

    def print(self, debug_level: str):
        if debug_level == "agents":
            return self._indent(f"[{self.agent}: finished turn]")
        return super().print(debug_level)

class TurnCancelled(Event):
    def __init__(self, agent: str, depth: int = 0):
        super().__init__(agent=agent, type="turn_cancelled", payload={}, depth=depth)

class TurnCancelledError(Exception):
    def __init__(self):
        super().__init__(f"Turn cancelled")

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
OAUTH_FLOW_SENTINEL = "__OAUTH_FLOW__"


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
    request_id: Optional[str] = None

    def __init__(self, agent, request_keys: dict, request_id: str|None = None):
        super().__init__(agent=agent, type="resume_with_input", payload=request_keys)
        self.request_id = request_id

    @property
    def request_keys(self):
        return self.payload

class OAuthFlow(Event):
    """Event emitted when OAuth flow needs to be initiated"""
    def __init__(self, agent: str, auth_url: str, tool_name: str, depth: int = 0):
        super().__init__(
            agent=agent, 
            type="oauth_flow",
            payload={"auth_url": auth_url, "tool_name": tool_name},
            depth=depth
        )

    def __str__(self):
        return self._indent(
            f"OAuth authorization required for {self.payload['tool_name']}.\n"
            f"Please visit: {self.payload['auth_url']}\n"
            "After authorizing, the flow will continue automatically."
        )

class OAuthFlowResult(Result):
    """Result indicating OAuth flow needs to be initiated"""
    request_keys: dict = {}

    def __init__(self, request_keys: dict):
        """
        Args:
            request_keys: Dictionary containing 'auth_url' and 'tool_name' keys
        """
        super().__init__(value=OAUTH_FLOW_SENTINEL)
        self.request_keys = request_keys

    @property
    def auth_url(self) -> str:
        return self.request_keys["auth_url"]
        
    @property
    def tool_name(self) -> str:
        return self.request_keys["tool_name"]

    @staticmethod 
    def matches_sentinel(value) -> bool:
        return value == OAUTH_FLOW_SENTINEL

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
    prompts: Dict[str, str] = {}

class StartRequestResponse(BaseModel):
    request_id: str
    run_id: Optional[str] = None
from sse_starlette.event import ServerSentEvent

class SSEDecoder:
    _data: list[str]
    _event: str | None
    _retry: int | None
    _last_event_id: str | None

    def __init__(self) -> None:
        self._event = None
        self._data = []
        self._last_event_id = None
        self._retry = None

    def iter_bytes(self, iterator: typing.Iterator[bytes]) -> typing.Iterator[ServerSentEvent]:
        """Given an iterator that yields raw binary data, iterate over it & yield every event encountered"""
        for chunk in self._iter_chunks(iterator):
            # Split before decoding so splitlines() only uses \r and \n
            for raw_line in chunk.splitlines():
                line = raw_line.decode("utf-8")
                sse = self.decode(line)
                if sse:
                    yield sse

    def _iter_chunks(self, iterator: typing.Iterator[bytes]) -> typing.Iterator[bytes]:
        """Given an iterator that yields raw binary data, iterate over it and yield individual SSE chunks"""
        data = b""
        for chunk in iterator:
            for line in chunk.splitlines(keepends=True):
                data += line
                if data.endswith((b"\r\r", b"\n\n", b"\r\n\r\n")):
                    yield data
                    data = b""
        if data:
            yield data

    def decode(self, line: str) -> ServerSentEvent | None:
        # See: https://html.spec.whatwg.org/multipage/server-sent-events.html#event-stream-interpretation  # noqa: E501

        if not line:
            if not self._event and not self._data and not self._last_event_id and self._retry is None:
                return None

            sse = ServerSentEvent(
                event=self._event,
                data="\n".join(self._data),
                id=self._last_event_id,
                retry=self._retry,
            )

            # NOTE: as per the SSE spec, do not reset last_event_id.
            self._event = None
            self._data = []
            self._retry = None

            return sse

        if line.startswith(":"):
            return None

        fieldname, _, value = line.partition(":")

        if value.startswith(" "):
            value = value[1:]

        if fieldname == "event":
            self._event = value
        elif fieldname == "data":
            self._data.append(value)
        elif fieldname == "id":
            if "\0" in value:
                pass
            else:
                self._last_event_id = value
        elif fieldname == "retry":
            try:
                self._retry = int(value)
            except (TypeError, ValueError):
                pass
        else:
            pass  # Field is ignored.

        return None
