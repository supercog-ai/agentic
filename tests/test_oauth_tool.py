import pytest
from unittest.mock import Mock, AsyncMock, patch
from agentic.tools.oauth_tool import OAuthTool, OAuthConfig
from agentic.events import OAuthFlowResult
from agentic.common import ThreadContext

@pytest.fixture
def oauth_config():
    return OAuthConfig(
        authorize_url="https://test.com/auth",
        token_url="https://test.com/token",
        client_id_key="TEST_CLIENT_ID",
        client_secret_key="TEST_CLIENT_SECRET",
        scopes="test_scope",
        tool_name="test_tool"
    )

@pytest.fixture
def mock_thread_context():
    context = Mock(spec=ThreadContext)
    context.thread_id = "test_run_123"
    return context

@pytest.fixture
def oauth_tool(oauth_config):
    return OAuthTool(oauth_config)

@pytest.mark.asyncio
async def test_authenticate_with_existing_token(oauth_tool, mock_thread_context):
    # Setup mock to return existing token
    mock_thread_context.get_oauth_token.return_value = "existing_token"
    
    result = await oauth_tool.authenticate(mock_thread_context)
    
    assert result == "Already authenticated with test_tool"
    mock_thread_context.get_oauth_token.assert_called_once_with("test_tool")

@pytest.mark.asyncio
async def test_authenticate_with_auth_code(oauth_tool, mock_thread_context):
    # Setup mocks
    mock_thread_context.get_oauth_token.return_value = None
    mock_thread_context.get_oauth_auth_code.return_value = "test_auth_code"
    
    # Mock the token exchange
    with patch.object(oauth_tool, '_exchange_code_for_token', new_callable=AsyncMock) as mock_exchange:
        mock_exchange.return_value = "new_token"
        
        result = await oauth_tool.authenticate(mock_thread_context)
        
        assert result == "Successfully authenticated with test_tool"
        mock_exchange.assert_called_once_with("test_auth_code", mock_thread_context)

@pytest.mark.asyncio
async def test_authenticate_start_oauth_flow(oauth_tool, mock_thread_context, monkeypatch):
    # Setup mocks to trigger OAuth flow start
    mock_thread_context.get_oauth_token.return_value = None
    mock_thread_context.get_oauth_auth_code.return_value = None
    mock_thread_context.get_oauth_callback_url.return_value = "https://callback.url"
    
    # Use monkeypatch instead of directly setting env var
    monkeypatch.setenv("TEST_CLIENT_ID", "test_client_id")
    
    result = await oauth_tool.authenticate(mock_thread_context)
    
    assert isinstance(result, OAuthFlowResult)
    assert "auth_url" in result.request_keys
    assert result.request_keys["tool_name"] == "test_tool"

@pytest.mark.asyncio
async def test_exchange_code_for_token(oauth_tool, mock_thread_context, monkeypatch):
    # Use monkeypatch for environment variables
    monkeypatch.setenv("TEST_CLIENT_ID", "test_client_id")
    monkeypatch.setenv("TEST_CLIENT_SECRET", "test_client_secret")
    
    with patch('httpx.AsyncClient.post', new_callable=AsyncMock) as mock_post:
        mock_response = AsyncMock()
        mock_response.status_code = 200
        # Mock json as a regular method, not async
        mock_response.json = Mock(return_value={"access_token": "new_token"})
        mock_post.return_value = mock_response
        
        token = await oauth_tool._exchange_code_for_token("test_auth_code", mock_thread_context)
        
        assert token == "new_token"
        mock_thread_context.set_oauth_token.assert_called_once_with("test_tool", "new_token")

@pytest.mark.asyncio
async def test_exchange_code_for_token_failure(oauth_tool, mock_thread_context, monkeypatch):
    # Use monkeypatch for environment variables
    monkeypatch.setenv("TEST_CLIENT_ID", "test_client_id")
    monkeypatch.setenv("TEST_CLIENT_SECRET", "test_client_secret")
    
    with patch('httpx.AsyncClient.post', new_callable=AsyncMock) as mock_post:
        mock_response = AsyncMock()
        mock_response.status_code = 400
        mock_response.json = Mock(return_value={})
        mock_post.return_value = mock_response
        
        token = await oauth_tool._exchange_code_for_token("test_auth_code", mock_thread_context)
        
        assert token is None
        mock_thread_context.set_oauth_token.assert_not_called()

@pytest.mark.asyncio
async def test_start_oauth_flow_missing_client_id(oauth_tool, mock_thread_context):
    mock_thread_context.get_oauth_callback_url.return_value = "https://callback.url"
    mock_thread_context.get_secret.return_value = None
    
    with pytest.raises(ValueError) as exc_info:
        await oauth_tool._start_oauth_flow(mock_thread_context)
    
    assert "TEST_CLIENT_ID not found in environment variables" in str(exc_info.value)

def test_extra_params_methods(oauth_tool, mock_thread_context):
    # Test default implementations of extra params methods
    assert oauth_tool._get_extra_auth_params(mock_thread_context) == {}
    assert oauth_tool._get_extra_token_data(mock_thread_context) == {}

@pytest.mark.asyncio
async def test_handle_token_response(oauth_tool, mock_thread_context):
    # Test default implementation of handle token response
    token_data = {"access_token": "test_token"}
    await oauth_tool._handle_token_response(token_data, mock_thread_context)
    # Should complete without errors
