# AirbnbCalendarTool

The `AirbnbCalendarTool` enables agents to access and analyze Airbnb calendar data from iCal feeds. This tool helps property hosts manage bookings, check availability, calculate occupancy rates, and identify blocked dates.

## Features

- View upcoming bookings and events
- Check availability for specific date ranges
- Generate booking statistics and occupancy rates
- List blocked/unavailable dates

## Authentication

Requires an Airbnb calendar URL (iCal format) which can be stored in Agentic's secrets system as `AIRBNB_CALENDAR_URL`. This URL can be found in your Airbnb host dashboard under Calendar > Availability > Connect to another website.

## Methods

### list_events

```python
async def list_events(thread_context: ThreadContext, start_date: Optional[str] = None, end_date: Optional[str] = None) -> str
```

List all events/bookings in the calendar within the specified date range.

**Parameters:**

- `thread_context (ThreadContext)`: The execution context
- `start_date (Optional[str])`: Start date in ISO format (YYYY-MM-DD)
- `end_date (Optional[str])`: End date in ISO format (YYYY-MM-DD)

**Returns:**
A JSON string containing the events in the calendar.

### check_availability

```python
async def check_availability(thread_context: ThreadContext, start_date: Optional[str] = None, end_date: Optional[str] = None) -> str
```

Check if the property is available for a specific date range.

**Parameters:**

- `thread_context (ThreadContext)`: The execution context
- `start_date (Optional[str])`: Start date in ISO format (YYYY-MM-DD)
- `end_date (Optional[str])`: End date in ISO format (YYYY-MM-DD)

**Returns:**
A JSON string indicating availability and any conflicts.

### get_booking_stats

```python
async def get_booking_stats(thread_context: ThreadContext, start_date: Optional[str] = None, end_date: Optional[str] = None) -> str
```

Get booking statistics for a specified date range.

**Parameters:**

- `thread_context (ThreadContext)`: The execution context
- `start_date (Optional[str])`: Start date in ISO format (YYYY-MM-DD)
- `end_date (Optional[str])`: End date in ISO format (YYYY-MM-DD)

**Returns:**
A JSON string containing booking statistics including total days, booked days, booking count, and occupancy rate.

### get_blocked_dates

```python
async def get_blocked_dates(thread_context: ThreadContext, start_date: Optional[str] = None, end_date: Optional[str] = None) -> str
```

Get a list of blocked/unavailable dates.

**Parameters:**

- `thread_context (ThreadContext)`: The execution context
- `start_date (Optional[str])`: Start date in ISO format (YYYY-MM-DD)
- `end_date (Optional[str])`: End date in ISO format (YYYY-MM-DD)

**Returns:**
A JSON string containing a sorted list of blocked dates.

## Example Usage

```python
from agentic.common import Agent
from agentic.tools import AirbnbCalendarTool

# Create an agent with Airbnb calendar capabilities
airbnb_agent = Agent(
    name="Airbnb Calendar Assistant",
    instructions="You help manage Airbnb property calendars and bookings.",
    tools=[AirbnbCalendarTool()]
)

# Use the agent
response = airbnb_agent << "Check if my property is available from June 15, 2025 to June 20, 2025"
print(response)
```
