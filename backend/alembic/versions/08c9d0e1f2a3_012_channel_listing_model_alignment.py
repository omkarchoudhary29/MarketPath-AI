"""012_channel_listing_model_alignment

Add the channel listing fields referenced by the current ChannelListing model.

Revision ID: 08c9d0e1f2a3
Revises: f7b8c9d0e1f2
Create Date: 2026-11-18 22:14:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

from backend.app.models.base import GUID


# revision identifiers, used by Alembic.
revision: str = "08c9d0e1f2a3"
down_revision: Union[str, None] = "f7b8c9d0e1f2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "channel_listings",
        sa.Column("organization_id", GUID(), nullable=True),
    )
    op.create_foreign_key(
        "fk_channel_listings_organization_id",
        "channel_listings",
        "organizations",
        ["organization_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.create_index(
        "ix_channel_listings_organization_id",
        "channel_listings",
        ["organization_id"],
        unique=False,
    )

    op.add_column(
        "channel_listings",
        sa.Column("remote_variant_id", sa.String(length=255), nullable=True),
    )
    op.add_column(
        "channel_listings",
        sa.Column("external_sku", sa.String(length=255), nullable=True),
    )
    op.add_column(
        "channel_listings",
        sa.Column("channel_title", sa.String(length=255), nullable=True),
    )
    op.add_column(
        "channel_listings",
        sa.Column("channel_price", sa.Float(), nullable=True),
    )
    op.add_column(
        "channel_listings",
        sa.Column("channel_attributes", sa.JSON(), nullable=True),
    )
    op.add_column(
        "channel_listings",
        sa.Column("last_error", sa.Text(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("channel_listings", "last_error")
    op.drop_column("channel_listings", "channel_attributes")
    op.drop_column("channel_listings", "channel_price")
    op.drop_column("channel_listings", "channel_title")
    op.drop_column("channel_listings", "external_sku")
    op.drop_column("channel_listings", "remote_variant_id")
    op.drop_index("ix_channel_listings_organization_id", table_name="channel_listings")
    op.drop_constraint("fk_channel_listings_organization_id", "channel_listings", type_="foreignkey")
    op.drop_column("channel_listings", "organization_id")
