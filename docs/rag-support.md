# RAG Support

Agentic has a basic RAG feature set built on the [Weaviate](https://weaviate.io/) vector database.

You can manage vectorstore indexes using the CLI:

```sh

# Chunk a file, calculate chunk embeddings, and add them to the vectorstore
agentic index_file <index name> <file path>

# Remove all the chunks of a file from the vector store
agentic delete_document <index name> <file path|document ID>

# list the indexes
agentic list-indexes

# rename an index
agentic rename-index <from name> <to name>

# delete a whole index
agentic delete-index <index name>

# List the documents in a vector store
agentic list-documents <index name>

# Show the metadata for a doc in the vector store
agentic show-document <file path|document ID>

# Perform a search of the vector store. Searches by vector by default, or can do hybrid search
agentic search <index name> <query> [hybrid=true]

```

Example usage:

```sh

$ agentic index_file index1 tests/data/agentic_reasoning.pdf

$ agentic list-documents index1
                                                         Documents in 'index1' (3)                                                         
- agentic_reasoning.pdf 
  ID: 27c0600f... | Chunks: 19 | Last indexed: 2025-02-22 05:54:51+00:00

$ agentic search index1 "reasoning models"
                                                     Result 1 - agentic_reasoning.pdf                                                      
- Source: None
- Date: 2025-02-22 05:54:51+00:00
- Distance: 0.18599754571914673
- Score: N/A
...
```

And to use RAG with an agent, via _agentic RAG_, just enable the RAG Tool:

```python
from agentic.tools.rag_tool import RAGTool

agent=Agent(
    name="Agent with RAG",
    tools=[RAGTool("index1")]
)
print(agent << "What do we know about reasoning models?")
```

**Coming soon**: Classic RAG

Create an agent which programmatically loads content from RAG into the LLM context to
answer the user's query.
