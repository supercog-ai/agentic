import typing
import uuid
import warnings
import json
from datetime import timedelta
from litellm.types.utils import Message
from pydantic import BaseModel, ConfigDict
from typing import Any, Optional, Dict

from .swarm.types import Result, DebugLevel
from agentic.db.models import ThreadLog


# Shutup stupid pydantic warnings
warnings.filterwarnings("ignore", message="Valid config keys have changed in V2:*")

class Event(BaseModel):
    agent: str
    type: str
    payload: Any
    depth: int = 0

    model_config = ConfigDict(
        arbitrary_types_allowed=True
    )

    def to_llm_message(self) -> Optional[Message]:
        """Convert event to LLM message format if applicable"""
        return None

    @classmethod
    def from_thread_log(cls, log: 'ThreadLog') -> Optional['Event']:
        """Create an Event instance from a ThreadLog database record"""
        # This is the base implementation - subclasses should override
        return None

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

    @classmethod
    def from_thread_log(cls, log: 'ThreadLog') -> Optional['Prompt']:
        """Create a Prompt instance from a ThreadLog database record"""
        if log.event_name != "prompt":
            return None
            
        event_data = log.event
        return cls(
            agent=log.agent_id,
            message=event_data.get("content", ""),
            debug=DebugLevel(False),
            request_context=event_data.get("request_context", {}),
            depth=log.depth,
            request_id=event_data.get("request_id")
        )

class PromptStarted(Event):
    def __init__(self, agent: str, message: str|dict, depth: int = 0):
        if isinstance(message, str):
            message = {"content": message}
        super().__init__(agent=agent, type="prompt_started", payload=message, depth=depth)

    def print(self, debug_level: str):
        return self._indent(str(self))

    def to_llm_message(self) -> Optional[Dict[str, Any]]:
        """Convert event to LLM message format"""
        content = self.payload
        if isinstance(content, dict):
            content = content.get("content", "")
            # Handle buggy dual content structure
            if isinstance(content, dict):
                content = content.get("content", "")
        elif not isinstance(content, str):
            content = str(content)
            
        if content:
            return {
                "role": "user",
                "content": content,
            }
        return None

    @classmethod
    def from_thread_log(cls, log: 'ThreadLog') -> Optional['PromptStarted']:
        """Create a PromptStarted instance from a ThreadLog database record"""
        if log.event_name != "prompt_started":
            return None
            
        event_data = log.event
        # Handle the payload which could be a string or dict
        payload = event_data
        if isinstance(event_data, dict) and "content" in event_data:
            payload = event_data["content"]
            
        return cls(
            agent=log.agent_id,
            message=payload,
            depth=log.depth
        )

class ResetHistory(Event):
    def __init__(self, agent: str):
        super().__init__(agent=agent, type="reset_history", payload={})

    @classmethod
    def from_thread_log(cls, log: 'ThreadLog') -> Optional['ResetHistory']:
        """Create a ResetHistory instance from a ThreadLog database record"""
        if log.event_name != "reset_history":
            return None
            
        return cls(agent=log.agent_id)

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
    
    def to_llm_message(self) -> Optional[Dict[str, Any]]:
        """Convert event to LLM message format"""
        message = { "role": "assistant" }
        if isinstance(self.payload, str):
            message["content"] = self.payload
        elif isinstance(self.payload, dict):
            message["content"] = self.payload.get("content")
            
        return message

    @classmethod
    def from_thread_log(cls, log: 'ThreadLog') -> Optional['Output']:
        """Create an Output instance from a ThreadLog database record"""
        if log.event_name != "output":
            return None
            
        event_data = log.event
        return cls(
            agent=log.agent_id,
            message=event_data,
            depth=log.depth
        )

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

    def to_llm_message(self) -> Optional[Dict[str, Any]]:
        """Convert event to LLM message format"""
        content = ""
        if isinstance(self.payload, dict):
            content = self.payload.get("content", "")
        elif isinstance(self.payload, str):
            content = self.payload
            
        if content:
            return {
                "role": "assistant",
                "content": content,
            }
        return None

    @classmethod
    def from_thread_log(cls, log: 'ThreadLog') -> Optional['ChatOutput']:
        """Create a ChatOutput instance from a ThreadLog database record"""
        if log.event_name != "chat_output":
            return None
            
        event_data = log.event
        return cls(
            agent=log.agent_id,
            payload=event_data,
            depth=log.depth
        )


