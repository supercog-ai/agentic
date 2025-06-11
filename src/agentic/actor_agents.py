import asyncio
import inspect
import json
import litellm
import os
import re
import threading
import time
import traceback
import uuid
import yaml
from pprint import pprint

from copy import deepcopy
from dataclasses import dataclass
from datetime import timedelta
from jinja2 import Template, DebugUndefined
from litellm.types.utils import Message
from pathlib import Path
from pydantic import BaseModel, ConfigDict
from queue import Queue
from typing import Any, Callable, List, Optional, Generator, Literal, Type

from agentic.swarm.types import (
    agent_secret_key,
    AgentFunction,
    ChatCompletionMessage,
    ChatCompletionMessageToolCall,
    Function,
    Response,
    Result,
    ThreadContext,
    tool_name
)
from agentic.swarm.util import (
    debug_print,
    debug_completion_start,
    debug_completion_end,
    function_to_json,
    looks_like_langchain_tool,
    langchain_function_to_json,
    wrap_llm_function,
)

from agentic.events import (
    Event,
    Prompt,
    PromptStarted,
    Output,
    ChatOutput,
    ToolCall,
    ToolResult,
    TurnCancelledError,
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
    StartRequestResponse,
    OAuthFlow,
    OAuthFlowResult,
)
from agentic.db.models import Thread, ThreadLog
from agentic.tools.utils.registry import tool_registry
from agentic.db.db_manager import DatabaseManager
from agentic.models import get_special_model_params, mock_provider


__CTX_VARS_NAME__ = "thread_context"
__LEGACY_CTX_VARS_NAME__ = "run_context"

# define a CallbackType Enum with values: "handle_turn_start", "handle_event", "handle_turn_end"
CallbackType = Literal["handle_turn_start", "handle_event", "handle_turn_end"]

# make a Callable type that expects a Prompt and ThreadContext
CallbackFunc = Callable[[Event, ThreadContext], None]

@dataclass
class AgentPauseContext:
    orig_history_length: int
    tool_partial_response: Response
    #    sender: Optional[Actor] = None
    tool_function: Optional[Function] = None


litellm.drop_params = True

# Pick the agent runtime
if os.environ.get("AGENTIC_USE_RAY"):
    # Use the actual Ray implementation
    print("Using Ray engine for running agents")
    import ray

else:
    print("Using simple Thread engine for running agents")
    from .ray_mock import ray

_AGENT_REGISTRY = []

