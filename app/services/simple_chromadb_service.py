"""Simplified ChromaDB service without sentence-transformers dependency."""

import uuid
import logging
from typing import List, Dict, Any, Optional
import chromadb
from chromadb.config import Settings

logger = logging.getLogger(__name__)


class SimpleChromaDBService:
    """Simplified ChromaDB service for document embeddings and retrieval."""
    
    def __init__(self, host: str = "localhost", port: int = 8000, api_key: Optional[str] = None):
        """Initialize ChromaDB service."""
        self.host = host
        self.port = port
        self.api_key = api_key
        
        # Initialize ChromaDB client
        try:
            if api_key:
                self.client = chromadb.HttpClient(
                    host=host,
                    port=port,
                    settings=Settings(api_key=api_key)
                )
            else:
                # For local development, use persistent client
                self.client = chromadb.PersistentClient(path="./vector_storage")
            
            logger.info(f"ChromaDB client initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize ChromaDB client: {e}")
            raise
        
        # Get or create collections
        self.collections = {}
        self._initialize_collections()
    
    def _initialize_collections(self):
        """Initialize or get existing collections."""
        try:
            # Get or create collections for each tenant
            self.collections['default'] = self.client.get_or_create_collection(
                name="tutoring_documents",
                metadata={"description": "Tutoring assistant document embeddings"}
            )
            logger.info("Collections initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize collections: {e}")
            raise
    
    def add_document(self, collection_name: str, document: Dict[str, Any], document_id: str = None) -> str:
        """Add a single document to the vector store."""
        try:
            collection = self.collections.get(collection_name)
            if not collection:
                collection = self.client.get_or_create_collection(name=collection_name)
                self.collections[collection_name] = collection
            
            if not document_id:
                document_id = str(uuid.uuid4())
            
            # Add to collection (ChromaDB will generate embeddings automatically)
            collection.add(
                ids=[document_id],
                documents=[document['content']],
                metadatas=[{
                    'document_id': document.get('document_id', document_id),
                    'course_id': document.get('course_id'),
                    'tenant_id': document.get('tenant_id'),
                    'title': document.get('title', ''),
                    'content_type': document.get('content_type', 'text')
                }]
            )
            
            logger.info(f"Added document {document_id} to collection '{collection_name}'")
            return document_id
            
        except Exception as e:
            logger.error(f"Failed to add document: {e}")
            raise
    
    def search_similar(
        self, 
        collection_name: str, 
        query: str, 
        n_results: int = 5,
        filter_metadata: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Search for similar documents."""
        try:
            collection = self.collections.get(collection_name)
            if not collection:
                logger.warning(f"Collection '{collection_name}' not found")
                return []
            
            # Search using ChromaDB's built-in embedding
            results = collection.query(
                query_texts=[query],
                n_results=n_results,
                where=filter_metadata
            )
            
            # Format results
            formatted_results = []
            if results['documents'] and results['documents'][0]:
                for i, doc in enumerate(results['documents'][0]):
                    formatted_results.append({
                        'id': results['ids'][0][i],
                        'content': doc,
                        'metadata': results['metadatas'][0][i],
                        'distance': results['distances'][0][i] if 'distances' in results else 0.0
                    })
            
            logger.info(f"Found {len(formatted_results)} similar documents")
            return formatted_results
            
        except Exception as e:
            logger.error(f"Failed to search documents: {e}")
            raise
    
    def search_documents(self, 
                         query: str, 
                         n_results: int = 5,
                         filter_metadata: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Search for documents (alias for search_similar)."""
        return self.search_similar(
            collection_name='default',
            query=query,
            n_results=n_results,
            filter_metadata=filter_metadata
        )
    
    def add_documents(self, documents: List[Dict[str, Any]]) -> List[str]:
        """Add multiple documents to the vector store."""
        document_ids = []
        for doc in documents:
            doc_id = self.add_document('default', doc)
            document_ids.append(doc_id)
        return document_ids
    
    def health_check(self) -> Dict[str, Any]:
        """Check if ChromaDB service is healthy."""
        try:
            # Try to get collection stats
            collection = self.collections.get('default')
            if collection:
                count = collection.count()
                return {
                    "status": "healthy",
                    "chromadb_host": f"{self.host}:{self.port}",
                    "collections": list(self.collections.keys()),
                    "document_count": count
                }
            else:
                return {
                    "status": "healthy",
                    "chromadb_host": f"{self.host}:{self.port}",
                    "collections": [],
                    "document_count": 0
                }
        except Exception as e:
            logger.error(f"ChromaDB health check failed: {e}")
            return {
                "status": "unhealthy",
                "error": str(e)
            }
