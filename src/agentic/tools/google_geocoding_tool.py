import httpx
from typing import Callable, Dict, Optional, Union
import pandas as pd
import os
import json

from agentic.tools.base import BaseAgenticTool
from agentic.tools.utils.registry import tool_registry, ConfigRequirement
from agentic.common import ThreadContext, PauseForInputResult

@tool_registry.register(
    name="GoogleGeocodingTool",
    description="Tool for interacting with the Google Geocoding API",
    dependencies=[],  # List any required pip packages here that are not already in the pyproject.toml
    config_requirements=[
        # List any required configuration settings here
        ConfigRequirement(
            key="GOOGLE_API_KEY",
            description="API key for Google APIs",
            required=True,  # Set to True if this is mandatory
        ),
    ],
)

class GoogleGeocodingTool(BaseAgenticTool):
    
    # Instance variables for configuration
    api_key: Optional[str]
    base_url: str

    def __init__(self, api_key: str = None, base_url: str = "https://maps.googleapis.com/maps/api/geocode/json"):
        """
        Initialize the Google Geocoding tool.
        
        Args:
            api_key: Optional API key for authentication, can also be provided via secrets
            base_url: Base URL for the API, defaults to https://api.example.com
        """
        self.api_key = api_key
        self.base_url = base_url

    def required_secrets(self) -> Dict[str, str]:
        """
        Define the secrets that this tool requires.
        
        Returns:
            Dictionary mapping secret names to descriptions
        """
        return {
            "GOOGLE_API_KEY": "API key for authenticating with Google Places API"
        }

    def get_tools(self) -> list[Callable]:
        """
        Return the list of callable methods that will be available to agents.
        
        Returns:
            List of callable methods
        """
        return [
            self.geocode,
        ]

    async def geocode(self,
    thread_context: ThreadContext,
    address: str
    ):
        """
        Wrapper for the Geocoding API.
        Docs: https://developers.google.com/maps/documentation/geocoding/requests-geocoding
        
        Parameters:
            address: Street address or plus code to be geocoded. Addresses should be formatted in the same format as the national post service of the country.

        Returns:
            Query results JSON object, including lat/long coordinates of the address.
        """

        api_key = os.environ.get("GOOGLE_API_KEY")
        
        # If no API key is available, request it from the user
        if not api_key:
            return PauseForInputResult(
                {"GOOGLE_API_KEY": "Please provide your Google API key"}
            )
        
        # Log the operation
        thread_context.info(f"Calling Google Geocoding API")
        thread_context.debug(f"Address: {address}")

        params = {
            "address": address,
            "key" : f"{api_key}"
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}",
                params=params,
                timeout=30,
            )

        response.raise_for_status()
        results = response.json()

        return results
