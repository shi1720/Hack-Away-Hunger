"""Exercise operator commands against live WAL databases and restored app instances."""

import os
import shutil
import stat
import subprocess
import sys
from pathlib import Path

import pytest
from conftest import action, create_lot, create_need, create_site, dispatch, register, reserve
from fastapi.testclient import TestClient

from backend.config import Settings
from backend.db import connect, transaction
from backend.main import create_app
from scripts import account_admin

ROOT = Path(__file__).resolve().parent.parent


def command(script, *args):
    return subprocess.run(
        [sys.executable, str(ROOT / "scripts" / script), *(str(arg) for arg in args)],
        capture_output=True,
        text=True,
        check=False,
        timeout=30,
    )


def test_online_backup_includes_live_wal_and_restores_a_working_application(tmp_path):
    source_path = tmp_path / "online ?food# network.sqlite3"
    backup_path = tmp_path / "backups" / "verified.sqlite3"
    source_app = create_app(Settings(database=str(source_path), environment="test"))
    with TestClient(source_app) as source:
        # Hold a connection open so committed writes remain in WAL during the backup.
        keeper = connect(str(source_path))
        keeper.execute("SELECT COUNT(*) FROM users").fetchone()
        try:
            register(source)
            origin = create_site(source, "Origin")
            destination = create_site(source, "Destination")
            lot = create_lot(source, origin["id"], quantity=300, reserve=180)
            need = create_need(source, destination["id"], quantity=120)
            transfer = reserve(
                source, {"lot_id": lot["id"], "need_id": need["id"], "quantity_lb": 120}
            )
            dispatch(source, transfer["id"])
            action(
                source,
                transfer["id"],
                "receive",
                {"received_lb": 112, "receiver_name": "Sam", "exception_reason": "8 lb damaged"},
            )
            before = source.get("/api/workspace").json()
            receipt_csv = source.get("/api/reports/receipts.csv").text
            assert Path(str(source_path) + "-wal").stat().st_size > 0
            result = command("backup.py", source_path, backup_path)
            assert result.returncode == 0, result.stderr
            assert "Verified backup" in result.stdout
            assert source.get("/api/health").status_code == 200
        finally:
            keeper.close()
    if os.name == "posix":
        assert stat.S_IMODE(backup_path.stat().st_mode) == 0o600
    restored_path = tmp_path / "restored.sqlite3"
    shutil.copyfile(backup_path, restored_path)
    restored_app = create_app(Settings(database=str(restored_path), environment="test"))
    with TestClient(restored_app) as restored:
        logged_in = restored.post(
            "/api/auth/login",
            json={"email": "owner@example.org", "password": "correct horse pantry relay"},
        )
        assert logged_in.status_code == 200
        restored.headers["X-CSRF-Token"] = logged_in.json()["csrf_token"]
        after = restored.get("/api/workspace").json()
        assert after == before
        assert after["metrics"]["received_lb"] == 112
        assert restored.get("/api/reports/receipts.csv").text == receipt_csv
        with transaction(str(restored_path)) as conn:
            assert conn.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
            assert not conn.execute("PRAGMA foreign_key_check").fetchall()


@pytest.mark.sqlite_only
def test_backup_refuses_overwrite_and_removes_failed_output(real_operator, app, tmp_path):
    destination = tmp_path / "existing.sqlite3"
    destination.write_bytes(b"preserve this prior backup")
    result = command("backup.py", app.state.settings.database, destination)
    assert result.returncode != 0
    assert "never overwritten" in result.stderr
    assert destination.read_bytes() == b"preserve this prior backup"
    corrupt = tmp_path / "corrupt.sqlite3"
    corrupt.write_bytes(b"not a sqlite database")
    failed = tmp_path / "failed-backup.sqlite3"
    result = command("backup.py", corrupt, failed)
    assert result.returncode != 0
    assert not failed.exists()
    missing = tmp_path / "missing.sqlite3"
    result = command("backup.py", missing, failed)
    assert result.returncode != 0
    assert "Source database does not exist" in result.stderr
    assert not missing.exists()
    assert not failed.exists()


