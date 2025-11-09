"""add_movie_vectors_table

Revision ID: 2a32558280a5
Revises: 342292faab66
Create Date: 2025-11-07 02:00:14.151769

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '2a32558280a5'
down_revision: Union[str, Sequence[str], None] = '342292faab66'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # 1. 啟用 pgvector 擴充（Neon 支援）
    op.execute('CREATE EXTENSION IF NOT EXISTS vector')
    
    # 2. 建立 movie_vectors 資料表
    op.create_table(
        'movie_vectors',
        sa.Column('tmdb_id', sa.Integer(), nullable=False),
        sa.Column('embedding', sa.Text(), nullable=False),  # 儲存為 JSON 字串（相容性更好）
        sa.Column('overview', sa.Text(), nullable=True),  # 儲存簡介以供後續更新
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('tmdb_id')
    )
    
    # 3. 建立索引加速查詢
    op.create_index('idx_movie_vectors_updated', 'movie_vectors', ['updated_at'])


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index('idx_movie_vectors_updated', table_name='movie_vectors')
    op.drop_table('movie_vectors')
    op.execute('DROP EXTENSION IF EXISTS vector')
