"""Transactional PostgreSQL persistence and SQLite for persistent local deployments.

Weight is stored as integer hundredths of a pound to avoid floating-point drift.
PostgreSQL writes serialize through a transaction advisory lock. SQLite uses
BEGIN IMMEDIATE. Both retain the same inventory and reservation invariants.
"""

import sqlite3
from contextlib import contextmanager
from pathlib import Path

SCHEMA = """
CREATE TABLE IF NOT EXISTS networks (
 id TEXT PRIMARY KEY, name TEXT NOT NULL, is_demo INTEGER NOT NULL DEFAULT 0,
 created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS users (
 id TEXT PRIMARY KEY, network_id TEXT NOT NULL REFERENCES networks(id), name TEXT NOT NULL,
 email TEXT NOT NULL UNIQUE COLLATE NOCASE, password_hash TEXT NOT NULL,
 role TEXT NOT NULL CHECK(role IN ('admin','coordinator','driver')), created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS sessions (
 token_hash TEXT PRIMARY KEY, user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
 csrf_token TEXT NOT NULL, expires_at TEXT NOT NULL, created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS invites (
 id TEXT PRIMARY KEY, network_id TEXT NOT NULL REFERENCES networks(id), token_hash TEXT UNIQUE NOT NULL,
 role TEXT NOT NULL CHECK(role IN ('coordinator','driver')), expires_at TEXT NOT NULL,
 used_at TEXT, created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS sites (
 id TEXT PRIMARY KEY, network_id TEXT NOT NULL REFERENCES networks(id), name TEXT NOT NULL,
 city TEXT NOT NULL, address TEXT NOT NULL, lat REAL NOT NULL, lng REAL NOT NULL,
 storage_types TEXT NOT NULL, capacity_units INTEGER NOT NULL CHECK(capacity_units > 0),
 notes TEXT NOT NULL DEFAULT '', created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS lots (
 id TEXT PRIMARY KEY, network_id TEXT NOT NULL REFERENCES networks(id), site_id TEXT NOT NULL REFERENCES sites(id),
 food_name TEXT NOT NULL, category TEXT NOT NULL, storage TEXT NOT NULL,
 quantity_units INTEGER NOT NULL CHECK(quantity_units >= 0), reserve_units INTEGER NOT NULL CHECK(reserve_units >= 0),
 expires_at TEXT NOT NULL, restricted INTEGER NOT NULL DEFAULT 0, notes TEXT NOT NULL DEFAULT '',
 version INTEGER NOT NULL DEFAULT 1, origin_transfer_id TEXT, created_at TEXT NOT NULL,
 CHECK(reserve_units <= quantity_units)
);
CREATE TABLE IF NOT EXISTS needs (
 id TEXT PRIMARY KEY, network_id TEXT NOT NULL REFERENCES networks(id), site_id TEXT NOT NULL REFERENCES sites(id),
 category TEXT NOT NULL, quantity_units INTEGER NOT NULL CHECK(quantity_units > 0),
 fulfilled_units INTEGER NOT NULL DEFAULT 0 CHECK(fulfilled_units >= 0), service_at TEXT NOT NULL,
 notes TEXT NOT NULL DEFAULT '', created_at TEXT NOT NULL, closed INTEGER NOT NULL DEFAULT 0,
 CHECK(fulfilled_units <= quantity_units)
);
CREATE TABLE IF NOT EXISTS transfers (
 id TEXT PRIMARY KEY, network_id TEXT NOT NULL REFERENCES networks(id), lot_id TEXT NOT NULL REFERENCES lots(id),
 need_id TEXT NOT NULL REFERENCES needs(id), source_id TEXT NOT NULL REFERENCES sites(id),
 destination_id TEXT NOT NULL REFERENCES sites(id), food_name TEXT NOT NULL, category TEXT NOT NULL,
 storage TEXT NOT NULL, quantity_units INTEGER NOT NULL CHECK(quantity_units > 0),
 received_units INTEGER NOT NULL DEFAULT 0 CHECK(received_units >= 0),
 status TEXT NOT NULL CHECK(status IN ('reserved','accepted','in_transit','arrived','received','cancelled','failed')),
 distance_miles REAL NOT NULL, receiver_name TEXT NOT NULL DEFAULT '', exception_reason TEXT NOT NULL DEFAULT '',
 created_at TEXT NOT NULL, updated_at TEXT NOT NULL, expires_at TEXT NOT NULL,
 pickup_temperature_f REAL, receipt_temperature_f REAL, refrigerated INTEGER NOT NULL,
 CHECK(received_units <= quantity_units)
);
CREATE TABLE IF NOT EXISTS events (
 id TEXT PRIMARY KEY, network_id TEXT NOT NULL REFERENCES networks(id), actor_id TEXT NOT NULL REFERENCES users(id),
 actor_name TEXT NOT NULL, action TEXT NOT NULL, entity_type TEXT NOT NULL, entity_id TEXT NOT NULL,
 description TEXT NOT NULL, data TEXT NOT NULL DEFAULT '{}', created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS auth_attempts (key TEXT NOT NULL, occurred_at REAL NOT NULL);
CREATE INDEX IF NOT EXISTS idx_sessions_expiry ON sessions(expires_at);
CREATE INDEX IF NOT EXISTS idx_auth_attempts ON auth_attempts(key, occurred_at);
CREATE INDEX IF NOT EXISTS idx_sites_network ON sites(network_id);
CREATE INDEX IF NOT EXISTS idx_lots_network ON lots(network_id, site_id);
CREATE INDEX IF NOT EXISTS idx_needs_network ON needs(network_id, site_id);
CREATE INDEX IF NOT EXISTS idx_transfers_network ON transfers(network_id, status);
CREATE INDEX IF NOT EXISTS idx_transfers_lot ON transfers(lot_id, status);
CREATE INDEX IF NOT EXISTS idx_transfers_need ON transfers(need_id, status);
CREATE INDEX IF NOT EXISTS idx_transfers_destination ON transfers(destination_id, status);
CREATE INDEX IF NOT EXISTS idx_events_network ON events(network_id, created_at);

"""


