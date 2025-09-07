"""Simplified RAG orchestrator for Vercel deployment."""

import json
import logging
from typing import List, Dict, Any, AsyncGenerator
from app.services.simple_vector_service import SimpleVectorService
from app.services.openai_service import OpenAIService
from app.core.vercel_config import settings

logger = logging.getLogger(__name__)


class SimpleRAGOrchestrator:
    """Simplified RAG orchestrator without ChromaDB for Vercel."""
    
    def __init__(self):
        self.vector_service = SimpleVectorService(settings.openai_api_key)
        self.llm_service = OpenAIService(
            api_key=settings.openai_api_key,
            model="gpt-4"
        )
    
    async def process_chat_query(self,
                                query: str,
                                tenant_id: str,
                                course_id: str,
                                chat_history: List[Dict[str, str]] = None,
                                db = None) -> AsyncGenerator[str, None]:
        """Process a chat query using simplified RAG."""
        try:
            # Retrieve relevant context
            context_chunks = self._retrieve_context(query, tenant_id, course_id)
            
            # Generate RAG response (streaming)
            async for chunk in self.llm_service.generate_rag_response_stream(
                question=query,
                context_documents=context_chunks,
                conversation_history=chat_history
            ):
                yield f"data: {json.dumps({'content': chunk})}\n\n"
            
        except Exception as e:
            logger.error(f"Error in RAG orchestrator: {e}")
            yield f"data: {json.dumps({'error': str(e)})}\n\n"
    
    def _retrieve_context(self, query: str, tenant_id: str, course_id: str) -> List[Dict[str, Any]]:
        """Retrieve relevant context using simplified vector search."""
        try:
            # Search for relevant documents
            results = self.vector_service.search_documents(
                query=query,
                tenant_id=tenant_id,
                course_id=course_id,
                n_results=5
            )
            
            # Format results for LLM
            context_chunks = []
            for result in results:
                context_chunks.append({
                    'content': result['content'],
                    'metadata': result['metadata']
                })
            
            return context_chunks
        except Exception as e:
            logger.error(f"Error retrieving context: {e}")
            return []
    
    def add_documents(self, documents: List[Dict[str, Any]], tenant_id: str, course_id: str):
        """Add documents to the vector store."""
        try:
            return self.vector_service.add_documents(documents, tenant_id, course_id)
        except Exception as e:
            logger.error(f"Error adding documents: {e}")
            return False