class ToolCall(Event):
    arguments: dict = {}
    tool_call_id: str = None

    def __init__(self, agent: str, name: str, arguments: dict, depth: int = 0, tool_call_id: str = None):
        super().__init__(
            agent=agent,
            type="tool_call",
            payload={
                "name": name,
                "arguments": arguments,
                "tool_call_id": tool_call_id
            },
            depth=depth
        )
        self.arguments = arguments
        self.tool_call_id = tool_call_id

    def __str__(self):
        name = self.payload["name"]
        return "  " * (self.depth + 1) + f"[TOOL: {name} >> ({self.arguments})]\n"
    
    def to_llm_message(self) -> Optional[Dict[str, Any]]:
        """Convert event to LLM message format"""
        tool_call = {
            "id": self.tool_call_id or f"call_{id(self)}",
            "type": "function",
            "function": {
                "name": self.payload.get("name", ""),
                "arguments": json.dumps(self.arguments) if self.arguments else "{}"
            }
        }
        
        return {
            "role": "assistant",
            "content": None,
            "tool_calls": [tool_call]
        }

    @classmethod
    def from_thread_log(cls, log: 'ThreadLog') -> Optional['ToolCall']:
        """Create a ToolCall instance from a ThreadLog database record"""
        if log.event_name != "tool_call":
            return None
            
        event_data = log.event
        return cls(
            agent=log.agent_id,
            name=event_data.get("name", ""),
            arguments=event_data.get("arguments", {}),
            depth=log.depth,
            tool_call_id=event_data.get("tool_call_id")
        )

class ToolResult(Event):
    result: Any = None
    tool_call_id: str = None

    def __init__(self, agent: str, name: str, result: Any, depth: int = 0, intermediate_result: bool = False, tool_call_id: str = None):
        super().__init__(
            agent=agent,
            type="tool_result",
            payload={
                "name": name,
                "result": result,
                "is_log": intermediate_result,
                "tool_call_id": tool_call_id
            },
            depth=depth,
        )
        self.result = result
        self.tool_call_id = tool_call_id

    def __str__(self):
        name = self.payload["name"]
        return "  " * (self.depth + 1) + f"[TOOL: {name}] <<\n{self.result}]\n"

    def to_llm_message(self) -> Optional[Dict[str, Any]]:
        """Convert event to LLM message format"""
        # Skip log messages
        if self.payload.get("is_log", False):
            return None
            
        if not self.tool_call_id:
            return None
            
        return {
            "role": "tool",
            "tool_call_id": self.tool_call_id,
            "content": str(self.result)
        }

    @classmethod
    def from_thread_log(cls, log: 'ThreadLog') -> Optional['ToolResult']:
        """Create a ToolResult instance from a ThreadLog database record"""
        if log.event_name != "tool_result":
            return None
            
        event_data = log.event
        return cls(
            agent=log.agent_id,
            name=event_data.get("name", ""),
            result=event_data.get("result"),
            depth=log.depth,
            intermediate_result=event_data.get("is_log", False),
            tool_call_id=event_data.get("tool_call_id")
        )

class ToolError(Event):
    _error: str
    tool_call_id: str = None

    def __init__(self, agent: str, name: str, error: str, depth: int = 0, tool_call_id: str = None):
        super().__init__(
            agent=agent,
            type="tool_error",
            payload={
                "name": name,
                "error": error,
                "tool_call_id": tool_call_id
            },
            depth=depth
        )
        self._error = error
        self.tool_call_id = tool_call_id

    @property
    def error(self):
        return self._error

    def print(self, debug_level: str):
        return str(self._error)

    def to_llm_message(self) -> Optional[Dict[str, Any]]:
        """Convert event to LLM message format"""
        if not self.tool_call_id:
            return None
            
        return {
            "role": "tool",
            "tool_call_id": self.tool_call_id,
            "content": {self._error}
        }

    @classmethod
    def from_thread_log(cls, log: 'ThreadLog') -> Optional['ToolError']:
        """Create a ToolError instance from a ThreadLog database record"""
        if log.event_name != "tool_error":
            return None
            
        event_data = log.event
        return cls(
            agent=log.agent_id,
            name=event_data.get("name", ""),
            error=event_data.get("error", ""),
            depth=log.depth,
            tool_call_id=event_data.get("tool_call_id")
        )


class StartCompletion(Event):
    def __init__(self, agent: str, depth: int = 0):
        super().__init__(agent=agent, type="completion_start", payload={}, depth=depth)

    @classmethod
    def from_thread_log(cls, log: 'ThreadLog') -> Optional['StartCompletion']:
        """Create a StartCompletion instance from a ThreadLog database record"""
        if log.event_name != "completion_start":
            return None
            
        return cls(
            agent=log.agent_id,
            depth=log.depth
        )


