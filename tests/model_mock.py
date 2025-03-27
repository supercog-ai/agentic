import pytest
import random
from typing import List, Dict, Optional, Any
from datetime import datetime
import unittest
from unittest.mock import patch
from typing import Optional, Dict, Any, List
import litellm
from datetime import datetime

class MockLiteLLMResponse:
    """
    Mock class for testing LiteLLM completion responses.
    Simulates both standard text completions and function calling responses.
    """
    def __init__(
        self,
        model: str = "gpt-3.5-turbo",
        messages: List[Dict[str, str]] = None,
        functions: Optional[List[Dict[str, Any]]] = None,
        mock_responses: List[str] = None,
    ):
        self.model = model
        self.messages = messages or []
        self.functions = functions
        self.mock_responses = mock_responses or [
            "This is a mock response.",
            "Here's another possible response.",
            "And one more mock response option."
        ]
        self._generate_response_id()

    def _generate_response_id(self) -> None:
        """Generate a unique response ID similar to OpenAI's format."""
        timestamp = datetime.now().strftime("%Y%m%d")
        self.response_id = f"mock-{timestamp}-{random.randint(1000, 9999)}"

    def _create_base_response(self) -> Dict[str, Any]:
        """Create the base response structure."""
        return {
            "id": self.response_id,
            "object": "chat.completion",
            "created": int(datetime.now().timestamp()),
            "model": self.model,
            "usage": {
                "prompt_tokens": random.randint(50, 200),
                "completion_tokens": random.randint(20, 100),
                "total_tokens": random.randint(70, 300)
            }
        }

    def _create_function_call_response(self) -> Dict[str, Any]:
        """Create a response that includes a function call."""
        if not self.functions:
            raise ValueError("No functions provided for function call response")

        # Randomly select a function to call
        selected_function = random.choice(self.functions)
        function_name = selected_function["name"]

        # Generate mock parameters based on function parameters
        mock_params = {}
        if "parameters" in selected_function:
            for param_name, param_info in selected_function["parameters"].get("properties", {}).items():
                # Generate mock value based on parameter type
                if param_info.get("type") == "string":
                    mock_params[param_name] = f"mock_{param_name}"
                elif param_info.get("type") == "number":
                    mock_params[param_name] = random.randint(1, 100)
                elif param_info.get("type") == "boolean":
                    mock_params[param_name] = random.choice([True, False])

        response = self._create_base_response()
        response["choices"] = [{
            "index": 0,
            "message": {
                "role": "assistant",
                "content": None,
                "function_call": {
                    "name": function_name,
                    "arguments": str(mock_params)
                }
            },
            "finish_reason": "function_call"
        }]
        return response

    def _create_text_response(self) -> Dict[str, Any]:
        """Create a standard text completion response."""
        response = self._create_base_response()
        response["choices"] = [{
            "index": 0,
            "message": {
                "role": "assistant",
                "content": random.choice(self.mock_responses)
            },
            "finish_reason": "stop"
        }]
        return response

    def get_response(self) -> Dict[str, Any]:
        """
        Get a mock completion response.
        Randomly decides between function call and text response if functions are available.
        """
        if self.functions and random.random() < 0.5:
            return self._create_function_call_response()
        return self._create_text_response()

# # Example usage:
# if __name__ == "__main__":
#     # Example functions for testing
#     example_functions = [{
#         "name": "get_weather",
#         "description": "Get the weather for a location",
#         "parameters": {
#             "type": "object",
#             "properties": {
#                 "location": {
#                     "type": "string",
#                     "description": "The city and state"
#                 },
#                 "unit": {
#                     "type": "string",
#                     "enum": ["celsius", "fahrenheit"]
#                 }
#             },
#             "required": ["location"]
#         }
#     }]

#     # Create mock response with functions
#     mock = MockLiteLLMResponse(
#         model="gpt-4",
#         functions=example_functions,
#         mock_responses=["The weather is sunny today!", "Expect rain in the afternoon."]
#     )

#     # Get multiple responses to demonstrate randomization
#     for _ in range(3):
#         response = mock.get_response()
#         print(f"\nResponse {_ + 1}:")
#         print(response)



class TestYourLLMCode(unittest.TestCase):
    def setUp(self):
        """Set up test fixtures before each test method."""
        self.mock_functions = [{
            "name": "get_weather",
            "description": "Get the weather for a location",
            "parameters": {
                "type": "object",
                "properties": {
                    "location": {"type": "string"},
                    "unit": {"type": "string", "enum": ["celsius", "fahrenheit"]}
                },
                "required": ["location"]
            }
        }]
        
        self.mock_response_generator = MockLiteLLMResponse(
            model="gpt-4",
            functions=self.mock_functions
        )

    def create_mock_completion(self, *args, **kwargs) -> Dict[str, Any]:
        """Helper method to generate mock completion responses"""
        return self.mock_response_generator.get_response()

    @patch('litellm.completion')
    def test_basic_completion(self, mock_completion):
        """Test basic text completion without functions"""
        # Setup the mock
        mock_completion.side_effect = self.create_mock_completion
        
        # Your actual code that uses litellm
        messages = [{"role": "user", "content": "Hello, how are you?"}]
        response = litellm.completion(
            model="gpt-4",
            messages=messages
        )
        
        # Assertions
        self.assertTrue(mock_completion.called)
        self.assertEqual(mock_completion.call_count, 1)
        self.assertIn("choices", response)
        self.assertIn("content", response["choices"][0]["message"])

    @patch('litellm.completion')
    def test_function_calling(self, mock_completion):
        """Test completion with function calling"""
        # Setup the mock with forced function call response
        def force_function_call(*args, **kwargs):
            response = self.mock_response_generator._create_function_call_response()
            return response

        mock_completion.side_effect = force_function_call
        
        # Your actual code that uses litellm
        messages = [{"role": "user", "content": "What's the weather like?"}]
        response = litellm.completion(
            model="gpt-4",
            messages=messages,
            functions=self.mock_functions
        )
        
        # Assertions
        self.assertTrue(mock_completion.called)
        self.assertIn("function_call", response["choices"][0]["message"])
        self.assertEqual(
            response["choices"][0]["message"]["function_call"]["name"],
            "get_weather"
        )

    @patch('litellm.completion')
    def test_completion_error(self, mock_completion):
        """Test handling of LiteLLM errors"""
        # Setup mock to raise an exception
        mock_completion.side_effect = Exception("API Error")
        
        # Test error handling
        with self.assertRaises(Exception):
            litellm.completion(
                model="gpt-4",
                messages=[{"role": "user", "content": "Hello"}]
            )

# Example of how to use in your actual code
class YourLLMClient:
    """Example class that uses LiteLLM"""
    
    def __init__(self, model: str = "gpt-4"):
        self.model = model
    
    async def get_completion(
        self,
        messages: List[Dict[str, str]],
        functions: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """Get completion from LiteLLM"""
        try:
            response = litellm.completion(
                model=self.model,
                messages=messages,
                functions=functions
            )
            return response
        except Exception as e:
            # Handle errors appropriately
            raise

# Example of how to test your actual code
@pytest.mark.asyncio
async def test_your_client():
    with patch('litellm.completion') as mock_completion:
        # Setup
        client = YourLLMClient()
        mock_response = MockLiteLLMResponse().get_response()
        mock_completion.return_value = mock_response
        
        # Test
        messages = [{"role": "user", "content": "Hello"}]
        response = await client.get_completion(messages)
        
        # Assertions
        assert mock_completion.called
        assert response == mock_response

if __name__ == '__main__':
    unittest.main()        