@ray.remote
class ActorBaseAgent:
    name: str = "Agent"
    model: str = "gpt-4o"  # Default model
    instructions_str: str = "You are a helpful agent."
    tools: list[str] = None
    functions: List[AgentFunction] = None
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
    thread_context: ThreadContext = None
    api_endpoint: str = None
    _prompter = None
    _callbacks: dict[CallbackType, CallbackFunc] = {}
    result_model: Type[BaseModel]|None = None,

    model_config = ConfigDict(
        arbitrary_types_allowed=True
    )

    def __init__(self, name: str):
        super().__init__()
        self.name = name
        self.history: list = []

        # Always register mock provider with litellm
        litellm.custom_provider_map = [
            {"provider": "mock", "custom_handler": mock_provider}
        ]

    def __repr__(self):
        return self.name

    def _get_llm_completion(
        self,
        history: List,
        thread_context: ThreadContext,
        model_override: str,
        stream: bool,
    ) -> ChatCompletionMessage:
        """Call the LLM completion endpoint"""
        instructions = self.get_instructions(thread_context)
        messages = [{"role": "system", "content": instructions}] + history

        tools = [function_to_json(f) for f in self.functions]
        # hide thread_context from model
        for tool in tools:
            params = tool["function"]["parameters"]
            params["properties"].pop(__CTX_VARS_NAME__, None)
            if __CTX_VARS_NAME__ in params["required"]:
                params["required"].remove(__CTX_VARS_NAME__)
            params["properties"].pop(__LEGACY_CTX_VARS_NAME__, None)
            if __LEGACY_CTX_VARS_NAME__ in params["required"]:
                params["required"].remove(__LEGACY_CTX_VARS_NAME__)

        # Create parameters for litellm call
        completion_params = {
            "model": model_override or self.model,
            "messages": messages,
            "temperature": 0.0,
            "tools": tools or None,
            "tool_choice": self.tool_choice,
            "stream": stream,
            "stream_options": {"include_usage": True},
        }
        if self.result_model:
            completion_params["response_format"] = self.result_model

        # Add any special parameters needed for specific model types
        completion_params.update(get_special_model_params(completion_params["model"]))

        if self.max_tokens:
            completion_params["max_tokens"] = self.max_tokens

        if tools:
            completion_params["parallel_tool_calls"] = self.parallel_tool_calls
            
        # Create simplified version of params for debug logging
        debug_params = completion_params.copy()
        if debug_params.get("tools"):
            debug_params["tools"] = [
                f["function"]["name"] for f in debug_params["tools"]
            ]

        # Get model name
        model_name = model_override or self.model
        
        # Import token estimation utilities
        from agentic.utils.token_estimation import (
            should_compress_context,
            create_compressed_messages
        )
        
        # Check if we need to compress context
        needs_compression, current_tokens, max_allowed = should_compress_context(
            messages=messages, 
            model=model_name,
            safety_factor=0.3  # Use 30% safety margin
        )
        
        # Debug logging for token count
        if self.debug.debug_all():
            print(f"[Token Count] Model: {model_name}, Current tokens: {current_tokens}, Max: {max_allowed}")

        # Compress context if needed
        if needs_compression:
            # Create compressed messages
            truncated_messages = create_compressed_messages(
                messages=messages,
                model=model_name,
                current_tokens=current_tokens,
                debug=self.debug.debug_all()
            )
            
            # Update completion params with compressed messages
            completion_params["messages"] = truncated_messages
            
            # Update history but preserve system message
            self.history = [messages[0]] + truncated_messages[2:]

        debug_completion_start(self.debug, self.model, debug_params)
        
        try:
            return litellm.completion(**completion_params)
        except litellm.exceptions.ContextWindowExceededError as e:
            # Emergency fallback
            print(f"Emergency fallback: {str(e)}")
            
            # Keep only the system message and most recent message
            emergency_messages = [messages[0], messages[-1]]
            completion_params["messages"] = emergency_messages
            self.history = emergency_messages
            
            # Try one more time with minimal context
            return litellm.completion(**completion_params)
        except Exception as e:
            traceback.print_exc()
            raise RuntimeError("Error calling LLM: " + str(e))

    def _execute_tool_calls(
        self,
        tool_calls: List[ChatCompletionMessageToolCall],
        functions: List[AgentFunction],
        thread_context: ThreadContext,
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

            func = function_map[name]
            if __CTX_VARS_NAME__ in func.__code__.co_varnames:
                args[__CTX_VARS_NAME__] = thread_context
            if __LEGACY_CTX_VARS_NAME__ in func.__code__.co_varnames:
                args[__LEGACY_CTX_VARS_NAME__] = thread_context

            events.append(ToolCall(self.name, name, args))

            # Call the function!!
            raw_result = None
            try:
                if asyncio.iscoroutinefunction(function_map[name]):
                    try:
                        loop = asyncio.get_running_loop()
                    except RuntimeError:
                        loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(loop)
                    
                    raw_result = loop.run_until_complete(function_map[name](**args))
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
                    if raw_result is None:
                        # Take last event as the function result
                        raw_result = events.pop()

                elif inspect.isasyncgenfunction(function_map[name]):
                    # Thread the async function in an event loop and yield events
                    async def run_async_gen():
                        async for event in function_map[name](**args):
                            events.append(event)
                    asyncio.run(run_async_gen())
                    # take the last yielded value as the function result
                    raw_result = events.pop()

                else:
                    raw_result = function_map[name](**args)
            except Exception as e:
                tb_list = traceback.format_exception(type(e), e, e.__traceback__)
                # Join all lines and split them to get individual lines
                full_traceback = "".join(tb_list).strip().split("\n")
                # Get the last 3 lines (or all if less than 3)
                if self.debug.debug_all():
                    last_three = full_traceback
                else:
                    last_three = (
                        full_traceback[-3:] if len(full_traceback) >= 3 else full_traceback
                    )
                raw_result = f"Tool error: {name}: {last_three}"

                events.append(ToolError(self.name, name, raw_result, self.depth))
                # thread_context.error(raw_result)

            # Let tools return additional events to publish
            if isinstance(raw_result, list):
                for result in raw_result:
                    if isinstance(result, Event):
                        events.append(result)
                raw_result = [result for result in raw_result if not isinstance(result, Event)]
                if len(raw_result) == 0:
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

            # Functions can queue log events when they run, and we publish after
            for log_event in thread_context.get_logs():
                events.append(log_event)
            thread_context.reset_logs()

            events.append(ToolResult(self.name, name, result.value))

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

    def handle_prompt_or_resume(self, actor_message: Prompt | ResumeWithInput):
        request_id = getattr(actor_message, 'request_id', None)
        if not request_id:
            raise ValueError("Request ID is required")
        
        if isinstance(actor_message, Prompt):
            self.thread_context = (
                ThreadContext(
                    agent_name=self.name,
                    agent=self,
                    debug_level=actor_message.debug,
                    api_endpoint=self.api_endpoint,
                    context=actor_message.request_context,
                )
                if self.thread_context is None
                else self.thread_context.update(actor_message.request_context)
            )
            if not self.thread_context.thread_id and "thread_id" in actor_message.request_context:
                self.thread_context.thread_id = actor_message.request_context["thread_id"]  

            # Middleware to modify the input prompt (or change agent context)
            if self._callbacks.get('handle_turn_start'):
                self._callbacks['handle_turn_start'](actor_message, self.thread_context)
                
            self.debug = actor_message.debug
            self.depth = actor_message.depth
            self.history.append({"role": "user", "content": actor_message.payload})
            yield PromptStarted(self.name, actor_message.payload, self.depth)

        elif isinstance(actor_message, ResumeWithInput):
            if not self.paused_context:
                self.thread_context.debug(
                    "Ignoring ResumeWithInput event, parent not paused: ",
                    actor_message,
                )
                return
                
            init_len = self.paused_context.orig_history_length
            self.thread_context.update(actor_message.request_keys.copy())
            
            tool_function = self.paused_context.tool_function
            if tool_function is None:
                raise RuntimeError("Tool function not found on AgentResume event")
                
            partial_response, events = self._execute_tool_calls(
                [ChatCompletionMessageToolCall(
                    id=(tool_function._request_id or ""),
                    function=tool_function,
                    type="function")],
                self.functions,
                self.thread_context
            )
            yield from events
            self.history.extend(partial_response.messages)

        # Main conversation loop: allow 25 tool calls in a row before stopping
        init_len = len(self.history)
        while len(self.history) - init_len < 50:
            for event in self._yield_completion_steps(request_id):
                yield event

            assert isinstance(event, FinishCompletion)
            response: Message = event.response
            
            self.history.append(response)
            if not response.tool_calls:
                break

            partial_response, events = self._execute_tool_calls(
                response.tool_calls,
                self.functions,
                self.thread_context
            )
            yield from events

            if partial_response.last_tool_result:
                if isinstance(partial_response.last_tool_result, PauseForInputResult):
                    self.paused_context = AgentPauseContext(
                        orig_history_length=init_len,
                        tool_partial_response=partial_response,
                        tool_function=partial_response.last_tool_result.tool_function
                    )
                    yield WaitForInput(self.name, partial_response.last_tool_result.request_keys)
                    return
                elif isinstance(partial_response.last_tool_result, OAuthFlowResult):
                    self.paused_context = AgentPauseContext(
                        orig_history_length=init_len,
                        tool_partial_response=partial_response,
                        tool_function=partial_response.last_tool_result.tool_function
                    )
                    # Add tool result message before yielding OAuthFlow event
                    self.history.extend([{
                        "role": "tool",
                        "content": "OAuth authentication required. Please complete the authorization flow.",
                        "tool_call_id": partial_response.last_tool_result.tool_function._request_id,
                        "name": partial_response.last_tool_result.tool_function.name
                    }])
                    yield OAuthFlow(
                        self.name,
                        partial_response.last_tool_result.auth_url,
                        partial_response.last_tool_result.tool_name,
                        depth=self.depth
                    )
                    return
                    
                elif FinishAgentResult.matches_sentinel(partial_response.messages[-1]["content"]):
                    self.history.extend(partial_response.messages)
                    break

            self.history.extend(partial_response.messages)

        # We have already emitted history for intervening events, and I think we just look at the
        # last message from TurnEnd anyway. So probably we just want to publish a single result here.
        # You can see it in TurnEnd.result which just returns the "content" part of the last message.
        yield TurnEnd(
            self.name,
            # result_model gets applied when TurnEnd is processed. We dont want to alter the the text response in history
            deepcopy(self.history[init_len:]),
            self.thread_context,
            self.depth
        )
        self.paused_context = None

    def _yield_completion_steps(self, request_id: str):
        yield StartCompletion(self.name, self.depth)

        self._callback_params = {}

        def custom_callback(kwargs, completion_response, start_time, end_time):
            try:
                self._callback_params["cost"] = kwargs["response_cost"]
            except:
                pass
            self._callback_params["elapsed"] = end_time - start_time

        litellm.success_callback = [custom_callback]

        try:
            completion = self._get_llm_completion(
                history=self.history,
                thread_context=self.thread_context,
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
                self.depth
            )
            return

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
        
        # Get usage directly from response
        usage = getattr(llm_message, "usage", None)
        if usage:
            self._callback_params["input_tokens"] = usage.prompt_tokens
            self._callback_params["output_tokens"] = usage.completion_tokens
        else:
            # Fallback to manual calculation if usage not in response
            if len(input) > 0:
                self._callback_params["input_tokens"] = litellm.token_counter(
                    self.model, messages=self.history[-1:]
                )
            if output.content:
                self._callback_params["output_tokens"] = litellm.token_counter(
                    self.model, text=output.content
                )

        debug_completion_end(self.debug, self.model, llm_message.choices[0].message)

        yield FinishCompletion.create(
            self.name,
            llm_message.choices[0].message,
            self.model,
            self._callback_params.get("cost", 0),
            self._callback_params.get("input_tokens"),
            self._callback_params.get("output_tokens"),
            self._callback_params.get("elapsed"),
            self.depth
        )

    def call_child(
        self,
        child_ref,
        handoff: bool,
        message,
    ):
        depth = self.depth if handoff else self.depth + 1
        if hasattr(child_ref.handle_prompt_or_resume, 'remote'):
            remote_gen = child_ref.handle_prompt_or_resume.remote(
                Prompt(
                    self.name,
                    message,
                    depth=depth,
                    debug=self.debug,
                )
            )
        else:
            remote_gen = child_ref.handle_prompt_or_resume(
                Prompt(
                    self.name,
                    message,
                    depth=depth,
                    debug=self.debug,
                    request_context=self.thread_context.get_context(),
                    request_id=str(uuid.uuid4())
                )
            )
        
        for remote_event in remote_gen:
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

    def get_instructions(self, context: ThreadContext):
        # Support context var substitution in prompts
        try:
            prompt = Template(
                self.instructions_str, 
                undefined=DebugUndefined
            ).render(
                context.get_context()
            )
            if self.memories:
                prompt += """
    <memory blocks>
    {% for memory in MEMORIES -%}
    {{memory|trim}}
    {%- endfor %}
    </memory>
    """
            # Fix for Jinja2 template rendering error if there is an unclosed comment, ensure all `{#` have a closing `#}`
            while re.search(r"\{#(?!.*#\})", prompt, re.DOTALL):
                prompt = re.sub(r"\{#(?!.*#\})", "{% raw %}{#{% endraw %}", prompt, count=1)

            return Template(prompt).render(
                context.get_context() | {"MEMORIES": self.memories}
            )
        except Exception as e:
            print("Error in prompt template, using raw prompt without subsitutions:", e)
            traceback.print_exc()
            return prompt

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
            "api_endpoint",
            "result_model",
        ]:
            if key in state:
                setattr(self, remap.get(key, key), state[key])

        if 'history' in state:
            self.history = state["history"]

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

    def webhook(self, thread_id: str, callback_name: str, args: dict) -> Any:
        """Handle webhook callbacks by executing the specified tool function
        
        Args:
            thread_id: ID of the agent thread this webhook is for
            callback_name: Name of the tool function to call
            args: Arguments to pass to the tool function
        """
        # Get the thread context from the database
        db_manager = DatabaseManager()
        thread = db_manager.get_thread(thread_id)
        if not thread:
            raise ValueError(f"No thread found with ID {thread_id}")
        # Recreate thread context
        self.thread_context = ThreadContext(
            agent=self,
            agent_name=self.name, 
            debug_level=self.debug,
            thread_id=thread_id,
            api_endpoint=self.api_endpoint
        )
        # Find the tool function
        function_map = {f.__name__: f for f in self.functions}
        if callback_name not in function_map:
            raise ValueError(f"No tool function found named {callback_name}")

        # Execute the tool call
        try:
            # Create tool call object
            tool_call = ChatCompletionMessageToolCall(
                id="",
                type="function",
                function=Function(
                    name=callback_name,
                    arguments=json.dumps({"webhook_data":args})
                )
            )

            # Execute the tool call
            response, events = self._execute_tool_calls(
                [tool_call],
                self.functions,
                self.thread_context
            )
            return response

        except Exception as e:
            raise RuntimeError(f"Error executing webhook {callback_name}: {str(e)}")

    # Add new methods to set mock configuration
    def set_mock_params(self, pattern: str, response: str, tools: dict):
        """Store mock parameters in the agent instance"""
        # Import here to avoid circular imports
        from agentic.models import mock_provider
        
        # Apply to the mock provider (happens in this worker process)
        mock_provider.set_response(pattern, response)
        mock_provider.clear_tools()
        for name, tool in tools.items():
            mock_provider.register_tool(name, tool)
            
        # Make sure custom provider is registered in litellm
        litellm.custom_provider_map = [
            {"provider": "mock", "custom_handler": mock_provider}
        ]

