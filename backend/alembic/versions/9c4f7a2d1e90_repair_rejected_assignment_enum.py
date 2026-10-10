"""repair rejected assignment enum

Revision ID: 9c4f7a2d1e90
Revises: 8f2c9a1d7b44
Create Date: 2026-10-02

"""
from typing import Sequence, Union

from alembic import op


revision: str = "9c4f7a2d1e90"
down_revision: Union[str, Sequence[str], None] = "8f2c9a1d7b44"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Existing development databases may contain a lowercase value from the
    # first Stage 9 migration. SQLAlchemy stores this enum by member name,
    # so ensure the canonical uppercase value exists.
    op.execute(
        """
        ALTER TYPE assignment_status
        ADD VALUE IF NOT EXISTS 'REJECTED'
        """
    )


def downgrade() -> None:
    # PostgreSQL enum values cannot be removed safely without rebuilding the
    # enum type. Leaving the value in place is the safe downgrade behavior.
    pass
