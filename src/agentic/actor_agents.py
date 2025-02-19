import asyncio
from typing import Any, Optional, Generator, Literal
from pydantic import BaseModel
from dataclasses import dataclass
from functools import partial
from collections import defaultdict
from pathlib import Path
import inspect
import json
import os
from copy import deepcopy
from pprint import pprint
from pathlib import Path
import os
import yaml
from jinja2 import Template
import ray
import traceback
from datetime import timedelta
from .swarm.types import agent_secret_key, tool_name
from ray import serve
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import yaml
from typing import Callable, Any, List
from pydantic import Field
from .swarm.types import (
    AgentFunction,
    Response,
    Result,
    RunContext,
    ChatCompletionMessageToolCall,
    Function,
)
from .swarm.util import (
    debug_print,
    debug_completion_start,
    debug_completion_end,
    function_to_json,
    looks_like_langchain_tool,
    langchain_function_to_json,
    wrap_llm_function,
)

from jinja2 import Template
import litellm
from litellm.types.utils import ModelResponse, Message
from litellm import completion_cost
from litellm import token_counter

from .swarm.types import (
    AgentFunction,
    ChatCompletionMessage,
    ChatCompletionMessageToolCall,
    Function,
    Response,
    Result,
    RunContext,
)
from .events import (
    Event,
    Prompt,
    PromptStarted,
    Output,
    ChatOutput,
    ToolCall,
    ToolResult,
    StartCompletion,
    FinishCompletion,
    FinishAgentResult,
    TurnEnd,
    SetState,
    AddChild,
    WaitForInput,
    PauseForInputResult,
    ResumeWithInput,
    DebugLevel,
    ToolError,
    AgentDescriptor,
)
from agentic.tools.registry import tool_registry

__CTX_VARS_NAME__ = "run_context"

# define a CallbackType Enum with values: "handle_turn_start", "handle_event", "handle_turn_end"
CallbackType = Literal["handle_turn_start", "handle_event", "handle_turn_end"]

# make a Callable type that expects a Prompt and RunContext
CallbackFunc = Callable[[Event, RunContext], None]

@dataclass
class AgentPauseContext:
    orig_history_length: int
    tool_partial_response: Response
    #    sender: Optional[Actor] = None
    tool_function: Optional[Function] = None


