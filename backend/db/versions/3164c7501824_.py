"""empty message

Revision ID: 3164c7501824
Revises: 20251113012025, 20251116000000
Create Date: 2025-11-16 04:31:00.902506

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '3164c7501824'
down_revision: Union[str, Sequence[str], None] = ('20251113012025', '20251116000000')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
