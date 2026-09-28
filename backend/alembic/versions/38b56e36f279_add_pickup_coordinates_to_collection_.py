from alembic import op
import sqlalchemy as sa


revision = "38b56e36f279"
down_revision = "81364da50d55"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "collection_requests",
        sa.Column(
            "pickup_latitude",
            sa.Numeric(10, 7),
            nullable=True,
        ),
    )

    op.add_column(
        "collection_requests",
        sa.Column(
            "pickup_longitude",
            sa.Numeric(10, 7),
            nullable=True,
        ),
    )


def downgrade() -> None:
    op.drop_column(
        "collection_requests",
        "pickup_longitude",
    )

    op.drop_column(
        "collection_requests",
        "pickup_latitude",
    )