"""Chat API endpoints."""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
from app.api.dependencies import get_current_user, get_db
from app.services.rag_orchestrator import RAGOrchestrator
from app.models.chat import ChatSession, ChatMessage
import uuid
import json
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/chat", tags=["chat"])


class ChatMessageRequest(BaseModel):
    """Request model for chat messages."""
    message: str
    session_id: Optional[str] = None
    course_id: str


class ChatSessionResponse(BaseModel):
    """Response model for chat sessions."""
    id: str
    title: str
    course_id: str
    created_at: str
    is_active: bool


class ChatMessageResponse(BaseModel):
    """Response model for chat messages."""
    id: str
    role: str
    content: str
    created_at: str
    metadata: Optional[dict] = None


@router.post("/sessions")
async def create_chat_session(
    course_id: str,
    title: Optional[str] = None,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> ChatSessionResponse:
    """Create a new chat session."""
    
    session = ChatSession(
        user_id=current_user["user_id"],
        course_id=course_id,
        title=title or "New Chat Session"
    )
    
    db.add(session)
    db.commit()
    db.refresh(session)
    
    return ChatSessionResponse(
        id=str(session.id),
        title=session.title,
        course_id=str(session.course_id),
        created_at=session.created_at.isoformat(),
        is_active=session.is_active
    )


@router.get("/sessions")
async def get_chat_sessions(
    course_id: Optional[str] = None,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> List[ChatSessionResponse]:
    """Get user's chat sessions."""
    
    query = db.query(ChatSession).filter(
        ChatSession.user_id == current_user["user_id"],
        ChatSession.is_active == True
    )
    
    if course_id:
        query = query.filter(ChatSession.course_id == course_id)
    
    sessions = query.order_by(ChatSession.updated_at.desc()).all()
    
    return [
        ChatSessionResponse(
            id=str(session.id),
            title=session.title,
            course_id=str(session.course_id),
            created_at=session.created_at.isoformat(),
            is_active=session.is_active
        )
        for session in sessions
    ]


@router.get("/sessions/{session_id}/messages")
async def get_chat_messages(
    session_id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> List[ChatMessageResponse]:
    """Get messages for a chat session."""
    
    # Verify session belongs to user
    session = db.query(ChatSession).filter(
        ChatSession.id == session_id,
        ChatSession.user_id == current_user["user_id"]
    ).first()
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chat session not found"
        )
    
    messages = db.query(ChatMessage).filter(
        ChatMessage.session_id == session_id
    ).order_by(ChatMessage.created_at.asc()).all()
    
    return [
        ChatMessageResponse(
            id=str(message.id),
            role=message.role,
            content=message.content,
            created_at=message.created_at.isoformat(),
            metadata=message.metadata
        )
        for message in messages
    ]


@router.post("/sessions/{session_id}/messages")
async def send_message(
    session_id: str,
    request: ChatMessageRequest,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Send a message and get a streaming response."""
    
    # Verify session belongs to user
    session = db.query(ChatSession).filter(
        ChatSession.id == session_id,
        ChatSession.user_id == current_user["user_id"]
    ).first()
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chat session not found"
        )
    
    # Save user message
    user_message = ChatMessage(
        session_id=session_id,
        role="user",
        content=request.message
    )
    db.add(user_message)
    db.commit()
    
    # Get chat history
    chat_history = db.query(ChatMessage).filter(
        ChatMessage.session_id == session_id
    ).order_by(ChatMessage.created_at.asc()).limit(10).all()
    
    history_messages = [
        {"role": msg.role, "content": msg.content}
        for msg in chat_history
    ]
    
    # Initialize RAG orchestrator
    rag = RAGOrchestrator()
    
    async def generate_response():
        """Generate streaming response."""
        response_content = ""
        
        try:
            async for chunk in rag.process_chat_query(
                query=request.message,
                tenant_id=current_user["tenant_id"],
                course_id=str(session.course_id),
                chat_history=history_messages,
                db=db
            ):
                response_content += chunk
                yield f"data: {json.dumps({'content': chunk})}\n\n"
            
            # Save assistant response
            assistant_message = ChatMessage(
                session_id=session_id,
                role="assistant",
                content=response_content,
                metadata={"sources": []}  # TODO: Add source citations
            )
            db.add(assistant_message)
            db.commit()
            
            yield f"data: {json.dumps({'done': True})}\n\n"
            
        except Exception as e:
            logger.error(f"Error generating response: {e}")
            yield f"data: {json.dumps({'error': 'Failed to generate response'})}\n\n"
    
    return StreamingResponse(
        generate_response(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache", 
            "Connection": "keep-alive",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "Cache-Control"
        }
    )


@router.delete("/sessions/{session_id}")
async def delete_chat_session(
    session_id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a chat session."""
    
    session = db.query(ChatSession).filter(
        ChatSession.id == session_id,
        ChatSession.user_id == current_user["user_id"]
    ).first()
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chat session not found"
        )
    
    session.is_active = False
    db.commit()
    
    return {"message": "Chat session deleted successfully"}
