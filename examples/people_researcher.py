from typing import Callable, Any
import asyncio

from agentic.common import Agent, AgentRunner, handoff, PauseForInputResult
from agentic.tools import LinkedinDataTool

def invoke_async(async_func: Callable, *args, **kwargs) -> Any:
    return asyncio.run(async_func(*args, **kwargs))


linkedin = LinkedinDataTool()


def search_profiles(name: str, company: str = ""):
    """Searches for linkedin profiles."""
    return invoke_async(linkedin.linkedin_people_search, name=name, company=company)


def get_profile(url: str):
    return invoke_async(linkedin.get_linkedin_profile_info, url)


def get_company_linkedin_info(company: str):
    return invoke_async(linkedin.get_company_linkedin_info, company)


def get_human_input(request_message: str):
    return PauseForInputResult({"input": request_message})


person_report_writer = Agent(
    name="Person Report Writer",
    instructions="""
You will receive the URL to a linkedin profile. Retreive and review the profile.
Now call the Company Reporter to research the company the person works for.
Finally, write an extensive background report on the person, focusing on their career progression
and last 3 roles.
""",
    max_tokens=10000,
    model="openai/gpt-4o",
    tools=[
        get_profile,
        Agent(
            name="Company Reporter",
            instructions="""
Retrieve Linkedin information on the company, and perform web research. Then write a 
background report on the company.
""",
            max_tokens=10000,
            tools=[get_company_linkedin_info],
        ),
    ],
)

people_researcher = Agent(
    name="Person Researcher",
    welcome="I am the People Researcher. Tell me who you want to know about.",
    instructions="""
You do research on people. Given a name and a company:
1. Search for matching profiles on linkedin.
2. If you find multiple matches, please ask the user which one they are interested in.
3. Now call the Person Report Writer and pass in the linked profile URL. Print the report and the linkedin profile URL.
""",
    #model="lm_studio/qwen2.5-7b-instruct-1m",
    #model="lm_studio/deepseek-r1-distill-qwen-7B",
    tools=[search_profiles, get_human_input, handoff(person_report_writer)],
)

if __name__ == "__main__":
    AgentRunner(people_researcher).repl_loop()
