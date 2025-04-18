from typing import List, Callable, Optional, Dict
import requests
import json
from datetime import datetime, date, timedelta, time
import icalendar
from agentic.common import RunContext
from agentic.tools.utils.registry import tool_registry, Dependency
from agentic.tools.base import BaseAgenticTool

@tool_registry.register(
    name="AirbnbCalendarTool",
    description="Get information from Airbnb calendar iCal feeds",
    dependencies=[
        Dependency(
            name="icalendar",
            version="6.1.3",
            type="pip",
        ),
    ])

class AirbnbCalendarTool(BaseAgenticTool):
    """Tool for accessing and analyzing Airbnb calendar data from iCal feeds."""
    
    def __init__(self):
        """Initialize the Airbnb calendar tool."""
        super().__init__()
    
    def required_secrets(self) -> dict[str, str]:
        return {
            "AIRBNB_CALENDAR_URL": "Your Airbnb calendar URL (iCal format). Find this by going to Calendar > Availability > Connect to another website"
        }
    
    def get_tools(self) -> List[Callable]:
        """Return the list of available calendar tools."""
        return [
            self.list_events,
            self.check_availability,
            self.get_booking_stats,
            self.get_blocked_dates
        ]
    
    def _fetch_calendar(self, calendar_url: str) -> str:
        """
        Fetch calendar data from URL.
        
        Args:
            calendar_url: The iCal/ICS feed URL
            
        Returns:
            str: The calendar data in iCal format
            
        Raises:
            ValueError: If URL is invalid
            IOError: If network error occurs
        """
        # Validate URL first
        self._validate_calendar_url(calendar_url)

        # Fetch from URL
        try:
            # Convert webcal:// to https:// if needed
            if calendar_url.startswith('webcal://'):
                calendar_url = 'https://' + calendar_url[9:]
                
            response = requests.get(calendar_url)
            if response.status_code != 200:
                raise IOError(f"Failed to fetch calendar: HTTP {response.status_code}")
            
            return response.text
            
        except Exception as e:
            raise IOError(f"Error fetching calendar data: {str(e)}")
    
    def _validate_calendar_url(self, url: str) -> bool:
        """
        Validate Airbnb-specific calendar URL format.
        
        Args:
            url: Calendar URL to validate
            
        Returns:
            bool: True if valid
            
        Raises:
            ValueError: If URL is invalid
        """
        if not url:
            raise ValueError("Calendar URL is required")
            
        # Check if it's a URL (very basic check)
        if not (url.startswith('http://') or url.startswith('https://') or url.startswith('webcal://')):
            raise ValueError("Calendar URL must start with http://, https://, or webcal://")
            
        # Check if it ends with .ics
        #if not url.endswith('.ics'):
            #raise ValueError("Calendar URL must end with .ics")
            
        return True
    
    def _parse_calendar(self, calendar_data: str) -> List[Dict]:
        """
        Parse iCal data into a list of events.

        Args:
            calendar_data: Raw iCal data

        Returns:
            List[Dict]: List of parsed calendar events
        """
        try:
            calendar = icalendar.Calendar.from_ical(calendar_data)
            events = []
            event_count = 0
            for component in calendar.walk('VEVENT'):
                event_count += 1
                # Extract start and end dates
                start_component = component.get('dtstart')
                start_dt = start_component.dt if start_component else None
                end_component = component.get('dtend')
                end_dt = end_component.dt if end_component else None
                # Create event object
                event = {
                    'summary': str(component.get('summary', 'Unavailable')),
                    'description': str(component.get('description', '')),
                    'status': str(component.get('status', 'CONFIRMED')),
                    'uid': str(component.get('uid', ''))
                }
                # Detect event type based on summary/description
                summary_lower = event['summary'].lower()
                keywords = ["not available", "blocked", "unavailable", "closed"]
                matches = [keyword for keyword in keywords if keyword in summary_lower]
                if matches:
                    event['event_type'] = "block"

                else:
                    event['event_type'] = "reservation"
                # Standardize dates to ISO format strings
                if isinstance(start_dt, datetime):
                    event['start'] = start_dt.isoformat()
                elif isinstance(start_dt, date):
                    event['start'] = datetime.combine(start_dt, time.min).isoformat()
                else:
                    event['start'] = str(start_dt)
                if isinstance(end_dt, datetime):
                    event['end'] = end_dt.isoformat()
                elif isinstance(end_dt, date):
                    event['end'] = datetime.combine(end_dt, time.min).isoformat()
                else:
                    event['end'] = str(end_dt)
                events.append(event)

            # Sort events by start date
            try:
                events.sort(key=lambda x: x['start'])
            except Exception as sort_error:
                # Provide fallback sorting that's more robust
                events.sort(key=lambda x: str(x['start']))
            return events
        except Exception as e:
            error_msg = f"Error parsing calendar data: {str(e)}"
            import traceback
            raise ValueError(error_msg)
    
    async def list_events(
        self, 
        run_context: RunContext,
        start_date: Optional[str] = None, 
        end_date: Optional[str] = None
    ) -> str:
        """
        List all events/bookings in the calendar within the specified date range.
        
        Args:
            run_context: The execution context
            start_date: Start date in ISO format (YYYY-MM-DD)
            end_date: End date in ISO format (YYYY-MM-DD)
            
        Returns:
            str: JSON string containing the events
        """
        try:
            calendar_url = run_context.get_secret("AIRBNB_CALENDAR_URL")
            if not calendar_url:
                return json.dumps({
                    "status": "error",
                    "message": "No calendar URL configured. Please set AIRBNB_CALENDAR_URL in secrets."
                })
                
            calendar_data = self._fetch_calendar(calendar_url)
            events = self._parse_calendar(calendar_data)
            
            if start_date or end_date:
                # Parse start_date and end_date
                start = datetime.fromisoformat(start_date) if start_date else None
                end = datetime.fromisoformat(end_date) if end_date else None
                
                filtered_events = []
                for event in events:
                    event_start = datetime.fromisoformat(event['start'])
                    event_end = datetime.fromisoformat(event['end'])
                    
                    # Apply date range filters
                    if start and event_end < start:
                        continue
                    if end and event_start > end:
                        continue
                    
                    filtered_events.append(event)
                    
                events = filtered_events
            
            return json.dumps({
                "status": "success",
                "events": events
            }, indent=2)
            
        except Exception as e:
            return json.dumps({
                "status": "error",
                "message": str(e)
            })
    
    async def check_availability(
        self, 
        run_context: RunContext,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> str:
        """
        Check if the property is available for a specific date range.
        
        Args:
            run_context: The execution context
            start_date: Start date in ISO format (YYYY-MM-DD)
            end_date: End date in ISO format (YYYY-MM-DD)
            
        Returns:
            str: JSON string indicating availability and any conflicts
        """
        try:
            calendar_url = run_context.get_secret("AIRBNB_CALENDAR_URL")
            if not calendar_url:

                return json.dumps({
                    "status": "error",
                    "message": "No calendar URL configured. Please set AIRBNB_CALENDAR_URL in secrets."
                })
            calendar_data = self._fetch_calendar(calendar_url)
            events = self._parse_calendar(calendar_data)
            try:
                check_start = datetime.fromisoformat(start_date)
                check_end = datetime.fromisoformat(end_date)
            except ValueError as date_error:
                raise
            conflicts = []
            for i, event in enumerate(events):
                event_start = datetime.fromisoformat(event['start'])
                event_end = datetime.fromisoformat(event['end'])
                if (event_start < check_end and event_end > check_start):
                    conflicts.append(event)
            result = {
                "status": "success",
                "available": len(conflicts) == 0,
                "conflicts": conflicts if conflicts else None
            }
            return json.dumps(result, indent=2)
            
        except Exception as e:
            return json.dumps({
                "status": "error",
                "message": str(e)
            })
    
    async def get_booking_stats(
        self, 
        run_context: RunContext,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> str:
        """
        Get booking statistics for a specified date range.
        
        Args:
            run_context: The execution context
            start_date: Start date in ISO format (YYYY-MM-DD)
            end_date: End date in ISO format (YYYY-MM-DD)
            
        Returns:
            str: JSON string containing booking statistics
        """

        try:
            calendar_url = run_context.get_secret("AIRBNB_CALENDAR_URL")
            if not calendar_url:

                return json.dumps({
                    "status": "error",
                    "message": "No calendar URL configured. Please set AIRBNB_CALENDAR_URL in secrets."
                })
                
            calendar_data = self._fetch_calendar(calendar_url)
            events = self._parse_calendar(calendar_data)
            
            # Filter by date range if specified
            reservation_events = []
            for event in events:
                if event['event_type'] == 'reservation':
                    if start_date or end_date:
                        event_start = datetime.fromisoformat(event['start'])
                        event_end = datetime.fromisoformat(event['end'])
                        start = datetime.fromisoformat(start_date) if start_date else None
                        end = datetime.fromisoformat(end_date) if end_date else None
                        
                        if start and event_end < start:
                            continue
                        if end and event_start > end:
                            continue
                            
                    reservation_events.append(event)
            
            # Calculate statistics
            total_days = 0
            booked_days = 0
            booking_count = len(reservation_events)
            
            for event in reservation_events:
                event_start = datetime.fromisoformat(event['start'])
                event_end = datetime.fromisoformat(event['end'])
                duration = (event_end - event_start).days
                booked_days += duration
            
            if start_date and end_date:
                total_days = (datetime.fromisoformat(end_date) - datetime.fromisoformat(start_date)).days
            else:
                # Use the span of events
                if events:
                    first_event = min(datetime.fromisoformat(e['start']) for e in events)
                    last_event = max(datetime.fromisoformat(e['end']) for e in events)
                    total_days = (last_event - first_event).days
            
            occupancy_rate = (booked_days / total_days * 100) if total_days > 0 else 0


            return json.dumps({
                "status": "success",
                "statistics": {
                    "total_days": total_days,
                    "booked_days": booked_days,
                    "booking_count": booking_count,
                    "occupancy_rate": round(occupancy_rate, 2)
                }
            }, indent=2)
            
        except Exception as e:

            return json.dumps({
                "status": "error",
                "message": str(e)
            })
    
    async def get_blocked_dates(
        self, 
        run_context: RunContext,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> str:
        """
        Get a list of blocked/unavailable dates.
        
        Args:
            run_context: The execution context
            start_date: Start date in ISO format (YYYY-MM-DD)
            end_date: End date in ISO format (YYYY-MM-DD)
            
        Returns:
            str: JSON string containing list of blocked dates
        """
        try:
            calendar_url = run_context.get_secret("AIRBNB_CALENDAR_URL")
            if not calendar_url:
                return json.dumps({
                    "status": "error",
                    "message": "No calendar URL configured. Please set AIRBNB_CALENDAR_URL in secrets."
                })
                
            calendar_data = self._fetch_calendar(calendar_url)
            events = self._parse_calendar(calendar_data)
            
            blocked_dates = []
            for event in events:
                event_start = datetime.fromisoformat(event['start'])
                event_end = datetime.fromisoformat(event['end'])
                
                if start_date:
                    start = datetime.fromisoformat(start_date)
                    if event_end < start:
                        continue
                if end_date:
                    end = datetime.fromisoformat(end_date)
                    if event_start > end:
                        continue
                
                # Add each date in the range to the list
                current = event_start
                while current < event_end:
                    blocked_dates.append(current.date().isoformat())
                    current += timedelta(days=1)
            
            return json.dumps({
                "status": "success",
                "blocked_dates": sorted(list(set(blocked_dates)))  # Remove duplicates
            }, indent=2)
            
        except Exception as e:
            return json.dumps({
                "status": "error",
                "message": str(e)
            })
