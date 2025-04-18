# Building Tools

This guide will walk you through the process of creating your own tools for the agentic framework. While you can always use basic functions as tools, creating a proper tool class with the right structure provides better integration with the framework and enables more advanced features.

## Getting Started

To create a new tool, you'll need to:

1. Install the agentic framework
2. Set up a project with `agentic init`
3. Create a new tool file in the tools directory
4. Register your tool with the framework
5. Implement the required functions

Let's walk through these steps in detail.

### 1. Installation

If you haven't already installed the agentic framework, do so with pip. It is best practice to create a new virtual environment for your project:

```bash
pip install uv
uv venv
source .venv/bin/activate
pip install agentic-framework
```

### 2. Project Setup

Create a new project or navigate to your existing project directory and initialize it with agentic::

```bash
agentic init
```

This will create the necessary directory structure, including a `tools` directory where your custom tools will live.

### 3. Creating a Tool File

Navigate to the `tools` directory and create a new Python file for your tool. For example, if you're creating a weather tool:

```bash
cd tools
touch weather_tool.py
```

### 4. Basic Tool Structure

Here's the basic structure for a tool:

```python
from typing import Callable, Dict, Optional
from agentic.tools.base import BaseAgenticTool
from agentic.tools.utils.registry import tool_registry, Dependency, ConfigRequirement
from agentic.common import RunContext

@tool_registry.register(
    name="YourToolName",
    description="A clear description of what your tool does",
    dependencies=[],  # Any pip packages your tool depends on
    config_requirements=[],  # Any required configuration settings
)
class YourTool(BaseAgenticTool):
    """Detailed description of your tool class."""
    
    def __init__(self, param1: str = None, param2: str = "default"):
        """Initialize your tool with any necessary parameters."""
        self.param1 = param1
        self.param2 = param2
    
    def get_tools(self) -> list[Callable]:
        """Return a list of functions that will be exposed to the agent."""
        return [
            self.your_function,
            # Add more functions here
        ]
    
    def your_function(self, run_context: RunContext, param: str) -> str:
        """
        A function that the agent can call.
        
        Args:
            run_context: Execution context for accessing secrets and settings
            param: Description of parameter
            
        Returns:
            Result of the operation
        """
        # Implement your functionality here
        return f"Processed {param} with {self.param1}"
```

## Tool Registry Decorator

The `@tool_registry.register` decorator registers your tool with the framework and provides important metadata:

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

## Required Methods

Every tool must implement:

1. `__init__`: Initialize the tool with any necessary parameters
2. `get_tools`: Return a list of callable functions that will be exposed to the agent

## Optional Methods

Common optional functions include:

```python
def required_secrets(self) -> Dict[str, str]:
    """Define secrets that this tool requires."""
    return {
        "API_KEY_NAME": "Description of the API key",
        "OTHER_SECRET": "Description of other secret",
    }

def test_credential(self, cred: str, secrets: Dict[str, str]) -> Optional[str]:
    """
    Test that the given credential secrets are valid.
    Return None if valid, otherwise return an error message.
    """
    # Validate credentials
    api_key = secrets.get("API_KEY_NAME")
    if not api_key:
        return "API key is missing"
    # Test the API key
    return None  # Return None if valid
```

## Advanced Features

### Asynchronous Methods

You can create asynchronous functions for operations that involve I/O or network requests:

```python
async def fetch_data(self, run_context: RunContext, query: str) -> Dict[str, any]:
    """
    Asynchronously fetch data based on the query.
    
    Args:
        run_context: Execution context
        query: Search query
        
    Returns:
        Dictionary containing the results
    """
    # Async implementation
    # You can use httpx, aiohttp, etc. for async HTTP requests
    
    return {"results": ["data1", "data2"]}
```

### Handling Authentication

Tools often need API keys or other credentials. You can get these from the RunContext:

```python
def authenticated_function(self, run_context: RunContext, param: str) -> str:
    """Method that requires authentication."""
    # Get API key from secrets or instance variable
    api_key = run_context.get_secret("API_KEY_NAME", self.api_key)
    
    # If no API key is available, request it from the user
    if not api_key:
        from agentic.events import PauseForInputResult
        return PauseForInputResult(
            {"API_KEY_NAME": "Please provide your API key"}
        )
    
    # Use the API key for authentication
    return "Authenticated operation completed"
```

