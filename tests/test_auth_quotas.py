"""Shared-proxy capacity must not weaken account-specific authentication throttling."""

from dataclasses import replace

import pytest
from fastapi.testclient import TestClient

from backend.config import Settings
from backend.main import create_app


def test_shared_proxy_accepts_distinct_accounts_to_ip_threshold_and_ignores_spoofed_xff(app):
    configured = create_app(replace(app.state.settings, auth_limit=30, auth_ip_limit=35))
    with TestClient(configured) as client:
        for number in range(35):
            result = client.post(
                "/api/auth/login",
                json={"email": f"visitor-{number}@example.org", "password": "incorrect"},
                headers={"X-Forwarded-For": f"192.0.2.{number + 1}"},
            )
            assert result.status_code == 401
        limited = client.post(
            "/api/auth/login",
            json={"email": "fresh@example.org", "password": "incorrect"},
            headers={"X-Forwarded-For": "198.51.100.5"},
        )
        assert limited.status_code == 429
        assert limited.headers["retry-after"] == "900"
        assert (
            client.post(
                "/api/auth/demo", json={}, headers={"X-Forwarded-For": "198.51.100.6"}
            ).status_code
            == 429
        )


def test_higher_proxy_allowance_preserves_thirty_attempt_email_limit(app):
    configured = create_app(replace(app.state.settings, auth_limit=30, auth_ip_limit=300))
    with TestClient(configured) as client:
        for _ in range(30):
            result = client.post(
                "/api/auth/login", json={"email": "target@example.org", "password": "incorrect"}
            )
            assert result.status_code == 401
        limited = client.post(
            "/api/auth/login", json={"email": "TARGET@EXAMPLE.ORG", "password": "incorrect"}
        )
        assert limited.status_code == 429
        # The blocked account has not exhausted the aggregate shared-proxy quota.
        assert (
            client.post(
                "/api/auth/login", json={"email": "another@example.org", "password": "incorrect"}
            ).status_code
            == 401
        )
        assert client.post("/api/auth/demo", json={}).status_code == 201


def test_ip_limit_environment_does_not_change_email_limit(monkeypatch):
    monkeypatch.setenv("PANTRY_AUTH_IP_LIMIT", "300")
    # There is intentionally no environment control that increases the email limit.
    monkeypatch.setenv("PANTRY_AUTH_LIMIT", "1000")
    configured = Settings.from_env()
    assert configured.auth_ip_limit == 300
    assert configured.auth_limit == 30
    configured.validate()
    monkeypatch.delenv("PANTRY_AUTH_IP_LIMIT")
    assert Settings.from_env().auth_ip_limit == 30


@pytest.mark.parametrize("limit", ["0", "-1", "1001", "many"])
def test_aggregate_ip_limit_is_bounded_and_must_be_an_integer(monkeypatch, limit):
    monkeypatch.setenv("PANTRY_AUTH_IP_LIMIT", limit)
    with pytest.raises(ValueError):
        Settings.from_env().validate()
