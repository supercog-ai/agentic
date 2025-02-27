import litellm
from litellm import CustomLLM
from typing import Iterator, AsyncIterator, Dict, List, Any, Optional
from litellm.types.utils import GenericStreamingChunk, ModelResponse
import re

# Default response if not set
DEFAULT_MOCK_RESPONSE = "This is a mock response."

class MockSettings:
    def __init__(self):
        self.pattern = ""
        self.response = DEFAULT_MOCK_RESPONSE
        self.available_tools = {}

    def set(self, pattern: str, response: str):
        """Set the pattern and response template"""
        self.pattern = pattern
        self.response = response

    def get(self) -> tuple[str, str]:
        """Get the current pattern and response template"""
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

# Create a singleton instance
mock_settings = MockSettings()

class MockModelProvider(CustomLLM):
    """Mock LLM provider for testing purposes."""
    def __init__(self):
        super().__init__()
        self.settings = mock_settings

    def set_response(self, pattern_or_response: str, response: str = None) -> None:
        """Set the response pattern and template"""
        if response is None:
            # Single argument case - direct response
            self.settings.set("", pattern_or_response)
        else:
            # Two argument case - pattern matching
            self.settings.set(pattern_or_response, response)
    
    def register_tool(self, name: str, function) -> None:
        """Register a tool function for mock tool calls"""
        self.settings.add_tool(name, function)
        
    def clear_tools(self) -> None:
        """Clear registered tools"""
        self.settings.clear_tools()

    def get_mock_response(self, input_text: str = "") -> str:
        """Get the current mock response, applying pattern matching if configured"""
        pattern, response = self.settings.get()
        
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
            available_tools = self.settings.get_tools()
            
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
            mock_response=mock_response
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
