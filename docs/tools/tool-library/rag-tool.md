# RAGTool

The `RAGTool` provides Retrieval-Augmented Generation (RAG) capabilities for agents. This tool allows agents to manage knowledge bases, index content, and perform semantic searches to retrieve relevant information.

## Features

- Create and manage knowledge indexes
- Save and index content from text, files, or URLs
- Search indexed content using semantic or hybrid search
- Review and manage indexed documents
- Chunking and embedding of content

## Initialization

```python
def __init__(default_index: str = "knowledge_base", index_paths: list[str] = [])
```

**Parameters:**

- `default_index (str)`: Name of the default vector store index (default: "knowledge_base")
- `index_paths (list[str])`: List of files or glob patterns to index during initialization

## Methods

### save_content_to_knowledge_index

```python
def save_content_to_knowledge_index(run_context: RunContext, content: str = None, index_name: str = None) -> str
```

Save content to a knowledge index. Accepts both text and file paths/URLs.

**Parameters:**

- `run_context (RunContext)`: The execution context
- `content (str)`: Text content or path to file/URL to index
- `index_name (str)`: Name of the index to save to (defaults to default_index)

**Returns:**
Status message indicating success or failure.

### search_knowledge_index

```python
def search_knowledge_index(query: str = None, limit: int = 1, hybrid: bool = False) -> str
```

Search a knowledge index for relevant documents.

**Parameters:**

- `query (str)`: The search query
- `limit (int)`: Maximum number of results to return (default: 1)
- `hybrid (bool)`: Whether to use hybrid search (vector + text) (default: False)

**Returns:**
List of dictionaries containing search results with metadata.

### list_documents

```python
def list_documents() -> str
```

List all documents in a knowledge index.

**Returns:**
String containing document information.

### review_full_document

```python
def review_full_document(document_id: str = None) -> str
```

Review a full document from a knowledge index.

**Parameters:**

- `document_id (str)`: ID of the document to review

**Returns:**
String containing the full document content.

## Example Usage

```python
from agentic.common import Agent
from agentic.tools import RAGTool

# Create a RAG tool with default settings
rag_tool = RAGTool()

# Create an agent with RAG capabilities
knowledge_agent = Agent(
    name="Knowledge Assistant",
    instructions="You help users find information in the knowledge base.",
    tools=[rag_tool]
)

# Index a file
response = knowledge_agent << "Save this document to the knowledge base: https://www.iana.org/reports/2014/transition-plan-201404.pdf"
print(response)

# Search for information
response = knowledge_agent << "What does the document say about the transistion of iana?"
print(response)

# Create a RAG tool with pre-indexed files
pre_indexed_rag = RAGTool(
    default_index="documentation",
    index_paths=["./docs/*.md"]
)

# Create an agent with pre-indexed documentation
docs_agent = Agent(
    name="Documentation Helper",
    instructions="You help users find information in the documentation.",
    tools=[pre_indexed_rag]
)

# Use the agent with pre-indexed content
response = docs_agent << "How do I install this software?"
print(response)
```

## Implementation Details

The RAGTool uses:

- Weaviate as the vector database backend
- Chunking to break documents into manageable pieces
- Embedding models to generate vector representations
- Document metadata tracking for source attribution
- Automatic deduplication of content

## CLI Integration

The tool integrates with Agentic's CLI for index management:

```bash
# Index a file
agentic index_file my_index path/to/document.pdf

# Search the index
agentic search my_index "my search query"

# List documents in an index
agentic list-documents my_index
```

## Notes

- The tool automatically handles document processing, chunking, and embedding
- Content is indexed in real-time
- Search supports both pure vector similarity and hybrid search
- Documents can be retrieved in full or as relevant chunks
- The tool tracks document metadata including source, timestamp, and fingerprints
