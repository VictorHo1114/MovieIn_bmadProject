"""
Quiz Schemas
"""
from datetime import datetime, date
from typing import Optional, List
from pydantic import BaseModel, Field
from uuid import UUID


class MovieReference(BaseModel):
    """Movie reference info"""
    title: str
    year: int
    poster_url: Optional[str] = None


class DailyQuizBase(BaseModel):
    """Base quiz schema"""
    question: str = Field(..., description="Question text")
    options: List[str] = Field(..., description="4 options", min_length=4, max_length=4)
    difficulty: str = Field(default="medium", description="Difficulty level")
    category: Optional[str] = Field(None, description="Category")
    movie_reference: Optional[MovieReference] = Field(None, description="Related movie")


class DailyQuizPublic(DailyQuizBase):
    """Public quiz (without answer)"""
    id: int
    date: date
    
    class Config:
        from_attributes = True


class DailyQuizWithAnswer(DailyQuizPublic):
    """Quiz with answer (shown after submission)"""
    correct_answer: int = Field(..., description="Correct answer index (0-3)")
    explanation: Optional[str] = Field(None, description="Answer explanation")
    
    class Config:
        from_attributes = True


class DailyQuizCreate(DailyQuizBase):
    """Create quiz"""
    date: date
    correct_answer: int = Field(..., ge=0, le=3, description="Correct answer index")
    explanation: Optional[str] = None


class QuizAttemptCreate(BaseModel):
    """Submit answer"""
    quiz_id: int
    answer: Optional[int] = Field(None, ge=0, le=3, description="Selected answer index (NULL=timeout)")
    time_spent: int = Field(..., ge=0, le=30, description="Time spent in seconds")
    practice_mode: bool = Field(default=False, description="Practice mode (no points, repeatable)")


class QuizAttemptResponse(BaseModel):
    """Quiz attempt result"""
    id: int
    quiz_id: int
    user_answer: Optional[int]
    is_correct: bool
    points_earned: int
    time_spent: int
    answered_at: datetime
    
    class Config:
        from_attributes = True


class UserStats(BaseModel):
    """User statistics"""
    total_points: int
    previous_points: int
    level: int
    previous_level: int
    level_up: bool
    global_rank: Optional[int] = None
    friend_rank: Optional[int] = None


class QuizSubmitResponse(BaseModel):
    """Submit answer response"""
    is_correct: bool
    correct_answer: int
    points_earned: int
    explanation: Optional[str]
    user_stats: UserStats
    movie_reference: Optional[MovieReference] = None


class TodayQuizResponse(BaseModel):
    """Today's quiz response"""
    quiz: Optional[DailyQuizPublic]
    user_attempt: Optional[QuizAttemptResponse]
    has_answered: bool
    time_until_next: Optional[str] = Field(None, description="Time until next quiz (HH:MM:SS)")
    daily_attempts: int = Field(default=0, description="Number of quizzes answered today")
    daily_limit: int = Field(default=3, description="Daily quiz limit")
    remaining_attempts: int = Field(default=3, description="Remaining attempts today")


class AllTodayQuizzesResponse(BaseModel):
    """All today's quizzes response (for replay mode)"""
    quizzes: List[DailyQuizWithAnswer]  # Changed to include answers and explanations
    user_attempts: List[QuizAttemptResponse]
    daily_attempts: int
    daily_limit: int = 3
    is_first_round: bool
    time_until_next: Optional[str] = None


class QuizHistoryItem(BaseModel):
    """Quiz history item"""
    id: int
    quiz: DailyQuizWithAnswer
    user_answer: Optional[int]
    is_correct: bool
    points_earned: int
    time_spent: int
    answered_at: datetime
    
    class Config:
        from_attributes = True


class QuizHistoryStats(BaseModel):
    """Quiz statistics"""
    total_attempts: int
    correct_count: int
    accuracy_rate: float
    streak_days: int


class QuizHistoryResponse(BaseModel):
    """Quiz history response"""
    attempts: List[QuizHistoryItem]
    stats: QuizHistoryStats