### Progress Reporting

For long-running operations, you can report progress using generators:

```python
def long_operation(self, run_context: RunContext) -> str:
    """Perform a long-running operation with progress updates."""
    total_steps = 10
    
    for step in range(total_steps):
        # Perform some work...
        
        # Report progress
        yield run_context.log(f"Step {step+1}/{total_steps} completed")
    
    return "Operation completed successfully"
```

## Registering Your Tool in the Framework

After creating your tool, you need to register it in the framework's tool registry. This happens automatically when your tool is loaded, thanks to the `@tool_registry.register` decorator.

## Example: Building a Simple Weather Tool

Here's a complete example of a simple weather tool:

```python
from typing import Callable, Dict, Optional
import requests

from agentic.tools.base import BaseAgenticTool
from agentic.tools.utils.registry import tool_registry, Dependency
from agentic.common import RunContext

@tool_registry.register(
    name="SimpleWeatherTool",
    description="A tool for getting basic weather information",
    dependencies=[
        Dependency(
            name="requests",
            version="2.28.1",
            type="pip",
        ),
    ],
)
class SimpleWeatherTool(BaseAgenticTool):
    """A simple tool for fetching weather data."""
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key
    
    def required_secrets(self) -> Dict[str, str]:
        return {
            "WEATHER_API_KEY": "API key for accessing weather data"
        }
    
    def get_tools(self) -> list[Callable]:
        return [
            self.get_current_weather,
        ]
    
    def get_current_weather(
        self, 
        run_context: RunContext, 
        city: str, 
        units: str = "metric"
    ) -> Dict[str, any]:
        """
        Get the current weather for a city.
        
        Args:
            run_context: Execution context
            city: The name of the city
            units: Units of measurement ('metric' or 'imperial')
            
        Returns:
            Weather data for the city
        """
        # Get API key from secrets or instance variable
        api_key = run_context.get_secret("WEATHER_API_KEY", self.api_key)
        
        # If no API key is available, request it from the user
        if not api_key:
            from agentic.events import PauseForInputResult
            return PauseForInputResult(
                {"WEATHER_API_KEY": "Please provide your weather API key"}
            )
        
        # Make API request
        url = f"https://api.example.com/weather"
        params = {
            "q": city,
            "units": units,
            "appid": api_key
        }
        
        run_context.info(f"Fetching weather data for {city}")
        
        try:
            response = requests.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            
            return {
                "city": city,
                "temperature": data["main"]["temp"],
                "conditions": data["weather"][0]["description"],
                "humidity": data["main"]["humidity"],
                "wind_speed": data["wind"]["speed"]
            }
        except Exception as e:
            run_context.error(f"Error fetching weather data: {str(e)}")
            return {"error": f"Failed to fetch weather data: {str(e)}"}
```

## Testing Your Tool

It's important to test your tool to ensure it works correctly. You can create a simple script to test your tool:

```python
from agentic.common import Agent
from your_tools import YourTool

# Create an instance of your tool
your_tool = YourTool()

# Create an agent with your tool
agent = Agent(
    name="TestAgent",
    tools=[your_tool]
)

# Test your agent with a prompt that will use your tool
result = agent.run("Use YourTool to perform a test operation")
print(result)
```

## Best Practices

1. **Clear Documentation**: Write comprehensive docstrings for your tool class and all its functions
2. **Descriptive Names**: Use clear, descriptive names for your tool and its functions
3. **Type Hints**: Always use proper type hints for parameters and return values
4. **Error Handling**: Handle errors gracefully and return informative error messages
5. **Async for I/O**: Use async functions for I/O operations to avoid blocking
6. **Progress Reporting**: For long-running operations, report progress using generators
7. **Secrets Management**: Use the required_secrets function to declare required secrets
8. **Testing**: Write tests for your tool to ensure it works correctly

By following these guidelines, you can create powerful, reliable tools that will enhance your agents' capabilities and provide a seamless experience for users.
