"""005_revision_v2_schema

Revision ID: a1b2c3d4e5f6
Revises: 9c0e1f22d334
Create Date: 2026-11-10 11:55:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
import backend.app.models.base


# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, Sequence[str], None] = '9c0e1f22d334'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. New Tables
    # 1.1 business_calendar_events
    op.create_table(
        'business_calendar_events',
        sa.Column('id', backend.app.models.base.GUID(), primary_key=True, nullable=False),
        sa.Column('organization_id', backend.app.models.base.GUID(), sa.ForeignKey('organizations.id', ondelete='CASCADE'), nullable=False),
        sa.Column('user_id', backend.app.models.base.GUID(), sa.ForeignKey('user_profiles.id', ondelete='SET NULL'), nullable=True),
        sa.Column('event_type', sa.String(length=50), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('start_time', sa.DateTime(timezone=True), nullable=False),
        sa.Column('end_time', sa.DateTime(timezone=True), nullable=True),
        sa.Column('is_all_day', sa.Boolean(), server_default='0', nullable=False),
        sa.Column('related_entity_type', sa.String(length=50), nullable=True),
        sa.Column('related_entity_id', backend.app.models.base.GUID(), nullable=True),
        sa.Column('color', sa.String(length=30), server_default='#6366F1', nullable=True),
        sa.Column('status', sa.String(length=30), server_default='scheduled', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
    )
    op.create_index('idx_calendar_org_start', 'business_calendar_events', ['organization_id', 'start_time'])
    op.create_index('idx_calendar_event_type', 'business_calendar_events', ['event_type'])

    # 1.2 consultation_requests
    op.create_table(
        'consultation_requests',
        sa.Column('id', backend.app.models.base.GUID(), primary_key=True, nullable=False),
        sa.Column('full_name', sa.String(length=150), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('phone', sa.String(length=50), nullable=True),
        sa.Column('brand_name', sa.String(length=150), nullable=False),
        sa.Column('category', sa.String(length=100), nullable=False),
        sa.Column('business_stage', sa.String(length=50), nullable=False),
        sa.Column('monthly_revenue', sa.String(length=50), nullable=True),
        sa.Column('challenges', sa.Text(), nullable=True),
        sa.Column('preferred_date', sa.Date(), nullable=True),
        sa.Column('preferred_time_slot', sa.String(length=50), nullable=True),
        sa.Column('status', sa.String(length=50), server_default='pending', nullable=False),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
    )
    op.create_index('idx_consultations_status', 'consultation_requests', ['status', 'created_at'])
    op.create_index('idx_consultations_email', 'consultation_requests', ['email'])

    # 1.3 brand_voice_sessions
    op.create_table(
        'brand_voice_sessions',
        sa.Column('id', backend.app.models.base.GUID(), primary_key=True, nullable=False),
        sa.Column('organization_id', backend.app.models.base.GUID(), sa.ForeignKey('organizations.id', ondelete='CASCADE'), nullable=False),
        sa.Column('audio_file_url', sa.Text(), nullable=True),
        sa.Column('duration_seconds', sa.Integer(), nullable=True),
        sa.Column('raw_transcript', sa.Text(), nullable=True),
        sa.Column('extracted_data', sa.JSON(), server_default='{}', nullable=False),
        sa.Column('confidence_score', sa.Float(), nullable=True),
        sa.Column('is_confirmed', sa.Boolean(), server_default='0', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
    )
    op.create_index('idx_voice_sessions_org', 'brand_voice_sessions', ['organization_id'])

    # 1.4 team_invitations
    op.create_table(
        'team_invitations',
        sa.Column('id', backend.app.models.base.GUID(), primary_key=True, nullable=False),
        sa.Column('organization_id', backend.app.models.base.GUID(), sa.ForeignKey('organizations.id', ondelete='CASCADE'), nullable=False),
        sa.Column('invited_by_user_id', backend.app.models.base.GUID(), sa.ForeignKey('user_profiles.id', ondelete='CASCADE'), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('role', sa.String(length=50), server_default='viewer', nullable=False),
        sa.Column('token_hash', sa.String(length=255), nullable=False),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('accepted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('status', sa.String(length=30), server_default='pending', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
    )
    op.create_index('idx_team_invitations_token', 'team_invitations', ['token_hash'], unique=True)
    op.create_index('idx_team_invitations_org', 'team_invitations', ['organization_id', 'status'])

    # 1.5 agency_members
    op.create_table(
        'agency_members',
        sa.Column('id', backend.app.models.base.GUID(), primary_key=True, nullable=False),
        sa.Column('agency_profile_id', backend.app.models.base.GUID(), sa.ForeignKey('agency_profiles.id', ondelete='CASCADE'), nullable=False),
        sa.Column('user_id', backend.app.models.base.GUID(), sa.ForeignKey('user_profiles.id', ondelete='CASCADE'), nullable=False),
        sa.Column('role', sa.String(length=50), server_default='agency_staff', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
    )
    op.create_index('idx_agency_members_agency', 'agency_members', ['agency_profile_id'])
    op.create_index('idx_agency_members_user', 'agency_members', ['user_id'])

    # 2. Add columns to existing tables using batch mode for SQLite compatibility
    with op.batch_alter_table('notifications', schema=None) as batch_op:
        batch_op.add_column(sa.Column('domain', sa.String(length=50), server_default='business', nullable=False))
        batch_op.add_column(sa.Column('severity', sa.String(length=20), server_default='info', nullable=False))
        batch_op.add_column(sa.Column('read_at', sa.DateTime(timezone=True), nullable=True))
        batch_op.add_column(sa.Column('metadata', sa.JSON(), server_default='{}', nullable=False))
        batch_op.create_index('idx_notifications_domain', ['domain'])

    with op.batch_alter_table('products', schema=None) as batch_op:
        batch_op.add_column(sa.Column('category_attributes', sa.JSON(), server_default='{}', nullable=False))
        batch_op.add_column(sa.Column('packaging_specs', sa.JSON(), server_default='{}', nullable=False))
        batch_op.add_column(sa.Column('shipping_specs', sa.JSON(), server_default='{}', nullable=False))
        batch_op.add_column(sa.Column('moq', sa.Integer(), server_default='1', nullable=False))
        batch_op.add_column(sa.Column('compliance_certificates', sa.JSON(), server_default='[]', nullable=False))

    with op.batch_alter_table('brand_profiles', schema=None) as batch_op:
        batch_op.add_column(sa.Column('mission', sa.Text(), nullable=True))
        batch_op.add_column(sa.Column('target_audience', sa.Text(), nullable=True))
        batch_op.add_column(sa.Column('visual_guidelines', sa.JSON(), server_default='{}', nullable=False))
        batch_op.add_column(sa.Column('key_usps', sa.JSON(), server_default='[]', nullable=False))
        batch_op.add_column(sa.Column('competitor_differentiation', sa.Text(), nullable=True))
        batch_op.add_column(sa.Column('brand_values', sa.JSON(), server_default='[]', nullable=False))
        batch_op.add_column(sa.Column('pricing_strategy', sa.String(length=100), nullable=True))
        batch_op.add_column(sa.Column('sustainability_practices', sa.Text(), nullable=True))
        batch_op.add_column(sa.Column('customer_demographics', sa.JSON(), server_default='{}', nullable=False))
        batch_op.add_column(sa.Column('packaging_philosophy', sa.Text(), nullable=True))
        batch_op.add_column(sa.Column('regulatory_disclaimers', sa.Text(), nullable=True))
        batch_op.add_column(sa.Column('product_stories', sa.JSON(), server_default='[]', nullable=False))

    with op.batch_alter_table('channel_connections', schema=None) as batch_op:
        batch_op.add_column(sa.Column('channel_group', sa.String(length=50), server_default='storefront', nullable=False))
        batch_op.add_column(sa.Column('partner_status', sa.String(length=50), server_default='connected', nullable=False))
        batch_op.create_index('idx_channel_conn_group', ['channel_group'])

    with op.batch_alter_table('organizations', schema=None) as batch_op:
        batch_op.add_column(sa.Column('org_type', sa.String(length=50), server_default='business', nullable=False))

    with op.batch_alter_table('user_profiles', schema=None) as batch_op:
        batch_op.add_column(sa.Column('account_type', sa.String(length=50), server_default='company', nullable=False))

    with op.batch_alter_table('agency_portfolios', schema=None) as batch_op:
        batch_op.add_column(sa.Column('is_demo_work', sa.Boolean(), server_default='0', nullable=False))

    with op.batch_alter_table('agency_quote_requests', schema=None) as batch_op:
        batch_op.add_column(sa.Column('sanitized_founder_data', sa.JSON(), server_default='{}', nullable=False))


def downgrade() -> None:
    with op.batch_alter_table('agency_quote_requests', schema=None) as batch_op:
        batch_op.drop_column('sanitized_founder_data')

    with op.batch_alter_table('agency_portfolios', schema=None) as batch_op:
        batch_op.drop_column('is_demo_work')

    with op.batch_alter_table('user_profiles', schema=None) as batch_op:
        batch_op.drop_column('account_type')

    with op.batch_alter_table('organizations', schema=None) as batch_op:
        batch_op.drop_column('org_type')

    with op.batch_alter_table('channel_connections', schema=None) as batch_op:
        batch_op.drop_index('idx_channel_conn_group')
        batch_op.drop_column('partner_status')
        batch_op.drop_column('channel_group')

    with op.batch_alter_table('brand_profiles', schema=None) as batch_op:
        batch_op.drop_column('product_stories')
        batch_op.drop_column('regulatory_disclaimers')
        batch_op.drop_column('packaging_philosophy')
        batch_op.drop_column('customer_demographics')
        batch_op.drop_column('sustainability_practices')
        batch_op.drop_column('pricing_strategy')
        batch_op.drop_column('brand_values')
        batch_op.drop_column('competitor_differentiation')
        batch_op.drop_column('key_usps')
        batch_op.drop_column('visual_guidelines')
        batch_op.drop_column('target_audience')
        batch_op.drop_column('mission')

    with op.batch_alter_table('products', schema=None) as batch_op:
        batch_op.drop_column('compliance_certificates')
        batch_op.drop_column('moq')
        batch_op.drop_column('shipping_specs')
        batch_op.drop_column('packaging_specs')
        batch_op.drop_column('category_attributes')

    with op.batch_alter_table('notifications', schema=None) as batch_op:
        batch_op.drop_index('idx_notifications_domain')
        batch_op.drop_column('metadata')
        batch_op.drop_column('read_at')
        batch_op.drop_column('severity')
        batch_op.drop_column('domain')

    op.drop_table('agency_members')
    op.drop_table('team_invitations')
    op.drop_table('brand_voice_sessions')
    op.drop_table('consultation_requests')
    op.drop_table('business_calendar_events')

