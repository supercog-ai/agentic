import os
import re
import json
import requests
from typing import Dict, List, Any, Generator, Optional, Tuple
from pydantic import Field, BaseModel
from dotenv import load_dotenv
from agentic.common import Agent, AgentRunner, ThreadContext
from agentic.events import Event, ChatOutput, TurnEnd, PromptStarted, Prompt
from agentic.models import GPT_4O_MINI

from code_rag_agent import CodeRagAgent
from summary_agent import SummaryAgent
from code_rag_agent import CodeSection, CodeSections
from pydantic import BaseModel

load_dotenv()

class SearchResult(BaseModel):
    query: str = Field(
        description="Query used in this search."
    )
    file_path: str = Field(
        description="Path of the file this code/documentation belongs to."
    )
    content: str = Field(
        description="Content returned from search."
    )
    similarity_score: float = Field(
        desciption="Similarity score returned from vector search."
    )
    is_relevant: bool = Field(
        default = True,
        description="Boolean describing if the search result is relevant to the query."
    )
    relevance_reason: str = Field(
        default = "",
        description="Boolean describing if the search result is relevant to the query."
    )
    included_defs: List[str] = Field(
        default_factory=list,
        desciption="Similarity score returned from vector search."
    )

class Searches(BaseModel):
    searches: List[str] = Field(
        description="Search queries."
    )

class RelevanceResult(BaseModel):
    relevant: bool 
    reason: str

class PRReviewAgent(Agent):

    def __init__(
        self,
        name: str = "PR Review Agent",
        model: str = GPT_4O_MINI,
        verbose: bool = False,
        **kwargs
    ):
        super().__init__(
            name=name,
            welcome="PR Review Agent initialized. Ready to process PRs.",
            model=model,
            **kwargs
        )
        self.code_rag_agent = CodeRagAgent()
        self.verbose = verbose

        self.queryAgent = Agent(
            name="Code Query Agent",
            instructions=
"""
You are an expert in generating NON-NATURAL LANGUAGE CODE search queries from a patch file to get additional context about changes to a code base. Your response must include a 'searches' field with a list of strings. Example outputs: Weather_Tool, SearchQuery, format_sections
""",
            model=GPT_4O_MINI,
            result_model=Searches,
        )

        self.relevanceAgent = Agent(
            name="Code Relevange Agent",
            instructions="""You are an expert in determining if a snippet of code or documentation is needed to determine the purpose of a code change from the patch file. Your response must include a 'relevant' field boolean and a 'reason' field with a brief explanation.""",
            model=GPT_4O_MINI,
            result_model=RelevanceResult,
        )

        self.summaryAgent = SummaryAgent()

    def prepare_summary(self, patch_content: str, filtered_results: List[SearchResult]) -> str:
        """Prepare for summary agent"""
        formatted_str = ""
        formatted_str += f"<Patch file>\n"
        formatted_str += f"{patch_content}\n"
        formatted_str += f"</Patch File>\n\n"
        
        for result in filtered_results:
            formatted_str += f"<{result.file_path}>\n"
            formatted_str += f"{result.content}\n"
            formatted_str += f"</{result.file_path}>\n\n"

        return formatted_str

    def post_to_github(self, summary: str) -> str:
        """Post summary as a GitHub comment"""
        repo_owner = os.getenv("REPO_OWNER")
        repo_name = os.getenv("REPO_NAME")
        pr_id = os.getenv("PR_ID")
        gh_token = os.getenv("GITHUB_API_KEY")
        
        if not all([repo_owner, repo_name, pr_id, gh_token]):
            raise ValueError("Missing required GitHub configuration")
            
        url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/issues/{pr_id}/comments"
        headers = {
            "Authorization": f"token {gh_token}",
        }
        data = {"body": summary}
        
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()
        return response.json().get("html_url")

    def next_turn(
        self,
        request: str,
        request_context: dict = None,
        request_id: str = None,
        continue_result: dict = {},
        debug = "",
    ) -> Generator[Event, Any, None]:
        
        query = request.payload if isinstance(request, Prompt) else request
        yield PromptStarted(query, {"query": query})
        
        # Generate search queries
        queries = yield from self.queryAgent.final_result(
            request_context.get("patch_content"),
            request_context={
                "thread_id": request_context.get("thread_id")
            }
        )

        print("quer"+str(queries))

        all_results = []
    
        for query in queries.searches[:10]:
            searchResponse = yield from self.code_rag_agent.final_result(
                f"Search codebase",
                request_context={
                    "query": query,
                    "thread_id": request_context.get("thread_id")
                }
            )
            
            # Process each result
            for result in searchResponse.sections.values():
                all_results.append(SearchResult(query=query,file_path=result.file_path,content=result.search_result,similarity_score=result.similarity_score,included_defs=result.included_defs))

        print("fil"+str(all_results))

        # Filter search results using LLM-based relevance checking
        filtered_results = []
        
        for result in all_results: 
            if result.similarity_score < 0.5:
                continue
                
            relevance_check = yield from self.relevanceAgent.final_result(
                f"<Patch File>\n{request_context.get("patch_content")}\n</Patch File>\n\n<Content>{result.content}</Content><Query>{result.query}</Query>"
            )

            print(relevance_check)
            
            result.is_relevant = relevance_check.relevant
            result.relevance_reason = relevance_check.reason
            
            if result.is_relevant:
                filtered_results.append(result)

        print(str(filtered_results))

        # Prepare for summary
        formatted_str = self.prepare_summary(request_context.get("patch_content"),filtered_results)

        summary = yield from self.summaryAgent.final_result(
            formatted_str
        )

        comment_url = self.post_to_github(summary)

        # Return the final result
        yield ChatOutput(
            self.name,
            [{"content": f"## PR Review Complete\n\nSummary posted to: {comment_url}"}]
        )
        
        yield TurnEnd(
            self.name,
            [{"content": summary}]
        )

# Create an instance of the agent
pr_review_agent = PRReviewAgent()

if __name__ == "__main__":
    with open("PRChanges.patch", "r") as f:
        patch_content = f.read()
    
    # Run the agent
    print(pr_review_agent.grab_final_result("Triggered by a PR",{"patch_content":patch_content}))