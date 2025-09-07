"""Content management API endpoints."""

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
from app.api.dependencies import get_current_user, get_db
from app.models.content import Course, Document, DocumentChunk
from app.services.rag_orchestrator import RAGOrchestrator
import uuid
import logging
import os
from datetime import datetime

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/content", tags=["content"])


class CourseRequest(BaseModel):
    """Request model for course creation."""
    name: str
    description: Optional[str] = None


class CourseResponse(BaseModel):
    """Response model for course."""
    id: str
    name: str
    description: Optional[str]
    created_at: str
    is_active: bool


class DocumentResponse(BaseModel):
    """Response model for document."""
    id: str
    title: str
    content_type: str
    file_size: int
    is_processed: bool
    created_at: str


@router.post("/courses")
def create_course(
    request: CourseRequest,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> CourseResponse:
    """Create a new course."""
    
    course = Course(
        name=request.name,
        description=request.description,
        tenant_id=current_user["tenant_id"],
        created_by=current_user["user_id"]
    )
    
    db.add(course)
    db.commit()
    db.refresh(course)
    
    return CourseResponse(
        id=str(course.id),
        name=course.name,
        description=course.description,
        created_at=course.created_at.isoformat(),
        is_active=course.is_active
    )


@router.get("/courses")
def get_courses(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> List[CourseResponse]:
    """Get all courses for the current tenant."""
    
    courses = db.query(Course).filter(
        Course.tenant_id == current_user["tenant_id"],
        Course.is_active == True
    ).order_by(Course.created_at.desc()).all()
    
    return [
        CourseResponse(
            id=str(course.id),
            name=course.name,
            description=course.description,
            created_at=course.created_at.isoformat(),
            is_active=course.is_active
        )
        for course in courses
    ]


@router.get("/courses/{course_id}")
async def get_course(
    course_id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> CourseResponse:
    """Get a specific course."""
    
    course = db.query(Course).filter(
        Course.id == course_id,
        Course.tenant_id == current_user["tenant_id"]
    ).first()
    
    if not course:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Course not found"
        )
    
    return CourseResponse(
        id=str(course.id),
        name=course.name,
        description=course.description,
        created_at=course.created_at.isoformat(),
        is_active=course.is_active
    )


@router.post("/courses/{course_id}/documents")
async def upload_document(
    course_id: str,
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> DocumentResponse:
    """Upload a document to a course."""
    
    # Verify course exists and user has access
    course = db.query(Course).filter(
        Course.id == course_id,
        Course.tenant_id == current_user["tenant_id"]
    ).first()
    
    if not course:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Course not found"
        )
    
    # Validate file type
    allowed_types = ["application/pdf", "text/plain", "application/vnd.openxmlformats-officedocument.wordprocessingml.document"]
    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unsupported file type"
        )
    
    # Read file content
    content = await file.read()
    file_size = len(content)
    
    # Generate file path (in production, this would be S3 or similar)
    file_path = f"uploads/{current_user['tenant_id']}/{course_id}/{uuid.uuid4()}_{file.filename}"
    
    # Create document record
    document = Document(
        title=file.filename,
        content_type=file.content_type,
        file_path=file_path,
        file_size=file_size,
        course_id=course_id,
        uploaded_by=current_user["user_id"],
        metadata={"original_filename": file.filename}
    )
    
    db.add(document)
    db.commit()
    db.refresh(document)
    
    # TODO: In production, save file to S3 and process asynchronously
    # For now, we'll just mark it as processed
    document.is_processed = True
    db.commit()
    
    return DocumentResponse(
        id=str(document.id),
        title=document.title,
        content_type=document.content_type,
        file_size=document.file_size,
        is_processed=document.is_processed,
        created_at=document.created_at.isoformat()
    )


@router.get("/courses/{course_id}/documents")
async def get_documents(
    course_id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> List[DocumentResponse]:
    """Get all documents for a course."""
    
    # Verify course access
    course = db.query(Course).filter(
        Course.id == course_id,
        Course.tenant_id == current_user["tenant_id"]
    ).first()
    
    if not course:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Course not found"
        )
    
    documents = db.query(Document).filter(
        Document.course_id == course_id
    ).order_by(Document.created_at.desc()).all()
    
    return [
        DocumentResponse(
            id=str(doc.id),
            title=doc.title,
            content_type=doc.content_type,
            file_size=doc.file_size,
            is_processed=doc.is_processed,
            created_at=doc.created_at.isoformat()
        )
        for doc in documents
    ]


@router.delete("/documents/{document_id}")
async def delete_document(
    document_id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a document."""
    
    document = db.query(Document).join(Course).filter(
        Document.id == document_id,
        Course.tenant_id == current_user["tenant_id"]
    ).first()
    
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )
    
    # TODO: Delete from S3 and vector store
    db.delete(document)
    db.commit()
    
    return {"message": "Document deleted successfully"}
