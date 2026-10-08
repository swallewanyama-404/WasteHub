"""resident profiles and service billing

Revision ID: d41b7c2e9f10
Revises: 8f2c9a1d7b44
Create Date: 2026-10-08
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "d41b7c2e9f10"
down_revision: Union[str, Sequence[str], None] = "8f2c9a1d7b44"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("users", sa.Column("client_type", sa.String(length=40), nullable=True))
    op.add_column("users", sa.Column("default_address", sa.String(length=500), nullable=True))
    op.add_column("users", sa.Column("default_latitude", sa.Numeric(10, 7), nullable=True))
    op.add_column("users", sa.Column("default_longitude", sa.Numeric(10, 7), nullable=True))
    op.add_column("users", sa.Column("collection_weekday", sa.Integer(), server_default="0", nullable=False))

    # SQLAlchemy stores enum member names in PostgreSQL for this model.
    op.execute("ALTER TYPE collection_request_status ADD VALUE IF NOT EXISTS 'PAYMENT_PENDING'")

    op.add_column(
        "payments",
        sa.Column("payment_type", sa.String(length=40), server_default="urgent_pickup", nullable=False),
    )
    op.create_index("ix_payments_payment_type", "payments", ["payment_type"], unique=False)
    op.alter_column("payments", "request_id", existing_type=sa.Integer(), nullable=True)


def downgrade() -> None:
    op.alter_column("payments", "request_id", existing_type=sa.Integer(), nullable=False)
    op.drop_index("ix_payments_payment_type", table_name="payments")
    op.drop_column("payments", "payment_type")

    op.drop_column("users", "collection_weekday")
    op.drop_column("users", "default_longitude")
    op.drop_column("users", "default_latitude")
    op.drop_column("users", "default_address")
    op.drop_column("users", "client_type")
    # PostgreSQL enum values are intentionally retained on downgrade.
