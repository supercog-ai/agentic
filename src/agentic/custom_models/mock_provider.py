import litellm
from litellm import CustomLLM
from typing import Iterator, AsyncIterator, Dict, List, Any, Optional
from litellm.types.utils import GenericStreamingChunk, ModelResponse
import re
import ray

# Default response if not set
DEFAULT_MOCK_RESPONSE = "This is a mock response."


@ray.remote
class MockSettings:
    def __init__(self):
        self.pattern = ""
        self.response = DEFAULT_MOCK_RESPONSE
        self.available_tools = {}

    def set(self, pattern: str, response: str):
        self.pattern = pattern
        self.response = response

    def get(self) -> tuple[str, str]:
        return self.pattern, self.response
    
    def add_tool(self, name: str, function):
        """Register a tool function"""
        self.available_tools[name] = function
        
    def clear_tools(self):
        """Clear registered tools"""
        self.available_tools = {}
        
    def get_tools(self) -> Dict[str, Any]:
        """Get available tools"""
        return self.available_tools

# Global settings actor with a fixed name
try:
    mock_settings = ray.get_actor("mock_settings")
except:
    mock_settings = MockSettings.options(name="mock_settings").remote()

class MockModelProvider(CustomLLM):
    """Mock LLM provider for testing purposes."""
    def __init__(self):
        super().__init__()
        # Make sure the actor exists
        try:
            self.settings = ray.get_actor("mock_settings")
        except:
            self.settings = MockSettings.options(name="mock_settings").remote()

    def set_response(self, pattern_or_response: str, response: str = None) -> None:
        """Set the response pattern and template"""
        if response is None:
            # Single argument case - direct response
            ray.get(self.settings.set.remote("", pattern_or_response))
        else:
            # Two argument case - pattern matching
            ray.get(self.settings.set.remote(pattern_or_response, response))
    
    def register_tool(self, name: str, function) -> None:
        """Register a tool function for mock tool calls"""
        ray.get(self.settings.add_tool.remote(name, function))
        
    def clear_tools(self) -> None:
        """Clear registered tools"""
        ray.get(self.settings.clear_tools.remote())

    def get_mock_response(self, input_text: str = "") -> str:
        """Get the current mock response, applying pattern matching if configured"""
        pattern, response = ray.get(self.settings.get.remote())
        
        if pattern:
            try:
                match = re.match(pattern, input_text, re.IGNORECASE)
                if match:
                    result = response
                    for i, group in enumerate(match.groups(), 1):
                        result = result.replace(f"${i}", group)
                    return result
            except re.error:
                pass
        
        # Check for tool calling syntax: "call the function {name} with {params}"
        tool_call_match = re.match(r"call\s+(?:the\s+)?function\s+(\w+)(?:\s+with\s+(.+))?", input_text, re.IGNORECASE)
        if tool_call_match:
            function_name = tool_call_match.group(1)
            params_text = tool_call_match.group(2) or ""
            
            # Get available tools
            available_tools = ray.get(self.settings.get_tools.remote())
            
            if function_name in available_tools:
                # Parse parameters
                params = {}
                if params_text:
                    # Match key=value pairs
                    param_matches = re.findall(r'(\w+)\s*=\s*([^,]+)(?:,|$)', params_text)
                    for key, value in param_matches:
                        # Strip quotes and whitespace
                        params[key] = value.strip().strip('"\'')
                
                try:
                    # Call the function with parsed parameters
                    function = available_tools[function_name]
                    result = function(**params)
                    return result
                except Exception as e:
                    return f"Error calling function {function_name}: {str(e)}"
            else:
                return f"Function {function_name} not found."
        
        return response

    def completion(self, messages: List[Dict[str, str]], *args, **kwargs) -> ModelResponse:
        """Synchronous completion"""
        last_message = next((m["content"] for m in reversed(messages) 
                           if m["role"] == "user"), "")
        
        # Register tools
        if "tools" in kwargs:
            for tool in kwargs.get("tools", []):
                if isinstance(tool, dict) and "function" in tool and "name" in tool["function"]:
                    # This is the OpenAI/LiteLLM tool format
                    self.register_tool(tool["function"]["name"], tool["function"])
                elif hasattr(tool, "__name__") and callable(tool):
                    # This is a function directly provided as a tool
                    self.register_tool(tool.__name__, tool)
        
        # Process message to check for tool calls
        mock_response = self.get_mock_response(last_message)
        
        return litellm.completion(
            model="openai/gpt-3.5-turbo",
            messages=messages,
            mock_response=mock_response,
        )
    
    async def acompletion(self, messages: List[Dict[str, str]], *args, **kwargs) -> ModelResponse:
        """Async version of completion"""
        last_message = next((m["content"] for m in reversed(messages) 
                           if m["role"] == "user"), "")
        
        # Register tools from kwargs if present
        if "tools" in kwargs:
            for tool in kwargs.get("tools", []):
                if isinstance(tool, dict) and "function" in tool and "name" in tool["function"]:
                    # This is the OpenAI/LiteLLM tool format
                    self.register_tool(tool["function"]["name"], tool["function"])
                elif hasattr(tool, "__name__") and callable(tool):
                    # This is a function directly provided as a tool
                    self.register_tool(tool.__name__, tool)
        
        return litellm.completion(
            model="gpt-3.5-turbo",
            messages=messages,
            mock_response=self.get_mock_response(last_message)
        )
    
    def streaming(self, model: str, messages: List[Dict[str, str]], *args, **kwargs) -> Iterator[GenericStreamingChunk]:
        """Return a mock streaming response"""
        last_message = next((m["content"] for m in reversed(messages) 
                         if m["role"] == "user"), "")
        
        generic_streaming_chunk: GenericStreamingChunk = {
            "finish_reason": "stop",
            "index": 0,
            "is_finished": True,
            "text": self.get_mock_response(last_message),
            "tool_use": None,
            "usage": {"completion_tokens": 0, "prompt_tokens": 0, "total_tokens": 0},
        }
        yield generic_streaming_chunk
    
    async def astreaming(self, model: str, messages: List[Dict[str, str]], *args, **kwargs) -> AsyncIterator[GenericStreamingChunk]:
        """Async version of streaming"""
        last_message = next((m["content"] for m in reversed(messages) 
                           if m["role"] == "user"), "")
        
        generic_streaming_chunk: GenericStreamingChunk = {
            "finish_reason": "stop",
            "index": 0,
            "is_finished": True,
            "text": self.get_mock_response(last_message),
            "tool_use": None,
            "usage": {"completion_tokens": 0, "prompt_tokens": 0, "total_tokens": 0},
        }
        yield generic_streaming_chunk
