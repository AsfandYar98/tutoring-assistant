"""Simplified LLM service for local development."""

import json
from typing import List, Dict, Any, Optional, AsyncGenerator
import httpx
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)


class SimpleLLMService:
    """Simplified LLM service for local development without vLLM."""
    
    def __init__(self):
        self.openai_api_key = settings.openai_api_key
        
    async def generate_chat_response(self, 
                                   messages: List[Dict[str, str]], 
                                   context_chunks: List[Dict[str, Any]] = None,
                                   temperature: float = 0.7) -> AsyncGenerator[str, None]:
        """Generate a streaming chat response using OpenAI API."""
        
        # Build system prompt
        system_prompt = self._build_tutor_system_prompt()
        
        # Add context if provided
        if context_chunks:
            context_text = self._format_context_chunks(context_chunks)
            system_prompt += f"\n\nRelevant context:\n{context_text}"
        
        # Prepare messages
        formatted_messages = [{"role": "system", "content": system_prompt}] + messages
        
        # Generate response using OpenAI API
        if self.openai_api_key:
            async with httpx.AsyncClient(timeout=30.0) as client:
                try:
                    async with client.stream(
                        "POST",
                        "https://api.openai.com/v1/chat/completions",
                        json={
                            "model": "gpt-3.5-turbo",
                            "messages": formatted_messages,
                            "temperature": temperature,
                            "stream": True,
                            "max_tokens": 1024
                        },
                        headers={"Authorization": f"Bearer {self.openai_api_key}"}
                    ) as response:
                        response.raise_for_status()
                        
                        async for line in response.aiter_lines():
                            if line.startswith("data: "):
                                data = line[6:]
                                if data.strip() == "[DONE]":
                                    break
                                try:
                                    chunk = json.loads(data)
                                    if "choices" in chunk and len(chunk["choices"]) > 0:
                                        delta = chunk["choices"][0].get("delta", {})
                                        if "content" in delta:
                                            yield delta["content"]
                                except json.JSONDecodeError:
                                    continue
                except Exception as e:
                    logger.error(f"Error generating chat response: {e}")
                    yield "I apologize, but I'm having trouble generating a response right now. Please try again."
        else:
            # Fallback response when no API key is provided
            yield "Hello! I'm your AI tutoring assistant. To enable full functionality, please configure your OpenAI API key in the environment variables."
    
    async def generate_quiz(self, 
                          topic: str, 
                          difficulty: str, 
                          num_questions: int = 5,
                          context_chunks: List[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Generate a quiz based on the given topic and difficulty."""
        
        # Build quiz generation prompt
        prompt = self._build_quiz_generation_prompt(topic, difficulty, num_questions, context_chunks)
        
        messages = [
            {"role": "system", "content": "You are an expert quiz generator. Generate structured quizzes in valid JSON format."},
            {"role": "user", "content": prompt}
        ]
        
        if self.openai_api_key:
            async with httpx.AsyncClient(timeout=30.0) as client:
                try:
                    response = await client.post(
                        "https://api.openai.com/v1/chat/completions",
                        json={
                            "model": "gpt-3.5-turbo",
                            "messages": messages,
                            "temperature": 0.3,
                            "max_tokens": 2048
                        },
                        headers={"Authorization": f"Bearer {self.openai_api_key}"}
                    )
                    response.raise_for_status()
                    
                    result = response.json()
                    content = result["choices"][0]["message"]["content"]
                    
                    # Parse JSON response
                    try:
                        quiz_data = json.loads(content)
                        return quiz_data
                    except json.JSONDecodeError:
                        # Fallback if JSON parsing fails
                        return self._create_fallback_quiz(topic, num_questions)
                        
                except Exception as e:
                    logger.error(f"Error generating quiz: {e}")
                    return self._create_fallback_quiz(topic, num_questions)
        else:
            return self._create_fallback_quiz(topic, num_questions)
    
    def _build_tutor_system_prompt(self) -> str:
        """Build the system prompt for tutoring responses."""
        return """You are an intelligent and helpful tutoring assistant. Your role is to:

1. Provide clear, educational explanations that help students learn
2. Ask clarifying questions when needed to better understand the student's needs
3. Break down complex topics into understandable parts
4. Encourage learning and provide positive reinforcement
5. Cite sources when referencing specific information
6. Adapt your explanations to the student's apparent level of understanding

Guidelines:
- Be encouraging and supportive
- Use examples and analogies when helpful
- Ask follow-up questions to check understanding
- If you're unsure about something, say so
- Keep responses concise but comprehensive
- Use a friendly, professional tone"""
    
    def _format_context_chunks(self, chunks: List[Dict[str, Any]]) -> str:
        """Format context chunks for inclusion in the prompt."""
        formatted_chunks = []
        for i, chunk in enumerate(chunks, 1):
            source = chunk.get("metadata", {}).get("title", "Unknown source")
            content = chunk["content"]
            formatted_chunks.append(f"[Source {i}: {source}]\n{content}")
        
        return "\n\n".join(formatted_chunks)
    
    def _build_quiz_generation_prompt(self, 
                                    topic: str, 
                                    difficulty: str, 
                                    num_questions: int,
                                    context_chunks: List[Dict[str, Any]] = None) -> str:
        """Build the prompt for quiz generation."""
        
        context_text = ""
        if context_chunks:
            context_text = f"\n\nUse this context to create relevant questions:\n{self._format_context_chunks(context_chunks)}"
        
        return f"""Create a {difficulty} level quiz about "{topic}" with {num_questions} questions.

Requirements:
- Each question should have 4 multiple choice options
- Include a clear explanation for each answer
- Vary the question types (conceptual, application, analysis)
- Ensure questions test understanding, not just memorization
- Make the quiz engaging and educational

{context_text}

Return the quiz in this JSON format:
{{
    "title": "Quiz Title",
    "description": "Brief description",
    "difficulty": "{difficulty}",
    "questions": [
        {{
            "question": "Question text",
            "options": ["A", "B", "C", "D"],
            "correct_answer": 0,
            "explanation": "Why this answer is correct"
        }}
    ]
}}"""
    
    def _create_fallback_quiz(self, topic: str, num_questions: int) -> Dict[str, Any]:
        """Create a simple fallback quiz if LLM generation fails."""
        return {
            "title": f"Quiz about {topic}",
            "description": "A basic quiz to test your knowledge",
            "difficulty": "intermediate",
            "questions": [
                {
                    "question": f"What is the main concept of {topic}?",
                    "options": ["Option A", "Option B", "Option C", "Option D"],
                    "correct_answer": 0,
                    "explanation": "This is the correct answer because..."
                }
            ]
        }
