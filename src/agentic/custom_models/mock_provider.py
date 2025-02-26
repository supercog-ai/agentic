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

    def set(self, pattern: str, response: str):
        self.pattern = pattern
        self.response = response

    def get(self) -> tuple[str, str]:
        return self.pattern, self.response

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
        
        return response

    def completion(self, messages: List[Dict[str, str]], *args, **kwargs) -> ModelResponse:
        """Synchronous completion"""
        last_message = next((m["content"] for m in reversed(messages) 
                           if m["role"] == "user"), "")
        
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
