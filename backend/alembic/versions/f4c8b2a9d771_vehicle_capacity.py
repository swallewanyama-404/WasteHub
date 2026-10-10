"""add vehicle capacity

Revision ID: f4c8b2a9d771
Revises: e8f9a1c3d2b4
Create Date: 2026-10-10
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "f4c8b2a9d771"
down_revision: Union[str, Sequence[str], None] = "e8f9a1c3d2b4"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "vehicles",
        sa.Column("capacity_tons", sa.Numeric(8, 2), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("vehicles", "capacity_tons")
