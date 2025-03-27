import pytest
from unittest.mock import patch
import copy
from litellm.utils import trim_messages


# Test fixtures
@pytest.fixture
def sample_messages():
    return [
        {"role": "user", "content": "Hello"},
        {"role": "assistant", "content": "Hi there"},
        {"role": "tool", "content": "Tool response 1"},
        {"role": "tool", "content": "Tool response 2"},
    ]


@pytest.fixture
def mock_token_counter():
    with patch("litellm.token_counter", return_value=50) as mock:
        yield mock


@pytest.mark.skip(reason="Waiting for LiteLLM to fix this")
def test_tool_messages_preserved_when_under_limit(sample_messages, mock_token_counter):
    """
    Test that tool messages are preserved when messages are under the token limit.
    This test verifies the bug where tool messages are dropped even when no trimming is needed.
    """
    # Call the trim_messages function
    result = trim_messages(
        messages=copy.deepcopy(sample_messages),
        max_tokens=100,  # Set high enough that no trimming should occur
    )

    # Verify total message count
    assert len(result) == len(
        sample_messages
    ), f"Expected {len(sample_messages)} messages, but got {len(result)}. Tool messages were lost!"

    # Get tool messages
    original_tool_messages = [m for m in sample_messages if m["role"] == "tool"]
    result_tool_messages = [m for m in result if m["role"] == "tool"]

    # Verify tool message count
    assert len(result_tool_messages) == len(
        original_tool_messages
    ), "Tool messages were dropped even though no trimming was needed!"

    # Verify tool message content
    assert (
        result_tool_messages == original_tool_messages
    ), "Content of tool messages was modified!"


@pytest.mark.skip(reason="Waiting for LiteLLM to fix this")
def test_messages_order_preserved(sample_messages, mock_token_counter):
    """
    Test that the order of messages is preserved when no trimming is needed.
    This ensures that tool messages stay at the end and in their original order.
    """
    result = trim_messages(messages=copy.deepcopy(sample_messages), max_tokens=100)

    assert (
        result == sample_messages
    ), "Message order was modified when no trimming was needed!"


def test_zero_tool_messages(mock_token_counter):
    """
    Test that the function works correctly with no tool messages present.
    This ensures the tool message handling code doesn't affect regular messages.
    """
    messages = [
        {"role": "user", "content": "Hello"},
        {"role": "assistant", "content": "Hi there"},
    ]

    result = trim_messages(messages=copy.deepcopy(messages), max_tokens=100)

    assert (
        result == messages
    ), "Regular messages were modified when no tool messages present!"