@ray.remote
class ActorBaseAgent:
    name: str = "Agent"
    model: str = "gpt-4o"
    instructions_str: str = "You are a helpful agent."
    tools: list[str] = []
    functions: List[AgentFunction] = []
    tool_choice: str = None
    parallel_tool_calls: bool = True
    paused_context: Optional[AgentPauseContext] = None
    debug: DebugLevel = DebugLevel(False)
    depth: int = 0
    children: dict = {}
    history: list = []
    # Memories are static facts that are always injected into the context on every turn
    memories: list[str] = []
    # The Actor who sent us our Prompt
    max_tokens: int = None
    run_context: RunContext = None
    _prompter = None
    _callbacks: dict[CallbackType, CallbackFunc] = {}
    class Config:
        arbitrary_types_allowed = True

    def __init__(self, name: str):
        super().__init__()
        self.name = name
        self.history: list = []

    def __repr__(self):
        return self.name

    def _get_llm_completion(
        self,
        history: List,
        run_context: RunContext,
        model_override: str,
        stream: bool,
    ) -> ChatCompletionMessage:
        """Call the LLM completion endpoint"""
        instructions = self.get_instructions(run_context)
        messages = [{"role": "system", "content": instructions}] + history

        tools = [function_to_json(f) for f in self.functions]
        # hide run_context from model
        for tool in tools:
            params = tool["function"]["parameters"]
            params["properties"].pop(__CTX_VARS_NAME__, None)
            if __CTX_VARS_NAME__ in params["required"]:
                params["required"].remove(__CTX_VARS_NAME__)

        create_params = {
            "model": model_override or self.model,
            "temperature": 0.0,
            "messages": messages,
            "tools": tools or None,
            "tool_choice": self.tool_choice,
            "stream": stream,
            "stream_options": {"include_usage": True},
        }
        if self.max_tokens:
            create_params["max_tokens"] = self.max_tokens

        if tools:
            create_params["parallel_tool_calls"] = self.parallel_tool_calls

        debug_params = create_params.copy()
        if debug_params.get("tools"):
            debug_params["tools"] = [
                f["function"]["name"] for f in debug_params["tools"]
            ]

        debug_completion_start(self.debug, self.model, debug_params)

        # Use LiteLLM's completion instead of OpenAI's client
        try:
            return litellm.completion(**create_params)
        except Exception as e:
            traceback.print_exc()
            raise RuntimeError("Error calling LLM: " + str(e))

    def _execute_tool_calls(
        self,
        tool_calls: List[ChatCompletionMessageToolCall],
        functions: List[AgentFunction],
        run_context: RunContext,
    ) -> tuple[Response, list[Event]]:
        """When the LLM completion includes tool calls, now invoke the tool functions.
        Returns the LLM processing response, and a list of events to publish
        """

        function_map = {f.__name__: f for f in functions}
        partial_response = Response(messages=[], agent=None)

        events = []

        for tool_call in tool_calls:
            name = tool_call.function.name
            # handle missing tool case, skip to next tool
            if name not in function_map:
                debug_print(
                    self.debug.debug_tools(), f"Tool {name} not found in function map."
                )
                partial_response.messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "tool_name": name,
                        "content": f"Error: Tool {name} not found.",
                    }
                )
                continue

            try:
                args = json.loads(tool_call.function.arguments)
            except Exception as e:
                debug_print(
                    self.debug.debug_tools(),
                    f"Error parsing tool call arguments: {e}\n"
                    + f"Tool call: {tool_call.function.arguments}",
                )
                args = {}

            # debug_print(
            #    self.debug.debug_tools(),
            #    f"Processing tool call: ", name, " with arguments:\n", args,
            # )

            func = function_map[name]
            if __CTX_VARS_NAME__ in func.__code__.co_varnames:
                args[__CTX_VARS_NAME__] = run_context

            events.append(ToolCall(self.name, name, args))

            # Call the function!!
            try:
                if asyncio.iscoroutinefunction(function_map[name]):
                    # Wrap async functions in asyncio.run
                    raw_result = asyncio.run(function_map[name](**args))
                elif inspect.isgeneratorfunction(function_map[name]):
                    # We use our generator for our call_child function. I guess we could let user's
                    # write generate functions as long as they yield events. Or we could catch
                    # strings and wrap them as events.
                    for child_event in function_map[name](**args):
                        if isinstance(child_event, TurnEnd):
                            raw_result = child_event.result
                            events.append(child_event)
                        elif isinstance(child_event, Result):
                            raw_result = child_event
                        else:
                            events.append(child_event)
                else:
                    raw_result = function_map[name](**args)
            except Exception as e:
                tb_list = traceback.format_exception(type(e), e, e.__traceback__)
                # Join all lines and split them to get individual lines
                full_traceback = "".join(tb_list).strip().split("\n")
                # Get the last 3 lines (or all if less than 3)
                last_three = (
                    full_traceback[-3:] if len(full_traceback) >= 3 else full_traceback
                )
                raw_result = f"Tool error: {name}: {last_three}"

                events.append(ToolError(self.name, name, raw_result, self.depth))
                # run_context.error(raw_result)

            # Let tools return additional events to publish
            if isinstance(raw_result, list):
                for result in raw_result:
                    if isinstance(result, Event):
                        events.append(result)
                raw_result = [result for result in raw_result if not isinstance(result, Event)]
                if raw_result:
                    # Would be good to allow multiple results and merge them
                    raw_result = raw_result[0]
                else:
                    raw_result = ""
                
            result: Result = (
                raw_result
                if isinstance(raw_result, Result)
                else Result(value=str(raw_result))
            )

            result.tool_function = Function(
                name=name,
                arguments=tool_call.function.arguments,
                _request_id=tool_call.id,
            )

            events.append(ToolResult(self.name, name, result.value))

            tool_name_key = ""
            partial_response.messages.append(
                {
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "name": name,
                    "content": result.value,
                }
            )
            partial_response.last_tool_result = result
            # This was the simple way that Swarm did handoff
            if result.agent:
                partial_response.agent = result.agent

        return partial_response, events

    def _yield_completion_steps(self, run_context: RunContext):
        llm_message = {
            "content": "",
            "sender": self.name,
            "role": "assistant",
            "function_call": None,
            "tool_calls": defaultdict(
                lambda: {
                    "function": {"arguments": "", "name": ""},
                    "id": "",
                    "type": "",
                }
            ),
        }
        yield StartCompletion(self.name, self.depth)

        self._callback_params = {}

        def custom_callback(
            kwargs,  # kwargs to completion
            completion_response,  # response from completion
            start_time,
            end_time,  # start/end time
        ):
            try:
                response_cost = kwargs[
                    "response_cost"
                ]  # litellm calculates response cost for you
                self._callback_params["cost"] = response_cost
            except:
                pass
            self._callback_params["elapsed"] = end_time - start_time

        # Assign the custom callback function
        litellm.success_callback = [custom_callback]

        # litellm._turn_on_debug()
        completion = None
        try:
            completion = self._get_llm_completion(
                history=self.history,
                run_context=run_context,
                model_override=None,
                stream=True,
            )
        except RuntimeError as e:
            yield FinishCompletion.create(
                self.name,
                Message(content=str(e), role="assistant"),
                self.model,
                0,
                0,
                timedelta(0),
                self.depth,
            )
            return

        # With 'streaming' we get the response back in chunks. For the output text
        # we want to emit events progressively with that output, but for tool calls
        # we just want to detect the single tool call and describe it in the final 'llm_result'
        # that we return at the end.

        chunks = []
        for chunk in completion:
            chunks.append(chunk)
            delta = json.loads(chunk.choices[0].delta.model_dump_json())
            if delta["role"] == "assistant":
                delta["sender"] = self.name
            if not delta.get("tool_calls") and delta.get("content"):
                yield ChatOutput(self.name, delta, self.depth)
            delta.pop("role", None)
            delta.pop("sender", None)

        llm_message = litellm.stream_chunk_builder(chunks, messages=self.history)
        input = self.history[-1:]
        output = llm_message.choices[0].message

        if len(input) > 0:
            self._callback_params["input_tokens"] = token_counter(
                self.model, messages=self.history[-1:]
            )
        if output.content:
            self._callback_params["output_tokens"] = token_counter(
                self.model, text=llm_message.choices[0].message.content
            )

        yield FinishCompletion.create(
            self.name,
            llm_message.choices[0].message,
            self.model,
            self._callback_params.get("cost", 0),
            self._callback_params.get("input_tokens"),
            self._callback_params.get("output_tokens"),
            self._callback_params.get("elapsed"),
            self.depth,
        )

    def handlePromptOrResume(self, actor_message: Prompt | ResumeWithInput):
        for event in self._handlePromptOrResume(actor_message):
            if self._callbacks.get('handle_event'):
                self._callbacks['handle_event'](event, self.run_context)
            yield event

    def _handlePromptOrResume(self, actor_message: Prompt | ResumeWithInput):
        if isinstance(actor_message, Prompt):
            # Middleware to modify the input prompt (or change agent context)
            self.run_context = (
                RunContext(
                    agent_name=self.name, agent=self, debug_level=actor_message.debug
                )
                if self.run_context is None
                else self.run_context
            )
            if self._callbacks.get('handle_turn_start') is not None:
                self._callbacks['handle_turn_start'](actor_message, self.run_context)
            self.debug = actor_message.debug
            self.depth = actor_message.depth
            init_len = len(self.history)
            self.history.append({"role": "user", "content": actor_message.payload})
            yield PromptStarted(self.name, actor_message.payload, self.depth)

        elif isinstance(actor_message, ResumeWithInput):
            # Call resuming us with user input after wait. We re-call our tool function after merging the human results
            if not self.paused_context:
                self.run_context.debug(
                    "Ignoring ResumeWithInput event, parent not paused: ",
                    actor_message,
                )
                return
            init_len = self.paused_context.orig_history_length
            # Copy human input into our context
            self.run_context.update(actor_message.request_keys.copy())
            # Re-call our tool function
            tool_function = self.paused_context.tool_function
            if tool_function is None:
                raise RuntimeError("Tool function not found on AgentResume event")
            # FIXME: Would be nice to DRY up the tool call handling
            partial_response, events = self._execute_tool_calls(
                [
                    ChatCompletionMessageToolCall(
                        id=(tool_function._request_id or ""),
                        function=tool_function,
                        type="function",
                    )
                ],
                self.functions,
                self.run_context,
            )
            yield from events
            self.history.extend(partial_response.messages)

        # MAIN TURN LOOP
        # Critically, if a "wait_for_human" tool is requested, then we save our
        # 'turn' state, send a 'gather_input' event, and then we return. The caller
        # should call send ResumeEvent when they have it and we will resume the turn.

        while len(self.history) - init_len < 10:
            for event in self._yield_completion_steps(self.run_context):
                # event] ", event.__dict__)
                yield event

            assert isinstance(event, FinishCompletion)

            response: Message = event.response

            debug_completion_end(self.debug, response)
            # debug_print(
            #    self.debug.debug_llm(), f"Completion finished:\n", response
            # )

            self.history.append(response)
            if not response.tool_calls:
                # No more tool calls, so assume this turn is done
                break

            # handle function calls
            partial_response, events = self._execute_tool_calls(
                response.tool_calls,
                self.functions,
                self.run_context,
            )
            yield from events

            # FIXME: handle this better, and handle the case of multiple tool calls

            last_tool_result: Result | None = partial_response.last_tool_result
            if last_tool_result:
                if isinstance(last_tool_result, PauseForInputResult):
                    # tool function has request user input. We save the tool function so we can re-call it when
                    # we get the response back
                    self.paused_context = AgentPauseContext(
                        orig_history_length=init_len,
                        tool_partial_response=partial_response,
                        tool_function=last_tool_result.tool_function,
                    )
                    yield WaitForInput(self.name, last_tool_result.request_keys)
                    return
                elif FinishAgentResult.matches_sentinel(
                    partial_response.messages[-1]["content"]
                ):
                    # short-circuit any further agent execution. But for chat history we need to
                    # record a result from the tool call
                    msg = deepcopy(partial_response.messages[-1])
                    msg["content"] = ""
                    self.history.extend(partial_response.messages)
                    break

            self.history.extend(partial_response.messages)
            # end of turn loop

        # Altough we emit interim events, we also publish all the messages from this 'turn'
        # in the final event. This lets a caller process our "function result" with a single event
        yield TurnEnd(
            self.name,
            self.history[init_len:],
            self.run_context,
            self.depth,
        )
        self.paused_context = None

    def call_child(
        self,
        child_ref,
        handoff: bool,
        message,
    ):
        depth = self.depth if handoff else self.depth + 1
        for remote_event in child_ref.handlePromptOrResume.remote(
            Prompt(
                self.name,
                message,
                depth=depth,
                debug=self.debug,
            )
        ):
            event = ray.get(remote_event)
            yield event

        if handoff:
            # by definition we don't care about remembering the child result since
            # the parent is gonna end anyway
            yield FinishAgentResult()

    def _build_child_func(self, event: AddChild) -> Callable:
        name = event.agent
        llm_name = f"call_{name.lower().replace(' ', '_')}"
        doc = f"Send a message to sub-agent {name}"

        return wrap_llm_function(
            llm_name, doc, self.call_child, event.remote_ref, event.handoff
        )

    def add_child(self, actor_message: AddChild):
        self.add_tool(actor_message)

    def add_tool(self, tool_func_or_cls):
        if isinstance(tool_func_or_cls, AddChild):
            tool_func_or_cls = self._build_child_func(tool_func_or_cls)

        if looks_like_langchain_tool(tool_func_or_cls):
            # Langchain tools which are single functions in a whole class inheriting from BaseTool
            self.functions.append(langchain_function_to_json(tool_func_or_cls))
            self.tools.append(self.functions[-1].__name__)
        else:
            if callable(tool_func_or_cls):
                self.functions.append(tool_func_or_cls)
                self.tools.append(self.functions[-1].__name__)
            else:
                if hasattr(tool_func_or_cls, "get_tools"):
                    self.functions.extend(tool_func_or_cls.get_tools())
                    self.tools.append(tool_func_or_cls.__class__.__name__)
                else:
                    print("ERROR: ", f"Tool {tool_func_or_cls} is not a callable, nor has 'get_tools' method")

    def reset_history(self):
        self.history = []

    def get_history(self):
        return self.history

    def inject_secrets_into_env(self):
        """Ensure the appropriate API key is set for the given model."""
        from agentic.agentic_secrets import agentic_secrets

        for key in agentic_secrets.list_secrets():
            if key not in os.environ:
                value = agentic_secrets.get_secret(key)
                if value:
                    os.environ[key] = value

    def get_instructions(self, context: RunContext):
        prompt = self.instructions_str
        if self.memories:
            prompt += """
<memory blocks>
{% for memory in MEMORIES -%}
{{memory|trim}}
{%- endfor %}
</memory>
"""
        return Template(prompt).render(
            context.get_context() | {"MEMORIES": self.memories}
        )

    def set_state(self, actor_message: SetState):
        self.inject_secrets_into_env()
        state = actor_message.payload
        remap = {"instructions": "instructions_str"}

        for key in [
            "name",
            "instructions",
            "model",
            "max_tokens",
            "memories",
        ]:
            if key in state:
                setattr(self, remap.get(key, key), state[key])

        if "handle_turn_start" in state:
            self._callbacks["handle_turn_start"] = state["handle_turn_start"]

        # Update our functions
        if "functions" in state:
            self.functions = []
            self.tools = []
            for f in state.get("functions"):
                self.add_tool(f)

        return Output(self.name, f"State updated: {actor_message.payload}", self.depth)

    def set_debug_level(self, debug: DebugLevel):
        self.debug = debug
        print("agent set new debug level: ", debug)

    def get_callback(self, key: CallbackType) -> Optional[CallbackFunc]:
        return self._callbacks.get(key)

    def set_callback(self, key: CallbackType, callback: Optional[CallbackFunc]):
        if callback is None:
            self._callbacks.pop(key, None)
        else:
            self._callbacks[key] = callback

    def list_tools(self) -> list[str]:
        return self.tools

    def list_functions(self) -> list[str]:
        def get_name(f):
            if hasattr(f, "__name__"):
                return f.__name__
            elif isinstance(f, dict):
                return f["name"]
            else:
                return str(f)

        return [get_name(f) for f in self.functions]

    def handle_request(self, method: str, data: dict):
        return f"Actor {self.name} processed {method} request with data: {data}"

