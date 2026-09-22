#!/usr/bin/env python3
"""Create an online SQLite backup without overwriting an existing file."""

import argparse
import os
import sqlite3
from contextlib import closing
from pathlib import Path


def backup_database(source_path: Path, destination_path: Path) -> None:
    """Copy a consistent snapshot, including live WAL contents, to a private file."""
    destination_path.parent.mkdir(parents=True, exist_ok=True)
    descriptor = os.open(destination_path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    os.close(descriptor)
    try:
        # as_uri percent-encodes path characters such as ?, #, and spaces before the
        # SQLite URI query is added. Read-only mode never creates a missing source.
        source_uri = source_path.resolve().as_uri() + "?mode=ro"
        with closing(sqlite3.connect(source_uri, uri=True)) as source:
            with closing(sqlite3.connect(destination_path)) as destination:
                source.backup(destination)
                result = destination.execute("PRAGMA integrity_check").fetchone()[0]
                if result != "ok":
                    raise RuntimeError(f"Backup integrity check failed: {result}")
                if destination.execute("PRAGMA foreign_key_check").fetchone() is not None:
                    raise RuntimeError("Backup contains inconsistent foreign-key references")
    except BaseException:
        destination_path.unlink(missing_ok=True)
        raise


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("destination", type=Path)
    args = parser.parse_args(argv)
    source = args.source.expanduser()
    destination = args.destination.expanduser()
    if not source.is_file():
        parser.error("Source database does not exist")
    try:
        backup_database(source, destination)
    except FileExistsError:
        parser.error("Destination already exists; existing backups are never overwritten")
    print(f"Verified backup: {destination}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
