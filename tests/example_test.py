import pytest

def test_non_llm_function():
    assert 1 + 1 == 2

@pytest.mark.requires_llm
def test_function_requiring_llm():
    result = call_to_llm_api("test prompt")
    assert result is not None