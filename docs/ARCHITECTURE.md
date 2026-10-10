# WasteHub architecture

WasteHub is a role-based full-stack application built around one shared operational data model.

```text
Resident / Collector / Supervisor / Administrator
                    |
                    v
          React + TypeScript frontend
                    |
                    v
             FastAPI REST API
                    |
       +------------+-------------+
       |            |             |
 Authentication  Operations   Administration
 RBAC            & routing     & audit
       |            |             |
       +------------+-------------+
                    |
                    v
                PostgreSQL
                    |
        +-----------+-----------+
        |                       |
  Evidence media           Adapter boundaries
  private volume        payments / notifications
```

## Backend boundaries

The FastAPI application separates:

- authentication and role enforcement,
- resident profiles and service plans,
- collection requests and assignments,
- automatic zone/provider/collector/vehicle routing,
- collector workflow and route progress,
- GPS tracking,
- collection evidence,
- complaints and feedback,
- provider applications,
- team/fleet administration,
- payment settlement verification,
- notifications,
- analytics and audit logs.

## Zone and organization isolation

A resident service location is resolved to a WasteHub service zone using stored coordinates. Provider-to-zone authorization is stored separately from the provider record.

Dispatch validation therefore checks:

1. request zone,
2. provider approval and provider-zone authorization,
3. collector organization/zone,
4. vehicle organization/zone and availability.

This prevents an organization from being assigned work outside its approved operating area.

## Routine routing

Routine work is generated only when the monthly service is active. WasteHub then selects:

- an approved provider serving the zone,
- a compatible active collector with the lowest current assignment load,
- an available compatible vehicle.

Known vehicle capacity is also considered when the request quantity can be converted to tons.

## Evidence and completion

Collection evidence metadata is stored in PostgreSQL while uploaded files are stored under the configured private media root. Completion is blocked until a collection photo exists for the assignment.

## Payment boundary

The core application owns payment records and service activation. The configured payment adapter creates a provider/reference pair.

The built-in `manual_verification` adapter provides an operational fallback: residents create payment records, and authorised operations users verify settlement references. External payment processors can implement the same adapter contract.

## Deployment

`docker-compose.yml` runs:

- PostgreSQL 16,
- FastAPI API,
- React/Nginx frontend.

The API applies Alembic migrations before starting. Persistent Docker volumes hold PostgreSQL data and evidence media.
