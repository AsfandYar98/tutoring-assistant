"""ChromaDB vector store service for production use."""

import uuid
from typing import List, Dict, Any, Optional
import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer
import logging

logger = logging.getLogger(__name__)


class ChromaDBService:
    """ChromaDB vector store service for document embeddings and retrieval."""
    
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
        
        # Initialize embedding model
        try:
            self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
            logger.info("Embedding model loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load embedding model: {e}")
            raise
        
        # Get or create collections
        self.collections = {}
        self._initialize_collections()
    
    def _initialize_collections(self):
        """Initialize or get existing collections."""
        try:
            # Get or create collections for each tenant
            # We'll use a default collection for now, but in production you'd want per-tenant collections
            self.collections['default'] = self.client.get_or_create_collection(
                name="tutoring_documents",
                metadata={"description": "Tutoring assistant document embeddings"}
            )
            logger.info("Collections initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize collections: {e}")
            raise
    
    def get_embedding(self, text: str) -> List[float]:
        """Generate embedding for text."""
        try:
            embedding = self.embedding_model.encode(text).tolist()
            return embedding
        except Exception as e:
            logger.error(f"Failed to generate embedding: {e}")
            raise
    
    def add_documents(self, documents: List[Dict[str, Any]], collection_name: str = "default") -> List[str]:
        """Add documents to the vector store."""
        try:
            collection = self.collections.get(collection_name)
            if not collection:
                collection = self.client.get_or_create_collection(name=collection_name)
                self.collections[collection_name] = collection
            
            # Prepare data for ChromaDB
            ids = []
            texts = []
            embeddings = []
            metadatas = []
            
            for doc in documents:
                doc_id = str(uuid.uuid4())
                ids.append(doc_id)
                texts.append(doc['content'])
                embeddings.append(self.get_embedding(doc['content']))
                metadatas.append({
                    'document_id': doc.get('document_id'),
                    'chunk_index': doc.get('chunk_index', 0),
                    'course_id': doc.get('course_id'),
                    'tenant_id': doc.get('tenant_id'),
                    'title': doc.get('title', ''),
                    'content_type': doc.get('content_type', 'text')
                })
            
            # Add to collection
            collection.add(
                ids=ids,
                documents=texts,
                embeddings=embeddings,
                metadatas=metadatas
            )
            
            logger.info(f"Added {len(documents)} documents to collection '{collection_name}'")
            return ids
            
        except Exception as e:
            logger.error(f"Failed to add documents: {e}")
            raise
    
    def search_documents(
        self, 
        query: str, 
        collection_name: str = "default",
        n_results: int = 5,
        filter_metadata: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Search for similar documents."""
        try:
            collection = self.collections.get(collection_name)
            if not collection:
                logger.warning(f"Collection '{collection_name}' not found")
                return []
            
            # Generate query embedding
            query_embedding = self.get_embedding(query)
            
            # Search
            results = collection.query(
                query_embeddings=[query_embedding],
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
    
    def delete_documents(self, document_ids: List[str], collection_name: str = "default") -> bool:
        """Delete documents by IDs."""
        try:
            collection = self.collections.get(collection_name)
            if not collection:
                logger.warning(f"Collection '{collection_name}' not found")
                return False
            
            collection.delete(ids=document_ids)
            logger.info(f"Deleted {len(document_ids)} documents from collection '{collection_name}'")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete documents: {e}")
            raise
    
    def get_collection_stats(self, collection_name: str = "default") -> Dict[str, Any]:
        """Get collection statistics."""
        try:
            collection = self.collections.get(collection_name)
            if not collection:
                return {"error": f"Collection '{collection_name}' not found"}
            
            count = collection.count()
            return {
                "collection_name": collection_name,
                "document_count": count,
                "status": "healthy"
            }
            
        except Exception as e:
            logger.error(f"Failed to get collection stats: {e}")
            return {"error": str(e)}
    
    def health_check(self) -> Dict[str, Any]:
        """Check if ChromaDB service is healthy."""
        try:
            # Try to get collection stats
            stats = self.get_collection_stats()
            return {
                "status": "healthy",
                "chromadb_host": f"{self.host}:{self.port}",
                "collections": list(self.collections.keys()),
                "stats": stats
            }
        except Exception as e:
            logger.error(f"ChromaDB health check failed: {e}")
            return {
                "status": "unhealthy",
                "error": str(e)
            }
