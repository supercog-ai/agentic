from typing import Callable, Dict, Optional
import datetime

import tzlocal
import requests

from agentic.tools.base import BaseAgenticTool
from agentic.tools.utils.registry import tool_registry

@tool_registry.register(
    name="GeolocationTool",
    description="Tool to get the current geographical location of the user",
    config_requirements=[],
)
class GeolocationTool(BaseAgenticTool):
    """
    A tool that retrieves the current geographical location of the user
    based on their public IP address.  NOTE: the tool only has access to 
    geolocation information for the machine it is running on, so this tool
    is useful when part of the client application (CLI) and less so when
    part of a cloud server solution.
    """
    
    def __init__(self):
        """
        Initialize the Geolocation tool.
        """
        pass

    def get_tools(self) -> list[Callable]:
        return [
            self.get_time,
            self.get_timezone,
            self.get_ip,
            self.get_location,
        ]


    async def get_time(self) -> str:
        """ Returns the current time of the client. """ 
        try:
            current_time = datetime.datetime.now()    
            return current_time.isoformat()

        except Exception as e:
            raise Exception(f"Failed to get current time: {str(e)}")

    async def get_timezone(self) -> str:
        """
        Get the current timezone information based on the user's location.
        
        Returns:
            Timezone string in "Region/City" IANA tz database format.
            https://en.wikipedia.org/wiki/List_of_tz_database_time_zones
        """
        try:
            # Get the local timezone
            local_tz = tzlocal.get_localzone()
            return local_tz

        except Exception as e:
            raise Exception(f"Failed to get timezone information: {str(e)}")
    
    async def get_ip(self) -> str:
        """
        Get the current public IP address of the client.
        
        Returns:
            Public IP address as a string.

        Use: if agent is being run locally then the ip adress will match the users location, otherwise the user can provide an ip to get location data.
        """
        try:
            # Step 1: Get the public IP address
            # We use ipify.org, a simple and reliable service for this.
            ip_response = requests.get('https://api.ipify.org?format=json')
            ip_response.raise_for_status()  # Raise an exception for bad status codes
            ip_data = ip_response.json()
            public_ip = ip_data['ip'] 

            return f"""
            IP: {public_ip}
            """

        except Exception as e:
            error_msg = f"An error occurred while getting ip: {str(e)}"
            print(error_msg)
            return error_msg

    async def get_location(self, ip: Optional[str] = None) -> str:
        """
        Get the current geographical location based on the user's public IP address.
        
        Args:
            ip: Optional IP address. If not provided, gets the current machine's IP.
            
        Returns:
            Geolocation data as a string in the following format:
                City: {city}
                Region: {region}
                Country: {country}
                Coordinates (Lat, Lon): {loc}
                Timezone: {timezone}
                IP: {ip}
                ISP: {org}
        """
        try:
            # If no IP provided, get the current machine's IP
            if ip is None:
                ip = await self.get_ip()
                # Extract just the IP address from the formatted string
                if ip.strip().startswith('IP:'):
                    ip = ip.strip().split(':', 1)[1].strip()
                if ip.startswith('An error occurred'):
                    return ip  # Return the error message
            
            # Get the location based on the IP address
            # We use ipinfo.io, which provides a free geolocation API.
            location_response = requests.get(f'https://ipinfo.io/{ip}/json')
            location_response.raise_for_status()
            location_data = location_response.json()

            # Print the location data in a readable format
            city = location_data.get('city', 'N/A')
            region = location_data.get('region', 'N/A')
            country = location_data.get('country', 'N/A')
            loc = location_data.get('loc', 'N/A') # Latitude,Longitude
            service_provider = location_data.get('org', 'N/A') # ISP (Internet Service Provider)
            timezone = location_data.get('timezone', 'N/A')

            return f"""
            City: {city}
            Region: {region}
            Country: {country}
            Coordinates (Lat, Lon): {loc}
            Timezone: {timezone}
            IP: {ip}
            Service Provider: {service_provider}
            """

        except Exception as e:
            error_msg = f"An error occurred while getting location: {str(e)}"
            print(error_msg)
            return error_msg
