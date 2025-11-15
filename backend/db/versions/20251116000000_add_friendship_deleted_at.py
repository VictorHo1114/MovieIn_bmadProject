"""add deleted_at to friendships

Revision ID: 20251116000000
Revises: 20251111002325
Create Date: 2025-11-16 00:00:00.000000
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '20251116000000'
down_revision = '20251111002325'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('friendships', sa.Column('deleted_at', sa.TIMESTAMP(timezone=True), nullable=True))


def downgrade():
    op.drop_column('friendships', 'deleted_at')
