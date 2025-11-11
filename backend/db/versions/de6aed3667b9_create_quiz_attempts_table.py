"""create_quiz_attempts_table

Revision ID: de6aed3667b9
Revises: 9bb8c37ce9a8
Create Date: 2025-11-12 02:39:20.729001

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'de6aed3667b9'
down_revision: Union[str, Sequence[str], None] = '9bb8c37ce9a8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Create quiz_attempts table
    op.create_table(
        'quiz_attempts',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.dialects.postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('quiz_id', sa.Integer(), nullable=False),
        sa.Column('user_answer', sa.Integer(), nullable=True, comment='User selected option (0-3), NULL if timeout'),
        sa.Column('is_correct', sa.Boolean(), nullable=False),
        sa.Column('points_earned', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('time_spent', sa.Integer(), nullable=True, comment='Time spent in seconds'),
        sa.Column('answered_at', sa.TIMESTAMP(), server_default=sa.text('NOW()'), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.user_id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['quiz_id'], ['daily_quiz.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', 'quiz_id', name='unique_user_quiz_attempt')
    )
    
    # Create indexes for query performance
    op.create_index('idx_quiz_attempts_user_id', 'quiz_attempts', ['user_id'], unique=False)
    op.create_index('idx_quiz_attempts_quiz_id', 'quiz_attempts', ['quiz_id'], unique=False)
    op.create_index('idx_quiz_attempts_answered_at', 'quiz_attempts', ['answered_at'], unique=False, postgresql_using='btree')
    op.create_index('idx_quiz_attempts_user_correct', 'quiz_attempts', ['user_id', 'is_correct'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    # Drop indexes first
    op.drop_index('idx_quiz_attempts_user_correct', table_name='quiz_attempts')
    op.drop_index('idx_quiz_attempts_answered_at', table_name='quiz_attempts')
    op.drop_index('idx_quiz_attempts_quiz_id', table_name='quiz_attempts')
    op.drop_index('idx_quiz_attempts_user_id', table_name='quiz_attempts')
    
    # Drop table
    op.drop_table('quiz_attempts')
