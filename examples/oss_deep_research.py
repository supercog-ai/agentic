# Our version of the LangChain "Deep Research" agent, which is itself a version of
# the OpenAI "Deep Researcher".
# This code was adapted from: https://github.com/langchain-ai/open_deep_research. All
# credit to LangChain for the original.
#
# See 'oss_deep_research.prompts.yaml' for all the agent prompts.
#
# This agent is a prototype for a "deterministic orchestration" agent where the overall
# logic is in code (rather than determined by the LLM).
#
# We start by constructing all our agents.
# Then the main orchestration is in the `next_turn`. It calls to the agents in turn, 
# using `yield from` so that events generated by the agents and publisher to our caller.
# 
# For each report section we call 'process_section' which does content gathering and writing
# for each section.
#
### RUNNING ###
#
# You need a TAVILY_API_KEY, and the API key for whatever model you are using, like OPENAI_API_KEY.
# Set these in your environment or use `agentic set-secret` to set them.
#
#   python examples/oss_deep_research.py
#
# Or serve the FastAPI API:
#
#   agentic serve examples/oss_deep_research.py
#
# And then run the WebUI:
#
#   agentic webui
#
#
# Examples:
#
# "A report on the history of golden retrievers and their presence in popular culture"
#
# "A market comparison for e-foils, including popular manufacturers and models, plus customer reviews"



import asyncio
from typing import Generator
from pprint import pprint
from typing import Any, Generator, Dict, List
from pydantic import BaseModel, Field


from agentic.common import Agent, AgentRunner, cached_call, RunContext
from agentic.actor_agents import RayFacadeAgent
from agentic.events import Prompt, TurnEnd

from agentic.agentic_secrets import agentic_secrets
from agentic.models import GPT_4O_MINI, CLAUDE, GPT_4O
from agentic.events import Event, ChatOutput, WaitForInput, PromptStarted, TurnEnd
from agentic.tools.tavily_search_tool import TavilySearchTool

# These can take any Litellm model path [see https://supercog-ai.github.io/agentic/Models/]
# Or use aliases 'GPT_4O' or 'CLAUDE'
PLANNER_MODEL = GPT_4O
WRITER_MODEL = GPT_4O_MINI

class Section(BaseModel):
    name: str = Field(
        description="Name for this section of the report.",
    )
    description: str = Field(
        description="Brief overview of the main topics and concepts to be covered in this section.",
    )
    research: bool = Field(
        description="Whether to perform web research for this section of the report."
    )
    content: str = Field(
        description="The content of the section."
    )   

class Sections(BaseModel):
    sections: List[Section] = Field(
        description="Sections of the report.",
    )


