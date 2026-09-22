#!/usr/bin/env python3
"""Local operator account recovery. Requires direct access to the private database."""

import argparse
import getpass
import os
import sys
from pathlib import Path

# Allow direct invocation from any directory without installing the application package.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from backend.db import is_postgres, transaction  # noqa: E402
from backend.domain import audit  # noqa: E402
from backend.security import password_hash  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=["reset-password", "revoke-sessions"])
    parser.add_argument(
        "--database",
        default=os.getenv("PANTRY_DATABASE"),
        help="Database path or PostgreSQL URL; defaults to PANTRY_DATABASE",
    )
    parser.add_argument("--email", required=True)
    args = parser.parse_args(argv)
    if not args.database:
        parser.error("Set PANTRY_DATABASE or pass --database")
    database = (
        args.database if is_postgres(args.database) else str(Path(args.database).expanduser())
    )
    if not is_postgres(database) and not Path(database).is_file():
        parser.error("Database does not exist")
    new_hash = None
    if args.action == "reset-password":
        password = getpass.getpass("New password (at least 12 characters): ")
        confirmation = getpass.getpass("Repeat new password: ")
        if password != confirmation or not 12 <= len(password) <= 256:
            parser.error("Passwords must match and have 12-256 characters")
        new_hash = password_hash(password)
    with transaction(database, write=True) as conn:
        row = conn.execute(
            "SELECT * FROM users WHERE lower(email)=lower(?)", (args.email.strip(),)
        ).fetchone()
        if not row:
            parser.error("No such account")
        user = dict(row)
        if new_hash:
            conn.execute("UPDATE users SET password_hash=? WHERE id=?", (new_hash, user["id"]))
        count = conn.execute("DELETE FROM sessions WHERE user_id=?", (user["id"],)).rowcount
        audit(
            conn,
            {**user, "name": "Local database operator"},
            "operator." + args.action,
            "user",
            user["id"],
            "Local database operator performed account recovery; account owner attribution is not asserted",
            {
                "actor_kind": "local_database_operator",
                "subject_user_id": user["id"],
                "sessions_revoked": count,
            },
        )
    print(f"Completed {args.action}; revoked {count} session(s). Passwords were not logged.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
