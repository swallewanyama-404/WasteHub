"""multi organization contacts and routing

Revision ID: e8f9a1c3d2b4
Revises: d41b7c2e9f10
Create Date: 2026-10-10
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "e8f9a1c3d2b4"
down_revision: Union[str, Sequence[str], None] = "d41b7c2e9f10"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("zones", sa.Column("municipality", sa.String(length=150), nullable=True))
    op.add_column("zones", sa.Column("center_latitude", sa.Numeric(10, 7), nullable=True))
    op.add_column("zones", sa.Column("center_longitude", sa.Numeric(10, 7), nullable=True))
    op.add_column("zones", sa.Column("radius_km", sa.Numeric(8, 2), nullable=True))
    op.create_index("ix_zones_municipality", "zones", ["municipality"], unique=False)

    op.add_column("service_providers", sa.Column("registered_address", sa.String(length=500), nullable=True))
    op.add_column("service_providers", sa.Column("website", sa.String(length=255), nullable=True))
    op.add_column("service_providers", sa.Column("company_registration_number", sa.String(length=120), nullable=True))
    op.add_column("service_providers", sa.Column("tin", sa.String(length=80), nullable=True))
    op.add_column("service_providers", sa.Column("nema_license_number", sa.String(length=120), nullable=True))
    op.add_column("service_providers", sa.Column("kcca_trading_license_number", sa.String(length=120), nullable=True))
    op.add_column("service_providers", sa.Column("tax_clearance_reference", sa.String(length=120), nullable=True))
    op.add_column("service_providers", sa.Column("powers_of_attorney_reference", sa.String(length=120), nullable=True))
    op.add_column("service_providers", sa.Column("gazette_reference", sa.String(length=180), nullable=True))
    op.add_column("service_providers", sa.Column("disposal_facility_name", sa.String(length=200), nullable=True))
    op.add_column("service_providers", sa.Column("disposal_facility_location", sa.String(length=500), nullable=True))
    op.add_column("service_providers", sa.Column("disposal_authorization_reference", sa.String(length=180), nullable=True))
    op.add_column("service_providers", sa.Column("daily_capacity_tons", sa.Numeric(10, 2), nullable=True))
    op.add_column("service_providers", sa.Column("years_experience", sa.Integer(), nullable=True))
    op.add_column("service_providers", sa.Column("approval_status", sa.String(length=30), server_default="approved", nullable=False))
    op.add_column("service_providers", sa.Column("approved_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("service_providers", sa.Column("approved_by", sa.Integer(), nullable=True))
    op.create_index("ix_service_providers_approval_status", "service_providers", ["approval_status"], unique=False)
    op.create_index("ix_service_providers_approved_by", "service_providers", ["approved_by"], unique=False)

    op.add_column("users", sa.Column("phone_number", sa.String(length=30), nullable=True))
    op.add_column("users", sa.Column("provider_id", sa.Integer(), nullable=True))
    op.add_column("users", sa.Column("zone_id", sa.Integer(), nullable=True))
    op.create_index("ix_users_phone_number", "users", ["phone_number"], unique=False)
    op.create_index("ix_users_provider_id", "users", ["provider_id"], unique=False)
    op.create_index("ix_users_zone_id", "users", ["zone_id"], unique=False)

    op.add_column("collection_requests", sa.Column("zone_id", sa.Integer(), nullable=True))
    op.add_column("collection_requests", sa.Column("cancellation_reason", sa.Text(), nullable=True))
    op.add_column("collection_requests", sa.Column("cancelled_at", sa.DateTime(timezone=True), nullable=True))
    op.create_index("ix_collection_requests_zone_id", "collection_requests", ["zone_id"], unique=False)

    op.add_column("vehicles", sa.Column("zone_id", sa.Integer(), nullable=True))
    op.create_index("ix_vehicles_zone_id", "vehicles", ["zone_id"], unique=False)

    op.add_column("collection_assignments", sa.Column("vehicle_id", sa.Integer(), nullable=True))
    op.create_index("ix_collection_assignments_vehicle_id", "collection_assignments", ["vehicle_id"], unique=False)

    op.create_foreign_key("fk_vehicles_zone_id", "vehicles", "zones", ["zone_id"], ["id"], ondelete="SET NULL")
    op.create_foreign_key("fk_users_provider_id", "users", "service_providers", ["provider_id"], ["id"], ondelete="SET NULL")
    op.create_foreign_key("fk_users_zone_id", "users", "zones", ["zone_id"], ["id"], ondelete="SET NULL")
    op.create_foreign_key("fk_requests_zone_id", "collection_requests", "zones", ["zone_id"], ["id"], ondelete="SET NULL")
    op.create_foreign_key("fk_assignments_vehicle_id", "collection_assignments", "vehicles", ["vehicle_id"], ["id"], ondelete="SET NULL")
    op.create_foreign_key("fk_service_providers_approved_by", "service_providers", "users", ["approved_by"], ["id"], ondelete="SET NULL")

    op.create_table(
        "provider_zones",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("provider_id", sa.Integer(), nullable=False),
        sa.Column("zone_id", sa.Integer(), nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default=sa.true(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["provider_id"], ["service_providers.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["zone_id"], ["zones.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("provider_id", "zone_id", name="uq_provider_zone"),
    )
    op.create_index("ix_provider_zones_provider_id", "provider_zones", ["provider_id"], unique=False)
    op.create_index("ix_provider_zones_zone_id", "provider_zones", ["zone_id"], unique=False)

    op.create_table(
        "provider_applications",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("organization_name", sa.String(length=200), nullable=False),
        sa.Column("proposed_code", sa.String(length=50), nullable=False),
        sa.Column("registered_address", sa.String(length=500), nullable=False),
        sa.Column("contact_email", sa.String(length=255), nullable=False),
        sa.Column("contact_phone", sa.String(length=30), nullable=False),
        sa.Column("website", sa.String(length=255), nullable=True),
        sa.Column("company_registration_number", sa.String(length=120), nullable=False),
        sa.Column("tin", sa.String(length=80), nullable=False),
        sa.Column("nema_license_number", sa.String(length=120), nullable=False),
        sa.Column("kcca_trading_license_number", sa.String(length=120), nullable=False),
        sa.Column("tax_clearance_reference", sa.String(length=120), nullable=False),
        sa.Column("powers_of_attorney_reference", sa.String(length=120), nullable=False),
        sa.Column("gazette_reference", sa.String(length=180), nullable=True),
        sa.Column("years_experience", sa.Integer(), nullable=False),
        sa.Column("daily_capacity_tons", sa.Numeric(10, 2), nullable=False),
        sa.Column("disposal_facility_name", sa.String(length=200), nullable=False),
        sa.Column("disposal_facility_location", sa.String(length=500), nullable=False),
        sa.Column("disposal_authorization_reference", sa.String(length=180), nullable=False),
        sa.Column("monitoring_capability", sa.Text(), nullable=False),
        sa.Column("client_service_hours", sa.Integer(), nullable=False),
        sa.Column("requested_zone_ids", sa.JSON(), nullable=False),
        sa.Column("fleet", sa.JSON(), nullable=False),
        sa.Column("supervisor_user_id", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=30), server_default="pending", nullable=False),
        sa.Column("review_notes", sa.Text(), nullable=True),
        sa.Column("reviewed_by", sa.Integer(), nullable=True),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("provider_id", sa.Integer(), nullable=True),
        sa.Column("submitted_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["supervisor_user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["reviewed_by"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["provider_id"], ["service_providers.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_provider_applications_proposed_code", "provider_applications", ["proposed_code"], unique=False)
    op.create_index("ix_provider_applications_status", "provider_applications", ["status"], unique=False)
    op.create_index("ix_provider_applications_supervisor_user_id", "provider_applications", ["supervisor_user_id"], unique=False)
    op.create_index("ix_provider_applications_reviewed_by", "provider_applications", ["reviewed_by"], unique=False)
    op.create_index("ix_provider_applications_provider_id", "provider_applications", ["provider_id"], unique=False)
    op.create_index("ix_provider_applications_submitted_at", "provider_applications", ["submitted_at"], unique=False)


def downgrade() -> None:
    op.drop_table("provider_applications")
    op.drop_table("provider_zones")

    op.drop_constraint("fk_service_providers_approved_by", "service_providers", type_="foreignkey")
    op.drop_constraint("fk_assignments_vehicle_id", "collection_assignments", type_="foreignkey")
    op.drop_constraint("fk_vehicles_zone_id", "vehicles", type_="foreignkey")
    op.drop_constraint("fk_requests_zone_id", "collection_requests", type_="foreignkey")
    op.drop_constraint("fk_users_zone_id", "users", type_="foreignkey")
    op.drop_constraint("fk_users_provider_id", "users", type_="foreignkey")

    op.drop_index("ix_collection_assignments_vehicle_id", table_name="collection_assignments")
    op.drop_column("collection_assignments", "vehicle_id")
    op.drop_index("ix_vehicles_zone_id", table_name="vehicles")
    op.drop_column("vehicles", "zone_id")
    op.drop_index("ix_collection_requests_zone_id", table_name="collection_requests")
    op.drop_column("collection_requests", "cancelled_at")
    op.drop_column("collection_requests", "cancellation_reason")
    op.drop_column("collection_requests", "zone_id")

    op.drop_index("ix_users_zone_id", table_name="users")
    op.drop_index("ix_users_provider_id", table_name="users")
    op.drop_index("ix_users_phone_number", table_name="users")
    op.drop_column("users", "zone_id")
    op.drop_column("users", "provider_id")
    op.drop_column("users", "phone_number")

    for column in [
        "approved_by", "approved_at", "approval_status", "years_experience",
        "daily_capacity_tons", "disposal_authorization_reference",
        "disposal_facility_location", "disposal_facility_name", "gazette_reference",
        "powers_of_attorney_reference", "tax_clearance_reference",
        "kcca_trading_license_number", "nema_license_number", "tin",
        "company_registration_number", "website", "registered_address"
    ]:
        op.drop_column("service_providers", column)

    op.drop_index("ix_zones_municipality", table_name="zones")
    op.drop_column("zones", "radius_km")
    op.drop_column("zones", "center_longitude")
    op.drop_column("zones", "center_latitude")
    op.drop_column("zones", "municipality")
