import pytest
from unittest.mock import patch, MagicMock
import litellm

from agentic.events import FinishCompletion
from litellm.types.utils import Message


# Extract the exact token usage logic from actor_agents.py
def extract_token_usage(llm_message, model, history):
    """
    Extract token usage from LiteLLM response or fall back to manual calculation.
    This function contains the exact same logic as in actor_agents.py.
    """
    callback_params = {}
    
    # Try to get usage directly from response - exactly as in actor_agents.py
    usage = getattr(llm_message, "usage", None)
    if usage:
        callback_params["input_tokens"] = usage.prompt_tokens
        callback_params["output_tokens"] = usage.completion_tokens
    else:
        # Fall back to manual calculation - exactly as in actor_agents.py
        if len(history) > 0:
            callback_params["input_tokens"] = litellm.token_counter(
                model, messages=history[-1:]
            )
        output = llm_message.choices[0].message
        if output.content:
            callback_params["output_tokens"] = litellm.token_counter(
                model, text=output.content
            )
    
    return callback_params


class MockUsage:
    """Mock for token usage data in LiteLLM response"""
    def __init__(self, prompt_tokens=100, completion_tokens=50):
        self.prompt_tokens = prompt_tokens
        self.completion_tokens = completion_tokens


class MockCompletion:
    """Mock for LiteLLM completion response"""
    def __init__(self, with_usage=True, prompt_tokens=100, completion_tokens=50, content="Test response"):
        self.choices = [
            MagicMock(message=Message(content=content, role="assistant"))
        ]
        if with_usage:
            self.usage = MockUsage(prompt_tokens, completion_tokens)

def test_usage_extraction_from_response():
    """Test that token usage is extracted from the LiteLLM response when available"""
    # Create mock completion response with usage data
    mock_completion = MockCompletion(with_usage=True, prompt_tokens=150, completion_tokens=75)
    history = [{"role": "user", "content": "Test prompt"}]
    model = "gpt-4o"
    
    # Extract token usage using our function
    callback_params = extract_token_usage(mock_completion, model, history)
    
    # Verify the token usage was extracted from the response
    assert callback_params["input_tokens"] == 150
    assert callback_params["output_tokens"] == 75
    
    # Verify token usage correctly flows to FinishCompletion event
    finish_event = FinishCompletion.create(
        "TestAgent",
        Message(content="Test response", role="assistant"),
        model,
        0,  # cost
        callback_params.get("input_tokens"),
        callback_params.get("output_tokens"),
        0,  # elapsed time
        0  # depth
    )
    
    assert finish_event.metadata[FinishCompletion.INPUT_TOKENS_KEY] == 150
    assert finish_event.metadata[FinishCompletion.OUTPUT_TOKENS_KEY] == 75

def test_usage_fallback_calculation():
    """Test that token usage falls back to manual calculation when not available in response"""
    # Create mock completion response without usage data
    mock_completion = MockCompletion(with_usage=False)
    history = [{"role": "user", "content": "Test prompt"}]
    model = "gpt-4o"
    
    # Set up mocking for token_counter
    with patch('litellm.token_counter', side_effect=[120, 60]):
        # Extract token usage using our function
        callback_params = extract_token_usage(mock_completion, model, history)
        
        # Verify the token usage was calculated manually
        assert callback_params["input_tokens"] == 120
        assert callback_params["output_tokens"] == 60
        
        # Verify token usage correctly flows to FinishCompletion event
        finish_event = FinishCompletion.create(
            "TestAgent",
            Message(content="Test response", role="assistant"),
            model,
            0,  # cost
            callback_params.get("input_tokens"),
            callback_params.get("output_tokens"),
            0,  # elapsed time
            0  # depth
        )
        
        assert finish_event.metadata[FinishCompletion.INPUT_TOKENS_KEY] == 120
        assert finish_event.metadata[FinishCompletion.OUTPUT_TOKENS_KEY] == 60

def test_empty_response_handling():
    """Test handling of empty response content"""
    # Create mock completion with empty content
    mock_completion = MockCompletion(with_usage=False, content="")
    history = [{"role": "user", "content": "Test prompt"}]
    model = "gpt-4o"
    
    # Set up mocking for token_counter - should only be called once for input
    with patch('litellm.token_counter', return_value=120) as mock_counter:
        # Extract token usage
        callback_params = extract_token_usage(mock_completion, model, history)
        
        # Verify token counter was only called once (for input)
        assert mock_counter.call_count == 1
        assert callback_params["input_tokens"] == 120
        assert "output_tokens" not in callback_params

def test_missing_history_handling():
    """Test handling when history is empty"""
    # Create mock completion
    mock_completion = MockCompletion(with_usage=False)
    empty_history = []
    model = "gpt-4o"
    
    # Set up mocking for token_counter - should only be called once for output
    with patch('litellm.token_counter', return_value=60) as mock_counter:
        # Extract token usage
        callback_params = extract_token_usage(mock_completion, model, empty_history)
        
        # Verify token counter was only called once (for output)
        assert mock_counter.call_count == 1
        assert "input_tokens" not in callback_params
        assert callback_params["output_tokens"] == 60

def test_token_counter_error_handling():
    """Test handling of errors in token counter"""
    mock_completion = MockCompletion(with_usage=False)
    history = [{"role": "user", "content": "Test prompt"}]
    model = "gpt-4o"
    
    # Simulate token_counter raising an exception
    with patch('litellm.token_counter', side_effect=Exception("Token counting failed")):
        try:
            # This should raise the exception
            callback_params = extract_token_usage(mock_completion, model, history)
            assert False, "Should have raised an exception"
        except Exception as e:
            # Verify the exception was properly raised
            assert str(e) == "Token counting failed"

@pytest.mark.requires_llm
def test_real_llm_usage_tracking():
    """Test token usage tracking with actual LLM API call"""
    from agentic.llm import llm_generate, LLMUsage
    
    usage = LLMUsage()
    prompt = "Respond only with the word 'test' in lowercase"
    model = "gpt-3.5-turbo"
    
    response = llm_generate(prompt, model=model, usage=usage)
    
    # Basic response validation
    assert response.strip().lower() == "test"
    
    # Verify token counts were tracked
    assert usage.input_tokens > 0, "Input tokens should be tracked"
    assert usage.output_tokens == 1, "Output tokens should be 1"
    assert usage.model == model, "Model should be recorded"
    
    # Verify usage flows through to FinishCompletion
    finish_event = FinishCompletion.create(
        "TestAgent",
        Message(content=response, role="assistant"),
        model,
        0,  # cost
        usage.input_tokens,
        usage.output_tokens,
        0,  # elapsed time
        0  # depth
    )
    
    assert finish_event.metadata[FinishCompletion.INPUT_TOKENS_KEY] == usage.input_tokens
    assert finish_event.metadata[FinishCompletion.OUTPUT_TOKENS_KEY] == usage.output_tokens