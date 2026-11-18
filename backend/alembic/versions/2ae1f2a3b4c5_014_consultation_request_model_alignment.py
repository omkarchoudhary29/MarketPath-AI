"""014_consultation_request_model_alignment

Add consultation lifecycle, assignment, reporting, delivery and reference fields
required by the current ConsultationRequest model.

Revision ID: 2ae1f2a3b4c5
Revises: 19d0e1f2a3b4
Create Date: 2026-11-18 22:16:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

from backend.app.models.base import GUID


# revision identifiers, used by Alembic.
revision: str = "2ae1f2a3b4c5"
down_revision: Union[str, None] = "19d0e1f2a3b4"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Populate stable unique references for pre-existing consultation rows.
    op.add_column(
        "consultation_requests",
        sa.Column("reference_code", sa.String(length=50), nullable=True),
    )
    op.execute(
        "UPDATE consultation_requests "
        "SET reference_code = 'MP-LEGACY-' || upper(replace(id::text, '-', '')) "
        "WHERE reference_code IS NULL"
    )
    op.alter_column(
        "consultation_requests",
        "reference_code",
        existing_type=sa.String(length=50),
        nullable=False,
    )
    op.create_index(
        "ix_consultation_requests_reference_code",
        "consultation_requests",
        ["reference_code"],
        unique=True,
    )

    op.add_column(
        "consultation_requests",
        sa.Column(
            "timezone",
            sa.String(length=50),
            server_default=sa.text("'Asia/Kolkata'"),
            nullable=False,
        ),
    )
    op.add_column(
        "consultation_requests",
        sa.Column("assigned_consultant_id", GUID(), nullable=True),
    )
    op.create_foreign_key(
        "fk_consultation_requests_assigned_consultant",
        "consultation_requests",
        "user_profiles",
        ["assigned_consultant_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_index(
        "ix_consultation_requests_assigned_consultant_id",
        "consultation_requests",
        ["assigned_consultant_id"],
        unique=False,
    )
    op.add_column(
        "consultation_requests",
        sa.Column("assigned_consultant_name", sa.String(length=150), nullable=True),
    )
    op.add_column(
        "consultation_requests",
        sa.Column(
            "scheduled_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
    )
    op.add_column(
        "consultation_requests",
        sa.Column(
            "duration_minutes",
            sa.Integer(),
            server_default=sa.text("30"),
            nullable=False,
        ),
    )
    op.add_column(
        "consultation_requests",
        sa.Column("meeting_link", sa.String(length=255), nullable=True),
    )
    op.add_column("consultation_requests", sa.Column("internal_notes", sa.Text(), nullable=True))
    op.add_column("consultation_requests", sa.Column("report_summary", sa.Text(), nullable=True))
    op.add_column(
        "consultation_requests",
        sa.Column(
            "recommendations",
            sa.JSON(),
            server_default=sa.text("'[]'::json"),
            nullable=False,
        ),
    )
    op.add_column(
        "consultation_requests",
        sa.Column(
            "action_items",
            sa.JSON(),
            server_default=sa.text("'[]'::json"),
            nullable=False,
        ),
    )
    op.add_column(
        "consultation_requests",
        sa.Column("cancellation_reason", sa.Text(), nullable=True),
    )
    op.add_column(
        "consultation_requests",
        sa.Column(
            "email_delivery_status",
            sa.String(length=50),
            server_default=sa.text("'unconfigured_provider'"),
            nullable=False,
        ),
    )
    op.alter_column(
        "consultation_requests",
        "status",
        existing_type=sa.String(length=50),
        server_default=sa.text("'submitted'"),
    )


def downgrade() -> None:
    op.alter_column(
        "consultation_requests",
        "status",
        existing_type=sa.String(length=50),
        server_default=sa.text("'pending'"),
    )
    op.drop_column("consultation_requests", "email_delivery_status")
    op.drop_column("consultation_requests", "cancellation_reason")
    op.drop_column("consultation_requests", "action_items")
    op.drop_column("consultation_requests", "recommendations")
    op.drop_column("consultation_requests", "report_summary")
    op.drop_column("consultation_requests", "internal_notes")
    op.drop_column("consultation_requests", "meeting_link")
    op.drop_column("consultation_requests", "duration_minutes")
    op.drop_column("consultation_requests", "scheduled_at")
    op.drop_column("consultation_requests", "assigned_consultant_name")
    op.drop_index(
        "ix_consultation_requests_assigned_consultant_id",
        table_name="consultation_requests",
    )
    op.drop_constraint(
        "fk_consultation_requests_assigned_consultant",
        "consultation_requests",
        type_="foreignkey",
    )
    op.drop_column("consultation_requests", "assigned_consultant_id")
    op.drop_column("consultation_requests", "timezone")
    op.drop_index(
        "ix_consultation_requests_reference_code",
        table_name="consultation_requests",
    )
    op.drop_column("consultation_requests", "reference_code")