class HandoffAgentWrapper:
    def __init__(self, agent):
        self.agent = agent

    def get_agent(self):
        return self.agent


def handoff(agent, **kwargs):
    """Signal that a child agent should take over the execution context instead of being
    called as a subroutine."""
    return HandoffAgentWrapper(agent)

class ProcessRequest(BaseModel):
    prompt: str
    debug: Optional[str] = None
    thread_id: Optional[str] = None

class ResumeWithInputRequest(BaseModel):
    continue_result: dict[str, str]
    debug: Optional[str] = None
    thread_id: Optional[str] = None


depthLocal = threading.local()
depthLocal.depth = -1

# The common agent proxy interface
# The core of the interface is 'start_request' and 'get_events'. Use these in
# pairs to request operation threads from the agent.
# It is deprecated to call 'next_turn' directly now.
#
# Subclasses can override next_turn to do their own orchestration logic.

class BaseAgentProxy:
    """Base agent proxy class with common functionality. Manages multiple parallel
    requests, delegating each request to an instance of the agent class.
    The proxy keeps a thread queue to dispatch agent events to the caller.
    Subclasses will handle specific implementation details for different 
    execution environments (Ray, local, etc.)
    """
    _agent: Any

    def __init__(
        self,
        name: str,
        instructions: str | None = "You are a helpful assistant.",
        welcome: str | None = None,
        tools: list = None,
        model: str | None = None,
        template_path: str | Path | None = None,
        max_tokens: int = None,
        db_path: Optional[str | Path] = "./agent_threads.db",
        memories: list[str] = [],
        handle_turn_start: Callable[[Prompt, ThreadContext], None] = None,
        result_model: Type[BaseModel]|None = None,
        debug: DebugLevel = DebugLevel(os.environ.get("AGENTIC_DEBUG") or ""),
        mock_settings: dict = None,
        prompts: Optional[dict[str, str]] = None,
    ):
        self.name = name
        self.welcome = welcome or f"Hello, I am {name}."
        self.model = model or "gpt-4o-mini"
        self.prompts = prompts or {}
        self.cancelled = False
        self.mock_settings = mock_settings
        
        # Find template path if not provided
        from agentic.utils.template import find_template_path
        self.template_path = template_path or find_template_path()
        
        # Setup tools and other properties
        self._tools = []
        if tools:
            self._tools.extend(tools)
            
        self.max_tokens = max_tokens
        self.memories = memories
        self.debug = debug
        self._handle_turn_start = handle_turn_start
        self.request_queues: dict[str,Queue] = {}
        self.result_model = result_model
        self.queue_done_sentinel = "QUEUE_DONE"
        
        # Track active agent instances by request ID
        self.agent_instances = {}

        # Process instructions
        if instructions and instructions.strip():
            template = Template(instructions, undefined=DebugUndefined)
            self.instructions = template.render(**self.prompt_variables)
            # Allow one level of nested references
            self.instructions = Template(self.instructions, undefined=DebugUndefined).render(**self.prompt_variables)
            if self.instructions.strip() == "":
                raise ValueError(
                    f"Instructions are required for {self.name}. Maybe interpolation failed from: {instructions}"
                )
        else:
            self.instructions = "You are a helpful assistant."

        # Check we have all the secrets
        self._ensure_tool_secrets()

        # Initialize thread tracking
        self.db_path = db_path
        self.thread_id = None  # This will be set per request

        # Ensure API key is set
        self.ensure_api_key_for_model(self.model)
        
        # Handle mock settings - subclasses should implement this
        self._handle_mock_settings(mock_settings)

    def _check_for_prompt_match(self, user_input: str) -> str:
        """Check if user input matches a prompt key and return the corresponding content if it does."""
        if not self.prompts:
            return user_input
            
        # Check if the input exactly matches a prompt key
        if user_input in self.prompts:
            return self.prompts[user_input]
            
        # Check if the input matches a prompt key when lowercase
        lower_input = user_input.lower()
        for key, value in self.prompts.items():
            if lower_input == key.lower():
                return value
                
        # No match found, return original input
        return user_input

    def _handle_mock_settings(self, mock_settings):
        """Handle mock settings - to be implemented by subclasses"""
        pass
        
    def _ensure_tool_secrets(self):
        """Ensure that all required secrets for tools are available"""
        from .agentic_secrets import agentic_secrets

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

    def cancel(self):
        """Flag this agent to cancel whatever it is doing"""
        self.cancelled = True

    def is_cancelled(self):
        """Check if this agent has been cancelled"""
        return self.cancelled
    
    def uncancel(self):
        """Reset the cancelled flag"""
        self.cancelled = False

    def add_tool(self, tool: Any):
        """Add a tool to this agent"""
        self._tools.append(tool)
        self._update_state({"functions": self._get_funcs(self._tools)})

    def add_child(self, child_agent):
        """Add a child agent as a tool"""
        self.add_tool(child_agent)

    def set_model(self, model: str):
        """Set the model to use for this agent"""
        self.model = model
        self._update_state({"model": model})

    def set_debug_level(self, level: DebugLevel):
        """Set the debug level for this agent"""
        self.debug.raise_level(level)
        self._set_agent_debug_level(self.debug)

    def set_result_model(self, model: Type[BaseModel]):
        """Set the result model for this agent"""
        self.result_model = model
        self._update_state({"result_model": model})

    def reset_history(self):
        """Reset the conversation history"""
        self._reset_agent_history()

    def get_history(self):
        """Get the conversation history"""
        return self._get_agent_history()

    def init_thread_tracking(self, agent, thread_id: Optional[str] = None):
        """Initialize thread tracking"""
        pass

    def get_db_manager(self) -> DatabaseManager:
        """Get the database manager for this agent"""
        if self.db_path:
            db_manager = DatabaseManager(self.db_path)
        else:
            db_manager = DatabaseManager()
        return db_manager

    def get_threads(self, user_id: str|None) -> list[Thread]:
        """Get all threads for this agent"""
        db_manager = self.get_db_manager()
        
        try:
            return db_manager.get_threads_by_agent(self.name, user_id=user_id)
        except Exception as e:
            print(f"Error getting threads: {e}")
            return []
        
    def get_thread_logs(self, thread_id: str) -> list[ThreadLog]:
        """Get logs for a specific thread"""
        db_manager = self.get_db_manager()
        
        try:
            return db_manager.get_thread_logs(thread_id)
        except Exception as e:
            print(f"Error getting thread logs: {e}")
            return []

    @property
    def prompt_variables(self) -> dict:
        """Dictionary of variables to make available to prompt templates."""
        if self.template_path is None:
            return {"name": self.name}  # Return default values when no template path exists
            
        path = Path(self.template_path)
        if path.exists():
            try:
                with open(path, "r") as f:
                    prompts = yaml.safe_load(f)
                    return prompts or {"name": self.name}
            except Exception as e:
                print(f"Error loading prompt template: {e}")
        
        return {"name": self.name}

    @property
    def safe_name(self) -> str:
        """Renders the Agent's name, but filesystem safe."""
        return "".join(c if c.isalnum() else "_" for c in self.name).lower()

    def ensure_api_key_for_model(self, model: str):
        """Ensure the appropriate API key is set for the given model."""
        from agentic.agentic_secrets import agentic_secrets

        for key in agentic_secrets.list_secrets():
            if key not in os.environ:
                value = agentic_secrets.get_secret(key)
                if value:
                    os.environ[key] = value

    def _get_funcs(self, thefuncs: list):
        """Get the functions to provide to the agent implementation"""
        useable = []
        for func in thefuncs:
            if callable(func):
                tool_registry.ensure_dependencies(func)
                useable.append(func)
            elif isinstance(func, HandoffAgentWrapper):
                # add a child agent as a tool
                useable.append(
                    AddChild(
                        func.get_agent().name, 
                        func.get_agent()._agent, 
                        handoff=True
                    )
                )
            elif isinstance(func, BaseAgentProxy):
                useable.append(
                    AddChild(
                        func.name,
                        func._agent,
                    )
                )
            else:
                tool_registry.ensure_dependencies(func)
                useable.append(func)

        return useable
        
    def _update_state(self, state: dict):
        """Update the agent's state"""
        # To be overridden by subclasses
        pass

    def _set_agent_debug_level(self, debug_level):
        """Set the debug level on the agent implementation"""
        # To be overridden by subclasses
        pass

    def _reset_agent_history(self):
        """Reset the agent's conversation history"""
        # To be overridden by subclasses
        pass

    def _get_agent_history(self):
        """Get the agent's conversation history"""
        # To be overridden by subclasses
        pass

    def _reload_thread_history(self, thread_id: str):
        # We load the thread history from the ThreadManager, and pass it to the agent.
        # We have to keep a flag to avoid loading all of history every time that 'start_request' is
        # is called. But the agent also has logic to only load its history once.
        from .thread_manager import reconstruct_chat_history_from_thread_logs, validate_chat_history

        if thread_id == 'NEW':
            history = []
        else:
            print("LOADING THREAD LOGS FOR ID: ", thread_id)
            history = validate_chat_history(
                reconstruct_chat_history_from_thread_logs(self.get_thread_logs(thread_id))
            )
        update = {"history": history}
        pprint(update)
        self._update_state(update)

    def _create_agent_instance(self, request_id: str):
        """Create a new agent instance for a request"""
        # This is implemented by the subclasses (e.g., RayAgentProxy, LocalAgentProxy)
        raise NotImplementedError("Subclasses must implement _create_agent_instance")

    def _get_agent_for_request(self, request_id: str):
        """Get the agent instance for a request, creating it if needed"""
        # The logic here is to keep reusing the default '_agent' value created when the Proxy is
        # first constructed. We only go to create a new instance if a request is started before
        # the prior one finishes.
        # TODO: RESOLVE THIS TO WORK WITH RESUME WITH INPUT
        # if len(self.agent_instances) == 0:
        self.agent_instances[request_id] = self._agent or self._create_agent_instance(request_id)
        # else:
        #     self.agent_instances[request_id] = self._create_agent_instance(request_id)
        return self.agent_instances[request_id]

    def _cleanup_agent_instance(self, request_id: str):
        """Clean up an agent instance after a request is complete"""
        # We remove the agent from our set, but the _agent default instance will stay around
        if request_id in self.agent_instances:
            del self.agent_instances[request_id]

    def start_request(self, request: str, request_context: dict = {}, 
                     continue_result: dict = {}, thread_id: Optional[str] = None,
                     debug: DebugLevel = DebugLevel(DebugLevel.OFF)) -> StartRequestResponse:
        """Start a new agent request"""
        self.debug.raise_level(debug)

        if not hasattr(depthLocal, 'depth'):
            depthLocal.depth = 0
        else:
            depthLocal.depth += 1

        for key, value in request_context.items():
            if isinstance(value, Callable):
                request_context[key] = value()
                
        if isinstance(request, str):
            request = self._check_for_prompt_match(request)

        if not thread_id and "thread_id" in request_context:
            thread_id = request_context["thread_id"]

        # Create request ID if not provided in continue_result
        request_id = continue_result.get("request_id") or str(uuid.uuid4())

        agent_instance = self._get_agent_for_request(request_id)
        if (self.thread_id != thread_id or not self.thread_id) and self.db_path:
            if thread_id is not None:
                self._reload_thread_history(thread_id)

            self.init_thread_tracking(agent_instance, thread_id or self.thread_id)
            print("USING THREAD ID: ", self.thread_id)

        # Initialize new request
        request_obj = Prompt(
            self.name,
            request,
            debug=self.debug,
            depth=depthLocal.depth,
            request_context=request_context,
            request_id=request_id,
        )

        def producer(queue, request_obj, continue_result):
            depthLocal.depth = request_obj.depth
            for event in self._next_turn(request_obj, request_context=request_context, continue_result=continue_result, request_id=request_id):
                queue.put(event)
            queue.put(self.queue_done_sentinel)
            # Cleanup the agent instance when done
            self._cleanup_agent_instance(request_id)
            
        queue = Queue()
        self.request_queues[request_id] = queue

        t = threading.Thread(target=producer, args=(queue, request_obj, continue_result))
        t.start()
        return StartRequestResponse(request_id=request_id, thread_id=self.thread_id)

    def get_events(self, request_id: str, timeout: Optional[float] = None) -> Generator[Event, Any, Any]:
        """Get events for a request"""
        queue = self.request_queues[request_id]
        start_time = time.time()
        
        while True:
            try:
                if timeout is not None:
                    remaining_time = timeout - (time.time() - start_time)
                    if remaining_time <= 0:
                        # Timeout exceeded, set sentinel and return
                        queue.put(self.queue_done_sentinel)
                        break
                    event = queue.get(timeout=remaining_time)
                else:
                    event = queue.get()
                    
                if event == self.queue_done_sentinel:
                    break
                    
                yield event
                time.sleep(0.01)
                
            except Exception:
                # Timeout or other exception, set sentinel and break
                queue.put(self.queue_done_sentinel)
                break
        
        depthLocal.depth -= 1

    def next_turn(self, request: str | Prompt, request_context: dict = {},
              request_id: str = None, continue_result: dict = {},
              debug: DebugLevel = DebugLevel(DebugLevel.OFF)) -> Generator[Event, Any, Any]:
        """
        Default agent orchestration logic. Subclasses may override this.
        If not overridden, this handles prompt/resume and returns generator from agent.
        """
        # Get agent instance
        agent_instance = self._get_agent_for_request(request_id)

        # Prepare the prompt or resume input
        if not continue_result:
            prompt = (
                request if isinstance(request, Prompt)
                else Prompt(
                    self.name,
                    request,
                    debug=debug,
                    request_context=request_context,
                    request_id=request_id,
                )
            )


            # Transmit depth through the Prompt
            if hasattr(depthLocal, 'depth') and depthLocal.depth > prompt.depth:
                prompt.depth = depthLocal.depth

            return self._get_prompt_generator(agent_instance, prompt)

        else:
            resume_input = ResumeWithInput(
                self.name,
                continue_result,
                request_id=request_id
            )
            return self._get_resume_generator(agent_instance, resume_input)


    def _next_turn(self, request: str | Prompt, request_context: dict = {},
               request_id: str = None, continue_result: dict = {},
               debug: DebugLevel = DebugLevel(DebugLevel.OFF)) -> Generator[Event, Any, Any]:
        """
        Wraps `next_turn` to add thread tracking and handle_event logging.
        Always used internally by the proxy to ensure consistent behavior.
        """
        self.cancelled = False
        self.debug.raise_level(debug)

        if not request_id:
            request_id = continue_result.get("request_id") or str(uuid.uuid4())
            if isinstance(request, Prompt):
                request.request_id = request_id

        self._handle_mock_settings(self.mock_settings)

        if not self.thread_id and "thread_id" in request_context:
            self.thread_id = request_context["thread_id"]

        # Get agent instance for the thread
        agent_instance = self._get_agent_for_request(request_id)

        # Initialize thread tracking if needed
        if (not self.thread_id) and self.db_path:
            self.init_thread_tracking(agent_instance, self.thread_id)

        # Add thread_id into context explicitly so child agents inherit it
        request_context = {**request_context, "thread_id": self.thread_id}

        # Call the user’s or default next_turn
        event_gen = self.next_turn(
            request=request,
            request_context=request_context,
            request_id=request_id,
            continue_result=continue_result,
            debug=debug
        )

        # Central logging of all events
        for event in self._process_generator(event_gen):
            if self.cancelled:
                raise TurnCancelledError()

            # Handle TurnEnd result validation
            if isinstance(event, TurnEnd):
                event = self._process_turn_end(event)

            yield event

            if hasattr(event, "agent") and event.agent != self.name:
                # skipping event with wrong agent name
                continue    

            # Only now: do logging after yielding
            callback = self._agent.get_callback("handle_event") if hasattr(self, "_agent") else None
            if callback:
                context = ThreadContext(agent=self._agent, agent_name=self.name, thread_id=self.thread_id, context=request_context)
                try:
                    callback(event, context)
                except Exception as e:
                    print(f"Error in handle_event callback: {e}")
                        
        
    def _get_prompt_generator(self, agent_instance, prompt):
        """Get generator for a new prompt - to be implemented by subclasses"""
        pass
        
    def _get_resume_generator(self, agent_instance, resume_input):
        """Get generator for resuming with input - to be implemented by subclasses"""
        pass
        
    def _process_generator(self, generator):
        """Process generator events - to be implemented by subclasses"""
        pass
        
    def _process_turn_end(self, event):
        """Process TurnEnd event to handle result model validation"""
        if isinstance(event.result, str) and self.result_model:
            try:
                event.set_result(self.result_model.model_validate_json(event.result))
            except Exception as e:
                try:
                    # Hack for LLM poorly parsing Claude structured outputs
                    data = json.loads(event.result)
                    if 'values' in data:
                        event.set_result(self.result_model.model_validate(data['values']))
                except Exception as e:
                    # Create an error message event
                    error_event = ChatOutput.assistant_message(
                        self.name, 
                        f"Error validating result: {e}", 
                        depth=event.depth
                    )
                    # We'll yield this error event and then the original event
                    return error_event
        return event

    def final_result(self, request: str, request_context: dict = {}, 
                    event_handler: Callable[[Event], None] = None) -> Any:
        """Get the final result of a request"""
        request_id = self.start_request(
            request, 
            request_context=request_context, 
            debug=self.debug
        ).request_id
        turn_end = None
        for event in self.get_events(request_id):
            if event_handler:
                event_handler(event)
            yield event
            if isinstance(event, TurnEnd):
                turn_end = event
        if turn_end:
            return turn_end.result
        else:
            return event

    def grab_final_result(self, request: str, request_context: dict = {}) -> Any:
        """Convenience method to get the final result of a request"""
        try:
            items = list(self.final_result(request, request_context))
            if isinstance(items[-1], TurnEnd):
                return items[-1].result
            else:
                return items[-1]
        except StopIteration as e:
            return e.value

    def __lshift__(self, prompt: str):
        """
        Implement the << operator for sending prompts to agents.
        This allows syntax like: response = agent << "prompt"
        
        Args:
            prompt: The prompt to send to the agent
            
        Returns:
            The final response from the agent
        """
        return self.grab_final_result(prompt)

