"""011_inventory_stock_levels_and_ledger

Create the stock balance and immutable inventory movement tables used by the inventory module.

Revision ID: f7b8c9d0e1f2
Revises: f6a7b8c9d0e1
Create Date: 2026-11-18 22:13:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

from backend.app.models.base import GUID


# revision identifiers, used by Alembic.
revision: str = "f7b8c9d0e1f2"
down_revision: Union[str, None] = "f6a7b8c9d0e1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "stock_levels",
        sa.Column("id", GUID(), nullable=False),
        sa.Column("organization_id", GUID(), nullable=False),
        sa.Column("product_id", GUID(), nullable=False),
        sa.Column("product_variant_id", GUID(), nullable=False),
        sa.Column("sku", sa.String(length=100), nullable=False),
        sa.Column("location_id", sa.String(length=100), server_default=sa.text("'primary_warehouse'"), nullable=False),
        sa.Column("physical_stock", sa.Integer(), server_default="0", nullable=False),
        sa.Column("reserved_stock", sa.Integer(), server_default="0", nullable=False),
        sa.Column("available_to_sell", sa.Integer(), server_default="0", nullable=False),
        sa.Column("committed_stock", sa.Integer(), server_default="0", nullable=False),
        sa.Column("damaged_stock", sa.Integer(), server_default="0", nullable=False),
        sa.Column("returned_stock", sa.Integer(), server_default="0", nullable=False),
        sa.Column("reorder_point", sa.Integer(), server_default="10", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["product_id"], ["products.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["product_variant_id"], ["product_variants.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("organization_id", "product_variant_id", "location_id", name="uq_stock_loc_variant"),
    )
    op.create_index("ix_stock_levels_organization_id", "stock_levels", ["organization_id"], unique=False)
    op.create_index("ix_stock_levels_product_id", "stock_levels", ["product_id"], unique=False)
    op.create_index("ix_stock_levels_product_variant_id", "stock_levels", ["product_variant_id"], unique=False)
    op.create_index("ix_stock_levels_sku", "stock_levels", ["sku"], unique=False)

    op.create_table(
        "inventory_ledger",
        sa.Column("id", GUID(), nullable=False),
        sa.Column("organization_id", GUID(), nullable=False),
        sa.Column("product_id", GUID(), nullable=False),
        sa.Column("product_variant_id", GUID(), nullable=False),
        sa.Column("sku", sa.String(length=100), nullable=False),
        sa.Column("location_id", sa.String(length=100), server_default=sa.text("'primary_warehouse'"), nullable=False),
        sa.Column("movement_type", sa.String(length=50), nullable=False),
        sa.Column("quantity_change", sa.Integer(), nullable=False),
        sa.Column("previous_quantity", sa.Integer(), server_default="0", nullable=False),
        sa.Column("new_quantity", sa.Integer(), server_default="0", nullable=False),
        sa.Column("source_type", sa.String(length=50), server_default=sa.text("'manual'"), nullable=False),
        sa.Column("source_id", sa.String(length=100), nullable=True),
        sa.Column("actor_id", GUID(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["product_id"], ["products.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["product_variant_id"], ["product_variants.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["actor_id"], ["user_profiles.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_inventory_ledger_organization_id", "inventory_ledger", ["organization_id"], unique=False)
    op.create_index("ix_inventory_ledger_product_id", "inventory_ledger", ["product_id"], unique=False)
    op.create_index("ix_inventory_ledger_product_variant_id", "inventory_ledger", ["product_variant_id"], unique=False)
    op.create_index("ix_inventory_ledger_sku", "inventory_ledger", ["sku"], unique=False)
    op.create_index("ix_inventory_ledger_movement_type", "inventory_ledger", ["movement_type"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_inventory_ledger_movement_type", table_name="inventory_ledger")
    op.drop_index("ix_inventory_ledger_sku", table_name="inventory_ledger")
    op.drop_index("ix_inventory_ledger_product_variant_id", table_name="inventory_ledger")
    op.drop_index("ix_inventory_ledger_product_id", table_name="inventory_ledger")
    op.drop_index("ix_inventory_ledger_organization_id", table_name="inventory_ledger")
    op.drop_table("inventory_ledger")

    op.drop_index("ix_stock_levels_sku", table_name="stock_levels")
    op.drop_index("ix_stock_levels_product_variant_id", table_name="stock_levels")
    op.drop_index("ix_stock_levels_product_id", table_name="stock_levels")
    op.drop_index("ix_stock_levels_organization_id", table_name="stock_levels")
    op.drop_table("stock_levels")
