"""006_orders_and_sync_schema

Revision ID: b2c3d4e5f6a7
Revises: a1b2c3d4e5f6
Create Date: 2026-11-14 21:00:00.000000
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from backend.app.models.base import GUID

# revision identifiers, used by Alembic.
revision: str = 'b2c3d4e5f6a7'
down_revision: Union[str, None] = 'a1b2c3d4e5f6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Create channel_orders table
    op.create_table(
        'channel_orders',
        sa.Column('id', GUID(), primary_key=True),
        sa.Column('organization_id', GUID(), sa.ForeignKey('organizations.id', ondelete='CASCADE'), nullable=False),
        sa.Column('channel_connection_id', GUID(), sa.ForeignKey('channel_connections.id', ondelete='SET NULL'), nullable=True),
        sa.Column('channel_type', sa.String(50), nullable=False),
        sa.Column('remote_order_id', sa.String(255), nullable=False),
        sa.Column('order_number', sa.String(100), nullable=False),
        sa.Column('customer_email', sa.String(255), nullable=True),
        sa.Column('customer_name', sa.String(255), nullable=True),
        sa.Column('total_amount', sa.Numeric(12, 2), nullable=False),
        sa.Column('currency', sa.String(3), server_default='INR', nullable=False),
        sa.Column('financial_status', sa.String(50), server_default='paid', nullable=False),
        sa.Column('fulfillment_status', sa.String(50), server_default='unfulfilled', nullable=False),
        sa.Column('order_date', sa.DateTime(timezone=True), nullable=False),
        sa.Column('inventory_synced', sa.Boolean(), server_default=sa.false(), nullable=False),
        sa.Column('sync_status', sa.String(50), server_default='synced', nullable=False),
        sa.Column('sync_notes', sa.Text(), nullable=True),
        sa.Column('raw_payload', sa.JSON(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint('channel_connection_id', 'remote_order_id', name='uq_chan_order_remote')
    )
    op.create_index('ix_channel_orders_org_id', 'channel_orders', ['organization_id'])
    op.create_index('ix_channel_orders_channel_type', 'channel_orders', ['channel_type'])
    op.create_index('ix_channel_orders_remote_id', 'channel_orders', ['remote_order_id'])
    op.create_index('ix_channel_orders_financial', 'channel_orders', ['financial_status'])
    op.create_index('ix_channel_orders_fulfillment', 'channel_orders', ['fulfillment_status'])

    # 2. Create channel_order_items table
    op.create_table(
        'channel_order_items',
        sa.Column('id', GUID(), primary_key=True),
        sa.Column('order_id', GUID(), sa.ForeignKey('channel_orders.id', ondelete='CASCADE'), nullable=False),
        sa.Column('product_id', GUID(), sa.ForeignKey('products.id', ondelete='SET NULL'), nullable=True),
        sa.Column('product_variant_id', GUID(), sa.ForeignKey('product_variants.id', ondelete='SET NULL'), nullable=True),
        sa.Column('sku', sa.String(100), nullable=False),
        sa.Column('title', sa.String(255), nullable=False),
        sa.Column('quantity', sa.Integer(), server_default='1', nullable=False),
        sa.Column('unit_price', sa.Numeric(12, 2), nullable=False),
        sa.Column('total_price', sa.Numeric(12, 2), nullable=False),
        sa.Column('tax_amount', sa.Numeric(12, 2), server_default='0.0', nullable=True)
    )
    op.create_index('ix_channel_order_items_order_id', 'channel_order_items', ['order_id'])
    op.create_index('ix_channel_order_items_sku', 'channel_order_items', ['sku'])


def downgrade() -> None:
    op.drop_table('channel_order_items')
    op.drop_table('channel_orders')
