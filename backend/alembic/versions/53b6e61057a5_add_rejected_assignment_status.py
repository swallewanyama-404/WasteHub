"""add rejected assignment status

Revision ID: 53b6e61057a5
Revises: 17dec64ec620
Create Date: 2026-09-29 18:03:19.960999

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa



# revision identifiers, used by Alembic.
revision: str = '53b6e61057a5'
down_revision: Union[str, Sequence[str], None] = '17dec64ec620'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        """
        ALTER TYPE assignment_status
        ADD VALUE IF NOT EXISTS 'REJECTED'
        """
    )


def downgrade() -> None:
    pass