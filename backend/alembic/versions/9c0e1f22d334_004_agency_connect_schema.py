"""004_agency_connect_schema

Revision ID: 9c0e1f22d334
Revises: 8b9d0e11c223
Create Date: 2026-11-10 09:15:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
import backend.app.models.base


# revision identifiers, used by Alembic.
revision: str = '9c0e1f22d334'
down_revision: Union[str, Sequence[str], None] = '8b9d0e11c223'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. agency_profiles
    op.create_table(
        'agency_profiles',
        sa.Column('id', backend.app.models.base.GUID(), primary_key=True, nullable=False),
        sa.Column('organization_id', backend.app.models.base.GUID(), sa.ForeignKey('organizations.id', ondelete='CASCADE'), nullable=False),
        sa.Column('name', sa.String(length=150), nullable=False),
        sa.Column('slug', sa.String(length=100), nullable=False),
        sa.Column('tagline', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('logo_url', sa.Text(), nullable=True),
        sa.Column('website', sa.String(length=255), nullable=True),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('phone', sa.String(length=50), nullable=True),
        sa.Column('city', sa.String(length=100), nullable=False),
        sa.Column('state', sa.String(length=100), nullable=False),
        sa.Column('country', sa.String(length=100), server_default='India', nullable=False),
        sa.Column('remote_or_local', sa.String(length=50), server_default='both', nullable=False),
        sa.Column('team_size', sa.String(length=50), server_default='1-10', nullable=False),
        sa.Column('founded_year', sa.Integer(), server_default='2020', nullable=False),
        sa.Column('category_specialties', sa.JSON(), nullable=False),
        sa.Column('service_offerings', sa.JSON(), nullable=False),
        sa.Column('min_budget_inr', sa.Integer(), server_default='10000', nullable=False),
        sa.Column('max_budget_inr', sa.Integer(), nullable=True),
        sa.Column('gst_number', sa.String(length=20), nullable=True),
        sa.Column('verification_status', sa.String(length=50), server_default='registered', nullable=False),
        sa.Column('verification_notes', sa.Text(), nullable=True),
        sa.Column('verified_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('verified_by_user_id', backend.app.models.base.GUID(), sa.ForeignKey('user_profiles.id', ondelete='SET NULL'), nullable=True),
        sa.Column('is_available', sa.Boolean(), server_default='1', nullable=False),
        sa.Column('is_active', sa.Boolean(), server_default='1', nullable=False),
        sa.Column('is_featured', sa.Boolean(), server_default='0', nullable=False),
        sa.Column('is_demo', sa.Boolean(), server_default='0', nullable=False),
        sa.Column('tier', sa.String(length=50), server_default='standard', nullable=False),
        sa.Column('rating_avg', sa.Float(), server_default='0.0', nullable=False),
        sa.Column('reviews_count', sa.Integer(), server_default='0', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index('ix_agency_profiles_slug', 'agency_profiles', ['slug'], unique=True)
    op.create_index('ix_agency_profiles_org', 'agency_profiles', ['organization_id'])
    op.create_index('ix_agency_profiles_city', 'agency_profiles', ['city'])
    op.create_index('ix_agency_profiles_status', 'agency_profiles', ['verification_status'])

    # 2. agency_services
    op.create_table(
        'agency_services',
        sa.Column('id', backend.app.models.base.GUID(), primary_key=True, nullable=False),
        sa.Column('agency_profile_id', backend.app.models.base.GUID(), sa.ForeignKey('agency_profiles.id', ondelete='CASCADE'), nullable=False),
        sa.Column('name', sa.String(length=150), nullable=False),
        sa.Column('category', sa.String(length=100), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('deliverables', sa.JSON(), nullable=False),
        sa.Column('pricing_model', sa.String(length=50), server_default='monthly_retainer', nullable=False),
        sa.Column('min_price_inr', sa.Integer(), nullable=False),
        sa.Column('max_price_inr', sa.Integer(), nullable=True),
        sa.Column('estimated_duration', sa.String(length=100), server_default='Ongoing monthly', nullable=False),
        sa.Column('target_industries', sa.JSON(), nullable=False),
        sa.Column('is_available', sa.Boolean(), server_default='1', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index('ix_agency_services_agency', 'agency_services', ['agency_profile_id'])
    op.create_index('ix_agency_services_category', 'agency_services', ['category'])

    # 3. agency_service_packages
    op.create_table(
        'agency_service_packages',
        sa.Column('id', backend.app.models.base.GUID(), primary_key=True, nullable=False),
        sa.Column('agency_profile_id', backend.app.models.base.GUID(), sa.ForeignKey('agency_profiles.id', ondelete='CASCADE'), nullable=False),
        sa.Column('service_id', backend.app.models.base.GUID(), sa.ForeignKey('agency_services.id', ondelete='SET NULL'), nullable=True),
        sa.Column('name', sa.String(length=150), nullable=False),
        sa.Column('package_tier', sa.String(length=50), server_default='growth', nullable=False),
        sa.Column('price_inr', sa.Integer(), nullable=False),
        sa.Column('billing_interval', sa.String(length=50), server_default='monthly', nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('deliverables', sa.JSON(), nullable=False),
        sa.Column('turnaround_days', sa.Integer(), server_default='30', nullable=False),
        sa.Column('is_active', sa.Boolean(), server_default='1', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index('ix_agency_packages_agency', 'agency_service_packages', ['agency_profile_id'])

    # 4. agency_portfolios
    op.create_table(
        'agency_portfolios',
        sa.Column('id', backend.app.models.base.GUID(), primary_key=True, nullable=False),
        sa.Column('agency_profile_id', backend.app.models.base.GUID(), sa.ForeignKey('agency_profiles.id', ondelete='CASCADE'), nullable=False),
        sa.Column('client_brand_name', sa.String(length=150), nullable=False),
        sa.Column('category', sa.String(length=100), nullable=False),
        sa.Column('project_title', sa.String(length=200), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('case_study_url', sa.Text(), nullable=True),
        sa.Column('key_metrics', sa.JSON(), nullable=False),
        sa.Column('media_urls', sa.JSON(), nullable=False),
        sa.Column('display_order', sa.Integer(), server_default='0', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index('ix_agency_portfolios_agency', 'agency_portfolios', ['agency_profile_id'])
    op.create_index('ix_agency_portfolios_category', 'agency_portfolios', ['category'])

    # 5. seller_agency_requirements
    op.create_table(
        'seller_agency_requirements',
        sa.Column('id', backend.app.models.base.GUID(), primary_key=True, nullable=False),
        sa.Column('organization_id', backend.app.models.base.GUID(), sa.ForeignKey('organizations.id', ondelete='CASCADE'), nullable=False),
        sa.Column('brand_name', sa.String(length=150), nullable=False),
        sa.Column('product_category', sa.String(length=100), nullable=False),
        sa.Column('business_stage', sa.String(length=100), nullable=False),
        sa.Column('location', sa.String(length=100), nullable=False),
        sa.Column('website', sa.String(length=255), nullable=True),
        sa.Column('sales_channels', sa.JSON(), nullable=False),
        sa.Column('catalogue_size', sa.Integer(), nullable=True),
        sa.Column('target_market', sa.String(length=100), nullable=True),
        sa.Column('business_objectives', sa.JSON(), nullable=False),
        sa.Column('required_services', sa.JSON(), nullable=False),
        sa.Column('monthly_budget_inr', sa.Integer(), nullable=True),
        sa.Column('project_budget_inr', sa.Integer(), nullable=True),
        sa.Column('total_budget_inr', sa.Integer(), nullable=True),
        sa.Column('currency', sa.String(length=10), server_default='INR', nullable=False),
        sa.Column('engagement_duration', sa.String(length=100), nullable=True),
        sa.Column('preferred_location', sa.String(length=100), nullable=True),
        sa.Column('remote_or_local', sa.String(length=50), server_default='both', nullable=False),
        sa.Column('industry_experience_required', sa.String(length=255), nullable=True),
        sa.Column('preferred_agency_size', sa.String(length=50), nullable=True),
        sa.Column('expected_start_date', sa.String(length=100), nullable=True),
        sa.Column('special_requirements', sa.Text(), nullable=True),
        sa.Column('ai_search_brief', sa.Text(), nullable=True),
        sa.Column('ai_suggested_services', sa.JSON(), nullable=False),
        sa.Column('is_active', sa.Boolean(), server_default='1', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index('ix_seller_req_org', 'seller_agency_requirements', ['organization_id'])
    op.create_index('ix_seller_req_category', 'seller_agency_requirements', ['product_category'])

    # 6. agency_quote_requests
    op.create_table(
        'agency_quote_requests',
        sa.Column('id', backend.app.models.base.GUID(), primary_key=True, nullable=False),
        sa.Column('organization_id', backend.app.models.base.GUID(), sa.ForeignKey('organizations.id', ondelete='CASCADE'), nullable=False),
        sa.Column('agency_profile_id', backend.app.models.base.GUID(), sa.ForeignKey('agency_profiles.id', ondelete='CASCADE'), nullable=False),
        sa.Column('seller_requirement_id', backend.app.models.base.GUID(), sa.ForeignKey('seller_agency_requirements.id', ondelete='SET NULL'), nullable=True),
        sa.Column('project_title', sa.String(length=200), nullable=False),
        sa.Column('project_description', sa.Text(), nullable=False),
        sa.Column('budget_inr', sa.Integer(), nullable=False),
        sa.Column('budget_type', sa.String(length=50), server_default='monthly', nullable=False),
        sa.Column('timeframe', sa.String(length=100), nullable=False),
        sa.Column('attachment_urls', sa.JSON(), nullable=False),
        sa.Column('share_contact_consent', sa.Boolean(), server_default='1', nullable=False),
        sa.Column('contact_email', sa.String(length=255), nullable=False),
        sa.Column('contact_phone', sa.String(length=50), nullable=True),
        sa.Column('status', sa.String(length=50), server_default='submitted', nullable=False),
        sa.Column('agency_response_notes', sa.Text(), nullable=True),
        sa.Column('quotation_amount_inr', sa.Integer(), nullable=True),
        sa.Column('quotation_deliverables', sa.JSON(), nullable=True),
        sa.Column('quotation_valid_until', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index('ix_quote_requests_org', 'agency_quote_requests', ['organization_id'])
    op.create_index('ix_quote_requests_agency', 'agency_quote_requests', ['agency_profile_id'])
    op.create_index('ix_quote_requests_status', 'agency_quote_requests', ['status'])

    # 7. agency_engagements
    op.create_table(
        'agency_engagements',
        sa.Column('id', backend.app.models.base.GUID(), primary_key=True, nullable=False),
        sa.Column('quote_request_id', backend.app.models.base.GUID(), sa.ForeignKey('agency_quote_requests.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('organization_id', backend.app.models.base.GUID(), sa.ForeignKey('organizations.id', ondelete='CASCADE'), nullable=False),
        sa.Column('agency_profile_id', backend.app.models.base.GUID(), sa.ForeignKey('agency_profiles.id', ondelete='CASCADE'), nullable=False),
        sa.Column('package_id', backend.app.models.base.GUID(), sa.ForeignKey('agency_service_packages.id', ondelete='SET NULL'), nullable=True),
        sa.Column('agreed_price_inr', sa.Integer(), nullable=False),
        sa.Column('billing_type', sa.String(length=50), server_default='monthly', nullable=False),
        sa.Column('status', sa.String(length=50), server_default='in_progress', nullable=False),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index('ix_engagements_org', 'agency_engagements', ['organization_id'])
    op.create_index('ix_engagements_agency', 'agency_engagements', ['agency_profile_id'])
    op.create_index('ix_engagements_status', 'agency_engagements', ['status'])

    # 8. agency_saved_shortlists
    op.create_table(
        'agency_saved_shortlists',
        sa.Column('id', backend.app.models.base.GUID(), primary_key=True, nullable=False),
        sa.Column('organization_id', backend.app.models.base.GUID(), sa.ForeignKey('organizations.id', ondelete='CASCADE'), nullable=False),
        sa.Column('agency_profile_id', backend.app.models.base.GUID(), sa.ForeignKey('agency_profiles.id', ondelete='CASCADE'), nullable=False),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint('organization_id', 'agency_profile_id', name='uq_agency_saved_org'),
    )
    op.create_index('ix_saved_shortlists_org', 'agency_saved_shortlists', ['organization_id'])

    # 9. agency_reviews
    op.create_table(
        'agency_reviews',
        sa.Column('id', backend.app.models.base.GUID(), primary_key=True, nullable=False),
        sa.Column('engagement_id', backend.app.models.base.GUID(), sa.ForeignKey('agency_engagements.id', ondelete='CASCADE'), nullable=False, unique=True),
        sa.Column('organization_id', backend.app.models.base.GUID(), sa.ForeignKey('organizations.id', ondelete='CASCADE'), nullable=False),
        sa.Column('agency_profile_id', backend.app.models.base.GUID(), sa.ForeignKey('agency_profiles.id', ondelete='CASCADE'), nullable=False),
        sa.Column('rating', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(length=200), nullable=False),
        sa.Column('review_text', sa.Text(), nullable=False),
        sa.Column('is_verified', sa.Boolean(), server_default='1', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index('ix_agency_reviews_agency', 'agency_reviews', ['agency_profile_id'])


def downgrade() -> None:
    op.drop_table('agency_reviews')
    op.drop_table('agency_saved_shortlists')
    op.drop_table('agency_engagements')
    op.drop_table('agency_quote_requests')
    op.drop_table('seller_agency_requirements')
    op.drop_table('agency_portfolios')
    op.drop_table('agency_service_packages')
    op.drop_table('agency_services')
    op.drop_table('agency_profiles')