class WorkflowAgent(RayFacadeAgent):
    sections: Sections|None = None
    topic: str = ""

    def __init__(self, name: str="OSS Deep Research", model: str=GPT_4O_MINI):
        super().__init__(
            name, 
            welcome="I am the OSS Deep Research agent. Please provide me with a topic to research.",
            model=model,
        )
        self.tavily_tool = TavilySearchTool(api_key=agentic_secrets.get_required_secret("TAVILY_API_KEY"))
        self.add_tool(self.tavily_tool)
        
        # Generates web queries to popular initial context from which to generate the report plan
        self.query_planner = Agent(
            name="Report Query Planner",
            instructions="{{REPORT_QUERY_PLANNER}}",
            model=PLANNER_MODEL,
            result_model=Queries
        )

        # Generates the report plan, takes initial query results as input
        self.section_planner = Agent(
            name="Section Planner",
            instructions="{{REPORT_SECTION_PLANNER}}",
            model=PLANNER_MODEL,
            result_model=Sections
        )
        
        # Generates web queries to gather content for each section
        self.section_query_planner = Agent(
            name="Section Query Planner",
            instructions="{{SECTION_QUERY_PLANNER}}",
            model=WRITER_MODEL,
            result_model=Queries
        )
        
        # Writes the section content
        self.section_writer = Agent(
            name="Section Writer",
            instructions="{{SECTION_WRITER}}",
            model=WRITER_MODEL
        )

        # Revises each section after the full report draft is written
        self.final_section_writer = Agent(
            name="Final Section Writer",
            instructions="{{FINAL_SECTION_WRITER}}",
            model=WRITER_MODEL
        )

        self.final_reference_writer = Agent(
            name="Final Reference Writer",
            instructions="{{FINAL_REFERENCE_WRITER}}",
            model=WRITER_MODEL
        )

    def next_turn(
        self,
        request: str|Prompt,
        request_context: dict = {},
        request_id: str = None,
        continue_result: dict = {},
        debug = "",
    ) -> Generator[Event, Any, Any]:
        """Main workflow orchestration"""

        if request:
            self.topic = request.payload if isinstance(request, Prompt) else request

        # Yield the initial prompt
        yield PromptStarted(self.name, {"content": self.topic})

        feedback = continue_result.get("feedback", "")
        if feedback != "true" or self.sections is None:
            # Initial research queries
            queries = yield from self.query_planner.final_result(
                "Generate search queries that will help with planning the sections of the report.",
                request_context={
                    "topic": self.topic, 
                    "num_queries": 2
                }
            )
            msg = f"Initial research queries:\n" + "\n".join([q.search_query for q in queries.queries]) + "\n\n"
            yield ChatOutput(self.query_planner.name, {"content": msg})

            # Get initial web content
            content = self.query_web_content(queries)

            # Plan the report sections
            self.sections = yield from self.section_planner.final_result(
                """Generate the sections of the report. Your response must include a 'sections' field containing a list of sections.
                Each section must have: name, description, plan, research, and content fields.""",
                request_context={
                    "web_context": content, 
                    "topic": self.topic,
                    "feedback": feedback,
                }
            )

            msg = f"""
            Please provide feedback on the following report plan. \n\n{preview_report(self.sections.sections)}\n
            Does the report plan meet your needs? Pass 'true' to approve the report plan or provide feedback to regenerate the report plan:
            """

            yield WaitForInput(
                self.name, 
                {"feedback": msg}
            )
            return

        # FOR TESTING ONLY: limit report to 1 section
        #self.sections.sections = self.sections.sections[:1]

        # Do web research and writing for each section in turn
        for idx, section in enumerate(self.sections.sections):
            yield from self.process_section(section, idx)

        # Format complete report
        draft_report = format_sections(self.sections.sections)
        yield ChatOutput(self.name, {"content": f"REPORT DRAFT:\n{draft_report}\n\nWriting final report...\n"})

        # Rewrite the report sections with hindsight of the entire content of the report
        finals = []
        for section in self.sections.sections:
            report_section = yield from self.final_section_writer.final_result(
                "Generate a report section based on the provided sources.",
                {
                    "section_title": section.name,
                    "section_topic": section.description, 
                    "report_context": draft_report,
                    "section_content": section.content
                },
            )
            finals.append(report_section)
        
        sources = yield from self.final_reference_writer.final_result(
            "Generate a list of important sources referenced from the full report content.",
            {
                "report_context": draft_report
            }
        )

        report = "\n".join(finals) + "\n\n" + sources
        yield ChatOutput(
            self.name, 
            {
                "content": "## Here is your completed report:\n\n" + report + "\n\n"
            }
        )

        yield TurnEnd(
            self.name,
            [{"role": "assistant", "content": report}],
            run_context=None,
        )

    def process_section(self, section: "Section", index: int, report_context: str = None) -> Generator:
        """Handle the complete processing of a single section"""
        # Generates web queries to gather content for each section
        queries = yield from self.section_query_planner.final_result(
            "Generate search queries on the provided topic.",
            request_context={
                "section_topic": section.description, 
                "num_queries": 2
            },
        )
        msg = f"Research queries for section {index+1} - {section.name}:\n" + "\n".join([q.search_query for q in queries.queries]) + "\n\n"
        yield ChatOutput(self.section_query_planner.name, {"content": msg})

        # Get web content
        web_context = self.query_web_content(queries)

        yield ChatOutput(self.section_query_planner.name, {"content": f"Writing section {index+1}...\n\n"})

        # Write the section
        section.content = yield from self.section_writer.final_result(
            "Generate a report section based on the provided sources.",
            request_context={
                "section_title": section.name,
                "section_topic": section.description,
                "section_content": section.content,
                "web_context": web_context
            }
        )

    def query_web_content(self, queries: "Queries") -> str:
        async def _query_web_content(queries: Queries) -> str:
            all_results = []
            for query in queries.queries:
                res = await self.tavily_tool.perform_web_search(query.search_query, include_content=True)
                content = self.tavily_tool._deduplicate_and_format_sources(res, 10000)
                all_results.append(content)
            return "\n".join(all_results)
        return asyncio.run(_query_web_content(queries))


class SearchQuery(BaseModel):
    search_query: str = Field(None, description="Query for web search.")

class Queries(BaseModel):
    queries: List[SearchQuery] = Field(
        description="List of search queries.",
    )

def preview_report(sections: list[Section]) -> str:
    formatted_str = ""
    for idx, section in enumerate(sections, 1):
        formatted_str += f"""
{'='*30}
Section {idx}: {section.name}
{'='*30}
Description:
{section.description}
Requires Research: {section.research}
"""
    return formatted_str

def format_sections(sections: list[Section]) -> str:
    """ Format a list of sections into a string """
    formatted_str = ""
    for idx, section in enumerate(sections, 1):
        formatted_str += f"""
{'='*60}
Section {idx}: {section.name}
{'='*60}
Description:
{section.description}
Requires Research: 
{section.research}

Content:
{section.content if section.content else '[Not yet written]'}

"""
    return formatted_str


deep_researcher = WorkflowAgent(name="OSS Deep Research", model=GPT_4O_MINI)

if __name__ == "__main__":
    AgentRunner(deep_researcher).repl_loop()
