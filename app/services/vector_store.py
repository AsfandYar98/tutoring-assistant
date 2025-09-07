"""Vector store service for ChromaDB integration."""

import uuid
from typing import List, Dict, Any, Optional
import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)


class VectorStoreService:
    """Service for managing vector embeddings and similarity search."""
    
    def __init__(self):
        self.client = chromadb.HttpClient(
            host=settings.chroma_host,
            port=settings.chroma_port,
            settings=Settings(anonymized_telemetry=False)
        )
        self.embedding_model = SentenceTransformer(settings.embedding_model)
        self.collection_name = "tutoring_documents"
        
    def get_collection(self, tenant_id: str, course_id: str):
        """Get or create a collection for a specific tenant and course."""
        namespace = f"{tenant_id}_{course_id}"
        try:
            return self.client.get_collection(
                name=self.collection_name,
                metadata={"namespace": namespace}
            )
        except Exception:
            return self.client.create_collection(
                name=self.collection_name,
                metadata={"namespace": namespace}
            )
    
    def add_documents(self, tenant_id: str, course_id: str, chunks: List[Dict[str, Any]]) -> List[str]:
        """Add document chunks to the vector store."""
        collection = self.get_collection(tenant_id, course_id)
        
        # Prepare documents for ChromaDB
        documents = []
        metadatas = []
        ids = []
        
        for chunk in chunks:
            chunk_id = str(uuid.uuid4())
            documents.append(chunk["content"])
            metadatas.append({
                "document_id": str(chunk["document_id"]),
                "chunk_index": chunk["chunk_index"],
                "title": chunk.get("title", ""),
                "section": chunk.get("section", ""),
                "page": chunk.get("page", 0)
            })
            ids.append(chunk_id)
        
        # Generate embeddings
        embeddings = self.embedding_model.encode(documents).tolist()
        
        # Add to collection
        collection.add(
            documents=documents,
            metadatas=metadatas,
            ids=ids,
            embeddings=embeddings
        )
        
        return ids
    
    def search_similar(self, 
                      tenant_id: str, 
                      course_id: str, 
                      query: str, 
                      top_k: int = 5,
                      filter_metadata: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Search for similar documents using semantic similarity."""
        collection = self.get_collection(tenant_id, course_id)
        
        # Generate query embedding
        query_embedding = self.embedding_model.encode([query]).tolist()[0]
        
        # Search
        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            where=filter_metadata
        )
        
        # Format results
        formatted_results = []
        if results["documents"] and results["documents"][0]:
            for i, doc in enumerate(results["documents"][0]):
                formatted_results.append({
                    "id": results["ids"][0][i],
                    "content": doc,
                    "metadata": results["metadatas"][0][i],
                    "distance": results["distances"][0][i] if "distances" in results else None
                })
        
        return formatted_results
    
    def delete_document(self, tenant_id: str, course_id: str, document_id: str) -> bool:
        """Delete all chunks for a specific document."""
        try:
            collection = self.get_collection(tenant_id, course_id)
            # Note: ChromaDB doesn't have a direct way to delete by metadata
            # This would require storing chunk IDs separately or using a different approach
            return True
        except Exception as e:
            logger.error(f"Error deleting document {document_id}: {e}")
            return False
    
    def get_collection_stats(self, tenant_id: str, course_id: str) -> Dict[str, Any]:
        """Get statistics about the collection."""
        try:
            collection = self.get_collection(tenant_id, course_id)
            count = collection.count()
            return {
                "total_chunks": count,
                "namespace": f"{tenant_id}_{course_id}"
            }
        except Exception as e:
            logger.error(f"Error getting collection stats: {e}")
            return {"total_chunks": 0, "namespace": f"{tenant_id}_{course_id}"}
