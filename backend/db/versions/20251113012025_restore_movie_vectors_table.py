"""Restore movie_vectors table with enhanced schema

Revision ID: 20251113012025
Revises: 20251111002325
Create Date: 2025-11-13 01:20:25

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '20251113012025'
down_revision: Union[str, Sequence[str], None] = ('1ff3dd734da9', '20251111002325')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create movie_vectors table with enhanced embedding support."""
    op.create_table(
        'movie_vectors',
        sa.Column('tmdb_id', sa.Integer(), nullable=False),
        sa.Column('embedding_text', sa.Text(), nullable=True, comment='Full text used to generate embedding'),
        sa.Column('embedding', postgresql.JSONB(astext_type=sa.Text()), nullable=True, comment='1536-dim vector from text-embedding-3-small'),
        sa.Column('embedding_version', sa.String(50), nullable=True, comment='Model version (e.g., text-embedding-3-small)'),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['tmdb_id'], ['movies.tmdb_id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('tmdb_id')
    )
    
    # Create indexes for performance
    op.create_index('idx_movie_vectors_tmdb_id', 'movie_vectors', ['tmdb_id'], unique=False)
    op.create_index('idx_movie_vectors_updated', 'movie_vectors', ['updated_at'], unique=False)


def downgrade() -> None:
    """Drop movie_vectors table."""
    op.drop_index('idx_movie_vectors_updated', table_name='movie_vectors')
    op.drop_index('idx_movie_vectors_tmdb_id', table_name='movie_vectors')
    op.drop_table('movie_vectors')
