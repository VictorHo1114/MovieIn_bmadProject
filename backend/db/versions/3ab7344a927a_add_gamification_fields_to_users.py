"""add_gamification_fields_to_users

Revision ID: 3ab7344a927a
Revises: 633510998b1b
Create Date: 2025-11-12 02:36:22.590259

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '3ab7344a927a'
down_revision: Union[str, Sequence[str], None] = '633510998b1b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema - Add gamification fields to users table."""
    # Add gamification columns to users table
    op.add_column('users', sa.Column('total_points', sa.Integer(), nullable=False, server_default='0'))
    op.add_column('users', sa.Column('level', sa.Integer(), nullable=False, server_default='1'))
    
    # Create indexes for performance optimization
    op.create_index('idx_users_total_points', 'users', ['total_points'], unique=False)
    op.create_index('idx_users_level', 'users', ['level'], unique=False)
    
    # Create function to automatically update user level based on points
    op.execute("""
        CREATE OR REPLACE FUNCTION update_user_level()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.level = CASE
                WHEN NEW.total_points >= 1000 THEN 5
                WHEN NEW.total_points >= 600 THEN 4
                WHEN NEW.total_points >= 300 THEN 3
                WHEN NEW.total_points >= 100 THEN 2
                ELSE 1
            END;
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
    """)
    
    # Create trigger to automatically update level when points change
    op.execute("""
        CREATE TRIGGER trigger_update_user_level
        BEFORE UPDATE OF total_points ON users
        FOR EACH ROW
        EXECUTE FUNCTION update_user_level();
    """)


def downgrade() -> None:
    """Downgrade schema - Remove gamification fields from users table."""
    # Drop trigger and function
    op.execute("DROP TRIGGER IF EXISTS trigger_update_user_level ON users;")
    op.execute("DROP FUNCTION IF EXISTS update_user_level();")
    
    # Drop indexes
    op.drop_index('idx_users_level', table_name='users')
    op.drop_index('idx_users_total_points', table_name='users')
    
    # Drop columns
    op.drop_column('users', 'level')
    op.drop_column('users', 'total_points')
