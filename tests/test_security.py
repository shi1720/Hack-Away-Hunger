from datetime import timedelta

import pytest
from conftest import action, register, reserve
from fastapi.testclient import TestClient

from backend.config import Settings
from backend.db import is_postgres, transaction
from backend.main import create_app
from backend.security import COOKIE, digest, iso, now


def test_registration_real_workspace_is_empty_and_password_and_sessions_are_hashed(client, app):
    password = "  correct horse pantry relay  "
    auth = register(client, password=password)
    workspace = client.get("/api/workspace").json()
    assert workspace["network"]["is_demo"] is False
    assert (
        workspace["sites"]
        == workspace["lots"]
        == workspace["needs"]
        == workspace["transfers"]
        == []
    )
    assert auth["user"]["name"] == "Shivam Gupta"
    with transaction(app.state.settings.database) as conn:
        user = conn.execute("SELECT * FROM users").fetchone()
        session = conn.execute("SELECT * FROM sessions").fetchone()
        assert user["password_hash"].startswith("scrypt$")
        assert password not in user["password_hash"]
        assert session["token_hash"] == digest(client.cookies.get(COOKIE))
        assert session["token_hash"] != client.cookies.get(COOKIE)
    assert client.post("/api/auth/logout", json={}).status_code == 200
    assert client.get("/api/auth/me").status_code == 401
    assert (
        client.post(
            "/api/auth/login", json={"email": "owner@example.org", "password": password.strip()}
        ).status_code
        == 401
    )
    result = client.post(
        "/api/auth/login", json={"email": "OWNER@EXAMPLE.ORG", "password": password}
    )
    assert result.status_code == 200
    assert "HttpOnly" in result.headers["set-cookie"]
    assert "SameSite=lax" in result.headers["set-cookie"]
    assert "password" not in str(result.json())


def test_csrf_session_expiry_and_unknown_session_fail_closed(demo, app):
    csrf = demo.headers.pop("X-CSRF-Token")
    assert demo.post("/api/planner", json={}).status_code == 403
    assert demo.post("/api/auth/logout", json={}).status_code == 403
    demo.headers["X-CSRF-Token"] = "wrong-token"
    assert demo.post("/api/planner", json={}).status_code == 403
    demo.headers["X-CSRF-Token"] = csrf
    assert demo.post("/api/planner", json={}).status_code == 200
    with transaction(app.state.settings.database, write=True) as conn:
        conn.execute("UPDATE sessions SET expires_at=?", (iso(now() - timedelta(seconds=1)),))
    assert demo.get("/api/workspace").status_code == 401
    demo.cookies.clear()
    demo.cookies.set(COOKIE, "invented")
    assert demo.get("/api/auth/me").status_code == 401


def test_host_origin_body_size_and_security_headers(demo):
    assert demo.get("/api/health", headers={"Host": "evil.example"}).status_code == 400
    assert (
        demo.post("/api/planner", json={}, headers={"Origin": "https://evil.example"}).status_code
        == 403
    )
    assert demo.post("/api/planner", content="x" * 65537).status_code == 413
    response = demo.get("/api/workspace")
    assert response.headers["cache-control"] == "no-store"
    assert response.headers["x-content-type-options"] == "nosniff"
    assert "frame-ancestors 'none'" in response.headers["content-security-policy"]


def test_tenant_isolation_across_every_mutation_and_export(demo, app):
    transfer = reserve(demo)
    workspace = demo.get("/api/workspace").json()
    original_lot = next(lot for lot in workspace["lots"] if lot["id"] == transfer["lot_id"])
    with TestClient(app) as stranger:
        register(stranger, "stranger@example.org")
        assert stranger.get("/api/workspace").json()["sites"] == []
        assert (
            stranger.patch(
                f"/api/lots/{transfer['lot_id']}",
                json={"version": original_lot["version"], "quantity_lb": 0},
            ).status_code
            == 404
        )
        assert (
            stranger.patch(
                f"/api/sites/{transfer['source_id']}", json={"name": "Stolen"}
            ).status_code
            == 404
        )
        assert (
            stranger.post(
                "/api/needs",
                json={
                    "site_id": transfer["source_id"],
                    "category": "produce",
                    "quantity_lb": 1,
                    "service_at": iso(now() + timedelta(days=1)),
                },
            ).status_code
            == 404
        )
        assert (
            stranger.post(
                "/api/lots",
                json={
                    "site_id": transfer["source_id"],
                    "food_name": "Stolen",
                    "category": "produce",
                    "storage": "ambient",
                    "quantity_lb": 1,
                    "expires_at": iso(now() + timedelta(days=1)),
                },
            ).status_code
            == 404
        )
        assert (
            stranger.post(
                "/api/transfers",
                json={
                    "lot_id": transfer["lot_id"],
                    "need_id": transfer["need_id"],
                    "quantity_lb": 1,
                },
            ).status_code
            == 404
        )
        for name, body in [
            ("accept", {"receiver_name": "Intruder"}),
            ("pickup", {"condition_confirmed": True}),
            ("arrive", {}),
            ("receive", {"received_lb": 1, "receiver_name": "Intruder"}),
            ("cancel", {"reason": "Intruder"}),
        ]:
            action(stranger, transfer["id"], name, body, expected=404)
        assert transfer["id"] not in stranger.get("/api/reports/audit.csv").text
        assert "Cedar Grove" not in stranger.get("/api/reports/receipts.csv").text
    assert demo.get("/api/workspace").json()["transfers"][0]["status"] == "reserved"


