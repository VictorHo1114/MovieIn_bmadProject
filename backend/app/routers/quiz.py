"""
Quiz API Router
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from uuid import UUID

from db.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.schemas.quiz import (
    QuizAttemptCreate,
    QuizSubmitResponse,
    TodayQuizResponse,
    QuizHistoryResponse
)
from app.services.quiz_service import QuizService

router = APIRouter(
    tags=["quiz"]
)


@router.get("/today", response_model=TodayQuizResponse)
async def get_today_quiz(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get today's quiz"""
    try:
        return QuizService.get_today_quiz(db, current_user.user_id)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get today's quiz: {str(e)}"
        )


@router.post("/submit", response_model=QuizSubmitResponse)
async def submit_answer(
    submission: QuizAttemptCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Submit quiz answer"""
    try:
        return QuizService.submit_answer(db, current_user.user_id, submission)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to submit answer: {str(e)}"
        )


@router.get("/history", response_model=QuizHistoryResponse)
async def get_quiz_history(
    limit: int = 30,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get quiz history"""
    try:
        return QuizService.get_quiz_history(db, current_user.user_id, limit)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get quiz history: {str(e)}"
        )
