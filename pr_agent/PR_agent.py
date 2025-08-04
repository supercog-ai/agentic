import os
import re
import json
import requests
from typing import Dict, List, Any, Generator, Optional, Tuple
from pydantic import Field
from dotenv import load_dotenv
from agentic.common import Agent, AgentRunner, ThreadContext
from agentic.events import Event, ChatOutput, TurnEnd
from agentic.models import GPT_4O_MINI, GPT_4O
from agentic.tools.a2a_tool import A2ATool

import rag_sub_agent
import summary_agent
from code_rag_agent import CodeSection, CodeSections
from pydantic import BaseModel

load_dotenv()

class SearchResult(BaseModel):
    query: str
    file_path: str
    content: str
    similarity_score: float
    is_relevant: bool = True
    relevance_reason: str = ""
    included_defs: List[str] = Field(default_factory=list)

class PRReviewContext(BaseModel):
    # Input
    patch_content: str = Field(..., description="The content of the patch file")
    
    # Generated Data
    search_queries: List[str] = Field(default_factory=list)
    search_results: List[SearchResult] = Field(default_factory=list)
    code_sections: CodeSections = Field(default_factory=CodeSections)
    pr_summary: str = ""
    github_comment_url: Optional[str] = None

class PRReviewAgent(Agent):
    context: PRReviewContext
    a2a_tool: A2ATool

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
        self.a2a_tool = A2ATool()
        self._register_agents()
        self.verbose = verbose
        self.relevance_model = GPT_4O

    def _register_agents(self):
        """Register sub-agents with the A2A tool"""
        self.a2a_tool.register_agent(
            "rag_sub_agent",
            rag_sub_agent.agent,
            "Expert in using RAG for retrieving relevant code context."
        )
        self.a2a_tool.register_agent(
            "pr_summary_agent",
            summary_agent.agent,
            "Expert in generating PR summaries based on code changes and context."
        )

    def generate_search_queries(self, patch_content: str) -> List[str]:
        """Generate search queries from patch file content"""
        queries = set()
        
        # Extract added lines
        added_lines = [line[1:].strip() for line in patch_content.split('\n') 
                      if line.startswith('+') and not line.startswith('+++')]
        
        # Extract function/class definitions
        for line in added_lines:
            if line.startswith('def '):
                func_match = re.match(r'def\s+(\w+)', line)
                if func_match:
                    queries.add(f"function {func_match.group(1)} implementation")
                    queries.add(f"function {func_match.group(1)} usage")
            elif line.startswith('class '):
                class_match = re.match(r'class\s+(\w+)', line)
                if class_match:
                    queries.add(f"class {class_match.group(1)} definition")
                    queries.add(f"class {class_match.group(1)} usage")
        
        # Add general context queries if we have changes
        if added_lines:
            queries.add("relevant code context for changes")
            queries.add("related implementation details")
        
        return list(queries)[:5]  # Limit to 5 queries

    async def execute_searches(self, queries: List[str]) -> List[SearchResult]:
        """Execute searches using RAG sub-agent and collect results"""
        all_results = []
        
        for query in queries:
            response = await self.a2a_tool.arun_agent(
                "rag_sub_agent",
                f"Find relevant code and documentation for: {query}",
                ThreadContext(self.name)
            )
            
            # Process each result
            for file_path, file_data in response.get("files", {}).items():
                content = file_data.get("content", "")
                included_defs = file_data.get("included_defs", [])
                score = response.get("scores", {}).get(file_path, 0.0)
                result = SearchResult(
                    query=query,
                    file_path=file_path,
                    content=content,
                    similarity_score=score,
                    included_defs=included_defs
                )
                all_results.append(result)
        
        return all_results

    async def filter_relevant_results(
        self, 
        results: List[SearchResult], 
        patch_content: str
    ) -> List[SearchResult]:
        """Filter search results using LLM-based relevance checking"""
        filtered_results = []
        
        for result in sorted(results, key=lambda x: x.similarity_score, reverse=True)[:10]:  # Top 10 results
            if result.similarity_score < 0.5:
                continue
                
            relevance_check = await self.check_result_relevance(
                result.content, 
                result.query,
                patch_content
            )
            
            result.is_relevant = relevance_check["is_relevant"]
            result.relevance_reason = relevance_check["reason"]
            
            if result.is_relevant:
                filtered_results.append(result)
        
        return filtered_results

    async def check_result_relevance(
        self, 
        content: str, 
        query: str,
        patch_content: str
    ) -> Dict[str, Any]:
        """Check if a search result is relevant to the PR changes"""
        prompt = f"""
        Determine if this code snippet is relevant to the PR changes.
        
        PR Changes:
        {patch_content[:2000]}
        
        Search Query: {query}
        
        Code Snippet:
        {content[:2000]}
        
        Is this code relevant? Consider:
        1. Does it contain related functionality?
        2. Is it part of the same module/package?
        3. Does it share dependencies with the changed code?
        
        Return a JSON response with:
        {{
            "is_relevant": boolean,
            "reason": "Brief explanation"
        }}
        """
        
        response = await self.relevance_model.generate(
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"}
        )
        
        try:
            return json.loads(response.choices[0].message.content)
        except (json.JSONDecodeError, IndexError, AttributeError):
            return {"is_relevant": False, "reason": "Error parsing response"}

    def create_code_sections(self, results: List[SearchResult]) -> CodeSections:
        """Create CodeSections from filtered search results"""
        code_sections = CodeSections()
        seen_files = set()
        
        for result in results:
            if not result.is_relevant or result.file_path in seen_files:
                continue
                
            file_name = os.path.basename(result.file_path)
            
            section = CodeSection(
                search_query=result.query,
                search_result=result.content,
                file_name=file_name,
                included_defs=result.included_defs,
                similarity_score=result.similarity_score
            )
            
            code_sections.sections.append(section)
            seen_files.add(result.file_path)
        
        return code_sections

    async def generate_summary(self, patch_content: str, code_sections: CodeSections) -> str:
        """Generate PR summary using summary agent"""
        context = "\n\n".join(
            f"File: {section.file_name}\n"
            f"Query: {section.search_query}\n"
            f"Similarity: {section.similarity_score:.2f}\n"
            f"Defines: {', '.join(section.included_defs)}\n"
            f"Content:\n{section.search_result[:2000]}"
            for section in code_sections.sections
        )
        
        summary = await self.a2a_tool.arun_agent(
            "pr_summary_agent",
            f"""
            Generate a detailed PR summary based on these changes:
            {patch_content[:4000]}
            
            Relevant code context:
            {context}
            """,
            ThreadContext(self.name)
        )
        return summary.get("summary", "No summary generated.")

    async def post_to_github(self, summary: str) -> str:
        """Post summary as a GitHub comment"""
        repo_owner = os.getenv("REPO_OWNER")
        repo_name = os.getenv("REPO_NAME")
        pr_id = os.getenv("PR_ID")
        gh_token = os.getenv("GITHUB_TOKEN")
        
        if not all([repo_owner, repo_name, pr_id, gh_token]):
            raise ValueError("Missing required GitHub configuration")
            
        url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/issues/{pr_id}/comments"
        headers = {
            "Authorization": f"token {gh_token}",
            "Accept": "application/vnd.github.v3+json"
        }
        data = {"body": summary}
        
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()
        return response.json().get("html_url")

    async def process_patch(self, patch_content: str) -> Dict[str, Any]:
        """Process patch file through the entire workflow"""
        # 1. Generate search queries
        queries = self.generate_search_queries(patch_content)
        
        # 2. Execute searches
        search_results = await self.execute_searches(queries)
        
        # 3. Filter results using LLM
        filtered_results = await self.filter_relevant_results(search_results, patch_content)
        
        # 4. Create code sections
        code_sections = self.create_code_sections(filtered_results)
        
        # 5. Generate summary
        summary = await self.generate_summary(patch_content, code_sections)
        
        # 6. Post to GitHub
        comment_url = await self.post_to_github(summary)
        
        return {
            "search_queries": queries,
            "num_code_sections": len(code_sections.sections),
            "summary": summary,
            "github_comment_url": comment_url
        }

    def next_turn(
        self,
        request: str,
        request_context: dict = None,
        request_id: str = None,
        continue_result: dict = None,
        debug: str = ""
    ) -> Generator[Event, Any, None]:
        """Main workflow orchestration - fully automated"""
        try:
            # Process the patch through the entire workflow
            result = yield from self.process_patch(request)
            
            # Return the final result
            yield ChatOutput(
                self.name,
                {"content": f"## PR Review Complete\n\nSummary posted to: {result['github_comment_url']}"}
            )
            
            yield TurnEnd(
                self.name,
                [{"role": "assistant", "content": result['summary']}]
            )
        except Exception as e:
            error_msg = f"Error processing PR: {str(e)}"
            yield ChatOutput(self.name, {"content": f"Error: {error_msg}"})
            yield TurnEnd(self.name, [{"role": "assistant", "content": error_msg}])

# Create an instance of the agent
pr_review_agent = PRReviewAgent()

if __name__ == "__main__":
    # Example usage - fully automated
    with open("PRChanges.patch", "r") as f:
        patch_content = f.read()
    
    # Run the agent
    AgentRunner(pr_review_agent).run(patch_content)