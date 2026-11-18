"""003_analytics_and_billing_enhancements

Revision ID: 8b9d0e11c223
Revises: 7a8c9e10b112
Create Date: 2026-11-10 08:38:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import backend.app.models.base


# revision identifiers, used by Alembic.
revision: str = '8b9d0e11c223'
down_revision: Union[str, Sequence[str], None] = '7a8c9e10b112'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Enhance plans table
    with op.batch_alter_table('plans') as batch_op:
        batch_op.add_column(sa.Column('description', sa.Text(), nullable=True))
        batch_op.add_column(sa.Column('features', sa.JSON(), nullable=True))

    # 2. Enhance subscriptions table
    with op.batch_alter_table('subscriptions') as batch_op:
        batch_op.add_column(sa.Column('gateway_customer_id', sa.String(length=255), nullable=True))

    # 3. Enhance payments table
    with op.batch_alter_table('payments') as batch_op:
        batch_op.add_column(sa.Column('gateway_order_id', sa.String(length=255), nullable=True))
        batch_op.add_column(sa.Column('currency', sa.String(length=3), server_default='INR', nullable=False))
        batch_op.add_column(sa.Column('receipt_url', sa.Text(), nullable=True))

    # 4. Enhance service_orders table
    with op.batch_alter_table('service_orders') as batch_op:
        batch_op.add_column(sa.Column('due_date', sa.Date(), nullable=True))
        batch_op.add_column(sa.Column('requirements_json', sa.JSON(), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table('service_orders') as batch_op:
        batch_op.drop_column('requirements_json')
        batch_op.drop_column('due_date')

    with op.batch_alter_table('payments') as batch_op:
        batch_op.drop_column('receipt_url')
        batch_op.drop_column('currency')
        batch_op.drop_column('gateway_order_id')

    with op.batch_alter_table('subscriptions') as batch_op:
        batch_op.drop_column('gateway_customer_id')

    with op.batch_alter_table('plans') as batch_op:
        batch_op.drop_column('features')
        batch_op.drop_column('description')

