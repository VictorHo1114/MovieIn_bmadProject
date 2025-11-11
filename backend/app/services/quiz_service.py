"""
Quiz Service
"""
from datetime import datetime, date, timedelta, timezone
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, desc
from uuid import UUID

from app.models.quiz import DailyQuiz, QuizAttempt
from app.models.user import User
from app.schemas.quiz import (
    QuizAttemptCreate,
    QuizSubmitResponse,
    TodayQuizResponse,
    QuizHistoryResponse,
    QuizHistoryItem,
    QuizHistoryStats,
    UserStats,
    DailyQuizPublic,
    DailyQuizWithAnswer,
    QuizAttemptResponse,
    MovieReference
)


class QuizService:
    """Quiz service"""
    
    @staticmethod
    def get_today_quiz(db: Session, user_id: UUID) -> TodayQuizResponse:
        """Get today's quiz - supports 3 quizzes per day"""
        today = date.today()
        DAILY_LIMIT = 3
        
        # Get all today's quizzes (should be 3)
        all_today_quizzes = db.query(DailyQuiz).filter(DailyQuiz.date == today).all()
        
        if not all_today_quizzes:
            return TodayQuizResponse(
                quiz=None,
                user_attempt=None,
                has_answered=False,
                time_until_next=QuizService._calculate_time_until_next(),
                daily_attempts=0,
                daily_limit=DAILY_LIMIT,
                remaining_attempts=DAILY_LIMIT
            )
        
        # Get all user's attempts for today
        today_attempts = db.query(QuizAttempt).filter(
            and_(
                QuizAttempt.user_id == user_id,
                QuizAttempt.quiz_id.in_([q.id for q in all_today_quizzes])
            )
        ).all()
        
        answered_quiz_ids = {attempt.quiz_id for attempt in today_attempts}
        daily_attempts_count = len(today_attempts)
        remaining = DAILY_LIMIT - daily_attempts_count
        
        # Find first unanswered quiz
        unanswered_quiz = None
        current_attempt = None
        
        for quiz in all_today_quizzes:
            if quiz.id not in answered_quiz_ids:
                unanswered_quiz = quiz
                break
        
        # If user has answered this specific quiz
        if unanswered_quiz:
            has_answered_current = False
        else:
            # All quizzes answered, show the last one
            unanswered_quiz = all_today_quizzes[-1] if all_today_quizzes else None
            has_answered_current = True
            if today_attempts:
                current_attempt = today_attempts[-1]
        
        return TodayQuizResponse(
            quiz=DailyQuizPublic.model_validate(unanswered_quiz) if unanswered_quiz else None,
            user_attempt=QuizAttemptResponse.model_validate(current_attempt) if current_attempt else None,
            has_answered=has_answered_current,
            time_until_next=QuizService._calculate_time_until_next(),
            daily_attempts=daily_attempts_count,
            daily_limit=DAILY_LIMIT,
            remaining_attempts=max(0, remaining)
        )
    
    @staticmethod
    def submit_answer(db: Session, user_id: UUID, submission: QuizAttemptCreate) -> QuizSubmitResponse:
        """Submit answer"""
        quiz = db.query(DailyQuiz).filter(DailyQuiz.id == submission.quiz_id).first()
        if not quiz:
            raise ValueError("Quiz not found")
        
        existing_attempt = db.query(QuizAttempt).filter(
            and_(
                QuizAttempt.user_id == user_id,
                QuizAttempt.quiz_id == submission.quiz_id
            )
        ).first()
        
        if existing_attempt:
            raise ValueError("Already answered this quiz")
        
        user = db.query(User).filter(User.user_id == user_id).first()
        if not user:
            raise ValueError("User not found")
        
        previous_points = user.total_points or 0
        previous_level = user.level or 1
        
        is_correct = submission.answer == quiz.correct_answer if submission.answer is not None else False
        points_earned = 10 if is_correct else 0
        
        attempt = QuizAttempt(
            user_id=user_id,
            quiz_id=submission.quiz_id,
            user_answer=submission.answer,
            is_correct=is_correct,
            points_earned=points_earned,
            time_spent=submission.time_spent
        )
        db.add(attempt)
        
        if points_earned > 0:
            user.total_points = (user.total_points or 0) + points_earned
        
        db.commit()
        db.refresh(user)
        
        global_rank = QuizService._calculate_global_rank(db, user_id)
        friend_rank = QuizService._calculate_friend_rank(db, user_id)
        
        user_stats = UserStats(
            total_points=user.total_points or 0,
            previous_points=previous_points,
            level=user.level or 1,
            previous_level=previous_level,
            level_up=(user.level or 1) > previous_level,
            global_rank=global_rank,
            friend_rank=friend_rank
        )
        
        movie_ref = None
        if quiz.movie_reference:
            movie_ref = MovieReference(**quiz.movie_reference)
        
        return QuizSubmitResponse(
            is_correct=is_correct,
            correct_answer=quiz.correct_answer,
            points_earned=points_earned,
            explanation=quiz.explanation,
            user_stats=user_stats,
            movie_reference=movie_ref
        )
    
    @staticmethod
    def get_quiz_history(db: Session, user_id: UUID, limit: int = 30) -> QuizHistoryResponse:
        """Get quiz history"""
        attempts = db.query(QuizAttempt).join(DailyQuiz).filter(
            QuizAttempt.user_id == user_id
        ).order_by(desc(QuizAttempt.answered_at)).limit(limit).all()
        
        history_items = []
        for attempt in attempts:
            quiz_with_answer = DailyQuizWithAnswer.model_validate(attempt.quiz)
            history_items.append(QuizHistoryItem(
                id=attempt.id,
                quiz=quiz_with_answer,
                user_answer=attempt.user_answer,
                is_correct=attempt.is_correct,
                points_earned=attempt.points_earned,
                time_spent=attempt.time_spent,
                answered_at=attempt.answered_at
            ))
        
        stats = QuizService._calculate_quiz_stats(db, user_id)
        
        return QuizHistoryResponse(
            attempts=history_items,
            stats=stats
        )
    
    @staticmethod
    def _calculate_time_until_next() -> str:
        """Calculate time until next quiz"""
        now = datetime.now(timezone.utc)
        tomorrow = (now + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
        diff = tomorrow - now
        
        hours, remainder = divmod(int(diff.total_seconds()), 3600)
        minutes, seconds = divmod(remainder, 60)
        
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
    
    @staticmethod
    def _calculate_global_rank(db: Session, user_id: UUID) -> Optional[int]:
        """Calculate global rank"""
        user = db.query(User).filter(User.user_id == user_id).first()
        if not user:
            return None
        
        higher_count = db.query(func.count(User.user_id)).filter(
            User.total_points > (user.total_points or 0)
        ).scalar()
        
        return higher_count + 1
    
    @staticmethod
    def _calculate_friend_rank(db: Session, user_id: UUID) -> Optional[int]:
        """Calculate friend rank"""
        return None
    
    @staticmethod
    def _calculate_quiz_stats(db: Session, user_id: UUID) -> QuizHistoryStats:
        """Calculate quiz statistics"""
        total_attempts = db.query(func.count(QuizAttempt.id)).filter(
            QuizAttempt.user_id == user_id
        ).scalar() or 0
        
        correct_count = db.query(func.count(QuizAttempt.id)).filter(
            and_(
                QuizAttempt.user_id == user_id,
                QuizAttempt.is_correct == True
            )
        ).scalar() or 0
        
        accuracy_rate = (correct_count / total_attempts * 100) if total_attempts > 0 else 0.0
        
        streak_days = QuizService._calculate_streak_days(db, user_id)
        
        return QuizHistoryStats(
            total_attempts=total_attempts,
            correct_count=correct_count,
            accuracy_rate=round(accuracy_rate, 1),
            streak_days=streak_days
        )
    
    @staticmethod
    def _calculate_streak_days(db: Session, user_id: UUID) -> int:
        """Calculate streak days"""
        attempts = db.query(
            func.date(QuizAttempt.answered_at).label('answer_date')
        ).filter(
            QuizAttempt.user_id == user_id
        ).group_by(
            func.date(QuizAttempt.answered_at)
        ).order_by(
            desc('answer_date')
        ).all()
        
        if not attempts:
            return 0
        
        streak = 0
        expected_date = date.today()
        
        for attempt in attempts:
            answer_date = attempt.answer_date
            
            if answer_date == expected_date:
                streak += 1
                expected_date = expected_date - timedelta(days=1)
            else:
                break
        
        return streak
