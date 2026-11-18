"""009_consultation_availability_and_idempotency

Revision ID: e5f6a7b8c9d0
Revises: d4e5f6a7b8c9
Create Date: 2026-11-16 15:15:00.000000
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from backend.app.models.base import GUID

# revision identifiers, used by Alembic.
revision: str = 'e5f6a7b8c9d0'
down_revision: Union[str, None] = 'd4e5f6a7b8c9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Add idempotency_key to consultation_requests
    op.add_column('consultation_requests', sa.Column('idempotency_key', sa.String(length=64), nullable=True))
    op.create_index('ix_consultation_requests_idempotency_key', 'consultation_requests', ['idempotency_key'])

    # 2. Create consultation_availability_rules table
    op.create_table(
        'consultation_availability_rules',
        sa.Column('id', GUID(), primary_key=True),
        sa.Column('rule_type', sa.String(length=50), server_default='blocked_date', nullable=False),
        sa.Column('specific_date', sa.Date(), nullable=True),
        sa.Column('day_of_week', sa.Integer(), nullable=True),
        sa.Column('start_time', sa.String(length=20), nullable=True),
        sa.Column('end_time', sa.String(length=20), nullable=True),
        sa.Column('slot_capacity', sa.Integer(), server_default='1', nullable=False),
        sa.Column('is_blocked', sa.Boolean(), server_default=sa.text('1'), nullable=False),
        sa.Column('notes', sa.String(length=255), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index('ix_consultation_avail_rules_date', 'consultation_availability_rules', ['specific_date'])


def downgrade() -> None:
    op.drop_index('ix_consultation_avail_rules_date', table_name='consultation_availability_rules')
    op.drop_table('consultation_availability_rules')
    op.drop_index('ix_consultation_requests_idempotency_key', table_name='consultation_requests')
    op.drop_column('consultation_requests', 'idempotency_key')
