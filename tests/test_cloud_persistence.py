"""Firebase proxy session compatibility and PostgreSQL durability/serialization."""

from concurrent.futures import ThreadPoolExecutor

import psycopg
import pytest
from conftest import action, dispatch
from fastapi.testclient import TestClient

from backend.config import Settings
from backend.db import is_postgres, transaction
from backend.main import create_app
from backend.postgres import parameters_sql
from backend.security import COOKIE


def test_firebase_session_cookie_survives_proxy_and_requires_csrf(tmp_path):
    app = create_app(
        Settings(
            database=str(tmp_path / "firebase-proxy.sqlite3"),
            environment="production",
            demo_only=True,
            cookie_secure=True,
            allowed_hosts=("pantry-service.a.run.app", "pantryrelay.web.app"),
            trusted_origins=("https://pantryrelay.web.app",),
        )
    )
    # Firebase forwards the Hosting browser origin while Cloud Run can see its service Host.
    with TestClient(app, base_url="https://pantry-service.a.run.app") as client:
        response = client.post(
            "/api/auth/demo", json={}, headers={"Origin": "https://pantryrelay.web.app"}
        )
        assert response.status_code == 201
        assert COOKIE == "__session"
        cookie = response.headers["set-cookie"]
        assert cookie.startswith("__session=")
        assert "HttpOnly" in cookie and "Secure" in cookie and "SameSite=lax" in cookie
        assert client.get("/api/auth/me").status_code == 200
        assert (
            client.post(
                "/api/planner", json={}, headers={"Origin": "https://pantryrelay.web.app"}
            ).status_code
            == 403
        )
        client.headers["X-CSRF-Token"] = response.json()["csrf_token"]
        assert (
            client.post(
                "/api/planner", json={}, headers={"Origin": "https://pantryrelay.web.app"}
            ).status_code
            == 200
        )
        for bad_origin in (
            "https://pantryrelay.web.app.evil.example",
            "http://pantryrelay.web.app",
            "https://[",
            "https://pantryrelay.web.app/path",
        ):
            assert (
                client.post("/api/planner", json={}, headers={"Origin": bad_origin}).status_code
                == 403
            )
        assert client.get("/api/workspace").headers["cache-control"] == "no-store"
        assert (
            client.post(
                "/api/auth/logout", json={}, headers={"Origin": "https://pantryrelay.web.app"}
            ).status_code
            == 200
        )
        assert client.get("/api/auth/me").status_code == 401


def test_non_ascii_csrf_is_forbidden_instead_of_server_error(demo):
    response = demo.post("/api/planner", json={}, headers=[(b"x-csrf-token", b"\xff")])
    assert response.status_code == 403


def test_malformed_origin_is_forbidden_instead_of_server_error(demo):
    assert demo.post("/api/planner", json={}, headers={"Origin": "https://["}).status_code == 403


@pytest.mark.parametrize(
    "origin",
    [
        "http://pantry.example",
        "https://*.example",
        "https://pantry.example/path",
        "https://user@pantry.example",
        "https://[",
    ],
)
def test_production_requires_exact_https_trusted_origins(origin):
    with pytest.raises(ValueError):
        Settings(
            environment="production",
            demo_enabled=False,
            cookie_secure=True,
            allowed_hosts=("pantry.example",),
            trusted_origins=(origin,),
        ).validate()


def test_production_real_and_demo_accounts_require_explicit_durable_mode():
    values = dict(
        environment="production",
        demo_enabled=True,
        demo_only=False,
        cookie_secure=True,
        allowed_hosts=("pantry.example",),
    )
    with pytest.raises(ValueError):
        Settings(**values, database="postgresql://localhost/pantry").validate()
    with pytest.raises(ValueError):
        Settings(**values, database="data/local.sqlite3", allow_public_demo=True).validate()
    Settings(**values, database="postgresql://localhost/pantry", allow_public_demo=True).validate()
    with pytest.raises(ValueError):
        Settings(
            environment="production",
            demo_enabled=False,
            cookie_secure=True,
            allowed_hosts=("*.run.app",),
        ).validate()


def test_postgresql_parameter_translation_preserves_quoted_question_marks_and_percent():
    assert (
        parameters_sql("SELECT '?' AS literal, ? AS bound, '100%' AS percentage")
        == "SELECT '?' AS literal, %s AS bound, '100%%' AS percentage"
    )
    assert parameters_sql("SELECT 'isn''t ?' AS literal, ?") == "SELECT 'isn''t ?' AS literal, %s"


