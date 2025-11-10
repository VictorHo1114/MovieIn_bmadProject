"""expand_profiles_and_social_tables

Revision ID: 20251111002325
Revises: be60923c8af8
Create Date: 2025-11-11 00:23:25

此 migration 達成以下目標：
1. 擴展 profiles 表從 5 欄位到 9 欄位（達標）
2. 創建 watchlist 表（7 欄位）
3. 創建 top10_list 表（8 欄位）
4. 創建 friendships 表（7 欄位）
5. 創建 shared_lists 表（9 欄位）
6. 創建 list_interactions 表（6 欄位）

總計：6 張表 ≥6 欄位（包含 users 9欄, movies 17欄）= 作業達標！
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

# revision identifiers, used by Alembic.
revision: str = '20251111002325'
down_revision: Union[str, Sequence[str], None] = 'be60923c8af8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    
    # ===== 1. 擴展 profiles 表（5 -> 9 欄位）=====
    print("擴展 profiles 表...")
    op.execute("""
        ALTER TABLE profiles
        ADD COLUMN IF NOT EXISTS bio TEXT,
        ADD COLUMN IF NOT EXISTS favorite_genres JSONB DEFAULT '[]'::jsonb,
        ADD COLUMN IF NOT EXISTS privacy_level VARCHAR(20) DEFAULT 'public',
        ADD COLUMN IF NOT EXISTS last_active TIMESTAMP WITH TIME ZONE DEFAULT now()
    """)
    op.create_index('idx_profiles_privacy', 'profiles', ['privacy_level'])
    op.create_index('idx_profiles_last_active', 'profiles', ['last_active'])
    
    # ===== 2. 創建 watchlist 表（7 欄位）=====
    print("創建 watchlist 表...")
    op.create_table(
        'watchlist',
        sa.Column('id', UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), primary_key=True),
        sa.Column('user_id', UUID(as_uuid=True), sa.ForeignKey('users.user_id', ondelete='CASCADE'), nullable=False),
        sa.Column('tmdb_id', sa.Integer(), sa.ForeignKey('movies.tmdb_id', ondelete='CASCADE'), nullable=False),
        sa.Column('added_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('is_watched', sa.Boolean(), default=False, nullable=False),
        sa.Column('priority', sa.Integer(), default=0, nullable=False),  # 1=高, 0=中, -1=低
    )
    op.create_index('idx_watchlist_user', 'watchlist', ['user_id'])
    op.create_index('idx_watchlist_movie', 'watchlist', ['tmdb_id'])
    op.create_index('idx_watchlist_added_at', 'watchlist', ['added_at'])
    # 確保同一使用者不會重複加入同一部電影
    op.create_unique_constraint('uq_watchlist_user_movie', 'watchlist', ['user_id', 'tmdb_id'])
    
    # ===== 3. 創建 top10_list 表（8 欄位）=====
    print("創建 top10_list 表...")
    op.create_table(
        'top10_list',
        sa.Column('id', UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), primary_key=True),
        sa.Column('user_id', UUID(as_uuid=True), sa.ForeignKey('users.user_id', ondelete='CASCADE'), nullable=False),
        sa.Column('tmdb_id', sa.Integer(), sa.ForeignKey('movies.tmdb_id', ondelete='CASCADE'), nullable=False),
        sa.Column('rank', sa.Integer(), nullable=False),  # 1-10
        sa.Column('added_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('rating_by_user', sa.Float(), nullable=True),  # 使用者個人評分
        sa.Column('category', sa.String(50), nullable=True),  # 例如: 動作片、喜劇片 Top 10
    )
    op.create_index('idx_top10_user', 'top10_list', ['user_id'])
    op.create_index('idx_top10_rank', 'top10_list', ['rank'])
    op.create_index('idx_top10_category', 'top10_list', ['category'])
    # 確保同一類別中，同一使用者的 rank 不重複
    op.create_unique_constraint('uq_top10_user_category_rank', 'top10_list', ['user_id', 'category', 'rank'])
    
    # ===== 4. 創建 friendships 表（7 欄位）=====
    print("創建 friendships 表...")
    op.create_table(
        'friendships',
        sa.Column('id', UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), primary_key=True),
        sa.Column('user_id', UUID(as_uuid=True), sa.ForeignKey('users.user_id', ondelete='CASCADE'), nullable=False),
        sa.Column('friend_id', UUID(as_uuid=True), sa.ForeignKey('users.user_id', ondelete='CASCADE'), nullable=False),
        sa.Column('status', sa.String(20), nullable=False, default='pending'),  # pending/accepted/blocked
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('accepted_at', sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column('message', sa.Text(), nullable=True),  # 好友邀請訊息
    )
    op.create_index('idx_friendships_user', 'friendships', ['user_id'])
    op.create_index('idx_friendships_friend', 'friendships', ['friend_id'])
    op.create_index('idx_friendships_status', 'friendships', ['status'])
    # 確保兩個使用者之間只能有一個好友關係
    op.create_unique_constraint('uq_friendships_pair', 'friendships', ['user_id', 'friend_id'])
    # 防止自己加自己為好友
    op.execute("ALTER TABLE friendships ADD CONSTRAINT chk_no_self_friend CHECK (user_id != friend_id)")
    
    # ===== 5. 創建 shared_lists 表（9 欄位）=====
    print("創建 shared_lists 表...")
    op.create_table(
        'shared_lists',
        sa.Column('id', UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), primary_key=True),
        sa.Column('owner_id', UUID(as_uuid=True), sa.ForeignKey('users.user_id', ondelete='CASCADE'), nullable=False),
        sa.Column('list_name', sa.String(100), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('is_public', sa.Boolean(), default=False, nullable=False),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('view_count', sa.Integer(), default=0, nullable=False),
        sa.Column('like_count', sa.Integer(), default=0, nullable=False),
    )
    op.create_index('idx_shared_lists_owner', 'shared_lists', ['owner_id'])
    op.create_index('idx_shared_lists_public', 'shared_lists', ['is_public'])
    op.create_index('idx_shared_lists_created', 'shared_lists', ['created_at'])
    
    # ===== 6. 創建 list_interactions 表（6 欄位）=====
    print("創建 list_interactions 表...")
    op.create_table(
        'list_interactions',
        sa.Column('id', UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), primary_key=True),
        sa.Column('user_id', UUID(as_uuid=True), sa.ForeignKey('users.user_id', ondelete='CASCADE'), nullable=False),
        sa.Column('list_id', UUID(as_uuid=True), sa.ForeignKey('shared_lists.id', ondelete='CASCADE'), nullable=False),
        sa.Column('interaction_type', sa.String(20), nullable=False),  # like/view/share
        sa.Column('comment_text', sa.Text(), nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=False),
    )
    op.create_index('idx_list_interactions_user', 'list_interactions', ['user_id'])
    op.create_index('idx_list_interactions_list', 'list_interactions', ['list_id'])
    op.create_index('idx_list_interactions_type', 'list_interactions', ['interaction_type'])
    # 每個使用者對同一個清單只能有一次特定類型的互動（避免重複按讚）
    op.create_unique_constraint('uq_list_interaction', 'list_interactions', ['user_id', 'list_id', 'interaction_type'])
    
    print("✅ 所有表格創建完成！")


def downgrade() -> None:
    """Downgrade schema."""
    
    # 刪除順序：先刪除有外鍵依賴的表
    print("刪除所有新增的表格...")
    
    op.drop_table('list_interactions')
    op.drop_table('shared_lists')
    op.drop_table('friendships')
    op.drop_table('top10_list')
    op.drop_table('watchlist')
    
    # 移除 profiles 新增的欄位
    op.drop_index('idx_profiles_privacy', table_name='profiles')
    op.drop_index('idx_profiles_last_active', table_name='profiles')
    op.execute("""
        ALTER TABLE profiles
        DROP COLUMN IF EXISTS bio,
        DROP COLUMN IF EXISTS favorite_genres,
        DROP COLUMN IF EXISTS privacy_level,
        DROP COLUMN IF EXISTS last_active
    """)
    
    print("✅ Downgrade 完成！")
