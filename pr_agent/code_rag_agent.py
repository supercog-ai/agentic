from typing import Any, Generator, List
from agentic.common import Agent, AgentRunner, ThreadContext
from agentic.events import Event, ChatOutput, WaitForInput, Prompt, PromptStarted, TurnEnd, ResumeWithInput
from agentic.models import GPT_4O_MINI # model (using GPT for testing)
from pydantic import BaseModel, Field
from src.agentic.tools.rag_tool import RAGTool
import ast

class CodeSection(BaseModel):
    search_result: str = Field(
        description="Part returned from search.",
    )
    file_name: str = Field(
        description="Name of the file this code belongs to."
    )
    included_defs: list[str] = Field(
        description="Classes and functions defined in this file."
    )
    similarity_score: int = Field(
        desciption="Similarity score returned from vector search."
    )

class CodeSections(BaseModel):
    sections: List[CodeSection] = Field(
        description="Sections of the codebase returned from the search.",
    )
    search_query: str = Field(
        description="Query used to return this section.",
    )

class CodeRagAgent(Agent):
    def __init__(self,
        name="Code Rag Agent",
        welcome="I am the Code Rag Agent. Please give me a search query (function name,class name, etc.) and I'll return relevant parts of the code.",
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

        self.ragTool = RAGTool(
                default_index="codebase",
                index_paths=["../../*.md","../../*.py"]
            )
        

    def next_turn(
        self,
        request: str|Prompt,
    ) -> Generator[Event, Any, Any]:
        
        query = request.payload if isinstance(request, Prompt) else request
        yield PromptStarted(query, {"query": query})

        searchResult = self.ragTool.search_knowledge_index(query=query,limit=5)

        allSections = CodeSections(sections=[],search_query=query)

        for nextResult in searchResult:
            filename = nextResult["filename"]
            similarity_score = nextResult["score"]

            # Only works with Python files
            included_defs = []
            with open(filename) as file:
                node = ast.parse(file.read)
                included_defs = [n.name for n in node.body if isinstance(n, ast.ClassDef) or isinstance(n, ast.FunctionDef)]
            
            allSections.sections.append(CodeSection(search_result=searchResult,file_name=filename,included_defs=included_defs,similarity_score=similarity_score))

        yield ChatOutput(
            self.name,
            {"content": allSections}
        )
        
        yield TurnEnd(self.name, {"status": "Search completed."})
