# Deployment

## Local showcase: zero service fees

Run `./scripts/start.sh`, then open http://localhost:8010. Dependencies require internet on first installation. Subsequent operation uses local assets and SQLite. Keep the computer awake during the presentation. The app does not require a model provider or mapping API.

`docker compose up --build -d` provides the same local app with a named persistent volume. The supplied Compose file binds only to localhost and intentionally uses development cookie settings. Do not expose that configuration directly to the internet.

## Durable pilot deployment

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

## Disposable public showcase

For a separate free demonstration service, use the same production security settings with `PANTRY_DEMO_ONLY=true` and `PANTRY_DEMO_ENABLED=true`. This mode disables real account creation and invitations, creates isolated sample workspaces, and labels the app as disposable. Set the allowed host to the actual public service hostname. All state can disappear when an ephemeral host restarts. Do not put real records into this mode.

## Free cloud hosting caveat

Render's free web service filesystem is ephemeral and its free Postgres expires after 30 days. A free web service with SQLite is therefore only a disposable demo, not durable storage. Official docs checked September 22, 2026: https://render.com/docs/free and https://render.com/docs/disks.

This repository does not silently deploy into a paid plan or promise a permanent free production service. Hosting cost is a hypothesis in the business model. A durable hosted pilot requires an existing server or an explicitly chosen paid persistent-storage plan. No cloud account is required to evaluate the complete local app.

## Backup and restore

Use the SQLite online backup API while the application is running:

```sh
uv run python scripts/backup.py data/pantry-relay.sqlite3 backups/pantry-2026-09-22.sqlite3
```

The script refuses to overwrite an existing backup and runs an integrity check. Protect backups as private operational data. Store an encrypted copy outside the server. Choose retention and recovery targets with the network operator; a daily backup and a tested one-business-day recovery procedure are suggested pilot defaults, not delivered guarantees.

Restore into a separate stopped test instance first. Check database integrity and counts, then test login and a report. For production restoration: stop writes, preserve the current database and WAL files, restore the verified backup to the configured database path with correct ownership, and restart. Do not copy only the live SQLite main file while WAL writes are active.

## Upgrades and rollback

Back up before changing versions. Build the new container, run the tests and verify it against a copy of the database. This release initializes a versioned schema but is not a general automatic migration platform. Inspect any future migration before adopting it. Roll back the image and matching verified database backup only with the network operator's approval, because records created after the backup could otherwise be lost.
