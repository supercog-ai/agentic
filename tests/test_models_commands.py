import pytest
from typer.testing import CliRunner
from unittest.mock import patch, MagicMock, ANY
from agentic.cli import app
from agentic.llm import LLMUsage

runner = CliRunner()

def test_models_list():
    """Test the models list command"""
    result = runner.invoke(app, ["models", "list"])
    assert result.exit_code == 0
    # Check that the output contains expected text
    assert "Visit https://docs.litellm.ai/docs/providers" in result.stdout
    assert "Popular models:" in result.stdout
    assert "openai/gpt-4o" in result.stdout
    assert "anthropic/claude-3-5-sonnet" in result.stdout

@patch('requests.get')
@patch('agentic.llm.llm_generate')
def test_models_ollama(mock_llm_generate, mock_requests_get):
    """Test the models ollama command"""
    # Mock the HTTP response
    mock_response = MagicMock()
    mock_response.content = b"<html>Model1\nModel2</html>"
    mock_requests_get.return_value = mock_response
    
    # Mock the LLM response
    mock_llm_generate.return_value = "## Popular Models\n- Model1: Description\n- Model2: Description"
    
    # Mock the file_cache to avoid tuple input error
    with patch('agentic.cli.file_cache.get') as mock_cache:
        mock_cache.return_value = "## Popular Models\n- Model1: Description\n- Model2: Description"
        result = runner.invoke(app, ["models", "ollama"])
    
        assert result.exit_code == 0
        assert "Current popular Ollama models:" in result.stdout
        assert "Popular Models" in result.stdout
        
        # Verify the mocks were called correctly
        mock_requests_get.assert_called_once_with("https://ollama.com/library")

@patch('agentic.llm.llm_generate')
def test_models_claude(mock_llm_generate):
    """Test the models claude command"""
    test_prompt = "Test prompt"
    mock_llm_generate.return_value = "Claude response"
    
    result = runner.invoke(app, ["models", "claude", test_prompt])
    
    assert result.exit_code == 0
    assert "Claude response" in result.stdout
    
    # Verify the mock was called with correct arguments
    mock_llm_generate.assert_called_once_with(
        test_prompt,
        model="anthropic/claude-3-5-sonnet-20240620",
        usage=ANY
    )
    # Verify usage object was passed
    usage_arg = mock_llm_generate.call_args[1]['usage']
    assert isinstance(usage_arg, LLMUsage)

@patch('agentic.llm.llm_generate')
def test_models_gpt(mock_llm_generate):
    """Test the models gpt command"""
    test_prompt = "Test prompt"
    test_model = "openai/gpt-4o-mini"
    mock_llm_generate.return_value = "GPT response"
    
    result = runner.invoke(app, ["models", "gpt", test_prompt, "--model", test_model])
    
    assert result.exit_code == 0
    assert "GPT response" in result.stdout
    
    # Verify the mock was called with correct arguments
    mock_llm_generate.assert_called_once_with(
        test_prompt,
        model=test_model,
        usage=ANY
    )
    # Verify usage object was passed
    usage_arg = mock_llm_generate.call_args[1]['usage']
    assert isinstance(usage_arg, LLMUsage)

@patch('agentic.llm.llm_generate')
def test_models_gpt_default_model(mock_llm_generate):
    """Test the models gpt command with default model"""
    test_prompt = "Test prompt"
    mock_llm_generate.return_value = "GPT response"
    
    result = runner.invoke(app, ["models", "gpt", test_prompt])
    
    assert result.exit_code == 0
    assert "GPT response" in result.stdout
    
    # Verify the mock was called with correct arguments and default model
    mock_llm_generate.assert_called_once_with(
        test_prompt,
        model="openai/gpt-4o-mini",
        usage=ANY
    )
    # Verify usage object was passed
    usage_arg = mock_llm_generate.call_args[1]['usage']
    assert isinstance(usage_arg, LLMUsage) 