class ReasoningContent(Event):
    """Event to capture and display reasoning content from LLM models that support it"""
    
    def __init__(self, agent: str, reasoning_content: str, depth: int = 0):
        super().__init__(agent=agent, type="reasoning_content", payload={
            "reasoning_content": reasoning_content
        }, depth=depth)
    
    @property
    def reasoning_content(self) -> str:
        return self.payload.get("reasoning_content", "")
    
    @property
    def is_output(self):
        """Make reasoning content always visible like other output events"""
        return True
    
    def __str__(self):
        from .colors import Colors
        
        # Format with beautiful colors and visual separation
        brain_emoji = "🧠"
        separator = "━" * 50
        
        # Create visually separated header
        header = f"\n{Colors.OKCYAN}{separator}{Colors.ENDC}"
        header += f"\n{Colors.OKCYAN}{brain_emoji} REASONING PROCESS{Colors.ENDC}"
        header += f"\n{Colors.OKCYAN}{separator}{Colors.ENDC}"
        
        # Main reasoning content with full coloring
        content = f"{header}\n{Colors.OKCYAN}{Colors.ITALICS}{self.reasoning_content}{Colors.ENDC}"
        
        # Add closing separator
        footer = f"\n{Colors.OKCYAN}{separator}{Colors.ENDC}\n"
            
        return content + footer
    
    def print(self, debug_level: str):
        # Always show reasoning content with full formatting
        return self.__str__()

    @classmethod
    def from_thread_log(cls, log: 'ThreadLog') -> Optional['ReasoningContent']:
        """Create a ReasoningContent instance from a ThreadLog database record"""
        if log.event_name != "reasoning_content":
            return None
            
        event_data = log.event
        return cls(
            agent=log.agent_id,
            reasoning_content=event_data.get("reasoning_content", ""),
            depth=log.depth
        )


class FinishCompletion(Event):
    MODEL_KEY: typing.ClassVar[str] = "model"
    COST_KEY: typing.ClassVar[str]  = "cost"
    INPUT_TOKENS_KEY: typing.ClassVar[str] = "input_tokens"
    OUTPUT_TOKENS_KEY: typing.ClassVar[str] = "output_tokens"
    ELAPSED_TIME_KEY: typing.ClassVar[str] = "elapsed_time"
    REASONING_CONTENT_KEY: typing.ClassVar[str] = "reasoning_content"
    usage: dict = {}
    metadata: dict = {}
    llm_message: Message = None

    model_config = ConfigDict(
        arbitrary_types_allowed=True
    )

    def __init__(
        self, agent: str, llm_message: Message, usage: dict = {}, metadata: dict = {}, depth: int = 0
    ):
        # Serialize usage data before storing in payload
        serialized_usage = self._serialize_usage(usage)
        
        # Create payload with all data
        payload = {
            "usage": serialized_usage,
            "metadata": metadata,
            "llm_message": llm_message.model_dump() if hasattr(llm_message, 'model_dump') else dict(llm_message)
        }
        
        super().__init__(agent=agent, type="completion_end", payload=payload, depth=depth)
        self.usage = serialized_usage
        self.metadata = metadata
        self.llm_message = llm_message

    def _serialize_usage(self, usage: dict) -> dict:
        """Serialize usage data to handle timedelta objects"""
        serialized = {}
        for key, value in usage.items():
            if isinstance(value, timedelta):
                # Convert timedelta to total seconds
                serialized[key] = value.total_seconds()
            else:
                serialized[key] = value
        return serialized

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
        reasoning_content: str = None,
    ):
        usage = {
            cls.MODEL_KEY: model,
            cls.COST_KEY: cost or 0,
            cls.INPUT_TOKENS_KEY: input_tokens or 0,
            cls.OUTPUT_TOKENS_KEY: output_tokens or 0,
            cls.ELAPSED_TIME_KEY: elapsed_time or 0,
        }

        metadata = {}
        
        # Add reasoning data to metadata if present
        if reasoning_content:
            metadata[cls.REASONING_CONTENT_KEY] = reasoning_content

        if isinstance(llm_message, str):
            llm_message = Message(content=llm_message, role="assistant")

        return cls(agent, llm_message, usage, metadata, depth)

    @property
    def response(self) -> Message:
        return self.llm_message

    @property
    def reasoning_content(self) -> str:
        return self.metadata.get(self.REASONING_CONTENT_KEY, "")

    def __str__(self):
        base_str = f"[{self.agent}] {self.llm_message}, tokens: {self.usage}"
        if self.reasoning_content:
            base_str += f"\n[{self.agent}] 🧠 Reasoning: {self.reasoning_content}"
        return base_str

    @classmethod
    def from_thread_log(cls, log: 'ThreadLog') -> Optional['FinishCompletion']:
        """Create a FinishCompletion instance from a ThreadLog database record"""
        if log.event_name != "completion_end":
            return None
            
        event_data = log.event
        
        # Extract llm_message from the payload
        llm_message_data = event_data.get("llm_message", event_data)
        if isinstance(llm_message_data, dict):
            llm_message = Message(**llm_message_data)
        else:
            llm_message = Message(content=str(llm_message_data), role="assistant")
        
        return cls(
            agent=log.agent_id,
            llm_message=llm_message,
            usage=event_data.get("usage", {}),
            metadata=event_data.get("metadata", {}),
            depth=log.depth
        )

