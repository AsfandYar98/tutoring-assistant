"""Simplified vector service."""

import json
import logging
from typing import List, Dict, Any

logger = logging.getLogger(__name__)


class SimpleVectorService:
    """Simplified vector service."""
    
    def __init__(self, openai_api_key: str):
        self.openai_api_key = openai_api_key
        self.documents = {}  # Simple in-memory storage
    
    def add_documents(self, documents: List[Dict[str, Any]], tenant_id: str, course_id: str):
        """Add documents to the simple store."""
        try:
            key = f"{tenant_id}_{course_id}"
            if key not in self.documents:
                self.documents[key] = []
            
            self.documents[key].extend(documents)
            logger.info(f"Added {len(documents)} documents for {key}")
            return True
        except Exception as e:
            logger.error(f"Error adding documents: {e}")
            return False
    
    def search_documents(self, query: str, tenant_id: str, course_id: str, n_results: int = 5) -> List[Dict[str, Any]]:
        """Simple text search without embeddings."""
        try:
            key = f"{tenant_id}_{course_id}"
            if key not in self.documents:
                return []
            
            # Simple keyword matching
            query_lower = query.lower()
            results = []
            
            for doc in self.documents[key]:
                content = doc.get('content', '').lower()
                if query_lower in content:
                    results.append({
                        'content': doc.get('content', ''),
                        'metadata': doc.get('metadata', {})
                    })
            
            return results[:n_results]
        except Exception as e:
            logger.error(f"Error searching documents: {e}")
            return []