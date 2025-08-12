from typing import Any, Generator, List
from agentic.common import Agent
from agentic.events import Event, Prompt, PromptStarted, TurnEnd
from agentic.models import GPT_4O_MINI # model (using GPT for testing)
import subprocess
import ast 
import keyword
import logging

from code_rag_agent import CodeSection, CodeSections

def find_full_function(file_path: str, line_number: int) -> str:
    """Finds the full function definition given a file path and line number. Expects a properly formatted file."""

    SUPPORTED_EXTENSIONS = [".py"]
    line_number -= 1 # line numbers start at 1, not 0, bad for native zero indexing
    try:
        with open(file_path) as file:
            text = file.read()
    except Exception as e:
        return f"Error with file: {e}"
        
    if not any(file_path.endswith(ext) for ext in SUPPORTED_EXTENSIONS):
        logging.warning("File is not a supported extension, returning full file")
        return text

    if file_path.endswith(".py"):
        lines = text.splitlines()

        if len(lines) < line_number: # move this out of the if statement later
            logging.error("Line number is out of bounds, returning full file")
            return text

        # this function is "good enough" -- if there is any function that is not defined by the keyword module called outside of a class or function, it will keep it
        def is_a_zero(line: str) -> bool:
            if not line or line[0] == " " or not keyword.iskeyword(line.split()[0]):
                return False
            return True
        
        # The idea is to find the full class definition the function is embedded in, so we need to go up and down until we find this
        top_index = line_number

        while (top_index > 0 and not is_a_zero(lines[top_index])):
            top_index -= 1
        
        bottom_index = line_number + 1
        while (bottom_index < len(lines) and not is_a_zero(lines[bottom_index])):
            bottom_index += 1
        
        return "\n".join(lines[top_index:bottom_index])
    
    return text

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
                    matches.append((file_path, find_full_function(file_path, int(line_number))))
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
        for file_path, content in grep_results:
            if not file_path in allSections.sections:
                allSections.sections[file_path] = CodeSection(
                    search_result=content,
                    file_path=file_path,
                    included_defs=[],
                    similarity_score=1.0  # grep doesn't do semantic scoring
                )

        yield TurnEnd(self.name, [{"content": allSections}])

if __name__ == "__main__":
    print(find_full_function("git_grep_agent.py", 172))