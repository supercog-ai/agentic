import inspect
from datetime import datetime
from pprint import pformat
from typing import Union, Type, Callable
from functools import partial
from agentic.colors import Colors
from litellm.types.utils import ModelResponse, Message


def debug_print(debug: bool, *args: str) -> None:
    if not debug:
        return

    def format_part(part):
        if isinstance(part, str):
            return part
        return pformat(part)

    message = " ".join(map(format_part, args))
    print(message)
    # print(f"\033[97m]\033[90m {message}\033[0m")


def debug_completion_start(debug: "DebugLevel", model: str, params: dict) -> None:
    if debug.debug_llm():
        if "messages" in params:
            print(f"{Colors.GREEN}>> {model}:{Colors.ENDC}")
            msgs = [
                f"{Colors.GREEN}{m['role']}: {m['content']}{Colors.ENDC}"
                for m in params["messages"]
            ]
            print("\n".join(msgs))


def debug_completion_end(debug: "DebugLevel", model: str, message: Message) -> None:
    if debug.debug_llm():
        print(f"{Colors.GREEN}<< {model}: {Colors.ENDC}")
        for line in (message.content or "").split("\n"):
            print(f"{Colors.FOREST_GREEN}{line}{Colors.ENDC}")
        if message.tool_calls:
            print(Colors.GREEN + pformat(message.tool_calls) + Colors.ENDC)


def merge_fields(target, source):
    for key, value in source.items():
        if isinstance(value, str):
            target[key] += value
        elif value is not None and isinstance(value, dict):
            merge_fields(target[key], value)


def merge_chunk(final_response: dict, delta: dict) -> None:
    delta.pop("role", None)
    merge_fields(final_response, delta)

    tool_calls = delta.get("tool_calls")
    if tool_calls and len(tool_calls) > 0:
        index = tool_calls[0].pop("index")
        merge_fields(final_response["tool_calls"][index], tool_calls[0])


def looks_like_langchain_tool(func_or_tool) -> bool:
    is_langchain_link_class = (
        "langchain" in str(type(func_or_tool))  # Is it a class?
        and hasattr(func_or_tool, "_run")  # Does it have a _run method?
        and hasattr(func_or_tool, "name")  # Does it have a name attribute?
        and hasattr(
            func_or_tool, "description"
        )  # Does it have a description attribute?
    )
    return is_langchain_link_class


def function_to_json(func) -> dict:
    """
    Converts a Python function into a JSON-serializable dictionary
    that describes the function's signature, including its name,
    description, and parameters.

    Args:
        func: The function to be converted.

    Returns:
        A dictionary representing the function's signature in JSON format.
    """

    if isinstance(func, dict):
        return func  # someone already marshalled this. Probably a Langchain tool

    type_map = {
        str: "string",
        int: "integer",
        float: "number",
        bool: "boolean",
        list: "array",
        dict: "object",
        type(None): "null",
    }

    try:
        signature = inspect.signature(func)
    except ValueError as e:
        raise ValueError(
            f"Failed to get signature for function {func.__name__}: {str(e)}"
        )

    parameters = {}
    for param in signature.parameters.values():
        try:
            param_type = type_map.get(param.annotation, "string")
        except KeyError as e:
            raise KeyError(
                f"Unknown type annotation {param.annotation} for parameter {param.name}: {str(e)}"
            )
        parameters[param.name] = {"type": param_type}

    required = [
        param.name
        for param in signature.parameters.values()
        if param.default == inspect._empty
    ]

    return {
        "type": "function",
        "function": {
            "name": func.__name__,
            "description": func.__doc__ or "",
            "parameters": {
                "type": "object",
                "properties": parameters,
                "required": required,
            },
        },
    }


def wrap_llm_function(fname, doc, func, *args):
    f = partial(func, *args)
    setattr(f, "__name__", fname)
    f.__doc__ = doc
    setattr(f, "__code__", func.__code__)
    # Keep the original arg list
    f.__annotations__ = func.__annotations__
    return f


def langchain_function_to_json(func_or_tool: Union[Callable, Type]) -> Callable:
    """
    Converts a Python function or tool class into a JSON-serializable dictionary
    that describes the function's signature for the OpenAI API.
    Works with both regular functions and tool classes that follow the LangChain
    BaseTool pattern (having name, description, and _run attributes).

    Args:
        func_or_tool: The function or tool class to be converted.

    Returns:
        A dictionary representing the function's signature in JSON format.
    """
    type_map = {
        str: "string",
        int: "integer",
        float: "number",
        bool: "boolean",
        list: "array",
        dict: "object",
        type(None): "null",
    }

    # Check if it's a tool class (following LangChain BaseTool pattern)
    is_tool_class = (
        hasattr(func_or_tool, "_run")  # Does it have a _run method?
        and hasattr(func_or_tool, "name")  # Does it have a name attribute?
        and hasattr(
            func_or_tool, "description"
        )  # Does it have a description attribute?
    )

    if is_tool_class:
        return wrap_llm_function(
            func_or_tool.name, func_or_tool.description, func_or_tool._run
        )
        tool_instance = func_or_tool
        func = tool_instance._run
        setattr(func, "__name__", tool_instance.name)
        setattr(func, "__doc__", tool_instance.description)
        return func
    else:
        func = func_or_tool
        name = func.__name__
        description = func.__doc__ or ""

    try:
        signature = inspect.signature(func)
    except ValueError as e:
        raise ValueError(f"Failed to get signature for function {name}: {str(e)}")

    parameters = {}
    for param in signature.parameters.values():
        # Skip 'self' parameter for class methods
        if param.name == "self":
            continue

        try:
            param_type = type_map.get(param.annotation, "string")
        except KeyError as e:
            raise KeyError(
                f"Unknown type annotation {param.annotation} for parameter {param.name}: {str(e)}"
            )
        parameters[param.name] = {"type": param_type}

    required = [
        param.name
        for param in signature.parameters.values()
        if param.default == inspect._empty and param.name != "self"
    ]

    return {
        "type": "function",
        "function": {
            "name": name,
            "description": description,
            "parameters": {
                "type": "object",
                "properties": parameters,
                "required": required,
            },
        },
    }
