from agentic.common import Agent, AgentRunner, RunContext, PauseForInputResult
from agentic.tools import AirbnbCalendarTool
from typing import Optional
from typing import Any, Callable, Optional
import asyncio

def invoke_async(async_func: Callable, *args, **kwargs) -> Any:
    return asyncio.run(async_func(*args, **kwargs))

# Initialize the AirbnbCalendarTool
airbnb_tool = AirbnbCalendarTool()

# Create wrapper functions for each AirbnbCalendarTool method
def list_events(run_context: RunContext, start_date, end_date):
    """Lists all events/bookings in the Airbnb calendar within a specified date range."""
    return  invoke_async(airbnb_tool.list_events, run_context, start_date,  end_date)

def check_availability(run_context: RunContext,start_date: str, end_date: str):
    """Checks if the property is available for a specific date range."""
    return invoke_async(airbnb_tool.check_availability,run_context,start_date, end_date)

def get_booking_stats( run_context: RunContext,start_date: Optional[str] = None, end_date: Optional[str] = None):
    """Gets booking statistics for a specified date range."""
    print("<<<<<<<<<<<<< Starting booking stats >>>>>>>>>>>>")
    print(f"run context = {run_context}")
    return invoke_async(airbnb_tool.get_booking_stats,run_context, start_date, end_date)

def get_blocked_dates(run_context: RunContext,start_date: Optional[str] = None, end_date: Optional[str] = None):
    """Gets a list of blocked/unavailable dates."""
    return  invoke_async(airbnb_tool.get_blocked_dates,run_context, start_date, end_date)

def get_human_input(request_message: str, ):
    """Asks the user for input and pauses until input is received."""
    return PauseForInputResult({"input": request_message})

# Create the Airbnb calendar agent with wrapped functions as tools
airbnb_agent = Agent(
    name="Airbnb Calendar Assistant",
    welcome="👋 Hello! I'm your Airbnb Calendar Assistant. I can help you check availability, view upcoming bookings, and get statistics from your Airbnb calendar. What would you like to know?",
    instructions="""
You are a helpful assistant that helps users get information from their Airbnb calendar.
You have access to their Airbnb calendar data through several specialized tools.

Here are some things users might want to do:
- Check if specific dates are available
- List all upcoming bookings or blocks
- Get statistics about their booking rate
- Find all blocked dates within a time range

When the user asks for date-specific information, you should:
1. Parse their request to determine what they want to know
2. Identify any date ranges mentioned in their query
3. Use the appropriate tool function to retrieve the information
4. Format the response in a human-readable way

For date formatting, use ISO format YYYY-MM-DD when calling tools, but use a more human-friendly format in your responses.

If you need more information from the user to complete a request, use the get_human_input function.
""",
    model="gpt-4o-mini",
    tools=[list_events, check_availability, get_booking_stats, get_blocked_dates, get_human_input]
)

# To run the agent in a REPL
if __name__ == "__main__":
    # Set up the Airbnb calendar URL if not already set

    # Run the agent
    runner = AgentRunner(airbnb_agent)
    runner.repl_loop()
