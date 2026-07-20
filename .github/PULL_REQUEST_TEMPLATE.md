## Production ticket

Ticket: `PROD-___`

## Scope

- [ ] This change is limited to the linked production-hardening ticket.
- [ ] Unrelated pre-existing working-tree changes are excluded.
- [ ] Database, environment, and API contract changes are documented.

## Verification

- [ ] Backend Ruff and relevant pytest checks pass, or are not applicable.
- [ ] Admin tests, lint, and build pass, or are not applicable.
- [ ] Mobile tests and TypeScript pass, or are not applicable.
- [ ] Dependency, secret, CodeQL, and image gates pass.
- [ ] Acceptance evidence and tracker status are updated.

## Risk and rollback

Describe the failure impact, migration considerations, and rollback procedure.