def join_role(admin, member, role, email):
    invitation = admin.post("/api/invites", json={"role": role})
    assert invitation.status_code == 201
    token = invitation.json()["token"]
    response = member.post(
        "/api/auth/join",
        json={
            "token": token,
            "name": "New Member",
            "email": email,
            "password": "strong pantry password",
        },
    )
    assert response.status_code == 201, response.text
    member.headers["X-CSRF-Token"] = response.json()["csrf_token"]
    return token, response.json()


def test_driver_can_only_pick_up_and_arrive_and_invites_are_one_use(real_operator, app):
    demo = real_operator
    transfer = reserve(demo)
    with TestClient(app) as driver:
        token, joined = join_role(demo, driver, "driver", "driver@example.org")
        assert joined["user"]["network_id"] == demo.get("/api/auth/me").json()["user"]["network_id"]
        assert joined["user"]["role"] == "driver"
        assert driver.get("/api/team").status_code == 403
        assert driver.get("/api/reports/receipts.csv").status_code == 403
        assert driver.get("/api/reports/audit.csv").status_code == 403
        assert driver.get("/api/workspace").json()["lots"] == []
        assert driver.post("/api/planner", json={}).status_code == 403
        assert driver.post("/api/invites", json={"role": "coordinator"}).status_code == 403
        assert (
            driver.post(
                "/api/transfers",
                json={
                    "lot_id": transfer["lot_id"],
                    "need_id": transfer["need_id"],
                    "quantity_lb": 1,
                },
            ).status_code
            == 403
        )
        assert (
            driver.patch(
                f"/api/lots/{transfer['lot_id']}", json={"version": 1, "quantity_lb": 0}
            ).status_code
            == 403
        )
        action(driver, transfer["id"], "accept", {"receiver_name": "Driver"}, expected=403)
        action(
            driver,
            transfer["id"],
            "receive",
            {"received_lb": 120, "receiver_name": "Driver"},
            expected=403,
        )
        action(driver, transfer["id"], "cancel", {"reason": "Not authorized"}, expected=403)
        action(demo, transfer["id"], "accept", {"receiver_name": "Sam"})
        action(driver, transfer["id"], "pickup", {"condition_confirmed": True})
        action(driver, transfer["id"], "arrive")
        action(
            driver, transfer["id"], "fail", {"reason": "Driver cannot finalize loss"}, expected=403
        )
        replay = driver.post(
            "/api/auth/join",
            json={
                "token": token,
                "name": "Another",
                "email": "another@example.org",
                "password": "strong pantry password",
            },
        )
        assert replay.status_code == 400
    action(demo, transfer["id"], "receive", {"received_lb": 120, "receiver_name": "Sam"})
    events = demo.get("/api/workspace").json()["events"]
    assert (
        next(e for e in events if e["action"] == "transfer.picked_up")["actor_id"]
        == joined["user"]["id"]
    )


def test_coordinator_cannot_escalate_to_admin_and_expired_invites_rejected(real_operator, app):
    demo = real_operator
    with TestClient(app) as member:
        _, _ = join_role(demo, member, "coordinator", "coordinator@example.org")
        assert member.post("/api/planner", json={}).status_code == 200
        assert member.get("/api/team").status_code == 200
        assert member.post("/api/invites", json={"role": "driver"}).status_code == 403
    assert demo.post("/api/invites", json={"role": "admin"}).status_code == 422
    invite = demo.post("/api/invites", json={"role": "driver"}).json()
    with transaction(app.state.settings.database, write=True) as conn:
        conn.execute(
            "UPDATE invites SET expires_at=? WHERE token_hash=?",
            (iso(now() - timedelta(seconds=1)), digest(invite["token"])),
        )
    result = demo.post(
        "/api/auth/join",
        json={
            "token": invite["token"],
            "name": "Late",
            "email": "late@example.org",
            "password": "strong pantry password",
        },
    )
    assert result.status_code == 400
    assert "token_hash" not in str(demo.get("/api/team").json())
    assert invite["token"] not in demo.get("/api/reports/audit.csv").text


