"""add vehicle and GPS tracking

Revision ID: 17dec64ec620
Revises: 38b56e36f279
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "17dec64ec620"
down_revision: Union[str, Sequence[str], None] = "38b56e36f279"
branch_labels = None
depends_on = None


def upgrade() -> None:
    vehicle_status = sa.Enum(
        "available",
        "assigned",
        "on_route",
        "maintenance",
        "inactive",
        name="vehicle_status",
        create_type=False,
    )

    op.execute(
        """
        CREATE TYPE vehicle_status AS ENUM (
            'available',
            'assigned',
            'on_route',
            'maintenance',
            'inactive'
        )
        """
    )

    op.create_table(
        "vehicles",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column(
            "provider_id",
            sa.Integer(),
            nullable=False,
        ),
        sa.Column(
            "registration_number",
            sa.String(length=30),
            nullable=False,
        ),
        sa.Column(
            "vehicle_type",
            sa.String(length=100),
            nullable=False,
        ),
        sa.Column(
            "status",
            vehicle_status,
            nullable=False,
        ),
        sa.Column(
            "is_active",
            sa.Boolean(),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["provider_id"],
            ["service_providers.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_index(
        "ix_vehicles_id",
        "vehicles",
        ["id"],
        unique=False,
    )

    op.create_index(
        "ix_vehicles_provider_id",
        "vehicles",
        ["provider_id"],
        unique=False,
    )

    op.create_index(
        "ix_vehicles_registration_number",
        "vehicles",
        ["registration_number"],
        unique=True,
    )

    op.create_index(
        "ix_vehicles_status",
        "vehicles",
        ["status"],
        unique=False,
    )

    op.create_table(
        "tracking_sessions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column(
            "assignment_id",
            sa.Integer(),
            nullable=False,
        ),
        sa.Column(
            "vehicle_id",
            sa.Integer(),
            nullable=False,
        ),
        sa.Column(
            "collector_id",
            sa.Integer(),
            nullable=False,
        ),
        sa.Column(
            "started_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "ended_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["assignment_id"],
            ["collection_assignments.id"],
        ),
        sa.ForeignKeyConstraint(
            ["vehicle_id"],
            ["vehicles.id"],
        ),
        sa.ForeignKeyConstraint(
            ["collector_id"],
            ["users.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_index(
        "ix_tracking_sessions_id",
        "tracking_sessions",
        ["id"],
        unique=False,
    )

    op.create_index(
        "ix_tracking_sessions_assignment_id",
        "tracking_sessions",
        ["assignment_id"],
        unique=False,
    )

    op.create_index(
        "ix_tracking_sessions_vehicle_id",
        "tracking_sessions",
        ["vehicle_id"],
        unique=False,
    )

    op.create_index(
        "ix_tracking_sessions_collector_id",
        "tracking_sessions",
        ["collector_id"],
        unique=False,
    )

    op.create_table(
        "vehicle_locations",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column(
            "tracking_session_id",
            sa.Integer(),
            nullable=False,
        ),
        sa.Column(
            "latitude",
            sa.Numeric(precision=10, scale=7),
            nullable=False,
        ),
        sa.Column(
            "longitude",
            sa.Numeric(precision=10, scale=7),
            nullable=False,
        ),
        sa.Column(
            "accuracy_meters",
            sa.Numeric(precision=8, scale=2),
            nullable=True,
        ),
        sa.Column(
            "speed_kmh",
            sa.Numeric(precision=8, scale=2),
            nullable=True,
        ),
        sa.Column(
            "heading_degrees",
            sa.Numeric(precision=6, scale=2),
            nullable=True,
        ),
        sa.Column(
            "recorded_at",
            sa.DateTime(timezone=True),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["tracking_session_id"],
            ["tracking_sessions.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_index(
        "ix_vehicle_locations_id",
        "vehicle_locations",
        ["id"],
        unique=False,
    )

    op.create_index(
        "ix_vehicle_locations_tracking_session_id",
        "vehicle_locations",
        ["tracking_session_id"],
        unique=False,
    )

    op.create_index(
        "ix_vehicle_locations_recorded_at",
        "vehicle_locations",
        ["recorded_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        "ix_vehicle_locations_recorded_at",
        table_name="vehicle_locations",
    )

    op.drop_index(
        "ix_vehicle_locations_tracking_session_id",
        table_name="vehicle_locations",
    )

    op.drop_index(
        "ix_vehicle_locations_id",
        table_name="vehicle_locations",
    )

    op.drop_table("vehicle_locations")

    op.drop_index(
        "ix_tracking_sessions_collector_id",
        table_name="tracking_sessions",
    )

    op.drop_index(
        "ix_tracking_sessions_vehicle_id",
        table_name="tracking_sessions",
    )

    op.drop_index(
        "ix_tracking_sessions_assignment_id",
        table_name="tracking_sessions",
    )

    op.drop_index(
        "ix_tracking_sessions_id",
        table_name="tracking_sessions",
    )

    op.drop_table("tracking_sessions")

    op.drop_index(
        "ix_vehicles_status",
        table_name="vehicles",
    )

    op.drop_index(
        "ix_vehicles_registration_number",
        table_name="vehicles",
    )

    op.drop_index(
        "ix_vehicles_provider_id",
        table_name="vehicles",
    )

    op.drop_index(
        "ix_vehicles_id",
        table_name="vehicles",
    )

    op.drop_table("vehicles")

    op.execute("DROP TYPE IF EXISTS vehicle_status")