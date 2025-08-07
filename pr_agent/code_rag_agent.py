from typing import Any, Generator, List
from agentic.common import Agent, AgentRunner, ThreadContext
from agentic.events import Event, ChatOutput, WaitForInput, Prompt, PromptStarted, TurnEnd, ResumeWithInput
from agentic.models import GPT_4O_MINI # model (using GPT for testing)
from pydantic import BaseModel, Field
from agentic.tools.rag_tool import RAGTool
import ast

class CodeSection(BaseModel):
    search_result: str = Field(
        description="Part returned from search.",
    )
    file_path: str = Field(
        description="Path of the file this code belongs to."
    )
    included_defs: list[str] = Field(
        description="Classes and functions defined in this file."
    )
    similarity_score: float = Field(
        desciption="Similarity score returned from vector search."
    )

class CodeSections(BaseModel):
    sections: dict[str,CodeSection] = Field(
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
                index_paths=[],
                recursive=True
            )
        

    def next_turn(
        self,
        request: str|Prompt,
        request_context: dict = {},
        request_id: str = None,
        continue_result: dict = {},
        debug = "",
    ) -> Generator[Event, Any, Any]:
        
        query = request.payload if isinstance(request, Prompt) else request
        yield PromptStarted(query, {"query": query})

        searchQuery = request_context.get("query")

        searchResult = self.ragTool.search_knowledge_index(query=searchQuery,limit=5)
        
        allSections = CodeSections(sections={},search_query=query)

        for nextResult in searchResult:
            file_path = nextResult["source_url"]
            if not file_path in allSections.sections:
                #print(nextResult)
                
                similarity_score = nextResult["distance"] if nextResult["distance"] else 0
                content = nextResult["content"]

                # Only works with Python files
                included_defs = []
                try:
                    with open(file_path) as file:
                        node = ast.parse(file.read())
                        included_defs = [n.name for n in node.body if isinstance(n, ast.ClassDef) or isinstance(n, ast.FunctionDef)]
                except:
                    included_defs = []

                allSections.sections[file_path] = CodeSection(search_result=content,file_path=file_path,included_defs=included_defs,similarity_score=similarity_score)
            #else:
                #print("Skipping Duplicate: ",file_path)

        yield TurnEnd(self.name, [{"content": allSections}])
