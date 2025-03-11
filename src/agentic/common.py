from .runner import RayAgentRunner
from .events import SetState, AddChild, PauseForInputResult, WaitForInput
from .actor_agents import (
    AgentProxyClass,
    handoff,
)
from .swarm.types import RunContext
from .workflow import Pipeline
from jinja2 import Template
import os
import pickle
import tempfile
import hashlib
from typing import Any, Callable, TypeVar, ParamSpec, Dict, List
from pydantic import BaseModel, Field

# Common aliases
Agent = AgentProxyClass
AgentRunner = RayAgentRunner

def make_prompt(template: str, run_context: RunContext, **kwargs) -> str:
    context = run_context._context.copy() | kwargs
    return Template(template).render(context)


P = ParamSpec('P')
R = TypeVar('R')

def cached_call(func: Callable[P, R], *args: P.args, **kwargs: P.kwargs) -> R:
    """
    Explicitly cache a function call's result to a file in the temp directory.
    
    Args:
        func: The function to call with caching
        *args: Positional arguments to pass to the function
        **kwargs: Keyword arguments to pass to the function
        
    Returns:
        The result of the function call, either from cache or fresh execution
    """
    # Create a unique cache key based on function name and arguments
    key_parts = [func.__name__]
    key_parts.extend([str(arg) for arg in args])
    key_parts.extend([f"{k}:{v}" for k, v in sorted(kwargs.items())])
    
    # Create a hash of the key parts to use as filename
    cache_key = hashlib.md5(":".join(key_parts).encode()).hexdigest()
    cache_path = os.path.join(tempfile.gettempdir(), f"cache_{cache_key}.pkl")
    
    # Try to load from cache
    if os.path.exists(cache_path):
        try:
            with open(cache_path, 'rb') as f:
                print(f"Cache hit: Loading result for {func.__name__} from {cache_path}")
                return pickle.load(f)
        except (pickle.PickleError, IOError) as e:
            print(f"Cache error: {e}. Will recompute result.")
    
    # Cache miss or error - call the function
    result = func(*args, **kwargs)
    
    # Save result to cache
    try:
        with open(cache_path, 'wb') as f:
            pickle.dump(result, f)
            print(f"Cached result for {func.__name__} at {cache_path}")
    except (pickle.PickleError, IOError) as e:
        print(f"Failed to cache result: {e}")
        
    return result