class RayAgentProxy(BaseAgentProxy):
    """Ray-based implementation of the agent proxy.
    The actual agent is run as a remote actor on Ray.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.agent_config = {
            "name": self.name,
            "instructions": self.instructions,
            "model": self.model,
            "max_tokens": self.max_tokens,
            "memories": self.memories,
            "debug": self.debug,
            "result_model": self.result_model,
            "prompts": self.prompts,
            # Functions will be added when creating instances
        }
        _AGENT_REGISTRY.append(self)
        self._create_agent_instance()

    def _create_agent_instance(self, request_id: str|None=None):
        """Initialize the Ray actor"""
        agent = ActorBaseAgent.remote(name=self.name)
        
        # Set initial state
        obj_ref = agent.set_state.remote(
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
                    "result_model": self.result_model,
                },
            ),
        )
        ray.get(obj_ref)
        if self._handle_turn_start:
            agent.set_callback.remote("handle_turn_start", self._handle_turn_start)

        if request_id is None:
            self._agent = agent

        return agent

    def init_thread_tracking(self, agent, thread_id: Optional[str] = None):
        """Initialize thread tracking"""
        from .thread_manager import init_thread_tracking
        self.thread_id, callback = init_thread_tracking(self, db_path=self.db_path, resume_thread_id=thread_id)
        agent.set_callback.remote('handle_event', callback)

    def _handle_mock_settings(self, mock_settings):
        """Handle mock settings for Ray implementation"""
        if mock_settings and self.model and "mock" in self.model:
            from agentic.models import mock_provider
            
            pattern = mock_settings.get("pattern", "")
            response = mock_settings.get("response", "This is a mock response.")
            tools_dict = mock_settings.get("tools", {})
            
            # Set in the local mock_provider directly
            mock_provider.set_response(pattern, response)
            mock_provider.clear_tools()
            for tool_name, tool_func in tools_dict.items():
                mock_provider.register_tool(tool_name, tool_func)
            
            # Pass to the remote agent
            try:
                ray.get(self._agent.set_mock_params.remote(pattern, response, tools_dict))
            except Exception as e:
                print(f"Warning: Failed to set mock params on remote agent: {e}")

    def _update_state(self, state: dict):
        """Update the Ray agent's state"""
        obj_ref = self._agent.set_state.remote(SetState(self.name, state))
        ray.get(obj_ref)

    def _set_agent_debug_level(self, debug_level):
        """Set the debug level on the Ray agent"""
        ray.get(self._agent.set_debug_level.remote(debug_level))

    def _reset_agent_history(self):
        """Reset the Ray agent's conversation history"""
        ray.get(self._agent.reset_history.remote())

    def _get_agent_history(self):
        """Get the Ray agent's conversation history"""
        return ray.get(self._agent.get_history.remote())

    def list_tools(self) -> list[str]:
        """Gets the current tool list from the running Ray agent"""
        return ray.get(self._agent.list_tools.remote())

    def list_functions(self) -> list[str]:
        """Gets the current list of functions from the running Ray agent"""
        return ray.get(self._agent.list_functions.remote())
        
    def _get_prompt_generator(self, agent, prompt):
        """Get generator for a new prompt from a Ray agent"""
        return agent.handle_prompt_or_resume.remote(prompt)

    def _get_resume_generator(self, agent, resume_input):
        """Get generator for resuming with input from a Ray agent"""
        return agent.handle_prompt_or_resume.remote(resume_input)
        
    def _process_generator(self, generator):
        """Process generator events - Ray implementation"""
        for remote_next in generator:
            yield ray.get(remote_next)


