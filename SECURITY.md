# Security and responsible operation

Pantry Relay is a functioning release for a supervised pilot. It has not received an independent penetration test or compliance certification. Do not interpret automated test coverage as proof of production security.

## Implemented controls

- Opaque random sessions stored as hashes server-side, with a 12-hour expiration and HttpOnly, SameSite cookies.
- Server-side CSRF validation on authenticated writes and same-origin checks when an Origin header is present.
- Salted scrypt password hashes, bounded credential inputs, and persisted authentication throttling.
- Tenant-scoped records and role authorization on the backend. Drivers cannot change stock, accept transfers or record receiving quantities.
- Atomic SQLite write transactions for reservation and physical-stock changes. Optimistic versions protect inventory edits.
- Input validation, bounded numbers, integer hundredths-of-pound storage, prepared SQL and spreadsheet-formula protection in exports.
- Security headers, trusted hosts, no-store API responses and production secure-cookie configuration.
- One-use expiring invitations. Public demo-only deployments disable real registration and invitations.

## Operator responsibilities

Use HTTPS, explicit allowed hosts and a persistent private volume. Deploy a single instance. Restrict database and backup access, apply dependency patches, monitor disk usage, and test restore. Authorize network staff before sending invitations. Do not put recipient personal data into notes. A shared network is a shared operational trust boundary: coordinator access is network-wide, not restricted to one pantry.

The public demo is disposable. It is not an appropriate place for real organization data or contact details. Its sample records are fictional and reset with a new workspace or hosting restart.

## Recovery

There is no email provider or self-service email reset in this release. A trusted server operator verifies the requester through the network's established channel, then runs:

```sh
uv run python scripts/account_admin.py reset-password --database data/pantry-relay.sqlite3 --email user@example.org
```

The password is entered interactively and never placed in a shell argument. The command revokes all existing sessions. To revoke sessions without changing credentials, use `revoke-sessions`. Direct database access is privileged; never expose this command as a public HTTP endpoint.

## Known limits

No SSO, MFA, email verification, per-site coordinator permissions, independent receiver signature, abuse monitoring service or external security audit is included. The audit log is append-only through the API, but a database administrator can modify it; it is not cryptographically tamper-proof. Rate limits depend on deployment proxy configuration and should be paired with edge protections for an internet-facing pilot. The supported SQLite architecture has one instance, not a multi-region availability guarantee.

Send a private vulnerability report to the repository owner using GitHub's private reporting channel if enabled. Otherwise contact the owner privately; do not post exploit details or operational records in a public issue.
