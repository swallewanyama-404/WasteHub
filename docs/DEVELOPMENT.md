# WasteHub development and maintenance

## Branch workflow

Use feature branches for substantial changes and merge only after CI passes.

Before committing:

```bash
git status
python -m compileall backend
pytest -q
cd frontend
npm run build
```

The Docker-based deployment remains the reference runtime.

## Database changes

Create an Alembic migration for every schema change and verify:

```bash
python -m alembic -c backend/alembic.ini upgrade head
python -m alembic -c backend/alembic.ini check
```

Never rewrite migrations that may already have been applied to an existing WasteHub database.

## Security

- Never commit `.env`, credentials, API keys, private certificates or resident data.
- Enforce permissions in backend services/routes even when the frontend already hides an action.
- Keep provider/collector/vehicle zone checks server-side.
- Keep evidence behind authenticated endpoints.
- Record sensitive operational changes in the audit log.
- Use HTTPS and private storage for internet-facing deployments.

## External integrations

Payment and notification integrations are adapter boundaries. Do not hard-code provider credentials in source control.

When adding a live payment gateway, preserve the existing payment lifecycle and update automated tests for both initiation and confirmed settlement.

## Tests

New features should include automated regression coverage. The integrated workflow test is the main end-to-end API regression test and should remain green before merge.
