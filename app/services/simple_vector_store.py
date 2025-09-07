"""Simplified vector store service for local development."""

import uuid
from typing import List, Dict, Any, Optional
import json
import os
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)


class SimpleVectorStoreService:
    """Simplified vector store service using in-memory storage for local development."""
    
    def __init__(self):
        self.storage_dir = "vector_storage"
        os.makedirs(self.storage_dir, exist_ok=True)
        
    def get_collection_path(self, tenant_id: str, course_id: str) -> str:
        """Get the file path for a collection."""
        return os.path.join(self.storage_dir, f"{tenant_id}_{course_id}.json")
    
    def add_documents(self, tenant_id: str, course_id: str, chunks: List[Dict[str, Any]]) -> List[str]:
        """Add document chunks to the vector store."""
        collection_path = self.get_collection_path(tenant_id, course_id)
        
        # Load existing collection or create new one
        if os.path.exists(collection_path):
            with open(collection_path, 'r') as f:
                collection = json.load(f)
        else:
            collection = {"documents": [], "embeddings": []}
        
        # Add new chunks
        chunk_ids = []
        for chunk in chunks:
            chunk_id = str(uuid.uuid4())
            chunk_ids.append(chunk_id)
            
            # Simple text-based similarity (for demo purposes)
            # In production, you'd use actual embeddings
            collection["documents"].append({
                "id": chunk_id,
                "content": chunk["content"],
                "metadata": chunk.get("metadata", {}),
                "document_id": chunk["document_id"],
                "chunk_index": chunk["chunk_index"]
            })
        
        # Save collection
        with open(collection_path, 'w') as f:
            json.dump(collection, f, indent=2)
        
        return chunk_ids
    
    def search_similar(self, 
                      tenant_id: str, 
                      course_id: str, 
                      query: str, 
                      top_k: int = 5,
                      filter_metadata: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Search for similar documents using simple text matching."""
        collection_path = self.get_collection_path(tenant_id, course_id)
        
        if not os.path.exists(collection_path):
            return []
        
        with open(collection_path, 'r') as f:
            collection = json.load(f)
        
        documents = collection.get("documents", [])
        
        # Simple text-based similarity scoring
        scored_docs = []
        query_lower = query.lower()
        
        for doc in documents:
            content_lower = doc["content"].lower()
            
            # Simple scoring based on word overlap
            query_words = set(query_lower.split())
            content_words = set(content_lower.split())
            
            # Calculate simple similarity score
            common_words = query_words.intersection(content_words)
            similarity_score = len(common_words) / max(len(query_words), 1)
            
            scored_docs.append({
                "id": doc["id"],
                "content": doc["content"],
                "metadata": doc["metadata"],
                "distance": 1 - similarity_score  # Convert to distance
            })
        
        # Sort by similarity and return top-k
        scored_docs.sort(key=lambda x: x["distance"])
        return scored_docs[:top_k]
    
    def delete_document(self, tenant_id: str, course_id: str, document_id: str) -> bool:
        """Delete all chunks for a specific document."""
        try:
            collection_path = self.get_collection_path(tenant_id, course_id)
            
            if not os.path.exists(collection_path):
                return True
            
            with open(collection_path, 'r') as f:
                collection = json.load(f)
            
            # Remove documents with matching document_id
            collection["documents"] = [
                doc for doc in collection["documents"] 
                if doc.get("document_id") != document_id
            ]
            
            # Save updated collection
            with open(collection_path, 'w') as f:
                json.dump(collection, f, indent=2)
            
            return True
        except Exception as e:
            logger.error(f"Error deleting document {document_id}: {e}")
            return False
    
    def get_collection_stats(self, tenant_id: str, course_id: str) -> Dict[str, Any]:
        """Get statistics about the collection."""
        try:
            collection_path = self.get_collection_path(tenant_id, course_id)
            
            if not os.path.exists(collection_path):
                return {"total_chunks": 0, "namespace": f"{tenant_id}_{course_id}"}
            
            with open(collection_path, 'r') as f:
                collection = json.load(f)
            
            count = len(collection.get("documents", []))
            return {
                "total_chunks": count,
                "namespace": f"{tenant_id}_{course_id}"
            }
        except Exception as e:
            logger.error(f"Error getting collection stats: {e}")
            return {"total_chunks": 0, "namespace": f"{tenant_id}_{course_id}"}
