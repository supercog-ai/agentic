# Agentic Tools

This directory contains the tools available to agentic agents in the framework. Each tool is a Python module that provides specific functionality, which can be integrated into an agent's capabilities.

## What is a Tool?

In the agentic framework, a tool is a class that:
1. Inherits from `BaseAgenticTool`
2. Registers itself with the `tool_registry` 
3. Provides one or more functions that can be called by an agent
4. Declares functions inside the `get_tools` function that can be called by agents

Tools allow agents to interact with external services, access data, or perform operations that would otherwise be outside their capabilities.

## Tool Structure

Every tool must follow this basic structure:

```python
from typing import Callable
from agentic.tools.base import BaseAgenticTool
from agentic.tools.utils.registry import tool_registry

@tool_registry.register(
    name="YourToolName",
    description="A clear description of what your tool does",
    dependencies=[],
    config_requirements=[],
)
class YourTool(BaseAgenticTool):
    def __init__(self):
        # Initialize your tool here
        pass
        
    def get_tools(self) -> list[Callable]:
        # Return a list of the functions that can be called by agents
        return [
            self.your_function,
            # add more functions here
        ]
        
    def your_function(self, param1: str, param2: int) -> str:
        """
        A clear description of what this function does.
        
        Args:
            param1: Description of parameter
            param2: Description of parameter
            
        Returns:
            Description of return value
        """
        # Implement your functionality here
        return "Result"
```

## Key Components

### Registry Decorator

The `@tool_registry.register` decorator registers your tool with the framework and provides metadata:

```python
@tool_registry.register(
    name="YourToolName",           # Name of your tool
    description="Description",     # Description of what your tool does
    dependencies=[                 # External packages required by your tool
        Dependency(
            name="package-name",
            version="1.0.0",
            type="pip",
        ),
    ],
    config_requirements=[          # Configuration settings required by your tool
        ConfigRequirement(
            key="API_KEY_NAME",
            description="Description of the setting",
            required=True,         # Whether this setting is required
        ),
    ],
)
```

### Required Methods

Every tool must implement:

1. `__init__`: Initialize the tool with any necessary parameters
2. `get_tools`: Return a list of callable functions that will be available to the agent

### Optional Methods

Common optional functions include:

1. `required_secrets`: If your tool needs API keys or other secrets:
   ```python
   def required_secrets(self) -> dict[str, str]:
       return {
           "API_KEY_NAME": "Description of the API key",
           "OTHER_SECRET": "Description of other secret",
       }
   ```

2. `test_credential`: For validating credentials:
   ```python
   def test_credential(self, cred, secrets: dict) -> str | None:
       """Test that the given credential secrets are valid. 
       Return None if OK, otherwise return an error message.
       """
       # Validate credentials
       return None  # or error message
   ```

### Tool Functions

Each function that will be available to agents should:

1. Have a descriptive name
2. Include a clear docstring describing its purpose, parameters, and return value
3. For functions that need authentication, include a `thread_context` parameter
4. Have proper type hints for parameters and return values

Functions can be synchronous or asynchronous:

```python
def synchronous_function(self, param: str) -> str:
    """Description of function"""
    return "Result"

async def asynchronous_function(self, param: str) -> str:
    """Description of function"""
    # asynchronous operations
    return "Result"
```

## Authentication & Secrets

Tools can handle authentication in several ways:

1. Constructor parameters:
   ```python
   def __init__(self, api_key: str = None):
       self.api_key = api_key
   ```

2. Using the `thread_context` to get secrets:
   ```python
   def my_function(self, thread_context: RunContext, param: str) -> str:
       api_key = thread_context.get_secret("API_KEY_NAME", self.api_key)
       # use api_key to authenticate
   ```

3. Requesting input when secrets are missing:
   ```python
   if not api_key:
       return PauseForInputResult(
           {"API_KEY_NAME": "Please supply your API key"}
       )
   ```

## Adding a New Tool

To add a new tool to the repository:

1. Create a new Python file in the tools directory with a descriptive name (e.g., `your_tool.py`)
2. Implement your tool following the structure described above
3. Register it with the tool registry using the `@tool_registry.register` decorator
4. Add your tool to the `_TOOL_MAPPING` and `__all__` lists in `__init__.py`
5. Write tests for your tool in the appropriate test files

## Testing Your Tool

All tools should have tests. The test directory includes several test files for tool functionality:

- `test_tool_use.py`: Basic tool usage tests
- `test_tools_init.py`: Tests for proper tool initialization and registration
- `test_tools_registry.py`: Tests for the tool registry

Follow the patterns in these files to write tests for your own tool.

## Best Practices

1. **Descriptive Names**: Give your tool and its functions clear, descriptive names
2. **Detailed Docstrings**: Write clear docstrings for your tool and all its functions
3. **Error Handling**: Handle errors gracefully and return informative error messages
4. **Default Values**: Provide sensible defaults for parameters when possible
5. **Type Hints**: Use proper type hints for all parameters and return values
6. **Async Support**: Use `async def` for functions that involve I/O or network operations
7. **Minimal Dependencies**: Keep external dependencies to a minimum
8. **Proper Testing**: Write comprehensive tests for your tool

## Example Tools

For examples of well-implemented tools, see:

- `example_tool.py`: A simple template tool
- `weather_tool.py`: Tool for accessing weather data
- `tavily_search_tool.py`: Tool for performing web searches
- `github_tool.py`: Tool for interacting with GitHub