class TurnEnd(Event):
    def __init__(
        self, agent: str, messages: list, depth: int = 0
    ):
        messages_json = []
        for message in messages:
            if isinstance(message, Message):
                messages_json.append(message.model_dump())
            else:
                messages_json.append(message)

        super().__init__(
            agent=agent, type="turn_end", payload={"messages": messages_json}, depth=depth
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
    def thread_context(self):
        return self.payload["thread_context"]

    def print(self, debug_level: str):
        if debug_level == "agents":
            return self._indent(f"[{self.agent}: finished turn]")
        return super().print(debug_level)

    @classmethod
    def from_thread_log(cls, log: 'ThreadLog') -> Optional['TurnEnd']:
        """Create a TurnEnd instance from a ThreadLog database record"""
        if log.event_name != "turn_end":
            return None
            
        event_data = log.event
        return cls(
            agent=log.agent_id,
            messages=event_data.get("messages", []),
            depth=log.depth
        )

class TurnCancelled(Event):
    def __init__(self, agent: str, depth: int = 0):
        super().__init__(agent=agent, type="turn_cancelled", payload={}, depth=depth)

    @classmethod
    def from_thread_log(cls, log: 'ThreadLog') -> Optional['TurnCancelled']:
        """Create a TurnCancelled instance from a ThreadLog database record"""
        if log.event_name != "turn_cancelled":
            return None
            
        return cls(
            agent=log.agent_id,
            depth=log.depth
        )

class TurnCancelledError(Exception):
    def __init__(self):
        super().__init__(f"Turn cancelled")

class SetState(Event):
    def __init__(self, agent: str, payload: Any, depth: int = 0):
        super().__init__(agent=agent, type="set_state", payload=payload, depth=depth)

    @classmethod
    def from_thread_log(cls, log: 'ThreadLog') -> Optional['SetState']:
        """Create a SetState instance from a ThreadLog database record"""
        if log.event_name != "set_state":
            return None
            
        return cls(
            agent=log.agent_id,
            payload=log.event,
            depth=log.depth
        )

class AddChild(Event):
    handoff: Any = None

    def __init__(self, agent, remote_ref, handoff: bool = False):
        super().__init__(agent=agent, type="add_child", payload=remote_ref)
        self.handoff = handoff

    @property
    def remote_ref(self):
        return self.payload

    @classmethod
    def from_thread_log(cls, log: 'ThreadLog') -> Optional['AddChild']:
        """Create an AddChild instance from a ThreadLog database record"""
        if log.event_name != "add_child":
            return None
            
        event_data = log.event
        return cls(
            agent=log.agent_id,
            remote_ref=event_data.get("remote_ref"),
            handoff=event_data.get("handoff", False)
        )

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

    @classmethod
    def from_thread_log(cls, log: 'ThreadLog') -> Optional['WaitForInput']:
        """Create a WaitForInput instance from a ThreadLog database record"""
        if log.event_name != "wait_for_input":
            return None
            
        return cls(
            agent=log.agent_id,
            request_keys=log.event
        )

# Sent by the caller with human input
class ResumeWithInput(Event):
    request_id: Optional[str] = None

    def __init__(self, agent, request_keys: dict, request_id: str|None = None):
        super().__init__(agent=agent, type="resume_with_input", payload=request_keys)
        self.request_id = request_id

    @property
    def request_keys(self):
        return self.payload

    @classmethod
    def from_thread_log(cls, log: 'ThreadLog') -> Optional['ResumeWithInput']:
        """Create a ResumeWithInput instance from a ThreadLog database record"""
        if log.event_name != "resume_with_input":
            return None
            
        event_data = log.event
        return cls(
            agent=log.agent_id,
            request_keys=event_data.get("request_keys", {}),
            request_id=event_data.get("request_id")
        )

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

    @classmethod
    def from_thread_log(cls, log: 'ThreadLog') -> Optional['OAuthFlow']:
        """Create an OAuthFlow instance from a ThreadLog database record"""
        if log.event_name != "oauth_flow":
            return None
            
        event_data = log.event
        return cls(
            agent=log.agent_id,
            auth_url=event_data.get("auth_url", ""),
            tool_name=event_data.get("tool_name", ""),
            depth=log.depth
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
    thread_id: Optional[str] = None
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
