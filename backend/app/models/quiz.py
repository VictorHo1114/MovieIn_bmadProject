"""
Gamification - Quiz Models
"""
from datetime import datetime
from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    Date,
    Boolean,
    TIMESTAMP,
    ForeignKey,
    CheckConstraint,
    UniqueConstraint,
    text
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship
from .base import Base


class DailyQuiz(Base):
    """Daily Quiz Table"""
    __tablename__ = "daily_quiz"
    
    id = Column(Integer, primary_key=True)
    date = Column(Date, nullable=False, index=True)
    sequence_number = Column(Integer, nullable=False, server_default=text("1"))
    question = Column(Text, nullable=False)
    options = Column(JSONB, nullable=False, comment="Array of 4 options")
    correct_answer = Column(Integer, nullable=False, comment="Index 0-3 of correct option")
    explanation = Column(Text, nullable=True, comment="Answer explanation")
    difficulty = Column(String(20), nullable=False, server_default="medium")
    category = Column(String(50), nullable=True)
    movie_reference = Column(JSONB, nullable=True, comment="Related movie info")
    created_at = Column(TIMESTAMP, server_default=text("NOW()"), nullable=False)
    
    __table_args__ = (
        CheckConstraint("correct_answer >= 0 AND correct_answer <= 3", name="valid_answer"),
        CheckConstraint("difficulty IN ('easy', 'medium', 'hard')", name="valid_difficulty"),
        UniqueConstraint("date", "sequence_number", name="unique_quiz_date_sequence"),
    )
    
    attempts = relationship("QuizAttempt", back_populates="quiz", cascade="all, delete-orphan")


class QuizAttempt(Base):
    """Quiz Attempt Table"""
    __tablename__ = "quiz_attempts"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False)
    quiz_id = Column(Integer, ForeignKey("daily_quiz.id", ondelete="CASCADE"), nullable=False)
    user_answer = Column(Integer, nullable=True, comment="User selected option (0-3), NULL if timeout")
    is_correct = Column(Boolean, nullable=False)
    points_earned = Column(Integer, nullable=False, server_default="0")
    time_spent = Column(Integer, nullable=True, comment="Time spent in seconds")
    answered_at = Column(TIMESTAMP, server_default=text("NOW()"), nullable=False)
    
    __table_args__ = (
        UniqueConstraint("user_id", "quiz_id", name="unique_user_quiz_attempt"),
        CheckConstraint("user_answer >= 0 AND user_answer <= 3 OR user_answer IS NULL", name="valid_user_answer"),
    )
    
    quiz = relationship("DailyQuiz", back_populates="attempts")
    user = relationship("User", back_populates="quiz_attempts")
