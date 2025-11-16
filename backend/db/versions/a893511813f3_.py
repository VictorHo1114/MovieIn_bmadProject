"""empty message

Revision ID: a893511813f3
Revises: 20251117000000, 3164c7501824
Create Date: 2025-11-17 05:55:52.251852

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a893511813f3'
down_revision: Union[str, Sequence[str], None] = ('20251117000000', '3164c7501824')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