def test_subprocess_revoke_sessions_invalidates_all_target_sessions_only(client, app):
    auth = register(client)
    with TestClient(app) as second_session, TestClient(app) as unrelated:
        assert (
            second_session.post(
                "/api/auth/login",
                json={"email": "owner@example.org", "password": "correct horse pantry relay"},
            ).status_code
            == 200
        )
        register(unrelated, email="unrelated@example.org")
        with transaction(app.state.settings.database) as conn:
            old_hash = conn.execute(
                "SELECT password_hash FROM users WHERE id=?", (auth["user"]["id"],)
            ).fetchone()[0]
        result = command(
            "account_admin.py",
            "revoke-sessions",
            "--database",
            app.state.settings.database,
            "--email",
            "OWNER@EXAMPLE.ORG",
        )
        assert result.returncode == 0, result.stderr
        assert "revoked 2 session(s)" in result.stdout
        assert client.get("/api/auth/me").status_code == 401
        assert second_session.get("/api/auth/me").status_code == 401
        assert unrelated.get("/api/auth/me").status_code == 200
        with transaction(app.state.settings.database) as conn:
            assert (
                conn.execute(
                    "SELECT password_hash FROM users WHERE id=?", (auth["user"]["id"],)
                ).fetchone()[0]
                == old_hash
            )
            event = conn.execute(
                "SELECT * FROM events WHERE action='operator.revoke-sessions'"
            ).fetchone()
            assert event["actor_name"] == "Local database operator"
            assert "account owner attribution is not asserted" in event["description"]
        assert (
            client.post(
                "/api/auth/login",
                json={"email": "owner@example.org", "password": "correct horse pantry relay"},
            ).status_code
            == 200
        )


def test_password_recovery_changes_credentials_and_revokes_sessions_without_logging_password(
    client, app, monkeypatch, capsys
):
    register(client)
    new_password = "  newly recovered pantry password  "
    prompts = iter([new_password, new_password])
    monkeypatch.setattr(account_admin.getpass, "getpass", lambda _: next(prompts))
    assert (
        account_admin.main(
            [
                "reset-password",
                "--database",
                app.state.settings.database,
                "--email",
                "owner@example.org",
            ]
        )
        == 0
    )
    output = capsys.readouterr()
    assert new_password not in output.out + output.err
    assert client.get("/api/auth/me").status_code == 401
    assert (
        client.post(
            "/api/auth/login",
            json={"email": "owner@example.org", "password": "correct horse pantry relay"},
        ).status_code
        == 401
    )
    logged_in = client.post(
        "/api/auth/login", json={"email": "owner@example.org", "password": new_password}
    )
    assert logged_in.status_code == 200
    with transaction(app.state.settings.database) as conn:
        event = conn.execute(
            "SELECT * FROM events WHERE action='operator.reset-password'"
        ).fetchone()
        assert new_password not in str(dict(event))
        assert event["actor_name"] == "Local database operator"


def test_invalid_recovery_input_leaves_credentials_and_sessions_unchanged(client, app, monkeypatch):
    register(client)
    prompts = iter(["first strong password", "different strong password"])
    monkeypatch.setattr(account_admin.getpass, "getpass", lambda _: next(prompts))
    with pytest.raises(SystemExit):
        account_admin.main(
            [
                "reset-password",
                "--database",
                app.state.settings.database,
                "--email",
                "owner@example.org",
            ]
        )
    assert client.get("/api/auth/me").status_code == 200
    result = command(
        "account_admin.py",
        "revoke-sessions",
        "--database",
        app.state.settings.database,
        "--email",
        "absent@example.org",
    )
    assert result.returncode != 0
    assert "No such account" in result.stderr
    assert client.get("/api/auth/me").status_code == 200
    with transaction(app.state.settings.database) as conn:
        assert (
            conn.execute("SELECT COUNT(*) FROM events WHERE action LIKE 'operator.%'").fetchone()[0]
            == 0
        )