class LocalAgentProxy(BaseAgentProxy):
    """Local dispatch implementation of the agent proxy.
    This version makes calls directly to a local agent object.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.agent_config = {
            "name": self.name,
            "instructions": self.instructions,
            "welcome": self.welcome,
            "tools": self._tools.copy(),
            "model": self.model,
            "max_tokens": self.max_tokens,
            "memories": self.memories,
            "debug": self.debug,
            "handle_turn_start": self._handle_turn_start,
            "result_model": self.result_model,
            "prompts": self.prompts,
            "db_path": self.db_path,
            # Functions will be added when creating instances
        }
        _AGENT_REGISTRY.append(self)
        self._create_agent_instance()

    def _create_agent_instance(self, request_id: str|None=None):
        """Create a new local agent instance for a request"""
        agent = ActorBaseAgent(name=self.name)

        # Set initial state
        agent.set_state(
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
                    "result_model": self.result_model,
                },
            ),
        )        
        if self._handle_turn_start:
            agent.set_callback("handle_turn_start", self._handle_turn_start)

        if request_id is None:
            self._agent = agent

        return agent

    def init_thread_tracking(self, agent, thread_id: Optional[str] = None):
        """Initialize thread tracking"""
        from .thread_manager import init_thread_tracking
        self.thread_id, callback = init_thread_tracking(self, db_path=self.db_path, resume_thread_id=thread_id)
        agent.set_callback('handle_event', callback)

    def _handle_mock_settings(self, mock_settings):
        """Handle mock settings for local implementation"""
        if mock_settings and self.model and "mock" in self.model:
            from agentic.models import mock_provider
            
            pattern = mock_settings.get("pattern", "")
            response = mock_settings.get("response", "This is a mock response.")
            tools_dict = mock_settings.get("tools", {})
            
            # Set in the local mock_provider directly
            mock_provider.set_response(pattern, response)
            mock_provider.clear_tools()
            for tool_name, tool_func in tools_dict.items():
                mock_provider.register_tool(tool_name, tool_func)
            
            # Pass to the local agent
            try:
                self._agent.set_mock_params(pattern, response, tools_dict)
            except Exception as e:
                print(f"Warning: Failed to set mock params on local agent: {e}")

    def _update_state(self, state: dict):
        """Update the local agent's state"""
        self._agent.set_state(SetState(self.name, state))

    def _set_agent_debug_level(self, debug_level):
        """Set the debug level on the local agent"""
        self._agent.set_debug_level(debug_level)

    def _reset_agent_history(self):
        """Reset the local agent's conversation history"""
        self._agent.reset_history()

    def _get_agent_history(self):
        """Get the local agent's conversation history"""
        return self._agent.get_history()

    def list_tools(self) -> list[str]:
        """Gets the current tool list from the local agent"""
        return self._agent.list_tools()

    def list_functions(self) -> list[str]:
        """Gets the current list of functions from the local agent"""
        return self._agent.list_functions()

    def _get_prompt_generator(self, agent, prompt):
        """Get generator for a new prompt - Local implementation"""
        return agent.handle_prompt_or_resume(prompt)
        
    def _get_resume_generator(self, agent, resume_input):
        """Get generator for resuming with input - Local implementation"""
        return agent.handle_prompt_or_resume(resume_input)
        
    def _process_generator(self, generator):
        """Process generator events - Local implementation"""
        for event in generator:
            yield event

if os.environ.get("AGENTIC_USE_RAY"):
    AgentProxyClass = RayAgentProxy
else:
    AgentProxyClass = LocalAgentProxy
