"""allow_multiple_daily_quizzes

Revision ID: ab583c77746f
Revises: de6aed3667b9
Create Date: 2025-11-12 03:25:32.002958

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'ab583c77746f'
down_revision: Union[str, Sequence[str], None] = 'de6aed3667b9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Add sequence_number column
    op.add_column('daily_quiz', sa.Column('sequence_number', sa.Integer(), nullable=False, server_default='1'))
    
    # Drop unique constraint on date (may have different names)
    op.execute('ALTER TABLE daily_quiz DROP CONSTRAINT IF EXISTS daily_quiz_date_key')
    op.execute('ALTER TABLE daily_quiz DROP CONSTRAINT IF EXISTS unique_quiz_date')
    
    # Create unique constraint on (date, sequence_number)
    op.create_unique_constraint('unique_quiz_date_sequence', 'daily_quiz', ['date', 'sequence_number'])
    
    # Create index on (date, sequence_number)
    op.create_index('idx_daily_quiz_date_sequence', 'daily_quiz', ['date', 'sequence_number'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    # Drop index
    op.drop_index('idx_daily_quiz_date_sequence', table_name='daily_quiz')
    
    # Drop unique constraint
    op.drop_constraint('unique_quiz_date_sequence', 'daily_quiz', type_='unique')
    
    # Restore unique constraint on date
    op.create_unique_constraint('daily_quiz_date_key', 'daily_quiz', ['date'])
    
    # Drop sequence_number column
    op.drop_column('daily_quiz', 'sequence_number')
