# PostgreSQL deployment and recovery

The hosted application uses PostgreSQL through `PANTRY_DATABASE`. SQLite remains supported for a local installation with a persistent disk. The HTTP API and inventory rules are the same for both stores.

## Hosted configuration

Store the PostgreSQL connection URL in Secret Manager and expose it to Cloud Run as `PANTRY_DATABASE`. Attach the dedicated Cloud SQL instance to the Cloud Run service and grant that service account the Cloud SQL Client role. Do not put credentials in frontend configuration, committed files, build arguments, or deployment output.

The hosted configuration uses these additional settings:

```text
PANTRY_ENV=production
PANTRY_COOKIE_SECURE=true
PANTRY_DEMO_ENABLED=true
PANTRY_DEMO_ONLY=false
PANTRY_ALLOW_PUBLIC_DEMO=true
PANTRY_ALLOWED_HOSTS=pantryrelay.web.app,pantryrelay.firebaseapp.com,EXACT_SERVICE_HOST.run.app
PANTRY_TRUSTED_ORIGINS=https://pantryrelay.web.app,https://pantryrelay.firebaseapp.com
```

Use the actual Cloud Run hostname in `PANTRY_ALLOWED_HOSTS`. Wildcard hosts and wildcard origins are rejected in production. Firebase Hosting forwards the `__session` cookie to the backend; the cookie is HttpOnly and Secure in production. Authentication and workspace responses use `Cache-Control: no-store`.

Production supports real accounts and isolated demos together only when PostgreSQL and `PANTRY_ALLOW_PUBLIC_DEMO=true` are configured explicitly. Demo networks cannot invite real members. Demo creation reclaims disposable workspaces older than 24 hours; this cleanup does not delete real networks.

## Transaction behavior and limits

PostgreSQL write transactions acquire one application advisory lock before reading or changing operational state. This preserves the same allocation guarantees as SQLite's `BEGIN IMMEDIATE`, including across multiple application instances. Reads use a repeatable snapshot. PostgreSQL constraints protect physical quantities, reserves, references, and valid transfer states.

This is deliberately bounded write throughput, not a claim of unlimited horizontal scalability. The deployment caps Cloud Run concurrency at 8 and instance count at 2. Database lock waits and statements have timeouts. A storage failure returns a generic retryable error rather than exposing credentials or database details.

Startup initializes schema version 3 and applies the supported migrations under the advisory lock. It does not import an existing SQLite installation automatically. Back up before any upgrade. Preserve the old installation until an independently verified data migration is complete.

## Backups and restore

The `scripts/backup.py` online backup command is for SQLite only. For PostgreSQL, configure and verify Cloud SQL automated backups and retention, then test a restore into a separate database. Backup availability, retention, and costs depend on the instance configuration; they are not guaranteed by application code.

For a portable logical backup, use PostgreSQL client tools. Configure a private libpq service called `pantry` through a Cloud SQL Auth Proxy or another approved connection. Keep credential files readable only by their owner. The commands below keep passwords out of command arguments:

```sh
PGSERVICE=pantry pg_dump --format=custom --no-owner --no-acl --file backups/pantry.dump
PGSERVICE=pantry_restore pg_restore --exit-on-error --single-transaction --no-owner --no-acl backups/pantry.dump
```

`pantry_restore` must identify a separate, empty restore database. Start a separate application against it and verify login, network counts, open reservations, completed receipt totals, and exported reports. Restore into production only after stopping writes and preserving the current database; restoring an older snapshot can discard subsequent records.

## Account recovery

The local operator command supports PostgreSQL as well as SQLite. Supply the database URL through an environment populated from your secret store and do not print it:

```sh
uv run python scripts/account_admin.py reset-password --email user@example.org
uv run python scripts/account_admin.py revoke-sessions --email user@example.org
```

These commands read `PANTRY_DATABASE` when `--database` is omitted. Password entry is interactive. Both actions revoke every active session for the target account and create an audit entry attributed to the local database operator. The operator must verify the request through the network's established process.

## Database test coverage

Normal `uv run pytest` exercises SQLite. To run the same operational, authorization, concurrency, recovery, and food-handling tests against PostgreSQL too, set `PANTRY_TEST_POSTGRES` to a dedicated test database URL and run `uv run pytest`. The test user needs permission to create and drop schemas. Tests create temporary schemas and remove them afterward. Never point this setting at a production database.

The CI workflow provides an isolated PostgreSQL 15 service. Storage-specific tests run only for their applicable database. Additional PostgreSQL tests verify that independent application instances share session and receipt history, compete safely for stock, and roll back failed mutations.
