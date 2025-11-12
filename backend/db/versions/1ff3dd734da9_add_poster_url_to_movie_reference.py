"""add_poster_url_to_movie_reference

Revision ID: 1ff3dd734da9
Revises: ab583c77746f
Create Date: 2025-11-12 16:15:36.599669

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '1ff3dd734da9'
down_revision: Union[str, Sequence[str], None] = 'ab583c77746f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
