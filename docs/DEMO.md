# WasteHub classroom demonstration

This guide is for the academic WasteHub prototype. The service providers, vehicle, payments, GPS positions, and operational data used in the demo are sample data unless explicitly connected to an authorised real service.

## Demo accounts

| Role | Email | Password |
| --- | --- | --- |
| System administrator | admin@wastehub.demo | WasteHubAdmin123! |
| Supervisor | supervisor@wastehub.demo | WasteHubSupervisor123! |
| Collector | collector@wastehub.demo | WasteHubCollector123! |
| Resident | resident@wastehub.demo | WasteHubResident123! |

Run `python scripts/seed_demo.py` after migrations to create or refresh the demo accounts and sample operational records.

## Recommended presentation flow

1. Sign in as the resident. Show existing requests, create a new collection request, open request tracking, review notifications, demonstrate a sample payment, and submit feedback or a complaint where applicable.
2. Sign in as the supervisor or administrator. Show the operations dashboard, pending collection requests, collector workload, available vehicles, dispatch, monitoring, provider performance, alerts, complaints, payments, analytics, and audit logs.
3. Sign in as the collector. Show the queue, accept an assignment, start GPS tracking, send the browser GPS position, start the collection stop, upload collection evidence, complete or miss the stop, and show automatic resident/operations updates.
4. Return to the resident account and show the updated request timeline, truck progress, notifications, and completion status.
5. Return to the administrator account and show the final analytics and audit trail.

## Payment note

The repository contains a gateway-neutral payment record model and a demo payment flow. The `demo-success` endpoint is intentionally disabled when `APP_ENV=production`. Real Mobile Money or card settlement requires credentials and an authorised provider integration and should not be represented as live until that integration is configured.

## Evidence note

Collection evidence is stored locally under the configured `MEDIA_ROOT` for the classroom/demo deployment. A public production deployment should replace local disk persistence with private object storage while retaining the same API boundary.
