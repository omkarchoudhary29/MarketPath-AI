"""008_ai_conversations_persistence

Revision ID: d4e5f6a7b8c9
Revises: c3d4e5f6a7b8
Create Date: 2026-11-16 14:45:00.000000
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.sqlite import JSON
from backend.app.models.base import GUID

# revision identifiers, used by Alembic.
revision: str = 'd4e5f6a7b8c9'
down_revision: Union[str, None] = 'c3d4e5f6a7b8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Create ai_conversations table
    op.create_table(
        'ai_conversations',
        sa.Column('id', GUID(), primary_key=True),
        sa.Column('user_id', GUID(), sa.ForeignKey('user_profiles.id', ondelete='CASCADE'), nullable=False),
        sa.Column('organization_id', GUID(), sa.ForeignKey('organizations.id', ondelete='SET NULL'), nullable=True),
        sa.Column('title', sa.String(length=255), server_default='Operational AI Diagnostics', nullable=False),
        sa.Column('is_active', sa.Boolean(), server_default=sa.true(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index('ix_ai_conversations_user_id', 'ai_conversations', ['user_id'])
    op.create_index('ix_ai_conversations_org_id', 'ai_conversations', ['organization_id'])

    # 2. Create ai_chat_messages table
    op.create_table(
        'ai_chat_messages',
        sa.Column('id', GUID(), primary_key=True),
        sa.Column('conversation_id', GUID(), sa.ForeignKey('ai_conversations.id', ondelete='CASCADE'), nullable=False),
        sa.Column('sender', sa.String(length=20), nullable=False),
        sa.Column('message_text', sa.Text(), nullable=False),
        sa.Column('suggested_actions', JSON, nullable=True),
        sa.Column('diagnosed_issues', JSON, nullable=True),
        sa.Column('data_sources', JSON, nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index('ix_ai_chat_messages_conversation_id', 'ai_chat_messages', ['conversation_id'])


def downgrade() -> None:
    op.drop_index('ix_ai_chat_messages_conversation_id', table_name='ai_chat_messages')
    op.drop_table('ai_chat_messages')
    op.drop_index('ix_ai_conversations_org_id', table_name='ai_conversations')
    op.drop_index('ix_ai_conversations_user_id', table_name='ai_conversations')
    op.drop_table('ai_conversations')
