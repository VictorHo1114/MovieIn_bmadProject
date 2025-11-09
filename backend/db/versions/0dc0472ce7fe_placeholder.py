"""placeholder base revision to reconcile DB state

Revision ID: 0dc0472ce7fe
Revises: 
Create Date: 2025-11-07 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0dc0472ce7fe'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # no-op placeholder
    pass


def downgrade() -> None:
    # no-op placeholder
    pass
