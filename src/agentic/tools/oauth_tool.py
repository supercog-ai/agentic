from dataclasses import dataclass
from typing import Any, Callable, Dict, Optional
from urllib.parse import urlencode
import os
from dotenv import load_dotenv

import httpx
from agentic.common import RunContext
from agentic.events import OAuthFlowResult
from agentic.tools.base import BaseAgenticTool

@dataclass
class OAuthConfig:
    """Configuration for OAuth flow"""
    authorize_url: str
    token_url: str
    client_id_key: str
    client_secret_key: str
    scopes: str
    tool_name: str

class OAuthTool(BaseAgenticTool):
    """Base class for tools that need OAuth authentication"""
    
    def __init__(self, oauth_config: OAuthConfig):
        self.oauth_config = oauth_config

    def get_tools(self) -> list[Callable]:
        return [self.authenticate]

    async def authenticate(self, run_context: RunContext) -> str | OAuthFlowResult:
        """Start or continue OAuth authentication flow"""
        # Load environment variables from .env file
        load_dotenv()

        # Check for existing token
        token = run_context.get_oauth_token(self.oauth_config.tool_name)
        if token:
            return f"Already authenticated with {self.oauth_config.tool_name}"

        # Check for auth code
        auth_code = run_context.get_oauth_auth_code(self.oauth_config.tool_name)

        if auth_code:
            token = await self._exchange_code_for_token(auth_code, run_context)
            if token:
                return f"Successfully authenticated with {self.oauth_config.tool_name}"
            return f"Failed to exchange authorization code for token with {self.oauth_config.tool_name}"

        # Start OAuth flow
        return await self._start_oauth_flow(run_context)

    def _get_secret(self, key: str, run_context: RunContext) -> Optional[str]:
        """Get secret from environment or secrets database"""
        # First try environment variables (including .env file)
        value = os.getenv(key)
        if value:
            return value
            
        # Then try secrets database through run_context
        return run_context.get_secret(key)

    async def _start_oauth_flow(self, run_context: RunContext) -> OAuthFlowResult:
        """Initialize OAuth authorization flow"""
        
        client_id = self._get_secret(self.oauth_config.client_id_key, run_context)

        if not client_id:
            raise ValueError(f"{self.oauth_config.client_id_key} not found in environment variables or secrets")

        callback_url = run_context.get_oauth_callback_url(self.oauth_config.tool_name)
        
        params = {
            "client_id": client_id,
            "redirect_uri": callback_url,
            "scope": self.oauth_config.scopes,  
            "state": run_context.run_id
        }
        
        # Add any additional params from child class
        extra_params = self._get_extra_auth_params(run_context)
        if extra_params:
            params.update(extra_params)
        
        auth_url = f"{self.oauth_config.authorize_url}?{urlencode(params)}"

        return OAuthFlowResult({
            "auth_url": auth_url,
            "tool_name": self.oauth_config.tool_name
        })

    async def _exchange_code_for_token(self, auth_code: str, run_context: RunContext) -> Optional[str]:
        """Exchange OAuth code for access token"""
        client_id = self._get_secret(self.oauth_config.client_id_key, run_context)
        client_secret = self._get_secret(self.oauth_config.client_secret_key, run_context)

        if not client_id or not client_secret:
            return None

        data = {
            "client_id": client_id,
            "client_secret": client_secret,
            "code": auth_code
        }

        # Add any additional data from child class
        extra_data = self._get_extra_token_data(run_context)
        if extra_data:
            data.update(extra_data)

        async with httpx.AsyncClient() as client:
            headers = {"Accept": "application/json"}
            response = await client.post(
                self.oauth_config.token_url,
                json=data,
                headers=headers
            )

            if response.status_code == 200:
                token_data = response.json()
                access_token = token_data.get("access_token")
                if access_token:
                    run_context.set_oauth_token(self.oauth_config.tool_name, access_token)
                    # Allow child class to handle additional token data
                    await self._handle_token_response(token_data, run_context)
                    return access_token
        return None

    def _get_extra_auth_params(self, run_context: RunContext) -> Dict[str, Any]:
        """Override to add additional authorization parameters"""
        return {}

    def _get_extra_token_data(self, run_context: RunContext) -> Dict[str, Any]:
        """Override to add additional token exchange data"""
        return {}

    async def _handle_token_response(self, token_data: Dict[str, Any], run_context: RunContext):
        """Override to handle additional token response data"""
        pass
