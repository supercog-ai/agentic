# RAG Support

Agentic has a basic RAG feature set built on the [Weaviate](https://weaviate.io/) vector database.

You can manage vectorstore indexes using the CLI:

```sh

# Chunk a file, calculate chunk embeddings, and add them to the vectorstore
agentic index document add_doc <index name> <file path>

# Remove all the chunks of a file from the vector store
agentic index document delete_doc <index name> <file path|document ID>

# list the indexes
agentic index list

# rename an index
agentic index rename <from name> <to name>

# delete a whole index
agentic index delete <index name>

# List the documents in a vector store
agentic index document list_docs <index name>

# Show the metadata for a doc in the vector store
agentic index document show_doc <index name> <file path|document ID>

# Perform a search of the vector store. Searches by vector by default, or can do hybrid search
agentic index search <index name> <query> [--hybrid]

```

Example usage:

```sh

$ agentic index document add_doc index1 tests/data/agentic_reasoning.pdf

$ agentic index document list_docs index1
                                                         Documents in 'index1' (3)                                                         
- agentic_reasoning.pdf 
  ID: 27c0600f... | Chunks: 19 | Last indexed: 2025-02-22 05:54:51+00:00

$ agentic index search index1 "reasoning models"
                                                     Result 1 - agentic_reasoning.pdf                                                      
- Source: None
- Date: 2025-02-22 05:54:51+00:00
- Distance: 0.18599754571914673
- Score: N/A
...
```

And to use RAG with an agent, via _agentic RAG_, just enable the RAG Tool:

```python
from agentic.tools import MCPTool, RAGTool
from agentic.common import Agent

# Create Sequential Thinking MCP tool
sequential_thinker = MCPTool(
    command="npx",
    args=["-y", "@modelcontextprotocol/server-sequential-thinking"]
)

agent=Agent(
    name="Agent with RAG",
    tools=[
        RAGTool("index1"),
        sequential_thinker
    ]
)
print(agent << "What do we know about reasoning models?")
```

**Coming soon**: Classic RAG

Create an agent which programmatically loads content from RAG into the LLM context to
answer the user's query.
