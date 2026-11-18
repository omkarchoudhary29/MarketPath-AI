"""015_calendar_sync_model_alignment

Add external calendar integration and synchronization fields to business events.

Revision ID: 3bf2a3b4c5d6
Revises: 2ae1f2a3b4c5
Create Date: 2026-11-18 22:17:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "3bf2a3b4c5d6"
down_revision: Union[str, None] = "2ae1f2a3b4c5"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "business_calendar_events",
        sa.Column(
            "external_provider",
            sa.String(length=50),
            server_default=sa.text("'internal'"),
            nullable=False,
        ),
    )
    op.add_column(
        "business_calendar_events",
        sa.Column("external_calendar_id", sa.String(length=255), nullable=True),
    )
    op.add_column(
        "business_calendar_events",
        sa.Column("external_event_id", sa.String(length=255), nullable=True),
    )
    op.add_column(
        "business_calendar_events",
        sa.Column(
            "sync_status",
            sa.String(length=50),
            server_default=sa.text("'synced'"),
            nullable=False,
        ),
    )
    op.add_column(
        "business_calendar_events",
        sa.Column("last_synced_at", sa.DateTime(timezone=True), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("business_calendar_events", "last_synced_at")
    op.drop_column("business_calendar_events", "sync_status")
    op.drop_column("business_calendar_events", "external_event_id")
    op.drop_column("business_calendar_events", "external_calendar_id")
    op.drop_column("business_calendar_events", "external_provider")
