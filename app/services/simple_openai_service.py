"""Simplified OpenAI service for Vercel."""

import logging
from openai import OpenAI

logger = logging.getLogger(__name__)


class SimpleOpenAIService:
    """Simplified OpenAI service for Vercel deployment."""
    
    def __init__(self, api_key: str, model: str = "gpt-4"):
        self.client = OpenAI(api_key=api_key)
        self.model = model
    
    async def generate_simple_response(self, prompt: str) -> str:
        """Generate a simple text response."""
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a helpful tutoring assistant."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=500,
                temperature=0.7
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            logger.error(f"Error generating response: {e}")
            return "I apologize, but I'm having trouble generating a response right now."
    
    async def generate_rag_response_stream(self, question: str, context_documents: list, conversation_history: list = None):
        """Generate a streaming RAG response."""
        try:
            # Create context from documents
            context = "\n".join([doc.get('content', '') for doc in context_documents])
            
            # Create conversation history
            history_text = ""
            if conversation_history:
                for msg in conversation_history:
                    history_text += f"{msg['role']}: {msg['content']}\n"
            
            # Create prompt
            prompt = f"""
            Context: {context}
            
            Conversation History:
            {history_text}
            
            Question: {question}
            
            Please provide a helpful and educational response based on the context.
            """
            
            # Generate response
            response = await self.generate_simple_response(prompt)
            
            # Yield response in chunks
            for i in range(0, len(response), 50):
                yield response[i:i+50]
                
        except Exception as e:
            logger.error(f"Error generating RAG response: {e}")
            yield "I apologize, but I'm having trouble generating a response right now."
