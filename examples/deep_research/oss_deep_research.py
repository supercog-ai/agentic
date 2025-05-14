import asyncio
import os
from typing import Any, Generator, List, Optional
from pydantic import BaseModel, Field
from datetime import datetime

from agentic.agentic_secrets import agentic_secrets
from agentic.common import Agent, AgentRunner, RunContext
from agentic.events import Event, ChatOutput, WaitForInput, Prompt, PromptStarted, TurnEnd, ResumeWithInput
from agentic.models import GPT_4O_MINI, CLAUDE, GPT_4O
from agentic.tools import PlaywrightTool, TavilySearchTool

# These can take any Litellm model path [see https://supercog-ai.github.io/agentic/Models/]
# Or use aliases 'GPT_4O' or 'CLAUDE'
PLANNER_MODEL = GPT_4O
WRITER_MODEL = CLAUDE

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

class DeepResearchAgent(Agent):
    sections: Sections|None = None
    topic: str = ""

    def __init__(self,
        name: str="OSS Deep Research",
        welcome="I am the OSS Deep Research agent. Please provide me with a topic to research.",
        model: str=GPT_4O_MINI, 
        playwright_fallback: bool = False,
        verbose: bool = False,
        **kwargs
    ):
        super().__init__(
            name, 
            welcome=welcome,
            model=model,
            **kwargs
        )
        self.tavily_tool = TavilySearchTool(api_key=agentic_secrets.get_required_secret("TAVILY_API_KEY"))

        ## CONFIGURATION
        self.num_queries = 4
        self.playwright_fallback: bool = playwright_fallback
        self.sections_limit: Optional[int] = None  # For testing, limit the number of sections generated
        self.verbose = verbose
        
        if self.playwright_fallback:
            self.playwright_tool = PlaywrightTool()

        # Generates web queries to popular initial context from which to generate the report plan
        self.query_planner = Agent(
            name="Report Query Planner",
            instructions="{{REPORT_QUERY_PLANNER}}",
            model=PLANNER_MODEL,
            result_model=Queries,
            # Some research is sensitive to the date, and without telling the LLM the date it
            # may assume its training cut-off date.
            memories=[f"The current date is {datetime.now().strftime('%Y-%m-%d')}"]
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
            model=PLANNER_MODEL,
            result_model=Queries,
            memories=[f"The current date is {datetime.now().strftime('%Y-%m-%d')}"]
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

        # Generates the source reference list for the final report
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

        if not continue_result:
        # Starting a new turn with a Prompt
            self.topic = request.payload if isinstance(request, Prompt) else request
            prompt_event = PromptStarted(
                self.name,
                {"content": self.topic}
            )
            yield prompt_event
        else:
            # Resuming a previous turn with ResumeWithInput
            resume_event = ResumeWithInput(
                self.name,
                continue_result,
                request_id=request_id
            )
            yield resume_event

        if not continue_result:
            self.reset_history() # by default chat history is retained

        feedback = continue_result.get("feedback", "")
        if feedback != "true" or self.sections is None:
            # Initial research queries
            queries = yield from self.query_planner.final_result(
                "Generate search queries that will help with planning the sections of the report.",
                request_context={
                    "topic": self.topic, 
                    "num_queries": self.num_queries,
                    "run_id": request_context.get("run_id")
                }
            )

            if self.verbose:
                msg = f"Initial research queries:\n" + "\n".join([q.search_query for q in queries.queries]) + "\n\n"
                yield ChatOutput(self.query_planner.name, {"content": msg})

            # Get initial web content
            content = self.query_web_content(queries, run_context=RunContext(self.name))

            # Plan the report sections
            self.sections = yield from self.section_planner.final_result(
                """Generate the sections of the report. Your response must include a 'sections' field containing a list of sections.
                Each section must have: name, description, plan, research, and content fields.""",
                request_context={
                    "web_context": content, 
                    "topic": self.topic,
                    "feedback": feedback,
                    "run_id": request_context.get("run_id")
                }
            )

            msg = f"""
Please provide feedback on the following report plan. If the report meets your needs respond with 'true'.
Otherwise provide feedback to regenerate the report plan.\n
---
\n{preview_report(self.sections.sections)}\n
---
\nDoes the report plan meet your needs? Respond with 'true' to approve the report plan or
provide feedback to regenerate the report plan:\n
"""

            yield WaitForInput(
               self.name, 
               {"feedback": msg}
            )
            return

        if self.sections_limit:
            self.sections.sections = self.sections.sections[:self.sections_limit]

        # Do web research and writing for each section in turn
        for idx, section in enumerate(self.sections.sections):
            yield from self.process_section(section, idx)

        # Format complete report
        draft_report = format_sections(self.sections.sections)
        if self.verbose:
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
                    "section_content": section.content,
                    "run_id": request_context.get("run_id")
                },
            )
            finals.append(report_section)
        
        sources = yield from self.final_reference_writer.final_result(
            "Generate a list of important sources referenced from the full report content.",
            {
                "report_context": draft_report,
                "run_id": request_context.get("run_id")
            }
        )

        report = "\n".join(finals) + "\n\n" + sources
        content = "\n## Here is your completed report:\n\n" + report + "\n\n" if self.verbose else report
        yield ChatOutput(
            self.name, 
            {
                "content": content
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
                "num_queries": self.num_queries,
                "run_id": report_context.run_id if isinstance(report_context, RunContext) else None
            },
        )
        msg = f"Research queries for section {index+1} - {section.name}:\n" + "\n".join([q.search_query for q in queries.queries]) + "\n\n"
        yield ChatOutput(self.section_query_planner.name, {"content": msg})

        # Get web content
        web_context = self.query_web_content(queries, run_context=RunContext(self.name))

        yield ChatOutput(self.section_query_planner.name, {"content": f"Writing section {index+1}...\n\n"})

        # Write the section
        section.content = yield from self.section_writer.final_result(
            "Generate a report section based on the provided sources.",
            request_context={
                "section_title": section.name,
                "section_topic": section.description,
                "section_content": section.content,
                "web_context": web_context,
                "run_id": report_context.run_id if isinstance(report_context, RunContext) else None
            }
        )

    def query_web_content(self, queries: "Queries", run_context) -> str:
        content_max = 20000

        async def _query_web_content(queries: Queries, missing_results: list[str]) -> str:
            all_results = []
            for query in queries.queries:
                missing_pages = []
                try:
                    res = await self.tavily_tool.perform_web_search(
                        query.search_query, 
                        include_content=True
                    )
                except:
                    res = []
                content = self.tavily_tool._deduplicate_and_format_sources(
                    res, 
                    content_max, 
                    missing_pages_list=missing_pages
                )
                all_results.append(content)
                missing_results.extend(missing_pages)
            return "\n".join(all_results)
        
        missing_pages = []
        content = asyncio.run(_query_web_content(queries, missing_pages))

        # Use playwright browser for missing pages
        if (
            self.playwright_fallback and 
            len(missing_pages) > 0 and 
            len(content) < content_max
        ):
            max_playwright_pages = 3
            content_tuples = self.playwright_tool.download_pages(run_context, missing_pages[:max_playwright_pages])
            for _, title, page_content in content_tuples:
                if page_content:
                    content += f"\n\n===\n{title}\n===\n{page_content}\n\n"
                    if len(content) >= content_max:
                        break
        return content

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
### Section {idx}: {section.name}
**Description**: {section.description}
{' *Requires Research*' if section.research else ''}
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


deep_researcher = DeepResearchAgent(name="OSS Deep Research")

if __name__ == "__main__":
    AgentRunner(deep_researcher).repl_loop()
