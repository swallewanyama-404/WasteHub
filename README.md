# WasteHub

WasteHub is a full-stack waste collection and service-response management system for residents, licensed waste-service organizations, collectors/drivers, supervisors and platform administrators.

The current release includes resident registration and service profiles, zone-aware organization routing, routine and on-demand collection workflows, collector GPS operations, evidence capture, complaint handling, payments, provider onboarding, fleet/team management, notifications, analytics and audit logs.

## Technology

- **Frontend:** React, TypeScript, Vite, Nginx
- **Backend:** FastAPI, SQLAlchemy 2, Alembic
- **Database:** PostgreSQL 16
- **Deployment:** Docker Compose
- **Authentication:** JWT-based role access
- **Evidence storage:** private application media volume
- **Payments:** gateway-neutral payment records with authorised settlement verification
- **Maps / GPS:** browser geolocation plus WasteHub tracking APIs

## User roles

WasteHub provides separate workspaces for:

- **Resident** — service profile, monthly service, urgent pickup requests, cancellation, tracking, payments, complaints and feedback.
- **Collector / driver** — work queue, resident contact, GPS tracking, route progress, photo evidence, completion and missed/rejected stops.
- **Organization supervisor** — automatic and manual dispatch, alerts, exception recovery, completed evidence review, complaints, payment verification, team and fleet management.
- **Waste administrator** — cross-organization operational oversight.
- **System administrator** — platform users, organizations, service zones, audit logs and complete system administration.

## Major workflows

### Resident service

Residents register with their phone number, client type, address and GPS coordinates. WasteHub stores the service location and uses it as the default for future collections. The location can be updated from the resident profile.

The resident client type provides a suggested waste category. On-demand requests use selectable waste types and can be cancelled before collection begins.

### Routine collection

A verified monthly service payment enables the resident's weekly collection schedule. WasteHub prepares the next collection automatically and routes it to:

1. an approved provider serving the resident's zone,
2. an active collector belonging to that provider and compatible with the zone,
3. an available vehicle assigned to the same provider/zone and suitable for the known load.

### On-demand collection

Extra pickups are created when waste accumulates before the normal collection day. The request remains payment-pending until settlement is verified. It can then be manually dispatched by the responsible operations team.

### Collection execution

Collectors can:

- accept or reject assignments,
- call the resident,
- start GPS tracking,
- send current position,
- follow route/stop progress,
- preview collection evidence before upload,
- upload evidence,
- complete a collection,
- mark a stop missed with a reason.

WasteHub requires collection photo evidence before a stop can be completed.

### Exceptions and complaints

Missed and rejected assignments enter the organization review workflow. Supervisors can inspect the original assignment, select another eligible collector/truck and create a recovery assignment.

Complaints follow:

`Open -> In review -> Resolved by operations -> Closed by resident`

A missed-collection complaint cannot be marked resolved until the linked pickup has actually been completed.

### Organization onboarding

Waste-service organizations can apply online with:

- company registration and contact details,
- TIN / tax-clearance reference,
- NEMA licence reference,
- KCCA trading-licence reference,
- government/gazette authorization reference where applicable,
- disposal facility and disposal authorization,
- operating zones,
- experience and daily operating capacity,
- fleet registration numbers, capacities and zones,
- monitoring capability,
- supervisor account details.

Provider applications are not activated automatically. A system administrator reviews and approves or rejects the organization. Approval creates the provider, approved zone relationships, registered fleet and active supervisor account.

## First-time installation — Windows CMD

### Requirements

Install:

- Git
- Docker Desktop with Docker Compose
- a modern browser

Python and Node.js are not required on the host when using Docker.

Clone the repository and enter the folder:

```cmd
git clone https://github.com/swallewanyama-404/WasteHub.git
cd WasteHub
```

Run:

```cmd
scripts\setup.cmd
```

The setup asks for the first system administrator's:

- full name
- email
- phone number
- password

It then generates strong database/application secrets, creates `.env`, builds the containers, applies every database migration and creates the initial system administrator.

Open:

- WasteHub: http://localhost:3000
- API documentation: http://localhost:8000/docs
- API health: http://localhost:8000/api/v1/health

## Normal start and stop

Start:

```cmd
scripts\start.cmd
```

Stop:

```cmd
scripts\stop.cmd
```

Data is preserved in Docker volumes when the application is stopped.

## Manual environment configuration

For server deployments, copy `.env.example` to `.env` and replace every placeholder secret before starting:

```cmd
copy .env.example .env
docker compose up -d --build
docker compose exec -T api python scripts/bootstrap_admin.py
```

Do not commit `.env`.

## Payments

WasteHub ships with a complete internal payment-record and settlement-verification workflow. A resident creates a payment using Mobile Money, card or office/cash as the selected method. The payment remains pending until an authorised supervisor/administrator verifies the actual settlement reference. Successful verification activates the relevant monthly service or urgent request and records the action in the audit log.

The payment layer is intentionally gateway-neutral. A direct MTN Mobile Money, Airtel Money or card processor integration can replace the manual-verification adapter when authorised API credentials are available without changing the core collection workflow.

## Data persistence

Docker volumes hold:

- PostgreSQL application data
- uploaded collection evidence

Stopping containers with `docker compose down` does not delete these volumes.

To permanently remove all local WasteHub data:

```cmd
docker compose down -v
```

Use that command only when a complete reset is intended.

## Database migrations

The API container automatically applies Alembic migrations at startup.

Manual migration commands:

```cmd
docker compose exec -T api python -m alembic -c backend/alembic.ini current
docker compose exec -T api python -m alembic -c backend/alembic.ini upgrade head
docker compose exec -T api python -m alembic -c backend/alembic.ini check
```

## Testing

Backend integration tests cover the complete resident-to-collector-to-organization workflow, including:

- registration and authentication,
- service-zone resolution,
- cross-zone provider rejection,
- urgent payment settlement,
- dispatch,
- resident/collector phone access,
- GPS tracking,
- evidence-gated completion,
- resident tracking,
- complaints and resident closure,
- cancellation,
- monthly service activation,
- automatic routine routing,
- provider application/approval,
- analytics and audit logging.

GitHub Actions also compiles the backend, applies and validates all migrations, runs the test suite and builds/type-checks the frontend.

## Security notes

- Passwords are stored as secure hashes.
- Role checks are enforced in the API.
- Organization supervisors are scoped to their own provider/service area.
- Cross-zone collection dispatch is rejected by the backend.
- Production mode requires a non-placeholder application secret.
- Uploaded evidence is served only through authenticated API access.
- Audit logs record important operational and administrative actions.
- Regulatory/provider applications require administrator approval before activation.

For public internet deployment, place the application behind HTTPS, configure a real domain, use managed/private database backups, and use private object storage for evidence as required by the deployment environment.

## Project structure

```text
backend/                  FastAPI application
  alembic/                database migrations
  app/
    api/                  REST routes
    core/                 configuration, security, dependencies
    db/                   database session/base
    integrations/         external adapter boundaries
    models/               SQLAlchemy models
    repositories/         data-access helpers
    schemas/              request/response schemas
    services/             business workflows

frontend/                 React/TypeScript web application
scripts/                  setup, startup and administrator bootstrap
tests/                    automated backend integration tests
docs/                     architecture and development documentation
docker-compose.yml        complete application stack
```

## Release

**WasteHub 1.0** is the current complete self-hosted system release.
