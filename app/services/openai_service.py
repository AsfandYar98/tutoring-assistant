"""OpenAI LLM service for production use."""

from openai import OpenAI
from typing import List, Dict, Any, Optional
import logging
import json

logger = logging.getLogger(__name__)


class OpenAIService:
    """OpenAI LLM service for generating responses and embeddings."""
    
    def __init__(self, api_key: str, model: str = "gpt-4"):
        """Initialize OpenAI service."""
        self.api_key = api_key
        self.model = model
        
        # Initialize OpenAI client
        self.client = OpenAI(api_key=api_key)
        
        logger.info(f"OpenAI service initialized with model: {model}")
    
    def generate_response(
        self, 
        messages: List[Dict[str, str]], 
        max_tokens: int = 1000,
        temperature: float = 0.7,
        stream: bool = False
    ) -> str:
        """Generate a response using OpenAI API."""
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature,
                stream=stream
            )
            
            if stream:
                # Handle streaming response
                full_response = ""
                for chunk in response:
                    if chunk.choices[0].delta.content:
                        full_response += chunk.choices[0].delta.content
                return full_response
            else:
                return response.choices[0].message.content
                
        except Exception as e:
            logger.error(f"Failed to generate response: {e}")
            raise
    
    def generate_quiz_questions(
        self, 
        content: str, 
        num_questions: int = 5,
        difficulty: str = "medium"
    ) -> List[Dict[str, Any]]:
        """Generate quiz questions from content."""
        try:
            prompt = f"""
            Generate {num_questions} {difficulty} difficulty quiz questions based on the following content:
            
            Content: {content}
            
            Return the questions in JSON format with the following structure:
            [
                {{
                    "question": "Question text here",
                    "options": ["Option A", "Option B", "Option C", "Option D"],
                    "correct_answer": 0,
                    "explanation": "Explanation of the correct answer"
                }}
            ]
            """
            
            messages = [
                {"role": "system", "content": "You are an expert quiz generator. Generate high-quality educational quiz questions."},
                {"role": "user", "content": prompt}
            ]
            
            response = self.generate_response(messages, max_tokens=2000)
            
            # Parse JSON response
            try:
                questions = json.loads(response)
                return questions
            except json.JSONDecodeError:
                # Fallback if JSON parsing fails
                logger.warning("Failed to parse quiz questions as JSON, returning fallback")
                return self._generate_fallback_questions(content, num_questions)
                
        except Exception as e:
            logger.error(f"Failed to generate quiz questions: {e}")
            raise
    
    def _generate_fallback_questions(self, content: str, num_questions: int) -> List[Dict[str, Any]]:
        """Generate fallback questions if JSON parsing fails."""
        return [
            {
                "question": f"Based on the content, what is the main topic discussed?",
                "options": ["Topic A", "Topic B", "Topic C", "Topic D"],
                "correct_answer": 0,
                "explanation": "This is a fallback question generated when the main quiz generation failed."
            }
        ]
    
    def generate_rag_response(
        self, 
        question: str, 
        context_documents: List[Dict[str, Any]],
        conversation_history: List[Dict[str, str]] = None
    ) -> str:
        """Generate a RAG response using context documents."""
        try:
            # Prepare context from documents
            context = "\n\n".join([
                f"Document {i+1}: {doc.get('content', '')}"
                for i, doc in enumerate(context_documents)
            ])
            
            # Prepare conversation history
            messages = [
                {
                    "role": "system", 
                    "content": f"""You are a helpful tutoring assistant. Use the following context to answer questions accurately and helpfully. If you don't know the answer based on the context, say so.

Context:
{context}"""
                }
            ]
            
            # Add conversation history
            if conversation_history:
                messages.extend(conversation_history)
            
            # Add current question
            messages.append({"role": "user", "content": question})
            
            response = self.generate_response(messages, max_tokens=1500)
            return response
            
        except Exception as e:
            logger.error(f"Failed to generate RAG response: {e}")
            raise
    
    def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for texts using OpenAI."""
        try:
            response = self.client.embeddings.create(
                model="text-embedding-ada-002",
                input=texts
            )
            
            embeddings = [data.embedding for data in response.data]
            return embeddings
            
        except Exception as e:
            logger.error(f"Failed to generate embeddings: {e}")
            raise
    
    def health_check(self) -> Dict[str, Any]:
        """Check if OpenAI service is healthy."""
        try:
            # Test with a simple request
            test_response = self.generate_response(
                [{"role": "user", "content": "Hello"}],
                max_tokens=10
            )
            
            return {
                "status": "healthy",
                "model": self.model,
                "test_response": test_response[:50] + "..." if len(test_response) > 50 else test_response
            }
            
        except Exception as e:
            logger.error(f"OpenAI health check failed: {e}")
            return {
                "status": "unhealthy",
                "error": str(e)
            }
