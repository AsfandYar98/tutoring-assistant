"""Simplified RAG orchestrator."""

import json
import logging
from typing import List, Dict, Any, AsyncGenerator
from app.services.simple_vector_service import SimpleVectorService
from app.services.simple_openai_service import SimpleOpenAIService
from app.core.config import settings

logger = logging.getLogger(__name__)


class SimpleRAGOrchestrator:
    """Simplified RAG orchestrator."""
    
    def __init__(self):
        self.vector_service = SimpleVectorService(settings.openai_api_key)
        self.llm_service = SimpleOpenAIService(
            api_key=settings.openai_api_key,
            model="gpt-4"
        )
    
    async def process_chat_query(self,
                                query: str,
                                tenant_id: str,
                                course_id: str,
                                chat_history: List[Dict[str, str]] = None,
                                db = None) -> AsyncGenerator[str, None]:
        """Process a chat query using simple RAG."""
        try:
            # Get simple context
            context_chunks = self._get_simple_context(query, tenant_id, course_id)
            
            # Generate simple response
            response = await self._generate_simple_response(query, context_chunks, chat_history)
            
            # Yield response in chunks
            for i in range(0, len(response), 50):
                chunk = response[i:i+50]
                yield f"data: {json.dumps({'content': chunk})}\n\n"
            
            yield f"data: {json.dumps({'done': True})}\n\n"
            
        except Exception as e:
            logger.error(f"Error in RAG orchestrator: {e}")
            yield f"data: {json.dumps({'error': str(e)})}\n\n"
    
    def _get_simple_context(self, query: str, tenant_id: str, course_id: str) -> List[Dict[str, Any]]:
        """Get simple context without embeddings."""
        try:
            results = self.vector_service.search_documents(
                query=query,
                tenant_id=tenant_id,
                course_id=course_id,
                n_results=3
            )
            return results
        except Exception as e:
            logger.error(f"Error getting context: {e}")
            return []
    
    async def _generate_simple_response(self, query: str, context: List[Dict[str, Any]], chat_history: List[Dict[str, str]] = None) -> str:
        """Generate a simple response."""
        try:
            # Create context string
            context_text = "\n".join([doc.get('content', '') for doc in context])
            
            # Simple prompt
            prompt = f"""
            You are a helpful tutoring assistant. Answer the student's question based on the provided context.
            
            Context: {context_text}
            
            Question: {query}
            
            Please provide a helpful and educational response.
            """
            
            # Generate response using OpenAI
            response = await self.llm_service.generate_simple_response(prompt)
            return response
            
        except Exception as e:
            logger.error(f"Error generating response: {e}")
            return "I apologize, but I'm having trouble generating a response right now. Please try again."
    
    def add_documents(self, documents: List[Dict[str, Any]], tenant_id: str, course_id: str):
        """Add documents to the store."""
        try:
            return self.vector_service.add_documents(documents, tenant_id, course_id)
        except Exception as e:
            logger.error(f"Error adding documents: {e}")
            return False