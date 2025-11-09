"""add_movie_keywords_and_mood_columns

Revision ID: be60923c8af8
Revises: 8999b7a98e60
Create Date: 2025-11-08 13:55:21.384983

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'be60923c8af8'
down_revision: Union[str, Sequence[str], None] = '8999b7a98e60'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # 添加 keywords 欄位（JSONB 陣列，存儲電影的關鍵詞標籤）
    op.execute("""
        ALTER TABLE movies
        ADD COLUMN IF NOT EXISTS keywords JSONB DEFAULT '[]'::jsonb
    """)
    
    # 添加 mood_tags 欄位（JSONB 陣列，存儲電影的情緒/氛圍標籤）
    op.execute("""
        ALTER TABLE movies
        ADD COLUMN IF NOT EXISTS mood_tags JSONB DEFAULT '[]'::jsonb
    """)
    
    # 添加 tone 欄位（TEXT，存儲電影的整體基調）
    op.execute("""
        ALTER TABLE movies
        ADD COLUMN IF NOT EXISTS tone TEXT
    """)
    
    # 添加索引以提升查詢效能
    op.execute("CREATE INDEX IF NOT EXISTS idx_movies_keywords ON movies USING GIN (keywords)")
    op.execute("CREATE INDEX IF NOT EXISTS idx_movies_mood_tags ON movies USING GIN (mood_tags)")
    op.execute("CREATE INDEX IF NOT EXISTS idx_movies_tone ON movies(tone)")


def downgrade() -> None:
    """Downgrade schema."""
    op.execute("DROP INDEX IF EXISTS idx_movies_keywords")
    op.execute("DROP INDEX IF EXISTS idx_movies_mood_tags")
    op.execute("DROP INDEX IF EXISTS idx_movies_tone")
    op.execute("ALTER TABLE movies DROP COLUMN IF EXISTS keywords")
    op.execute("ALTER TABLE movies DROP COLUMN IF EXISTS mood_tags")
    op.execute("ALTER TABLE movies DROP COLUMN IF EXISTS tone")
