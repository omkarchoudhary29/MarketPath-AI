"""007_auth_sessions_and_passwords

Revision ID: c3d4e5f6a7b8
Revises: b2c3d4e5f6a7
Create Date: 2026-11-16 10:25:00.000000
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from backend.app.models.base import GUID

# revision identifiers, used by Alembic.
revision: str = 'c3d4e5f6a7b8'
down_revision: Union[str, None] = 'b2c3d4e5f6a7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Add password_hash to user_profiles (nullable for backward compatibility)
    op.add_column('user_profiles', sa.Column('password_hash', sa.String(length=255), nullable=True))

    # 2. Create user_sessions table
    op.create_table(
        'user_sessions',
        sa.Column('id', GUID(), primary_key=True),
        sa.Column('user_id', GUID(), sa.ForeignKey('user_profiles.id', ondelete='CASCADE'), nullable=False),
        sa.Column('organization_id', GUID(), sa.ForeignKey('organizations.id', ondelete='SET NULL'), nullable=True),
        sa.Column('token_hash', sa.String(length=64), nullable=False),
        sa.Column('session_type', sa.String(length=50), server_default='real', nullable=False),
        sa.Column('device_info', sa.Text(), nullable=True),
        sa.Column('ip_address', sa.String(length=50), nullable=True),
        sa.Column('is_active', sa.Boolean(), server_default=sa.true(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('last_activity_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('revoked_at', sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index('ix_user_sessions_user_id', 'user_sessions', ['user_id'])
    op.create_index('ix_user_sessions_org_id', 'user_sessions', ['organization_id'])
    op.create_index('ix_user_sessions_token_hash', 'user_sessions', ['token_hash'], unique=True)
    op.create_index('ix_user_sessions_is_active', 'user_sessions', ['is_active'])


def downgrade() -> None:
    op.drop_index('ix_user_sessions_is_active', table_name='user_sessions')
    op.drop_index('ix_user_sessions_token_hash', table_name='user_sessions')
    op.drop_index('ix_user_sessions_org_id', table_name='user_sessions')
    op.drop_index('ix_user_sessions_user_id', table_name='user_sessions')
    op.drop_table('user_sessions')
    op.drop_column('user_profiles', 'password_hash')