def test_two_postgresql_application_instances_share_durable_state_and_serialize_writes(demo, app):
    if not is_postgres(app.state.settings.database):
        pytest.skip("Exercises shared PostgreSQL state across application instances")
    proposal = demo.post("/api/planner", json={}).json()["proposals"][0]
    body = {key: proposal[key] for key in ("lot_id", "need_id", "quantity_lb")}
    persisted_cookie = demo.cookies.get(COOKIE)
    csrf = demo.headers["X-CSRF-Token"]
    # A fresh application instance has no process memory from the original instance.
    with TestClient(create_app(app.state.settings)) as second:
        second.cookies.set(COOKIE, persisted_cookie)
        second.headers["X-CSRF-Token"] = csrf
        assert second.get("/api/workspace").json() == demo.get("/api/workspace").json()
        with ThreadPoolExecutor(max_workers=2) as pool:
            responses = list(
                pool.map(lambda client: client.post("/api/transfers", json=body), (demo, second))
            )
        assert sorted(response.status_code for response in responses) == [201, 409]
        transfer_id = next(
            response.json()["id"] for response in responses if response.status_code == 201
        )
        dispatch(second, transfer_id)
        action(
            second,
            transfer_id,
            "receive",
            {
                "received_lb": 112,
                "receiver_name": "Sam",
                "exception_reason": "8 lb packaging damage",
            },
        )
    with TestClient(create_app(app.state.settings)) as restarted:
        restarted.cookies.set(COOKIE, persisted_cookie)
        restarted.headers["X-CSRF-Token"] = csrf
        workspace = restarted.get("/api/workspace").json()
        assert workspace["metrics"]["received_lb"] == 112
        assert workspace["transfers"][0]["status"] == "received"
        assert workspace["transfers"][0]["rejected_lb"] == 8
        assert len(workspace["transfers"]) == 1


def test_postgresql_database_constraints_and_rollback_preserve_physical_stock(demo, app):
    if not is_postgres(app.state.settings.database):
        pytest.skip("Exercises PostgreSQL CHECK enforcement and transactional rollback")
    before = demo.get("/api/workspace").json()
    lot = before["lots"][0]
    with (
        pytest.raises(psycopg.IntegrityError),
        transaction(app.state.settings.database, write=True) as conn,
    ):
        conn.execute("UPDATE lots SET quantity_units=-1 WHERE id=?", (lot["id"],))
    assert demo.get("/api/workspace").json() == before
    with pytest.raises(RuntimeError), transaction(app.state.settings.database, write=True) as conn:
        conn.execute("UPDATE lots SET notes=? WHERE id=?", ("uncommitted change", lot["id"]))
        raise RuntimeError("Simulated request failure before commit")
    assert demo.get("/api/workspace").json() == before


def test_driver_connection_errors_and_settings_do_not_disclose_database_secrets(monkeypatch):
    from backend.postgres import Connection

    def unavailable(*_args, **_kwargs):
        raise psycopg.OperationalError("invalid credential token: NEVER_PRINT_THIS_PASSWORD")

    monkeypatch.setattr(psycopg, "connect", unavailable)
    secret_url = "postgresql://owner:NEVER_PRINT_THIS_PASSWORD@database/pantry"
    assert "NEVER_PRINT_THIS_PASSWORD" not in repr(Settings(database=secret_url))
    with pytest.raises(psycopg.OperationalError) as raised:
        Connection(secret_url)
    assert "NEVER_PRINT_THIS_PASSWORD" not in str(raised.value)
    assert raised.value.__suppress_context__ is True


def test_postgresql_api_failure_returns_generic_retryable_error(client, monkeypatch):
    from contextlib import contextmanager

    @contextmanager
    def unavailable(*_args, **_kwargs):
        raise psycopg.OperationalError("database DSN has NEVER_PRINT_THIS_PASSWORD")
        yield

    monkeypatch.setattr("backend.main.transaction", unavailable)
    response = client.get("/api/health")
    assert response.status_code == 503
    assert response.headers["retry-after"] == "2"
    assert "NEVER_PRINT_THIS_PASSWORD" not in response.text


def test_duplicate_storage_patch_returns_validation_error_without_mutation(demo):
    before = demo.get("/api/workspace").json()
    site = before["sites"][0]
    result = demo.patch(f"/api/sites/{site['id']}", json={"storage_types": ["ambient", "ambient"]})
    assert result.status_code == 422
    assert "unique" in result.json()["detail"]
    assert demo.get("/api/workspace").json() == before
