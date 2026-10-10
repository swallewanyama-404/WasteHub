"""set operational payment provider default

Revision ID: b7e2c4d9a110
Revises: f4c8b2a9d771
Create Date: 2026-10-10
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "b7e2c4d9a110"
down_revision: Union[str, Sequence[str], None] = "f4c8b2a9d771"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column(
        "payments",
        "provider",
        existing_type=sa.String(length=50),
        server_default="manual_verification",
        existing_nullable=False,
    )


def downgrade() -> None:
    op.alter_column(
        "payments",
        "provider",
        existing_type=sa.String(length=50),
        server_default=None,
        existing_nullable=False,
    )
