"""013_order_and_returns_model_alignment

Align persisted order and returns schema with the current SQLAlchemy models.

Revision ID: 19d0e1f2a3b4
Revises: 08c9d0e1f2a3
Create Date: 2026-11-18 22:15:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

from backend.app.models.base import GUID


# revision identifiers, used by Alembic.
revision: str = "19d0e1f2a3b4"
down_revision: Union[str, None] = "08c9d0e1f2a3"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Complete channel_orders fields added to the current ChannelOrder model.
    for name in (
        "subtotal",
        "discount_amount",
        "shipping_amount",
        "tax_amount",
        "refund_amount",
    ):
        op.add_column(
            "channel_orders",
            sa.Column(
                name,
                sa.Numeric(12, 2),
                server_default=sa.text("0"),
                nullable=False,
            ),
        )

    op.add_column(
        "channel_orders",
        sa.Column(
            "order_lifecycle_status",
            sa.String(length=50),
            server_default=sa.text("'new'"),
            nullable=False,
        ),
    )
    op.add_column(
        "channel_orders",
        sa.Column(
            "shipping_address",
            sa.JSON(),
            server_default=sa.text("'{}'::json"),
            nullable=False,
        ),
    )
    op.add_column(
        "channel_orders",
        sa.Column(
            "billing_address",
            sa.JSON(),
            server_default=sa.text("'{}'::json"),
            nullable=False,
        ),
    )
    op.add_column("channel_orders", sa.Column("tracking_number", sa.String(length=100), nullable=True))
    op.add_column("channel_orders", sa.Column("carrier", sa.String(length=100), nullable=True))
    op.add_column("channel_orders", sa.Column("tracking_url", sa.Text(), nullable=True))
    op.add_column(
        "channel_orders",
        sa.Column("last_external_update_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column("channel_orders", sa.Column("cancellation_reason", sa.Text(), nullable=True))
    op.create_index(
        "ix_channel_orders_order_lifecycle_status",
        "channel_orders",
        ["order_lifecycle_status"],
        unique=False,
    )

    # Complete channel_order_items fields used by the current ChannelOrderItem model.
    op.add_column("channel_order_items", sa.Column("external_sku", sa.String(length=100), nullable=True))
    op.add_column(
        "channel_order_items",
        sa.Column("external_product_id", sa.String(length=255), nullable=True),
    )
    op.add_column(
        "channel_order_items",
        sa.Column("external_variant_id", sa.String(length=255), nullable=True),
    )
    op.add_column(
        "channel_order_items",
        sa.Column(
            "discount_amount",
            sa.Numeric(12, 2),
            server_default=sa.text("0"),
            nullable=False,
        ),
    )
    op.add_column(
        "channel_order_items",
        sa.Column(
            "returned_quantity",
            sa.Integer(),
            server_default=sa.text("0"),
            nullable=False,
        ),
    )
    op.add_column(
        "channel_order_items",
        sa.Column(
            "mapping_status",
            sa.String(length=30),
            server_default=sa.text("'mapped'"),
            nullable=False,
        ),
    )
    op.create_index(
        "ix_channel_order_items_product_id",
        "channel_order_items",
        ["product_id"],
        unique=False,
    )
    op.create_index(
        "ix_channel_order_items_product_variant_id",
        "channel_order_items",
        ["product_variant_id"],
        unique=False,
    )

    # Return management tables are part of the ORM but were absent from migration 006.
    op.create_table(
        "return_requests",
        sa.Column("id", GUID(), nullable=False),
        sa.Column("organization_id", GUID(), nullable=False),
        sa.Column("order_id", GUID(), nullable=False),
        sa.Column("return_number", sa.String(length=100), nullable=False),
        sa.Column(
            "status",
            sa.String(length=50),
            server_default=sa.text("'requested'"),
            nullable=False,
        ),
        sa.Column("reason", sa.String(length=255), nullable=False),
        sa.Column("tracking_number", sa.String(length=100), nullable=True),
        sa.Column("carrier", sa.String(length=100), nullable=True),
        sa.Column("authorized_by", GUID(), nullable=True),
        sa.Column("received_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("inspected_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "total_refund_amount",
            sa.Numeric(12, 2),
            server_default=sa.text("0"),
            nullable=False,
        ),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["order_id"], ["channel_orders.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("return_number", name="uq_return_requests_return_number"),
    )
    op.create_index(
        "ix_return_requests_organization_id",
        "return_requests",
        ["organization_id"],
        unique=False,
    )
    op.create_index(
        "ix_return_requests_order_id",
        "return_requests",
        ["order_id"],
        unique=False,
    )
    op.create_index(
        "ix_return_requests_return_number",
        "return_requests",
        ["return_number"],
        unique=True,
    )
    op.create_index(
        "ix_return_requests_status",
        "return_requests",
        ["status"],
        unique=False,
    )

    op.create_table(
        "return_items",
        sa.Column("id", GUID(), nullable=False),
        sa.Column("return_request_id", GUID(), nullable=False),
        sa.Column("order_item_id", GUID(), nullable=True),
        sa.Column("product_id", GUID(), nullable=True),
        sa.Column("product_variant_id", GUID(), nullable=True),
        sa.Column("sku", sa.String(length=100), nullable=False),
        sa.Column("quantity_ordered", sa.Integer(), server_default=sa.text("1"), nullable=False),
        sa.Column(
            "quantity_previously_returned",
            sa.Integer(),
            server_default=sa.text("0"),
            nullable=False,
        ),
        sa.Column("quantity_requested", sa.Integer(), server_default=sa.text("1"), nullable=False),
        sa.Column("quantity_received", sa.Integer(), server_default=sa.text("0"), nullable=False),
        sa.Column(
            "inspection_result",
            sa.String(length=50),
            server_default=sa.text("'pending'"),
            nullable=False,
        ),
        sa.Column("resalable_quantity", sa.Integer(), server_default=sa.text("0"), nullable=False),
        sa.Column("damaged_quantity", sa.Integer(), server_default=sa.text("0"), nullable=False),
        sa.Column("refund_amount", sa.Numeric(12, 2), server_default=sa.text("0"), nullable=False),
        sa.Column("restocked", sa.Boolean(), server_default=sa.false(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["return_request_id"], ["return_requests.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["order_item_id"], ["channel_order_items.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["product_id"], ["products.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["product_variant_id"], ["product_variants.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_return_items_return_request_id", "return_items", ["return_request_id"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_return_items_return_request_id", table_name="return_items")
    op.drop_table("return_items")

    op.drop_index("ix_return_requests_status", table_name="return_requests")
    op.drop_index("ix_return_requests_return_number", table_name="return_requests")
    op.drop_index("ix_return_requests_order_id", table_name="return_requests")
    op.drop_index("ix_return_requests_organization_id", table_name="return_requests")
    op.drop_table("return_requests")

    op.drop_index("ix_channel_order_items_product_variant_id", table_name="channel_order_items")
    op.drop_index("ix_channel_order_items_product_id", table_name="channel_order_items")
    op.drop_column("channel_order_items", "mapping_status")
    op.drop_column("channel_order_items", "returned_quantity")
    op.drop_column("channel_order_items", "discount_amount")
    op.drop_column("channel_order_items", "external_variant_id")
    op.drop_column("channel_order_items", "external_product_id")
    op.drop_column("channel_order_items", "external_sku")

    op.drop_index("ix_channel_orders_order_lifecycle_status", table_name="channel_orders")
    op.drop_column("channel_orders", "cancellation_reason")
    op.drop_column("channel_orders", "last_external_update_at")
    op.drop_column("channel_orders", "tracking_url")
    op.drop_column("channel_orders", "carrier")
    op.drop_column("channel_orders", "tracking_number")
    op.drop_column("channel_orders", "billing_address")
    op.drop_column("channel_orders", "shipping_address")
    op.drop_column("channel_orders", "order_lifecycle_status")
    op.drop_column("channel_orders", "refund_amount")
    op.drop_column("channel_orders", "tax_amount")
    op.drop_column("channel_orders", "shipping_amount")
    op.drop_column("channel_orders", "discount_amount")
    op.drop_column("channel_orders", "subtotal")
