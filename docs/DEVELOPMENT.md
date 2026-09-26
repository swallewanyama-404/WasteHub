# Development workflow

1. Work on one stage at a time.
2. Create a branch for substantial features.
3. Add/update tests with each feature.
4. Run the API locally before committing.
5. Never commit `.env`, passwords, private keys or real personal data.
6. Keep prototype/simulated provider data clearly labelled.
7. Do not describe an unimplemented integration as live.
8. Commit in small, understandable units.

Suggested commands:

```bash
git status
git add .
git commit -m "chore: initialise WasteHub backend"
```
