from typing import Callable, Dict, Optional, Tuple

import datetime

import tzlocal


#import requests
#from ip2geotools.databases.noncommercial import DbIpCity

from agentic.tools.base import BaseAgenticTool
from agentic.tools.utils.registry import tool_registry, ConfigRequirement
from agentic.common import ThreadContext

@tool_registry.register(
    name="GeolocationTool",
    description="Tool to get the current geographical location of the user",
    #dependencies=["ip2geotools"],
    config_requirements=[
        ConfigRequirement(
            key="free",
            description="API key for IP geolocation service (if using a paid service)",
            required=False,
        ),
    ],
)
class GeolocationTool(BaseAgenticTool):
    """
    A tool that retrieves the current geographical location of the user
    based on their public IP address.
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the Geolocation tool.
        
        Args:
            api_key: Optional API key for IP geolocation services
        """
        self.api_key = api_key

    def get_tools(self) -> list[Callable]:
        return [
            #self.get_current_location,
            self.get_current_time,
            self.get_current_timezone,
        ]

    
    async def get_current_location(self) -> Dict[str, str]:
        """
        Get the current geographical location based on the user's public IP address.
        
        Returns:
            Dictionary containing location information including:
            - ip: The public IP address
            - city: The city name
            - region: The region/state
            - country: The country name
            - latitude: The latitude coordinate
            - longitude: The longitude coordinate
            - timezone: The timezone
        """
        return "place"
        '''
        try:
            # First, get the public IP address
            ip_response = requests.get('https://api.ipify.org?format=json')
            ip_response.raise_for_status()
            ip_address = ip_response.json()['ip']
            
            # Get location information using the IP address
            response = DbIpCity.get(ip_address, api_key=self.api_key)
            
            return {
                'ip': ip_address,
                'city': response.city,
                'region': response.region,
                'country': response.country,
                'latitude': response.latitude,
                'longitude': response.longitude,
                'timezone': response.time_zone
            }
            
        except Exception as e:
            raise Exception(f"Failed to retrieve location information: {str(e)}")
        '''

    async def get_current_time(self, timezone: Optional[str] = None) -> Dict[str, str]:
        
        try:
            current_time = datetime.datetime.now()    
            return current_time.isoformat(),

        except Exception as e:
            raise Exception(f"Failed to get current time: {str(e)}")

    async def get_current_timezone(self) -> Dict[str, str]:
        """
        Get the current timezone information based on the user's location.
        
        Returns:
            Dictionary containing:
            - timezone: The timezone name (e.g., 'America/Los_Angeles')
            - offset: UTC offset in hours
        """
        try:
            '''
            location = self.get_current_location()
            timezone = location.get('timezone', 'UTC')
            tz = pytz.timezone(timezone)
            now = datetime.datetime.now(tz)
            offset = now.utcoffset(local_tz).total_seconds() / 3600  # Convert to hours
            return {
                'timezone': local_tz,
                'offset': offset
            }
            '''

            # Get the local timezone
            local_tz = tzlocal.get_localzone()
            return local_tz

        except Exception as e:
            raise Exception(f"Failed to get timezone information: {str(e)}")