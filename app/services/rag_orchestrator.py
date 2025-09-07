"""RAG (Retrieval-Augmented Generation) orchestrator service."""

import json
from typing import List, Dict, Any, Optional, AsyncGenerator
from sqlalchemy.orm import Session
from app.services.simple_chromadb_service import SimpleChromaDBService
from app.services.openai_service import OpenAIService
from app.models.content import DocumentChunk
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)


class RAGOrchestrator:
    """Orchestrates the RAG pipeline for chat and quiz generation."""
    
    def __init__(self):
        # Initialize services with configuration
        self.vector_store = SimpleChromaDBService(
            host=settings.chroma_host,
            port=settings.chroma_port,
            api_key=settings.chroma_api_key
        )
        self.llm_service = OpenAIService(
            api_key=settings.openai_api_key,
            model="gpt-4"
        )
    
    async def process_chat_query(self, 
                               query: str,
                               tenant_id: str,
                               course_id: str,
                               chat_history: List[Dict[str, str]] = None,
                               db: Session = None) -> AsyncGenerator[str, None]:
        """Process a chat query using RAG."""
        
        try:
            # Retrieve relevant context
            context_chunks = self._retrieve_context(query, tenant_id, course_id)
            
            # Generate RAG response
            response = self.llm_service.generate_rag_response(
                question=query,
                context_documents=context_chunks,
                conversation_history=chat_history
            )
            
            # Stream the response word by word
            words = response.split()
            for word in words:
                yield word + " "
                
        except Exception as e:
            logger.error(f"Error processing chat query: {e}")
            yield "I apologize, but I encountered an error processing your query. Please try again."
    
    async def generate_quiz_with_context(self,
                                       topic: str,
                                       difficulty: str,
                                       num_questions: int,
                                       tenant_id: str,
                                       course_id: str) -> Dict[str, Any]:
        """Generate a quiz with relevant context from the course."""
        
        try:
            # Retrieve relevant context for the topic
            context_chunks = self._retrieve_context(topic, tenant_id, course_id, top_k=10)
            
            # Combine context into a single text
            context_text = "\n\n".join([
                chunk.get('content', '') for chunk in context_chunks
            ])
            
            # Generate quiz using LLM with context
            quiz_questions = self.llm_service.generate_quiz_questions(
                content=context_text or topic,
                num_questions=num_questions,
                difficulty=difficulty
            )
            
            return {
                "questions": quiz_questions,
                "topic": topic,
                "difficulty": difficulty,
                "context_used": len(context_chunks),
                "metadata": {
                    "tenant_id": tenant_id,
                    "course_id": course_id
                }
            }
            
        except Exception as e:
            logger.error(f"Error generating quiz: {e}")
            return {
                "questions": [],
                "topic": topic,
                "difficulty": difficulty,
                "error": str(e)
            }
    
    def _retrieve_context(self, 
                         query: str, 
                         tenant_id: str, 
                         course_id: str,
                         top_k: int = 5) -> List[Dict[str, Any]]:
        """Retrieve relevant context chunks for a query."""
        
        try:
            # Use vector search to find similar chunks
            similar_chunks = self.vector_store.search_documents(
                query=query,
                n_results=top_k,
                filter_metadata={"tenant_id": tenant_id, "course_id": course_id}
            )
            
            # Format chunks for LLM consumption
            formatted_chunks = []
            for chunk in similar_chunks:
                formatted_chunks.append({
                    "content": chunk["content"],
                    "metadata": chunk["metadata"],
                    "relevance_score": 1 - chunk.get("distance", 0)  # Convert distance to relevance
                })
            
            return formatted_chunks
            
        except Exception as e:
            logger.error(f"Error retrieving context: {e}")
            return []
    
    def _format_citations(self, chunks: List[Dict[str, Any]]) -> str:
        """Format chunks as citations for the response."""
        if not chunks:
            return ""
            
        citations = []
        for i, chunk in enumerate(chunks, 1):
            metadata = chunk.get("metadata", {})
            title = metadata.get("title", "Unknown source")
            section = metadata.get("section", "")
            page = metadata.get("page", "")
            
            citation = f"[{i}] {title}"
            if section:
                citation += f", {section}"
            if page:
                citation += f" (page {page})"
            
            citations.append(citation)
        
        return "\n".join(citations)
    
    async def process_document_upload(self,
                                    document_id: str,
                                    chunks: List[Dict[str, Any]],
                                    tenant_id: str,
                                    course_id: str) -> bool:
        """Process uploaded document chunks and add to vector store."""
        
        try:
            # Format chunks for ChromaDB
            formatted_chunks = []
            for chunk in chunks:
                formatted_chunks.append({
                    "content": chunk.get("content", ""),
                    "document_id": document_id,
                    "chunk_index": chunk.get("chunk_index", 0),
                    "course_id": course_id,
                    "tenant_id": tenant_id,
                    "title": chunk.get("title", ""),
                    "content_type": chunk.get("content_type", "text")
                })
            
            # Add chunks to vector store
            embedding_ids = self.vector_store.add_documents(formatted_chunks)
            
            logger.info(f"Successfully processed {len(chunks)} chunks for document {document_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error processing document upload: {e}")
            return False