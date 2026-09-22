# Deployment

## Local showcase: zero service fees

Run `./scripts/start.sh`, then open http://localhost:8010. Dependencies require internet on first installation. Subsequent operation uses local assets and SQLite. Keep the computer awake during the presentation. The app does not require a model provider or mapping API.

`docker compose up --build -d` provides the same local app with a named persistent volume. The supplied Compose file binds only to localhost and intentionally uses development cookie settings. Do not expose that configuration directly to the internet.

## Durable SQLite deployment on an existing server

Run one Docker container behind an HTTPS reverse proxy on an existing server or a host offering persistent disks. Set:

```text
PANTRY_ENV=production
PANTRY_DATABASE=/app/data/pantry-relay.sqlite3
PANTRY_DEMO_ENABLED=false
PANTRY_COOKIE_SECURE=true
PANTRY_ALLOWED_HOSTS=relay.your-domain.org
```

Mount a durable volume at `/app/data`, writable by UID 10001. Proxy to port 8000. Terminate HTTPS at a trusted proxy, retain host headers, and do not trust arbitrary forwarded headers. Use exactly one instance and one worker for this release. Avoid network filesystems whose locking semantics do not support SQLite. Keep the database outside the image and release directory.

Before putting real operational data into the deployment, run a fresh account through the complete transfer, role invitation, CSV export and backup/restore flow. Disable demo creation. Ensure the public hostname and secure cookies work. Assign responsibility for updates, backups and account recovery.

## Firebase Hosting with durable PostgreSQL

The hosted path uses Firebase Hosting for the static application and a same-origin `/api/**` rewrite to Cloud Run. Cloud Run connects to a dedicated Cloud SQL PostgreSQL database. Cloud Run's local filesystem is not used for persistent records.

`scripts/deploy_firebase.sh` deploys the dedicated Pantry Relay service and Hosting site. It reads the database connection URL from Secret Manager, uses a dedicated service account, restricts allowed hosts and browser origins, and caps concurrency and instance count. Existing Cloud SQL, registry, service-account permissions and secrets must be provisioned first. The script does not create or modify other applications' databases.

This deployment supports real account registration and isolated demonstration networks together. PostgreSQL plus the explicit `PANTRY_ALLOW_PUBLIC_DEMO=true` setting are required for this production combination. Real networks are not affected by demo cleanup. Members can be invited only into real networks.

See [PostgreSQL deployment and recovery](POSTGRESQL.md) for the exact configuration, transaction behavior, Cloud SQL backup and logical restore procedures, operator account recovery, and dual-database test instructions. Use the actual deployment check results to establish hosted readiness; these instructions alone are not proof of a successful deployment.

## Disposable public showcase

For a separate free demonstration service, use the same production security settings with `PANTRY_DEMO_ONLY=true` and `PANTRY_DEMO_ENABLED=true`. This mode disables real account creation and invitations, creates isolated sample workspaces, and labels the app as disposable. Set the allowed host to the actual public service hostname. All state can disappear when an ephemeral host restarts. Do not put real records into this mode.

## Cloud operating cost

The selected Firebase and Cloud SQL deployment is a metered cloud service. Cloud SQL has ongoing instance and storage charges even when Cloud Run scales to zero. Set a budget alert, verify the instance size and region, and assign responsibility for the bill. It is not a permanent free production offer. No cloud account is required to evaluate the complete local SQLite application.

## SQLite backup and restore

For PostgreSQL, follow [the PostgreSQL backup and restore procedure](POSTGRESQL.md#backups-and-restore). For SQLite, use the online backup API while the application is running:

```sh
uv run python scripts/backup.py data/pantry-relay.sqlite3 backups/pantry-2026-09-22.sqlite3
```

The script refuses to overwrite an existing backup and runs an integrity check. Protect backups as private operational data. Store an encrypted copy outside the server. Choose retention and recovery targets with the network operator; a daily backup and a tested one-business-day recovery procedure are suggested pilot defaults, not delivered guarantees.

Restore into a separate stopped test instance first. Check database integrity and counts, then test login and a report. For production restoration: stop writes, preserve the current database and WAL files, restore the verified backup to the configured database path with correct ownership, and restart. Do not copy only the live SQLite main file while WAL writes are active.

## Upgrades and rollback

Back up before changing versions. Build the new container, run the tests and verify it against a copy of the database. This release initializes a versioned schema but is not a general automatic migration platform. Inspect any future migration before adopting it. Roll back the image and matching verified database backup only with the network operator's approval, because records created after the backup could otherwise be lost.