class HandoffAgentWrapper:
    def __init__(self, agent):
        self.agent = agent

    def get_agent(self):
        return self.agent


def handoff(agent, **kwargs):
    """Signal that a child agent should take over the execution context instead of being
    called as a subroutine."""
    return HandoffAgentWrapper(agent)


_AGENT_REGISTRY: list = []


app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)
class ProcessRequest(BaseModel):
    prompt: str

from sse_starlette.sse import EventSourceResponse

@serve.deployment
@serve.ingress(app)
class DynamicFastAPIHandler:
    def __init__(self, actor_ref: ray.actor.ActorHandle, agent_facade: "RayFacadeAgent"):
        self._agent = actor_ref
        self.agent_facade = agent_facade
        self.debug = DebugLevel.OFF
        self.name = self.agent_facade.name
        self.prompt: ProcessRequest = None
    
    @app.post("/process")
    async def handle_post(self, prompt: ProcessRequest):
        self.prompt = prompt

    @app.get("/getevents", response_model=None)
    async def get_events(self, stream: bool = False) -> list[str]|EventSourceResponse:
        if not stream:
            results = []
            for event in self.next_turn(self.prompt.prompt):
                results.append(str(event))
            return results
        else:
            def render_events():
                for event in self.next_turn(self.prompt.prompt):
                    yield (str(event))
            return EventSourceResponse(render_events())

    @app.post('/stream_request')
    async def stream_request(self, prompt: ProcessRequest) -> EventSourceResponse:
        def render_events():
            for event in self.next_turn(prompt.prompt):
                yield (str(event))
        return EventSourceResponse(render_events())

    def next_turn(
        self,
        request: str,
        continue_result: dict = {},
        debug: DebugLevel = DebugLevel(DebugLevel.OFF),
    ) -> Generator[Event, Any, Any]:
        """This is the key agent loop generator. It runs the agent for a single turn and
        emits events as it goes. If a WaitForInput event is emitted, then you should
        gather human input and call this function again with _continue_result_ to
        continue the turn."""
        self.debug = debug
        event: Event
        if not continue_result:
            remote_gen = self._agent.handlePromptOrResume.remote(
                Prompt(
                    self.name,
                    request,
                    depth=0,
                    debug=self.debug,
                )
            )
        else:
            remote_gen = self._agent.handlePromptOrResume.remote(
                ResumeWithInput(self.name, continue_result),
            )
        for remote_next in remote_gen:
            event = ray.get(remote_next)
            yield event

    @app.get("/describe")
    async def describe(self) -> AgentDescriptor:
        return AgentDescriptor(
            name=self.agent_facade.name,
            purpose=self.agent_facade.welcome,
            tools=self.agent_facade.list_tools(),
            endpoints=["/process", "/getevents", "/describe"],
            operations=["chat"],
        )
    


