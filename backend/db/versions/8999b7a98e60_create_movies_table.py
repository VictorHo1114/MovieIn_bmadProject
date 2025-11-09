"""create_movies_table

Revision ID: 8999b7a98e60
Revises: 46d616111780
Create Date: 2025-11-08 01:06:06.529381

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '8999b7a98e60'
down_revision: Union[str, Sequence[str], None] = '46d616111780'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # 創建 movies 表
    op.execute("""
        CREATE TABLE IF NOT EXISTS movies (
            tmdb_id INTEGER PRIMARY KEY,
            title TEXT NOT NULL,
            original_title TEXT,
            overview TEXT,
            poster_path TEXT,
            backdrop_path TEXT,
            release_date DATE,
            genres JSONB,
            vote_average FLOAT,
            vote_count INTEGER,
            popularity FLOAT,
            runtime INTEGER,
            original_language VARCHAR(10),
            adult BOOLEAN DEFAULT FALSE,
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT now()
        )
    """)
    
    # 創建索引以提升查詢效能
    op.execute("CREATE INDEX IF NOT EXISTS idx_movies_release_date ON movies(release_date)")
    op.execute("CREATE INDEX IF NOT EXISTS idx_movies_vote_average ON movies(vote_average)")
    op.execute("CREATE INDEX IF NOT EXISTS idx_movies_vote_count ON movies(vote_count)")
    op.execute("CREATE INDEX IF NOT EXISTS idx_movies_language ON movies(original_language)")
    op.execute("CREATE INDEX IF NOT EXISTS idx_movies_genres ON movies USING GIN (genres)")
    op.execute("CREATE INDEX IF NOT EXISTS idx_movies_updated ON movies(updated_at)")


def downgrade() -> None:
    """Downgrade schema."""
    op.execute("DROP TABLE IF EXISTS movies CASCADE")
