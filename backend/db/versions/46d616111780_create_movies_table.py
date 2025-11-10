"""create_movies_table

Revision ID: 46d616111780
Revises: f1f42a5897e2
Create Date: 2025-11-08 01:05:58.379434

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '46d616111780'
down_revision: Union[str, Sequence[str], None] = 'f1f42a5897e2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
