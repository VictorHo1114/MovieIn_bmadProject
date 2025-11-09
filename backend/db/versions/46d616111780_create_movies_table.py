"""create_movies_table

Revision ID: 46d616111780
Revises: 2a32558280a5
Create Date: 2025-11-08 01:05:58.379434

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '46d616111780'
down_revision: Union[str, Sequence[str], None] = '2a32558280a5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
