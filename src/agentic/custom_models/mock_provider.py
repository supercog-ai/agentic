import litellm
from litellm import CustomLLM
from typing import Iterator, AsyncIterator, Dict, List, Any, Optional
from litellm.types.utils import GenericStreamingChunk, ModelResponse
import os

# Default response if environment variable is not set
DEFAULT_MOCK_RESPONSE = "This is a mock response."

# Environment variable name to store the mock response, class-level variable editing is not allowed
MOCK_RESPONSE_ENV_VAR = "AGENTIC_MOCK_RESPONSE"

def get_mock_response():
    """Get the current mock response from environment variable"""
    return os.environ.get(MOCK_RESPONSE_ENV_VAR, DEFAULT_MOCK_RESPONSE)

class MockModelProvider(CustomLLM):
    """
    Mock LLM provider for testing purposes.
    """
    def __init__(self):
        super().__init__()
    
    def completion(self, messages: List[Dict[str, str]], *args, **kwargs) -> ModelResponse:
        """Synchronous completion"""
        return litellm.completion(
            model="openai/gpt-3.5-turbo",
            messages=messages,
            mock_response=get_mock_response(),
        )
    
    async def acompletion(self, messages: List[Dict[str, str]], *args, **kwargs) -> ModelResponse:
        """Async version of completion"""
        return litellm.completion(
            model="gpt-3.5-turbo",
            messages=messages,
            mock_response=get_mock_response()
        )
    
    def streaming(self, model: str, messages: List[Dict[str, str]], *args, **kwargs) -> Iterator[GenericStreamingChunk]:
        """Return a mock streaming response"""
        generic_streaming_chunk: GenericStreamingChunk = {
            "finish_reason": "stop",
            "index": 0,
            "is_finished": True,
            "text": get_mock_response(),
            "tool_use": None,
            "usage": {"completion_tokens": 0, "prompt_tokens": 0, "total_tokens": 0},
        }
        yield generic_streaming_chunk
    
    async def astreaming(self, model: str, messages: List[Dict[str, str]], *args, **kwargs) -> AsyncIterator[GenericStreamingChunk]:
        """Async version of streaming"""
        generic_streaming_chunk: GenericStreamingChunk = {
            "finish_reason": "stop",
            "index": 0,
            "is_finished": True,
            "text": get_mock_response(),
            "tool_use": None,
            "usage": {"completion_tokens": 0, "prompt_tokens": 0, "total_tokens": 0},
        }
        yield generic_streaming_chunk
