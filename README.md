# WasteHub

**Smart Waste Collection and Service Response Management System for Kampala**

WasteHub is an academic software-engineering project designed as a digital improvement layer around the existing waste-collection workflow involving residents, authorised waste collectors/service providers, and waste-management supervisors.

> **Important:** This repository is a prototype. It does not claim official KCCA integration or deployment.

## Development stages

0. PC preparation
1. Development environment
2. Project structure
3. PostgreSQL database
4. FastAPI backend
5. Authentication & roles
6. Waste collection requests
7. Zone/provider assignment
8. Collector workflow
9. Resident tracking
10. Notifications
11. Photos & location
12. Feedback & complaints
13. Admin dashboard
14. Analytics & audit logs
15. Security
16. Testing
17. Docker/deployment
18. Final demonstration
19. Scaling toward production

## Current repository state

This initial repository is intentionally small. It establishes the foundation for Stages 1–4:

- FastAPI application
- health endpoint
- versioned API structure
- environment configuration
- PostgreSQL-ready SQLAlchemy setup
- Alembic-ready migration structure
- Docker Compose for PostgreSQL
- initial user/role model
- basic project documentation

Authentication, collection workflows, complaints, notifications, dashboards and other modules will be implemented stage-by-stage rather than all at once.

## Prerequisites

- Python 3.12+
- Git
- Docker Desktop (recommended)
- VS Code or another IDE

## Quick start

### 1. Create and activate a virtual environment

Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

macOS/Linux:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 2. Install dependencies

```bash
pip install -r backend/requirements.txt
```

### 3. Configure environment

Copy `.env.example` to `.env`.

Windows PowerShell:

```powershell
Copy-Item .env.example .env
```

macOS/Linux:

```bash
cp .env.example .env
```

### 4. Start PostgreSQL

```bash
docker compose up -d db
```

### 5. Run the API

```bash
uvicorn backend.app.main:app --reload
```

Open:

- http://127.0.0.1:8000
- http://127.0.0.1:8000/docs

### 6. Stop PostgreSQL

```bash
docker compose down
```

## Project principles

1. Build one stage at a time.
2. Keep the existing waste-management workflow visible in the design.
3. Do not claim real integrations until they are authorised and implemented.
4. Use simulated/prototype data where real provider integrations are unavailable.
5. Test every stage before moving to the next.
