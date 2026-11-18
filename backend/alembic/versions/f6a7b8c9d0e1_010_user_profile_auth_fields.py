"""010_user_profile_auth_fields

Add the account security and lifecycle fields used by the current UserProfile model.

Revision ID: f6a7b8c9d0e1
Revises: e5f6a7b8c9d0
Create Date: 2026-11-18 22:10:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "f6a7b8c9d0e1"
down_revision: Union[str, None] = "e5f6a7b8c9d0"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # These fields are referenced by UserProfile and authentication flows.
    # Explicit server defaults make the migration safe for existing rows.
    op.add_column(
        "user_profiles",
        sa.Column("is_active", sa.Boolean(), server_default=sa.true(), nullable=False),
    )
    op.add_column(
        "user_profiles",
        sa.Column("must_change_password", sa.Boolean(), server_default=sa.false(), nullable=False),
    )
    op.add_column(
        "user_profiles",
        sa.Column("mfa_enabled", sa.Boolean(), server_default=sa.false(), nullable=False),
    )
    op.add_column(
        "user_profiles",
        sa.Column("mfa_secret", sa.String(length=100), nullable=True),
    )
    op.add_column(
        "user_profiles",
        sa.Column(
            "vetting_status",
            sa.String(length=50),
            server_default=sa.text("'approved'"),
            nullable=False,
        ),
    )


def downgrade() -> None:
    op.drop_column("user_profiles", "vetting_status")
    op.drop_column("user_profiles", "mfa_secret")
    op.drop_column("user_profiles", "mfa_enabled")
    op.drop_column("user_profiles", "must_change_password")
    op.drop_column("user_profiles", "is_active")
