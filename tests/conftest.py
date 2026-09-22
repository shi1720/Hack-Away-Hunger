import os
from datetime import timedelta
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit
from uuid import uuid4

import psycopg
import pytest
from fastapi.testclient import TestClient
from psycopg import sql

from backend.config import Settings
from backend.main import create_app
from backend.security import iso, now


@pytest.fixture(params=["sqlite"] + (["postgres"] if os.getenv("PANTRY_TEST_POSTGRES") else []))
def app(tmp_path, request):
    if request.param == "sqlite":
        yield create_app(
            Settings(database=str(tmp_path / "test.sqlite3"), environment="test", auth_limit=1000)
        )
        return
    if request.node.get_closest_marker("sqlite_only"):
        pytest.skip("This test exercises SQLite-specific backup or schema migration")
    base_url = os.environ["PANTRY_TEST_POSTGRES"]
    schema = "test_" + uuid4().hex
    with psycopg.connect(base_url, autocommit=True) as admin:
        admin.execute(sql.SQL("CREATE SCHEMA {}").format(sql.Identifier(schema)))
    parts = urlsplit(base_url)
    options = dict(parse_qsl(parts.query))
    options["options"] = "-csearch_path=" + schema
    database = urlunsplit(
        (parts.scheme, parts.netloc, parts.path, urlencode(options), parts.fragment)
    )
    try:
        yield create_app(Settings(database=database, environment="test", auth_limit=1000))
    finally:
        with psycopg.connect(base_url, autocommit=True) as admin:
            admin.execute(sql.SQL("DROP SCHEMA {} CASCADE").format(sql.Identifier(schema)))


@pytest.fixture
def client(app):
    with TestClient(app) as client:
        yield client


@pytest.fixture
def demo(client):
    response = client.post("/api/auth/demo", json={})
    assert response.status_code == 201, response.text
    client.headers["X-CSRF-Token"] = response.json()["csrf_token"]
    return client


def register(client, email="owner@example.org", password="correct horse pantry relay"):
    response = client.post(
        "/api/auth/register",
        json={
            "name": "Shivam Gupta",
            "email": email,
            "password": password,
            "network_name": "Test Pantry Network",
        },
    )
    assert response.status_code == 201, response.text
    client.headers["X-CSRF-Token"] = response.json()["csrf_token"]
    return response.json()


def create_site(client, name="Pantry", capacity=1000, storage=None, lat=41.6, lng=-93.6):
    response = client.post(
        "/api/sites",
        json={
            "name": name,
            "city": "Des Moines",
            "address": "Test address",
            "lat": lat,
            "lng": lng,
            "storage_types": storage or ["ambient", "chilled", "frozen"],
            "capacity_lb": capacity,
        },
    )
    assert response.status_code == 201, response.text
    return response.json()


def create_lot(
    client,
    site_id,
    quantity=120,
    reserve=0,
    storage="ambient",
    category="produce",
    hours=72,
    restricted=False,
    name="Apples",
):
    response = client.post(
        "/api/lots",
        json={
            "site_id": site_id,
            "food_name": name,
            "category": category,
            "storage": storage,
            "quantity_lb": quantity,
            "reserve_lb": reserve,
            "expires_at": iso(now() + timedelta(hours=hours)),
            "restricted": restricted,
        },
    )
    assert response.status_code == 201, response.text
    return response.json()


def create_need(client, site_id, quantity=120, category="produce", hours=24):
    response = client.post(
        "/api/needs",
        json={
            "site_id": site_id,
            "category": category,
            "quantity_lb": quantity,
            "service_at": iso(now() + timedelta(hours=hours)),
        },
    )
    assert response.status_code == 201, response.text
    return response.json()


def reserve(client, proposal=None, quantity=None):
    if proposal is None:
        proposals = client.post("/api/planner", json={}).json()["proposals"]
        assert proposals
        proposal = proposals[0]
    response = client.post(
        "/api/transfers",
        json={
            "lot_id": proposal["lot_id"],
            "need_id": proposal["need_id"],
            "quantity_lb": quantity if quantity is not None else proposal["quantity_lb"],
        },
    )
    assert response.status_code == 201, response.text
    return response.json()


def action(client, transfer_id, name, body=None, expected=200):
    response = client.post(f"/api/transfers/{transfer_id}/{name}", json=body or {})
    assert response.status_code == expected, response.text
    return response.json()


def dispatch(client, transfer_id, temperature=None):
    action(client, transfer_id, "accept", {"receiver_name": "Sam Receiver"})
    action(
        client, transfer_id, "pickup", {"condition_confirmed": True, "temperature_f": temperature}
    )
    action(client, transfer_id, "arrive")


@pytest.fixture
def real_operator(client):
    register(client)
    source = create_site(client, "Source")
    destination = create_site(client, "Destination")
    create_lot(client, source["id"], quantity=120)
    create_need(client, destination["id"], quantity=120)
    return client
