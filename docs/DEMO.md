# WasteHub classroom demonstration

This guide is for the academic WasteHub prototype. Service providers, vehicles, payments, GPS positions, regulatory references, and operational data used in the classroom demo are sample data unless explicitly connected to an authorised real service.

## Demo accounts

| Role | Email | Password |
| --- | --- | --- |
| System administrator | admin@wastehub.demo | WasteHubAdmin123! |
| Supervisor | supervisor@wastehub.demo | WasteHubSupervisor123! |
| Collector | collector@wastehub.demo | WasteHubCollector123! |
| Relief collector | relief.collector@wastehub.demo | WasteHubRelief123! |
| Resident | resident@wastehub.demo | WasteHubResident123! |

Run `python scripts/seed_demo.py` after migrations to create or refresh the demo accounts, Kampala demo zone, approved demo provider, two trucks, monthly resident service, and sample collection records.

## Recommended presentation flow

1. **Resident:** show Dashboard, saved contact/profile, routine monthly service, notifications, extra-pickup request, request cancellation, payment, live tracking, collector call button, complaint lifecycle, feedback, and resident-confirmed complaint closure.
2. **Supervisor:** show the provider-scoped Operations dashboard, actionable alerts, manual dispatch for on-demand/rejected work, live monitoring, Reviews for missed/rejected recovery and completed evidence, Service Desk complaint investigation, Team management, and Fleet management.
3. **Collector:** show Dashboard, queue, resident call button, reserved truck, GPS session, live route map, collection progress, photo preview before upload, uploaded evidence gallery, completion, missed stop, and rejection workflow.
4. **Resident again:** show the updated route/timeline, notifications, completed collection, and any complaint waiting for resident confirmation.
5. **System administrator:** show platform Overview, user creation/access management, private waste organization applications, organization approval, Audit trail, and cross-organization operations.
6. **Public provider onboarding:** from the landing page open “Apply to join WasteHub,” demonstrate legal/compliance references, operating zones, disposal facility, fleet and supervisor-account registration. Explain that the WasteHub form supports internal platform review and does not itself issue a KCCA/NEMA licence.

## Routing model

WasteHub separates routine service from exception work.

- A paid resident monthly plan prepares the next weekly routine collection.
- Routine work is automatically matched to an approved provider serving the resident's zone, then to an active collector and available truck in that provider/zone.
- The resident remains associated with the responsible provider while that provider remains approved for the service zone.
- Paid on-demand pickups are manually dispatched.
- Rejected or missed assignments go to the Reviews workflow for manual recovery/reassignment.
- Supervisors see only their organization's relevant operations, residents, complaints, fleet and service zones.
- System administrators retain platform-wide oversight.

## Provider onboarding note

WasteHub records provider information such as company registration, TIN/tax-clearance references, NEMA licence reference, KCCA trading-licence reference, powers-of-attorney reference, disposal facility/authorisation, operational capacity, monitoring capability, requested zones and registered fleet.

These fields are for the WasteHub academic onboarding workflow. Real deployment must independently verify current regulatory, procurement and licensing requirements and must not treat an application submitted in WasteHub as government approval.

## Phone/contact note

Resident and collector phone numbers are used for service coordination. An assigned collector can call the resident for access/pickup coordination, and the resident can call the assigned collector from the tracking screen. The current prototype uses the device's normal `tel:` calling capability; it does not implement masked in-app VoIP calling.

## Payment note

The repository contains a gateway-neutral payment record model and a demo payment flow. The `demo-success` endpoint is intentionally disabled when `APP_ENV=production`. Real Mobile Money or card settlement requires credentials and an authorised provider integration and should not be represented as live until that integration is configured.

## Evidence note

Collectors preview a selected image before upload and can see uploaded evidence afterward. Supervisors/system administrators can review completed-assignment evidence through the Reviews workspace. Evidence is stored locally under the configured `MEDIA_ROOT` for the classroom/demo deployment. A public production deployment should replace local disk persistence with private object storage while retaining the same API boundary.
