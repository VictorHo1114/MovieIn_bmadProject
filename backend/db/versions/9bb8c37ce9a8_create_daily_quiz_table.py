"""create_daily_quiz_table

Revision ID: 9bb8c37ce9a8
Revises: 3ab7344a927a
Create Date: 2025-11-12 02:36:53.504396

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '9bb8c37ce9a8'
down_revision: Union[str, Sequence[str], None] = '3ab7344a927a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Create daily_quiz table
    op.create_table(
        'daily_quiz',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('question', sa.Text(), nullable=False),
        sa.Column('options', sa.dialects.postgresql.JSONB(), nullable=False, comment='Array of 4 options'),
        sa.Column('correct_answer', sa.Integer(), nullable=False, comment='Index 0-3 of correct option'),
        sa.Column('explanation', sa.Text(), nullable=True, comment='Answer explanation'),
        sa.Column('difficulty', sa.String(20), nullable=False, server_default='medium'),
        sa.Column('category', sa.String(50), nullable=True),
        sa.Column('movie_reference', sa.dialects.postgresql.JSONB(), nullable=True, comment='Related movie info'),
        sa.Column('date', sa.Date(), nullable=False),
        sa.Column('created_at', sa.TIMESTAMP(), server_default=sa.text('NOW()'), nullable=False),
        sa.CheckConstraint('correct_answer >= 0 AND correct_answer <= 3', name='valid_answer'),
        sa.CheckConstraint("difficulty IN ('easy', 'medium', 'hard')", name='valid_difficulty'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('date', name='unique_quiz_date')
    )
    
    # Create indexes for performance
    op.create_index('idx_daily_quiz_date', 'daily_quiz', ['date'], unique=False, postgresql_using='btree')
    op.create_index('idx_daily_quiz_difficulty', 'daily_quiz', ['difficulty'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    # Drop indexes first
    op.drop_index('idx_daily_quiz_difficulty', table_name='daily_quiz')
    op.drop_index('idx_daily_quiz_date', table_name='daily_quiz')
    
    # Drop table
    op.drop_table('daily_quiz')