def is_postgres(database: str) -> bool:
    return database.startswith(("postgresql://", "postgres://"))


def connect(database: str):
    if is_postgres(database):
        from backend.postgres import Connection

        return Connection(database)
    conn = sqlite3.connect(database, timeout=15, isolation_level=None)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys=ON")
    conn.execute("PRAGMA busy_timeout=15000")
    return conn


def initialize(database: str) -> None:
    if is_postgres(database):
        from backend.postgres import initialize as initialize_postgres

        initialize_postgres(database, SCHEMA)
        return
    if database != ":memory:":
        Path(database).expanduser().resolve().parent.mkdir(parents=True, exist_ok=True)
    conn = connect(database)
    try:
        version = conn.execute("PRAGMA user_version").fetchone()[0]
        if version > 3:
            raise RuntimeError("Database schema is newer than this application")
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA synchronous=FULL")
        conn.executescript(SCHEMA)
        columns = {row[1] for row in conn.execute("PRAGMA table_info(needs)")}
        if "closed" not in columns:
            conn.execute("ALTER TABLE needs ADD COLUMN closed INTEGER NOT NULL DEFAULT 0")
        transfer_schema = conn.execute(
            "SELECT sql FROM sqlite_master WHERE type='table' AND name='transfers'"
        ).fetchone()[0]
        if "'failed'" not in transfer_schema:
            # SQLite cannot alter a CHECK constraint. Rebuild atomically, preserving every
            # column and row; there are intentionally no external FKs to transfer IDs.
            body = transfer_schema[transfer_schema.index("(") :].replace(
                "'received','cancelled'", "'received','cancelled','failed'"
            )
            if "'failed'" not in body:
                raise RuntimeError(
                    "Unrecognized legacy transfer schema; migration needs operator review"
                )
            conn.execute("BEGIN IMMEDIATE")
            try:
                conn.execute("CREATE TABLE transfers_v3 " + body)
                conn.execute("INSERT INTO transfers_v3 SELECT * FROM transfers")
                conn.execute("DROP TABLE transfers")
                conn.execute("ALTER TABLE transfers_v3 RENAME TO transfers")
                for statement in SCHEMA.split(";"):
                    if (
                        statement.strip().startswith("CREATE INDEX")
                        and " ON transfers(" in statement
                    ):
                        conn.execute(statement)
                conn.execute("PRAGMA user_version=3")
                conn.commit()
            except BaseException:
                conn.rollback()
                raise
        else:
            conn.execute("PRAGMA user_version=3")
    finally:
        conn.close()


@contextmanager
def transaction(database: str, write: bool = False):
    conn = connect(database)
    try:
        if is_postgres(database):
            from backend.postgres import WRITE_LOCK

            conn.execute("BEGIN" if write else "BEGIN ISOLATION LEVEL REPEATABLE READ READ ONLY")
            if write:
                conn.execute("SELECT pg_advisory_xact_lock(?)", (WRITE_LOCK,))
        else:
            conn.execute("BEGIN IMMEDIATE" if write else "BEGIN")
        yield conn
        conn.commit()
    except BaseException:
        conn.rollback()
        raise
    finally:
        conn.close()
