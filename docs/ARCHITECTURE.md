# WasteHub architecture

```text
Resident Web/PWA
Collector Web/Mobile
Admin Web
       |
       v
Next.js / React frontend
       |
       v
FastAPI REST API
       |
       +--> Authentication & RBAC
       +--> Zones & Providers
       +--> Collection Requests
       +--> Collector Workflow
       +--> Complaints & Feedback
       +--> Notifications
       +--> Analytics & Audit
       |
       v
PostgreSQL
       |
       +--> Redis (future)
       +--> Private object storage (future)
       +--> Authorised external integrations (future)
```

The first repository deliberately implements only the foundation. Features are added stage-by-stage so each milestone can be tested and demonstrated.
