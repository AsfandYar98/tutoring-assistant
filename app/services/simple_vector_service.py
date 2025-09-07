"""Simplified vector service for Vercel deployment."""

import json
import logging
from typing import List, Dict, Any
import numpy as np
from openai import OpenAI

logger = logging.getLogger(__name__)


class SimpleVectorService:
    """Simplified vector service without ChromaDB for Vercel."""
    
    def __init__(self, openai_api_key: str):
        self.openai_client = OpenAI(api_key=openai_api_key)
        self.documents = {}  # Simple in-memory storage
        self.embeddings = {}  # Simple in-memory storage
    
    def add_documents(self, documents: List[Dict[str, Any]], tenant_id: str, course_id: str):
        """Add documents to the simple vector store."""
        try:
            key = f"{tenant_id}_{course_id}"
            if key not in self.documents:
                self.documents[key] = []
                self.embeddings[key] = []
            
            for doc in documents:
                # Generate embedding
                embedding = self._get_embedding(doc.get('content', ''))
                
                # Store document and embedding
                self.documents[key].append(doc)
                self.embeddings[key].append(embedding)
            
            logger.info(f"Added {len(documents)} documents for {key}")
            return True
        except Exception as e:
            logger.error(f"Error adding documents: {e}")
            return False
    
    def search_documents(self, query: str, tenant_id: str, course_id: str, n_results: int = 5) -> List[Dict[str, Any]]:
        """Search for similar documents using simple cosine similarity."""
        try:
            key = f"{tenant_id}_{course_id}"
            if key not in self.documents:
                return []
            
            # Generate query embedding
            query_embedding = self._get_embedding(query)
            
            # Calculate similarities
            similarities = []
            for i, doc_embedding in enumerate(self.embeddings[key]):
                similarity = self._cosine_similarity(query_embedding, doc_embedding)
                similarities.append((similarity, i))
            
            # Sort by similarity and get top results
            similarities.sort(reverse=True)
            results = []
            
            for similarity, idx in similarities[:n_results]:
                if similarity > 0.1:  # Minimum similarity threshold
                    results.append({
                        'content': self.documents[key][idx].get('content', ''),
                        'metadata': self.documents[key][idx].get('metadata', {})
                    })
            
            return results
        except Exception as e:
            logger.error(f"Error searching documents: {e}")
            return []
    
    def _get_embedding(self, text: str) -> List[float]:
        """Get embedding from OpenAI."""
        try:
            response = self.openai_client.embeddings.create(
                model="text-embedding-ada-002",
                input=text
            )
            return response.data[0].embedding
        except Exception as e:
            logger.error(f"Error getting embedding: {e}")
            return [0.0] * 1536  # Default embedding size
    
    def _cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """Calculate cosine similarity between two vectors."""
        try:
            vec1 = np.array(vec1)
            vec2 = np.array(vec2)
            
            dot_product = np.dot(vec1, vec2)
            norm1 = np.linalg.norm(vec1)
            norm2 = np.linalg.norm(vec2)
            
            if norm1 == 0 or norm2 == 0:
                return 0.0
            
            return dot_product / (norm1 * norm2)
        except Exception as e:
            logger.error(f"Error calculating cosine similarity: {e}")
            return 0.0
