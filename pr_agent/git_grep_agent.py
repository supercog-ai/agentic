from typing import Any, Generator, List
from agentic.common import Agent, AgentRunner, ThreadContext
from agentic.events import Event, ChatOutput, WaitForInput, Prompt, PromptStarted, TurnEnd, ResumeWithInput
from agentic.models import GPT_4O_MINI # model (using GPT for testing)
from pydantic import BaseModel, Field
import subprocess
import ast 
import os

from code_rag_agent import CodeSection, CodeSections

# The actual sub-agent that runs git grep and returns structured results 
class GitGrepAgent(Agent):
    def __init__(self,
        name="Git-Grep Agent",
        welcome="I am the Git Grep Agent. Please give me a search query (function name,class name, etc.) and I'll return exact matches from the codebase.",
        model: str=GPT_4O_MINI, 
        result_model = CodeSections,
        **kwargs
    ):
        super().__init__(
            name=name, 
            welcome=welcome,
            model=model,
            result_model=result_model,
            **kwargs
        )


    def run_git_grep(self, query: str) -> List[tuple[str, str]]:
        # Runs "git grep -n <query>" for the given query to find exact matches in the codebase
        # parses each result line into (file_path, matched_line) both of which are strs
        #  and returns a list of (file_path, matched_line) tuples
        try:
            result = subprocess.run(
                        ["git", "grep", "-n", query],               # make sure that query is getting passed by the Main Agent!!!
                        capture_output=True,
                        text=True,
                        check=False
            )


            # example git grep output: "code_rag_agent.py:6:from agentic.tools.rag_tool import RAGTool"


            # TODO: need to determine if the line number is neccessary returning...
            matches = [] # list of matches from the git grep command --> will hold all (file_path, matched_line) tuples found! 
            for line in result.stdout.splitlines():             
                if not line:
                    continue
                parts = line.split(":", 2)  # file_path, line_number, line_text
                if len(parts) >= 3:         # if the output line is in the correct format 
                    file_path, line_number, matched_line = parts
                    matches.append((file_path, open(file_path).read()))
            return matches
        except Exception as e:
            print(f"Error running git grep: {e}")
            return []
        


    # the entry point for running one turn (input -> processing -> output)
    def next_turn(
        self,
        request: str | Prompt,
        request_context: dict = {},
        request_id: str = None,
        continue_result: dict = {},
        debug = "",
    ) -> Generator[Event, Any, Any]:
    # same as for the code_rag_context


        # Either use query from request_context or from direct input
        query = request.payload if isinstance(request, Prompt) else request         # extracts the query from the incoming request 
        yield PromptStarted(query, {"query": query})                                # yields a PromptStarted event to signal the beginning of processing 

        
        search_query = request_context.get("query")                                 # pulls the actual search query from the request context 
        grep_results = self.run_git_grep(search_query)                              # runs git grep for that specific query 


        # TODO: verify that sections doesn't have to be a dictionary instead (like code_rag_agent implementation)
        allSections = CodeSections(sections={}, search_query=search_query)          # creates an empty CodeSections object 

        # loops over each grep match
        for file_path, matched_line in grep_results:
            if not file_path in allSections.sections:
                included_defs = []
                try:
                    if file_path.endswith(".py"):           # if a python file, parse the AST, and collect all function/class names 
                        with open(file_path) as file:       # this gives structural context for the matched file 
                            node = ast.parse(file.read())
                            included_defs = [
                                n.name for n in node.body
                                if isinstance (n, ast.ClassDef) or isinstance(n, ast.FunctionDef)
                            ]
                    else:
                        continue # ONLY search for .py files

                except:
                    included_defs = []

                allSections.sections[file_path] = CodeSection(
                    search_result=matched_line,
                    file_path=file_path,
                    included_defs=included_defs,
                    similarity_score=1.0  # grep doesn't do semantic scoring
                )

        yield TurnEnd(self.name, [{"content": allSections}])