def test_auth_rate_limit_persists_across_client_sessions(tmp_path):
    app = create_app(
        Settings(database=str(tmp_path / "limited.sqlite3"), auth_limit=2, auth_ip_limit=2)
    )
    with TestClient(app) as client:
        for _ in range(2):
            assert (
                client.post(
                    "/api/auth/login", json={"email": "none@example.org", "password": "bad"}
                ).status_code
                == 401
            )
        assert client.post("/api/auth/demo", json={}).status_code == 429
    with TestClient(app) as client:
        response = client.post(
            "/api/auth/login", json={"email": "different@example.org", "password": "bad"}
        )
        assert response.status_code == 429
        assert response.headers["retry-after"] == "900"


@pytest.mark.parametrize(
    "overrides",
    [
        {
            "demo_enabled": True,
            "demo_only": False,
            "cookie_secure": True,
            "allowed_hosts": ("pantry.example",),
        },
        {"demo_enabled": False, "cookie_secure": False, "allowed_hosts": ("pantry.example",)},
        {"demo_enabled": False, "cookie_secure": True, "allowed_hosts": ("*",)},
        {"demo_enabled": False, "cookie_secure": True, "allowed_hosts": ("testserver",)},
        {
            "demo_enabled": False,
            "demo_only": True,
            "cookie_secure": True,
            "allowed_hosts": ("pantry.example",),
        },
    ],
)
def test_production_rejects_unsafe_configuration(overrides):
    with pytest.raises(ValueError):
        create_app(Settings(environment="production", **overrides))


def test_demo_only_public_deployment_rejects_real_accounts_and_has_secure_cookie(tmp_path):
    app = create_app(
        Settings(
            database=str(tmp_path / "showcase.sqlite3"),
            environment="production",
            demo_only=True,
            cookie_secure=True,
            allowed_hosts=("pantry.example",),
        )
    )
    with TestClient(app, base_url="https://pantry.example") as client:
        assert client.get("/api/config").json() == {
            "demo_enabled": True,
            "demo_only": True,
            "registration_enabled": False,
        }
        response = client.post("/api/auth/demo", json={})
        assert response.status_code == 201
        assert "Secure" in response.headers["set-cookie"]
        assert response.headers["strict-transport-security"]
        client.headers["X-CSRF-Token"] = response.json()["csrf_token"]
        assert client.post("/api/invites", json={"role": "driver"}).status_code == 403
        assert (
            client.post(
                "/api/auth/register",
                json={
                    "name": "Owner",
                    "email": "owner@example.org",
                    "network_name": "Real",
                    "password": "a strong password",
                },
            ).status_code
            == 403
        )
        assert (
            client.post(
                "/api/auth/join",
                json={
                    "token": "a" * 32,
                    "name": "Owner",
                    "email": "owner@example.org",
                    "password": "a strong password",
                },
            ).status_code
            == 403
        )
        assert (
            client.post(
                "/api/auth/login",
                json={"email": "owner@example.org", "password": "a strong password"},
            ).status_code
            == 403
        )


def test_demo_cleanup_removes_old_networks_without_affecting_real_networks(client, app):
    real = register(client)
    first = client.post("/api/auth/demo", json={}).json()
    old_id = first["user"]["network_id"]
    old_token = client.cookies.get(COOKIE)
    with transaction(app.state.settings.database, write=True) as conn:
        conn.execute("UPDATE networks SET created_at=?", (iso(now() - timedelta(days=2)),))
    second = client.post("/api/auth/demo", json={})
    assert second.status_code == 201
    with transaction(app.state.settings.database) as conn:
        assert conn.execute("SELECT 1 FROM networks WHERE id=?", (old_id,)).fetchone() is None
        assert (
            conn.execute(
                "SELECT 1 FROM sessions WHERE token_hash=?", (digest(old_token),)
            ).fetchone()
            is None
        )
        assert conn.execute(
            "SELECT 1 FROM networks WHERE id=?", (real["user"]["network_id"],)
        ).fetchone()
        if not is_postgres(app.state.settings.database):
            assert not conn.execute("PRAGMA foreign_key_check").fetchall()


def test_password_strength_and_unknown_fields_are_validated(client):
    payload = {
        "name": "Owner",
        "email": "owner@example.org",
        "network_name": "Network",
        "password": "short",
    }
    assert client.post("/api/auth/register", json=payload).status_code == 422
    assert (
        client.post(
            "/api/auth/register", json={**payload, "password": "strong password", "role": "admin"}
        ).status_code
        == 422
    )
    assert (
        client.post(
            "/api/auth/register",
            json={**payload, "password": "strong password", "email": "not-email"},
        ).status_code
        == 422
    )
