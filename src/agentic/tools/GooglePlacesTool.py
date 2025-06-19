import httpx
from typing import Callable, Dict, Optional, Union
import pandas as pd
import os
import json

from agentic.tools.base import BaseAgenticTool
from agentic.tools.utils.registry import tool_registry, ConfigRequirement
from agentic.common import ThreadContext, PauseForInputResult

@tool_registry.register(
    name="GooglePlacesTool",
    description="Tool for interacting with the Google Places API",
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

class GooglePlacesTool(BaseAgenticTool):
    
    # Instance variables for configuration
    api_key: Optional[str]
    base_url: str

    def __init__(self, api_key: str = None, base_url: str = "https://places.googleapis.com/v1/places:"):
        """
        Initialize the Google Places tool.
        
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
            self.nearby_search
        ]

    async def nearby_search(self,
    thread_context: ThreadContext,
    latitude: float,
    longitude: float,
    maxResultCount: int = 10,
    field_mask: str = "places.name,places.priceRange,places.rating",
    radius: float = 500,
    ):
        """
        Wrapper for the Nearby Search API.
        Docs: https://developers.google.com/maps/documentation/places/web-service/nearby-search
        
        Parameters:
            latitude: Search center
            longitude: Search center
            maxResultCount: Maximum number of results to return (default 10)
            field_mask: The fields to return WITHOUT space separated commas (eg. places.name,places.priceRange,places.rating)
            radius: Search radius (default 1000)

        Returns:
            DataFrame containing the query results
        """

        api_key = os.environ.get("GOOGLE_API_KEY")
        
        # If no API key is available, request it from the user
        if not api_key:
            return PauseForInputResult(
                {"GOOGLE_API_KEY": "Please provide your Google API key"}
            )
        
        # Log the operation
        thread_context.info(f"Calling Google API: Nearby Search")
        thread_context.info(f"Location: {latitude}, {longitude}")

        headers = {
            "Content-Type" : "application/json",
            "X-Goog-Api-Key" : f"{api_key}",
            "X-Goog-FieldMask" : f"places.displayName"
        }

        params = {
            "maxResultCount": maxResultCount,
            "locationRestriction" : {
                "circle": {
                    "center": {
                        "latitude": latitude,
                        "longitude": longitude,
                    },
                    "radius": radius
                }
            }
        }

        params = {
            "maxResultCount": 10,
            "locationRestriction" : {
                "circle": {
                    "center": {
                        "latitude": 43.874168,
                        "longitude": -79.258743,
                    },
                    "radius": 500
                }       
            }
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}searchNearby",
                headers=headers,
                json=params,
                timeout=30,
            )

        response.raise_for_status()
        results = response.json()

        return results