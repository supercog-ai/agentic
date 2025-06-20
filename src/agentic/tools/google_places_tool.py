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

    def __init__(self, api_key: str = None, base_url: str = "https://places.googleapis.com/v1/places"):
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
            self.place_details,
            self.nearby_search
        ]

    async def place_details(self, 
    thread_context: ThreadContext,
    place_id: str,
    field_mask_list: list[str]
    ) -> pd.DataFrame:
        """
        Wrapper for the Place Details API.
        Docs: https://developers.google.com/maps/documentation/places/web-service/place-details
        
        Parameters:
            place_id: A textual identifier that uniquely identifies a place
            field_mask_list: List of field masks to return
        
        Returns:
            DataFrame containing the included fields from field_mask
        """

        api_key = os.environ.get("GOOGLE_API_KEY")
        
        # If no API key is available, request it from the user
        if not api_key:
            return PauseForInputResult(
                {"GOOGLE_API_KEY": "Please provide your Google API key"}
            )
        
        # Log the operation
        thread_context.info(f"Calling Google API: Place Details")
        thread_context.debug(f"Place ID: {place_id}")

        field_mask = ",".join(field_mask_list)

        headers = {
            "Content-Type" : "application/json",
            "X-Goog-Api-Key" : f"{api_key}",
            "X-Goog-FieldMask" : f"{field_mask}"
        }

        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/{place_id}",
                headers=headers,
                timeout=30,
            )

        response.raise_for_status()
        results = response.json()
        df = pd.json_normalize(results)
        return df

    async def nearby_search(self,
    thread_context: ThreadContext,
    latitude: float,
    longitude: float,
    includedTypes: list[str],
    maxResultCount: int,
    field_mask: str,
    radius: float,
    ) -> pd.DataFrame:
        """
        Wrapper for the Nearby Search API.
        Docs: https://developers.google.com/maps/documentation/places/web-service/nearby-search
        
        Parameters:
            latitude: Search center
            longitude: Search center
            includedTypes: Included types (eg. ["restaurant"])
            maxResultCount: Maximum number of results to return (default 10)
            field_mask: The fields to return WITHOUT space separated commas (default: places.name,places.id), the best practice is to include few fields here and use place_details to find more details about a restaurant
            radius: Search radius (default 1000)

        Returns:
            DataFrame containing the query results as a list of place objects, containing the fields specified by field_mask
        """
        api_key = os.environ.get("GOOGLE_API_KEY")
        
        # If no API key is available, request it from the user
        if not api_key:
            return PauseForInputResult(
                {"GOOGLE_API_KEY": "Please provide your Google API key"}
            )
        
        # Log the operation
        thread_context.info(f"Calling Google API: Nearby Search")
        thread_context.debug(f"Location: {latitude}, {longitude}")

        headers = {
            "Content-Type" : "application/json",
            "X-Goog-Api-Key" : f"{api_key}",
            "X-Goog-FieldMask" : f"{field_mask}"
        }

        params = {
            "includedTypes": includedTypes,
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

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}:searchNearby",
                headers=headers,
                json=params,
                timeout=30,
            )

        response.raise_for_status()
        results = response.json()
        df = pd.json_normalize(results)
        return df