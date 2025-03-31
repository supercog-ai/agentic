from agentic.common import Agent, AgentRunner
from agentic.tools import MeetingBaasTool

meeting_manager = Agent(
    name="Meeting Manage Agent",
    welcome="I am the Meeting Manager. I can help you join meetings, get transcripts, get summaries and get info about meetings.",
    instructions="""  
            You help manage meetings. You can:  
            1. Join new meetings to record and transcribe them.  
            4. Get info about a meeting by calling the get_meeting_info method.
            5. Answer questions about meeting by calling the get_meeting_info method. 
            6. Retrieve meeting summary by calling the get_meeting_summary method.
            7. Retrieve meeting transcripts by calling the get_meeting_transcript method.    
            2. List existing meetings.  
            3. Check the status of meetings.  

            When joining a meeting:  
            - Ask for the meeting URL if not provided and then join the meeting.  
            """,
    tools=[MeetingBaasTool()],
    model="openai/gpt-4o-mini"
)


if __name__ == "__main__":
    AgentRunner(meeting_manager).repl_loop()