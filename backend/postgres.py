"""PostgreSQL persistence with the same bounded, serialized-write contract as SQLite.

The application intentionally uses one transaction-wide advisory lock for writes.
This preserves allocation invariants across Cloud Run instances without claiming
unbounded write throughput. Reads use a repeatable snapshot. SQL parameters remain
bound parameters and are never interpolated into SQL text.
"""

from collections.abc import Mapping

import psycopg

WRITE_LOCK = 1717202609
SCHEMA_VERSION = 3


class Record(Mapping):
    """Named and positional row access matching the sqlite.Row calls in the domain."""

    def __init__(self, names, values):
        self._names = tuple(names)
        self._values = tuple(values)
        self._mapping = dict(zip(self._names, self._values, strict=True))

    def __getitem__(self, key):
        return self._values[key] if isinstance(key, int) else self._mapping[key]

    def __iter__(self):
        return iter(self._names)

    def __len__(self):
        return len(self._names)


def row_factory(cursor):
    names = [column.name for column in cursor.description] if cursor.description else []
    return lambda values: Record(names, values)


def parameters_sql(sql: str) -> str:
    """Translate controlled qmark SQL without touching question marks inside literals."""
    result, quote, index = [], None, 0
    while index < len(sql):
        char = sql[index]
        if char == "%":
            result.append("%%")
        elif quote:
            result.append(char)
            if char == quote:
                if index + 1 < len(sql) and sql[index + 1] == quote:
                    result.append(sql[index + 1])
                    index += 1
                else:
                    quote = None
        elif char in {"'", '"'}:
            quote = char
            result.append(char)
        elif char == "?":
            result.append("%s")
        else:
            result.append(char)
        index += 1
    return "".join(result)


class Connection:
    def __init__(self, database: str):
        try:
            self.raw = psycopg.connect(
                database, autocommit=True, row_factory=row_factory, connect_timeout=15
            )
        except (psycopg.Error, ValueError):
            # Some driver parse errors echo malformed credential strings. Do not let
            # startup logs or API failures disclose any part of the secret DSN.
            raise psycopg.OperationalError(
                "PostgreSQL connection unavailable; check the configured secret and service access"
            ) from None
        # Bound lock waits and statements so a stalled database returns a retryable error.
        self.raw.execute("SET lock_timeout = '15s'")
        self.raw.execute("SET statement_timeout = '30s'")
        self.raw.execute("SET idle_in_transaction_session_timeout = '30s'")

    def execute(self, sql: str, parameters=None):
        if parameters is None:
            return self.raw.execute(sql)
        return self.raw.execute(parameters_sql(sql), parameters)

    def executemany(self, sql: str, parameters):
        cursor = self.raw.cursor()
        cursor.executemany(parameters_sql(sql), parameters)
        return cursor

    def commit(self):
        self.raw.execute("COMMIT")

    def rollback(self):
        if not self.raw.closed:
            self.raw.execute("ROLLBACK")

    def close(self):
        self.raw.close()


def initialize(database: str, sqlite_schema: str) -> None:
    conn = Connection(database)
    try:
        conn.execute("BEGIN")
        conn.execute("SELECT pg_advisory_xact_lock(?)", (WRITE_LOCK,))
        conn.execute(
            "CREATE TABLE IF NOT EXISTS pantry_schema (id INTEGER PRIMARY KEY CHECK(id=1), version INTEGER NOT NULL)"
        )
        row = conn.execute("SELECT version FROM pantry_schema WHERE id=1").fetchone()
        version = row[0] if row else 0
        if version > SCHEMA_VERSION:
            raise RuntimeError("Database schema is newer than this application")
        # PostgreSQL REAL is single precision. Coordinates and timestamps need doubles.
        schema = sqlite_schema.replace("UNIQUE COLLATE NOCASE", "UNIQUE").replace(
            " REAL", " DOUBLE PRECISION"
        )
        for statement in schema.split(";"):
            if statement.strip():
                conn.execute(statement)
        conn.execute(
            "CREATE UNIQUE INDEX IF NOT EXISTS idx_users_email_lower ON users (lower(email))"
        )
        if version < 2:
            conn.execute(
                "ALTER TABLE needs ADD COLUMN IF NOT EXISTS closed INTEGER NOT NULL DEFAULT 0"
            )
        if version < 3:
            conn.execute("ALTER TABLE transfers DROP CONSTRAINT IF EXISTS transfers_status_check")
            conn.execute(
                "ALTER TABLE transfers ADD CONSTRAINT transfers_status_check CHECK(status IN ('reserved','accepted','in_transit','arrived','received','cancelled','failed'))"
            )
        conn.execute(
            "INSERT INTO pantry_schema (id,version) VALUES (1,?) ON CONFLICT (id) DO UPDATE SET version=EXCLUDED.version",
            (SCHEMA_VERSION,),
        )
        conn.commit()
    except BaseException:
        conn.rollback()
        raise
    finally:
        conn.close()
