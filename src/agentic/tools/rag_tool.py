from typing import List, Callable
import glob

from agentic.common import RunContext
from agentic.tools.utils.registry import tool_registry, Dependency
from agentic.tools.base import BaseAgenticTool
from agentic.utils.rag_helper import (
    list_collections,
    init_weaviate,
    list_documents_in_collection,
    create_collection,
    prepare_document_metadata,
    check_document_exists,
    init_embedding_model,
    init_chunker,
    rag_index_file,
)

from agentic.utils.summarizer import generate_document_summary
from agentic.utils.file_reader import read_file
from weaviate.classes.query import Filter, HybridFusion
from weaviate.collections.classes.grpc import Sort
from weaviate.classes.config import VectorDistances


@tool_registry.register(
    name="RAGTool",
    description="Manage and query knowledge bases using RAG",
    dependencies=[
        Dependency(
            name="weaviate-client",
            version="4.10.4",
            type="pip",
        ),
    ]
)
class RAGTool(BaseAgenticTool):
    def __init__(
        self,
        default_index: str = "knowledge_base",
        index_paths: list[str] = []
    ):
        # Construct the RAG tool. You can pass a list of files and we will ensure that
        # they are added to the index on startup. Paths can include glob patterns also,
        # like './docs/*.md'.
        self.default_index = default_index
        self.index_paths = index_paths
        if self.index_paths:
            client = init_weaviate()
            if default_index not in list_collections(client):
                create_collection(client, default_index, VectorDistances.COSINE)
            for path in index_paths:
                for file_path in [path] if path.startswith("http") else glob.glob(path):
                    rag_index_file(file_path, self.default_index, client=client, ignore_errors=True)

    def get_tools(self) -> List[Callable]:
        return [
            self.save_content_to_knowledge_index,
            #self.list_indexes,
            self.search_knowledge_index,
            self.list_documents,
            self.review_full_document
        ]

    def save_content_to_knowledge_index(
        self,
        run_context: RunContext,
        content: str = None,
        index_name: str = None,
    ) -> str:
        """Save content to a knowledge index. Accepts both text and file paths/URLs."""
        try:
            client = init_weaviate()
            index_name = index_name or self.default_index
            create_collection(client, index_name, VectorDistances.COSINE)

            embed_model = init_embedding_model("BAAI/bge-small-en-v1.5")
            chunker = init_chunker(0.5, ". ,! ,? ,\n")

            text, mime_type = read_file(str(content))
            metadata = prepare_document_metadata(content, text, mime_type, "openai/gpt-4o-mini")
            
            collection = client.collections.get(index_name)
            exists, status = check_document_exists(
                collection, 
                metadata["document_id"],
                metadata["fingerprint"]
            )
            
            if status == "unchanged":
                return f"⏩ Document '{metadata['filename']}' unchanged[/yellow]"
            elif status == "duplicate":
                return f"⚠️ Content already exists under different filename[/yellow]"
            elif status == "changed":
                collection.data.delete_many(
                    where=Filter.by_property("document_id").equal(metadata["document_id"])
                )

            metadata["summary"] = generate_document_summary(
                text=text[:12000],
                mime_type=mime_type,
                model="openai/gpt-4o-mini"
            )
            
            chunks = chunker(text)
            chunks_text = [chunk.text for chunk in chunks]
            if not chunks_text:
                raise ValueError("No text chunks generated from document")
            
            batch_size = 128
            embeddings = []
            for i in range(0, len(chunks_text), batch_size):
                batch = chunks_text[i:i+batch_size]
                embeddings.extend(list(embed_model.embed(batch)))
            
            with collection.batch.dynamic() as batch:
                for i, chunk in enumerate(chunks):
                    vector = embeddings[i].tolist()
                    batch.add_object(
                        properties={
                            **metadata,
                        "content": chunk.text,
                        "chunk_index": i,
                        },
                        vector=vector
                    )
                    
            return f"✅ Indexed {len(chunks)} chunks in {index_name}"
        
        except Exception as e:
            return f"Error: {str(e)}"
        finally:
            if client:
                client.close()
        
    def list_indexes(self) -> str:
        """List all knowledge indexes"""
        try:
            client = init_weaviate()
            indexes = list_collections(client)
            return f"Available indexes: {', '.join(indexes)}"
        except Exception as e:
            return f"Error listing indexes: {str(e)}"
        finally:
            if client:
                client.close()
    
    def search_knowledge_index(self, query: str = None, limit: int = 1, hybrid: bool = False) -> str:
        """Search a knowledge index for relevant documents"""
        try:
            embed_model = init_embedding_model("BAAI/bge-small-en-v1.5")
            client = init_weaviate()
            collection = client.collections.get(self.default_index)

            query_vector = list(embed_model.embed([query]))[0].tolist()
        
            search_params = {
                "limit": limit,
                "return_metadata": ["distance", "score"] if hybrid else ["distance"],
                "return_properties": ["filename", "content", "source_url", "timestamp"]
            }

            if hybrid:
                result = collection.query.hybrid(
                    query=query,
                    vector=query_vector,
                    alpha=0.5,
                    fusion_type=HybridFusion.RELATIVE_SCORE,
                    **search_params
                )
            else:
                result = collection.query.near_vector(
                    near_vector=query_vector,
                    **search_params
                )

            return [
            {
                "filename": obj.properties.get("filename", "Unknown"),
                "content": obj.properties.get("content", ""),
                "source_url": obj.properties.get("source_url", ""),
                "timestamp": obj.properties.get("timestamp", ""),
                "distance": obj.metadata.distance if hasattr(obj.metadata, 'distance') else None,
                "score": obj.metadata.score if hasattr(obj.metadata, 'score') else None
            }
            for obj in result.objects]
        except Exception as e:
            return [{"error": f"Search failed: {str(e)}"}] 
        finally:
            if client:
                client.close()

    def list_documents(self) -> str:
        """List all documents in a knowledge index"""
        try:
            client = init_weaviate()
            collection = client.collections.get(self.default_index)
            documents = list_documents_in_collection(collection)
            return documents
        except Exception as e:
            return f"Error listing documents: {str(e)}"
        finally:
            if client:
                client.close()

    def review_full_document(self, document_id: str = None) -> str:
        """Review a full document from a knowledge index"""
        try:
            client = init_weaviate()
            collection = client.collections.get(self.default_index)

            # Get all chunks for the document ordered by chunk_index
            result = collection.query.fetch_objects(
                filters=Filter.by_property("document_id").equal(document_id),
                return_properties=["content", "chunk_index", "filename"],
                sort=Sort.by_property("chunk_index", ascending=True)
            )

            if not result.objects:
                return f"Document with ID {document_id} not found"

            # Combine all chunks into full document text
            filename = result.objects[0].properties.get("filename", "Unknown")
            full_text = "\n".join(obj.properties.get("content", "") for obj in result.objects)

            return f"Document: {filename}\n\n{full_text}"
        except Exception as e:
            return f"Error retrieving document: {str(e)}"
        finally:
            if client:
                client.close()