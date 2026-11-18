"""002_campaign_enhancements

Revision ID: 7a8c9e10b112
Revises: 6f6b7de9a303
Create Date: 2026-11-10 08:20:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import backend.app.models.base


# revision identifiers, used by Alembic.
revision: str = '7a8c9e10b112'
down_revision: Union[str, Sequence[str], None] = '6f6b7de9a303'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table('campaigns') as batch_op:
        batch_op.add_column(sa.Column('product_id', backend.app.models.base.GUID(), nullable=True))
        batch_op.add_column(sa.Column('channel', sa.String(length=50), server_default='meta_ads', nullable=False))
        batch_op.add_column(sa.Column('target_geography', sa.String(length=100), server_default='Pan-India', nullable=True))
        batch_op.add_column(sa.Column('landing_page_url', sa.Text(), nullable=True))
        batch_op.add_column(sa.Column('call_to_action', sa.String(length=50), server_default='Shop Now', nullable=True))
        batch_op.add_column(sa.Column('creative_format', sa.String(length=50), server_default='feed_image', nullable=True))
        batch_op.add_column(sa.Column('description', sa.Text(), nullable=True))
        batch_op.add_column(sa.Column('utm_params', sa.JSON(), nullable=True))
        batch_op.add_column(sa.Column('ai_proposal', sa.JSON(), nullable=True))
        batch_op.add_column(sa.Column('manual_setup_instructions', sa.JSON(), nullable=True))
        batch_op.add_column(sa.Column('rejection_reason', sa.Text(), nullable=True))
        batch_op.create_index(batch_op.f('ix_campaigns_product_id'), ['product_id'], unique=False)

    with op.batch_alter_table('campaign_creatives') as batch_op:
        batch_op.add_column(sa.Column('description_text', sa.Text(), nullable=True))
        batch_op.add_column(sa.Column('format', sa.String(length=50), server_default='feed_image', nullable=False))
        batch_op.add_column(sa.Column('version_number', sa.Integer(), server_default='1', nullable=False))
        batch_op.add_column(sa.Column('is_approved', sa.Boolean(), server_default='0', nullable=False))

    with op.batch_alter_table('external_campaigns') as batch_op:
        batch_op.add_column(sa.Column('platform', sa.String(length=50), server_default='meta_ads', nullable=False))
        batch_op.add_column(sa.Column('last_synced_at', sa.DateTime(timezone=True), nullable=True))

    with op.batch_alter_table('campaign_metrics_daily') as batch_op:
        batch_op.add_column(sa.Column('reach', sa.Integer(), server_default='0', nullable=True))


def downgrade() -> None:
    with op.batch_alter_table('campaign_metrics_daily') as batch_op:
        batch_op.drop_column('reach')

    with op.batch_alter_table('external_campaigns') as batch_op:
        batch_op.drop_column('last_synced_at')
        batch_op.drop_column('platform')

    with op.batch_alter_table('campaign_creatives') as batch_op:
        batch_op.drop_column('is_approved')
        batch_op.drop_column('version_number')
        batch_op.drop_column('format')
        batch_op.drop_column('description_text')

    with op.batch_alter_table('campaigns') as batch_op:
        batch_op.drop_index(batch_op.f('ix_campaigns_product_id'))
        batch_op.drop_column('rejection_reason')
        batch_op.drop_column('manual_setup_instructions')
        batch_op.drop_column('ai_proposal')
        batch_op.drop_column('utm_params')
        batch_op.drop_column('description')
        batch_op.drop_column('creative_format')
        batch_op.drop_column('call_to_action')
        batch_op.drop_column('landing_page_url')
        batch_op.drop_column('target_geography')
        batch_op.drop_column('channel')
        batch_op.drop_column('product_id')

