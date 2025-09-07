"""Quiz API endpoints."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
from app.api.dependencies import get_current_user, get_db
from app.services.rag_orchestrator import RAGOrchestrator
from app.models.quiz import Quiz, QuizQuestion, QuizAttempt, QuizAnswer
import uuid
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/quiz", tags=["quiz"])


class QuizRequest(BaseModel):
    """Request model for quiz generation."""
    topic: str
    difficulty: str = "intermediate"
    num_questions: int = 5
    course_id: str


class QuizResponse(BaseModel):
    """Response model for quiz."""
    id: str
    title: str
    description: str
    difficulty: str
    questions: List[dict]
    created_at: str


class QuizAttemptRequest(BaseModel):
    """Request model for quiz attempt."""
    quiz_id: str
    answers: List[dict]  # [{"question_id": "uuid", "answer": "text"}]


class QuizAttemptResponse(BaseModel):
    """Response model for quiz attempt."""
    id: str
    quiz_id: str
    score: float
    total_points: int
    is_completed: bool
    answers: List[dict]


@router.post("/generate")
async def generate_quiz(
    request: QuizRequest,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> QuizResponse:
    """Generate a new quiz based on topic and difficulty."""
    
    # Initialize RAG orchestrator
    rag = RAGOrchestrator()
    
    # Generate quiz with context
    quiz_data = await rag.generate_quiz_with_context(
        topic=request.topic,
        difficulty=request.difficulty,
        num_questions=request.num_questions,
        tenant_id=current_user["tenant_id"],
        course_id=request.course_id
    )
    
    # Create quiz record
    quiz = Quiz(
        title=quiz_data.get("title", f"Quiz about {request.topic}"),
        description=quiz_data.get("description", ""),
        course_id=request.course_id,
        created_by=current_user["user_id"],
        difficulty_level=request.difficulty
    )
    
    db.add(quiz)
    db.commit()
    db.refresh(quiz)
    
    # Create question records
    questions = []
    for i, question_data in enumerate(quiz_data.get("questions", [])):
        question = QuizQuestion(
            quiz_id=quiz.id,
            question_text=question_data["question"],
            question_type="multiple_choice",
            options=question_data.get("options", []),
            correct_answer=question_data["correct_answer"],
            explanation=question_data.get("explanation", ""),
            points=1,
            order_index=i
        )
        db.add(question)
        questions.append(question)
    
    db.commit()
    
    # Format response
    formatted_questions = []
    for question in questions:
        formatted_questions.append({
            "id": str(question.id),
            "question": question.question_text,
            "options": question.options,
            "points": question.points
        })
    
    return QuizResponse(
        id=str(quiz.id),
        title=quiz.title,
        description=quiz.description,
        difficulty=quiz.difficulty_level,
        questions=formatted_questions,
        created_at=quiz.created_at.isoformat()
    )


@router.get("/{quiz_id}")
async def get_quiz(
    quiz_id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> QuizResponse:
    """Get a specific quiz."""
    
    quiz = db.query(Quiz).filter(
        Quiz.id == quiz_id,
        Quiz.is_active == True
    ).first()
    
    if not quiz:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Quiz not found"
        )
    
    # Get questions
    questions = db.query(QuizQuestion).filter(
        QuizQuestion.quiz_id == quiz_id
    ).order_by(QuizQuestion.order_index).all()
    
    formatted_questions = []
    for question in questions:
        formatted_questions.append({
            "id": str(question.id),
            "question": question.question_text,
            "options": question.options,
            "points": question.points
        })
    
    return QuizResponse(
        id=str(quiz.id),
        title=quiz.title,
        description=quiz.description,
        difficulty=quiz.difficulty_level,
        questions=formatted_questions,
        created_at=quiz.created_at.isoformat()
    )


@router.post("/attempts")
async def submit_quiz_attempt(
    request: QuizAttemptRequest,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> QuizAttemptResponse:
    """Submit a quiz attempt."""
    
    # Get quiz
    quiz = db.query(Quiz).filter(
        Quiz.id == request.quiz_id,
        Quiz.is_active == True
    ).first()
    
    if not quiz:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Quiz not found"
        )
    
    # Create attempt
    attempt = QuizAttempt(
        quiz_id=request.quiz_id,
        user_id=current_user["user_id"]
    )
    db.add(attempt)
    db.commit()
    db.refresh(attempt)
    
    # Get questions for scoring
    questions = db.query(QuizQuestion).filter(
        QuizQuestion.quiz_id == request.quiz_id
    ).all()
    
    question_map = {str(q.id): q for q in questions}
    total_points = sum(q.points for q in questions)
    earned_points = 0
    
    # Process answers
    answers = []
    for answer_data in request.answers:
        question_id = answer_data["question_id"]
        answer_text = answer_data["answer"]
        
        if question_id not in question_map:
            continue
        
        question = question_map[question_id]
        is_correct = str(answer_text) == str(question.correct_answer)
        
        if is_correct:
            earned_points += question.points
        
        answer = QuizAnswer(
            attempt_id=attempt.id,
            question_id=question_id,
            answer_text=answer_text,
            is_correct=is_correct,
            points_earned=question.points if is_correct else 0
        )
        db.add(answer)
        answers.append({
            "question_id": question_id,
            "answer": answer_text,
            "is_correct": is_correct,
            "points_earned": answer.points_earned
        })
    
    # Update attempt
    attempt.score = earned_points
    attempt.total_points = total_points
    attempt.is_completed = True
    
    db.commit()
    
    return QuizAttemptResponse(
        id=str(attempt.id),
        quiz_id=str(attempt.quiz_id),
        score=attempt.score,
        total_points=attempt.total_points,
        is_completed=attempt.is_completed,
        answers=answers
    )


@router.get("/attempts/{attempt_id}")
async def get_quiz_attempt(
    attempt_id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> QuizAttemptResponse:
    """Get a specific quiz attempt with detailed results."""
    
    attempt = db.query(QuizAttempt).filter(
        QuizAttempt.id == attempt_id,
        QuizAttempt.user_id == current_user["user_id"]
    ).first()
    
    if not attempt:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Quiz attempt not found"
        )
    
    # Get answers
    answers = db.query(QuizAnswer).filter(
        QuizAnswer.attempt_id == attempt_id
    ).all()
    
    formatted_answers = []
    for answer in answers:
        formatted_answers.append({
            "question_id": str(answer.question_id),
            "answer": answer.answer_text,
            "is_correct": answer.is_correct,
            "points_earned": answer.points_earned
        })
    
    return QuizAttemptResponse(
        id=str(attempt.id),
        quiz_id=str(attempt.quiz_id),
        score=attempt.score,
        total_points=attempt.total_points,
        is_completed=attempt.is_completed,
        answers=formatted_answers
    )