class RayFacadeAgent:
    """The facade agent is the object directly instantiated in code. It holds a reference to the remote
    Ray agent object and proxies calls to it. The intention is that we should be able to build
    other 'agent' implementations that don't require Ray, for example are based on threads in a single process.
    """

    def __init__(
        self,
        name: str,
        instructions: str | None = "You are a helpful assistant.",
        welcome: str | None = None,
        tools: list = [],
        model: str | None = None,
        template_path: str | Path = None,
        max_tokens: int = None,
        enable_run_logs: bool = True,
        memories: list[str] = [],
        handle_turn_start: Callable[[Prompt, RunContext], None] = None,
        debug: DebugLevel = DebugLevel(DebugLevel.OFF),
    ):
        self.name = name
        self.welcome = welcome or f"Hello, I am {name}."
        self.model = model or "gpt-4o-mini"
        caller_frame = inspect.currentframe()
        if caller_frame:
            caller_file = inspect.getframeinfo(caller_frame.f_back).filename
            directory = os.path.dirname(caller_file)
            # Get just the filename without extension
            base = os.path.splitext(os.path.basename(caller_file))[0]

            # Create new path with .prompts.yaml extension
            template_path = os.path.join(directory, f"{base}.prompts.yaml")

        # Get the file where Agent() was called
        self.template_path = template_path
        self._tools = tools
        self.max_tokens = max_tokens
        self.memories = memories
        self.debug = debug
        self._handle_turn_start = handle_turn_start

        # Check we have all the secrets
        self._ensure_tool_secrets()

        # Initialize the base actor
        self._init_base_actor(instructions or "")

        # Initialize adding runs to the agent
        if enable_run_logs:
            from .run_manager import init_run_tracking
            self.run_manager = init_run_tracking(self)
        else:
            self.run_manager = None

        # Ensure API key is set
        self.ensure_api_key_for_model(self.model)
        _AGENT_REGISTRY.append(self)

    def _init_base_actor(self, instructions: str):
        # Process instructions if provided
        if instructions.strip():
            template = Template(instructions)
            self.instructions = template.render(**self.prompt_variables)
            if self.instructions.strip() == "":
                raise ValueError(
                    f"Instructions are required for {self.name}. Maybe interpolation failed from: {instructions}"
                )
        else:
            raise ValueError("Instructions are required")

        self._agent: ActorBaseAgent = ActorBaseAgent.remote(name=self.name)

        # Set initial state. Small challenge is that a child agent might have been
        # provided in tools. But we need to initialize ourselve
        obj_ref = self._agent.set_state.remote(
            SetState(
                self.name,
                {
                    "name": self.name,
                    "instructions": self.instructions,
                    "functions": self._get_funcs(self._tools),
                    "model": self.model,
                    "max_tokens": self.max_tokens,
                    "memories": self.memories,
                    "handle_turn_start": self._handle_turn_start,
                },
            ),
        )
        ray.get(obj_ref)

    def _create_fastapi_endpoint(self, port: int = 8086):
        serve.start(http_options={"host": "0.0.0.0", "port": port})
        deployment = serve.run(
            DynamicFastAPIHandler.bind(self._agent, self),
            route_prefix=f"/{self.safe_name}",
        )
        return deployment


    def start_api_server(self, port: int = 8086):
        self._create_fastapi_endpoint()

    def _ensure_tool_secrets(self):
        from agentic.agentic_secrets import agentic_secrets

        for tool in self._tools:
            if hasattr(tool, "required_secrets"):
                for key, help in tool.required_secrets().items():
                    value = agentic_secrets.get_secret(
                        agent_secret_key(self.name, key),
                        agentic_secrets.get_secret(key, os.environ.get(key)),
                    )
                    if not value:
                        value = input(f"{tool_name(tool)} requires {help}: ")
                        if value:
                            agentic_secrets.set_secret(
                                agent_secret_key(self.name, key), value
                            )
                        else:
                            raise ValueError(
                                f"Secret {key} is required for tool {tool_name(tool)}"
                            )

    def shutdown(self):
        pass

    def list_tools(self) -> list[str]:
        """Gets the current tool list from the running agent"""
        return ray.get(self._agent.list_tools.remote())

    def list_functions(self) -> list[str]:
        """Gets the current list of functions from the running agent"""
        return ray.get(self._agent.list_functions.remote())

    def add_tool(self, tool: Any):
        self._tools.append(tool)
        self._update_state({"functions": self._get_funcs(self._tools)})

    def _update_state(self, state: dict):
        obj_ref = self._agent.set_state.remote(SetState(self.name, state))
        ray.get(obj_ref)

    def set_model(self, model: str):
        self.model = model
        self._update_state({"model": model})

    def _get_funcs(self, thefuncs: list):
        useable = []
        for func in thefuncs:
            if callable(func):
                tool_registry.ensure_dependencies(func)
                useable.append(func)
            elif isinstance(func, RayFacadeAgent):
                # add a child agent as a tool
                useable.append(
                    AddChild(
                        func.name,
                        func._agent,
                    )
                )
            elif isinstance(func, HandoffAgentWrapper):
                # add a child agent as a tool
                useable.append(
                    AddChild(
                        func.get_agent().name,
                        func.get_agent()._agent,
                        handoff=True,
                    )
                )
            else:
                tool_registry.ensure_dependencies(func)
                useable.append(func)

        return useable

    def add_child(self, child_agent):
        self.add_tool(child_agent)

    @property
    def prompt_variables(self) -> dict:
        """Dictionary of variables to make available to prompt templates."""
        paths_to_search = [self.template_path]

        for path in [Path(p) for p in paths_to_search]:
            if path.exists():
                with open(path, "r") as f:
                    prompts = yaml.safe_load(f)
                return prompts

        return {"name": "John Doe"}

    @property
    def safe_name(self) -> str:
        """Renders the ActorAgent's name, but filesystem safe."""
        return "".join(c if c.isalnum() else "_" for c in self.name).lower()

    def ensure_api_key_for_model(self, model: str):
        """Ensure the appropriate API key is set for the given model."""
        from agentic.agentic_secrets import agentic_secrets

        for key in agentic_secrets.list_secrets():
            if key not in os.environ:
                value = agentic_secrets.get_secret(key)
                if value:
                    os.environ[key] = value

    def next_turn(
        self,
        request: str,
        continue_result: dict = {},
        debug: DebugLevel = DebugLevel(DebugLevel.OFF),
    ) -> Generator[Event, Any, Any]:
        """This is the key agent loop generator. It runs the agent for a single turn and
        emits events as it goes. If a WaitForInput event is emitted, then you should
        gather human input and call this function again with _continue_result_ to
        continue the turn."""
        self.debug = debug
        event: Event
        if not continue_result:
            remote_gen = self._agent.handlePromptOrResume.remote(
                Prompt(
                    self.name,
                    request,
                    debug=self.debug,
                    depth=0,
                )
            )
        else:
            remote_gen = self._agent.handlePromptOrResume.remote(
                ResumeWithInput(self.name, continue_result),
            )
        for remote_next in remote_gen:
            event = ray.get(remote_next)
            yield event

    def set_debug_level(self, level: DebugLevel):
        self.debug = level
        ray.get(self._agent.set_debug_level.remote(self.debug))

    def reset_history(self):
        ray.get(self._agent.reset_history.remote())

    def get_history(self):
        return ray.get(self._agent.get_history.remote())
        
    def set_run_tracking(self, enabled: bool, user_id: str = "default") -> None: #TODO: create a real user_id
        """Enable or disable run tracking for this agent"""
        if enabled and not self.run_manager:
            from .run_manager import init_run_tracking
            self.run_manager = init_run_tracking(self, user_id)
        elif not enabled and self.run_manager:
            from .run_manager import disable_run_tracking
            disable_run_tracking(self)
            self.run_manager = None
