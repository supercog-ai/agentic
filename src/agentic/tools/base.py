from abc import ABC, abstractmethod
from typing import Callable

class BaseAgenticTool(ABC):
    """Base class for all Agentic tools."""

    @abstractmethod
    def __init__(self):
        pass

    @abstractmethod
    def get_tools(self) -> list[Callable]:
        """Forward method that should be implemented by subclasses."""
        pass
    
    def __getstate__(self):
        """Custom serialization for Ray."""
        state = {}
        for key, value in self.__dict__.items():
            if not key.startswith('_'):
                state[key] = value
        return state
