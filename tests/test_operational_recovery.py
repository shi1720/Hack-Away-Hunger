import csv
import io
import secrets
from datetime import timedelta

from conftest import action, create_need, dispatch, register, reserve
from fastapi.testclient import TestClient

from backend.db import initialize, transaction
from backend.security import digest, identifier, iso, now


def test_received_stock_is_protected_for_service_until_coordinator_releases(demo):
    transfer = reserve(demo)
    dispatch(demo, transfer["id"])
    action(demo, transfer["id"], "receive", {"received_lb": 120, "receiver_name": "Sam"})
    workspace = demo.get("/api/workspace").json()
    lot = next(lot for lot in workspace["lots"] if lot["origin_transfer_id"] == transfer["id"])
    assert lot["quantity_lb"] == lot["reserve_lb"] == 120
    assert lot["available_lb"] == 0
    # A downstream need must not immediately divert just-received food from its service.
    target_id = next(
        site["id"]
        for site in workspace["sites"]
        if site["id"] not in {transfer["source_id"], transfer["destination_id"]}
    )
    create_need(demo, target_id, 120, hours=36)
    proposals = demo.post("/api/planner", json={}).json()["proposals"]
    assert not any(proposal["lot_id"] == lot["id"] for proposal in proposals)
    released = demo.patch(
        f"/api/lots/{lot['id']}", json={"version": lot["version"], "reserve_lb": 100}
    )
    assert released.status_code == 200
    assert released.json()["available_lb"] == 20
    assert any(
        event["action"] == "lot.adjusted" and event["entity_id"] == lot["id"]
        for event in demo.get("/api/workspace").json()["events"]
    )


def test_late_but_unexpired_receipt_records_throughput_without_fulfilling_missed_service(demo, app):
    transfer = reserve(demo)
    dispatch(demo, transfer["id"])
    # Simulate service passing during transit without using sleeps or weakening the cutoff.
    with transaction(app.state.settings.database, write=True) as conn:
        conn.execute(
            "UPDATE needs SET service_at=? WHERE id=?",
            (iso(now() - timedelta(seconds=1)), transfer["need_id"]),
        )
    receipt = action(demo, transfer["id"], "receive", {"received_lb": 120, "receiver_name": "Sam"})
    assert receipt["received_lb"] == 120
    assert receipt["on_time"] is False
    assert receipt["late"] is True
    assert receipt["need_credited_lb"] == 0
    workspace = demo.get("/api/workspace").json()
    need = next(need for need in workspace["needs"] if need["id"] == transfer["need_id"])
    assert need["fulfilled_lb"] == 0
    assert need["reserved_lb"] == 0
    assert need["remaining_lb"] == 120
    assert workspace["metrics"]["received_lb"] == 120
    event = next(event for event in workspace["events"] if event["action"] == "transfer.received")
    assert event["data"]["on_time"] is False
    assert event["data"]["need_credited_lb"] == 0
    assert "no service-gap fulfillment credited" in event["description"]
    row = next(
        csv.DictReader(io.StringIO(demo.get("/api/reports/receipts.csv").text.lstrip("\ufeff")))
    )
    assert row["received_lb"] == "120.0"
    assert row["on_time"] == "False"
    assert row["need_credited_lb"] == "0"


def test_restricted_and_expired_lot_display_no_shareable_stock(demo, app):
    workspace = demo.get("/api/workspace").json()
    restricted = next(lot for lot in workspace["lots"] if lot["restricted"])
    assert restricted["quantity_lb"] == 80
    assert restricted["available_lb"] == 0
    normal = next(
        lot for lot in workspace["lots"] if lot["food_name"] == "Harvest apples & carrots"
    )
    with transaction(app.state.settings.database, write=True) as conn:
        conn.execute(
            "UPDATE lots SET expires_at=? WHERE id=?",
            (iso(now() - timedelta(seconds=1)), normal["id"]),
        )
    after = demo.get("/api/workspace").json()
    expired = next(lot for lot in after["lots"] if lot["id"] == normal["id"])
    assert expired["quantity_lb"] == 300
    assert expired["available_lb"] == 0
    assert after["metrics"]["available_lb"] == workspace["metrics"]["available_lb"] - 120


def test_demo_invites_blocked_and_old_demo_invite_cannot_add_real_member(demo, app):
    assert demo.post("/api/invites", json={"role": "driver"}).status_code == 403
    token = secrets.token_urlsafe(32)
    network_id = demo.get("/api/auth/me").json()["user"]["network_id"]
    with transaction(app.state.settings.database, write=True) as conn:
        conn.execute(
            "INSERT INTO invites VALUES (?,?,?,?,?,?,?)",
            (
                identifier(),
                network_id,
                digest(token),
                "driver",
                iso(now() + timedelta(days=1)),
                None,
                iso(),
            ),
        )
    with TestClient(app) as member:
        response = member.post(
            "/api/auth/join",
            json={
                "token": token,
                "name": "Real Member",
                "email": "real@example.org",
                "password": "strong real password",
            },
        )
        assert response.status_code == 403
    assert len(demo.get("/api/team").json()["users"]) == 1


def test_close_need_rejects_active_transfers_and_replayed_or_stale_allocations(demo):
    proposal = demo.post("/api/planner", json={}).json()["proposals"][0]
    transfer = reserve(demo, proposal)
    url = f"/api/needs/{transfer['need_id']}/close"
    response = demo.post(url, json={"reason": "Request entered in error"})
    assert response.status_code == 409
    action(demo, transfer["id"], "cancel", {"reason": "Cancel mistaken request"})
    closed = demo.post(url, json={"reason": "Request entered in error"})
    assert closed.status_code == 200
    assert closed.json()["closed"] is True
    assert closed.json()["remaining_lb"] == 0
    assert demo.post(url, json={"reason": "Close again"}).status_code == 409
    assert (
        demo.post(
            "/api/transfers",
            json={key: proposal[key] for key in ("lot_id", "need_id", "quantity_lb")},
        ).status_code
        == 409
    )
    assert not any(
        p["need_id"] == proposal["need_id"]
        for p in demo.post("/api/planner", json={}).json()["proposals"]
    )
    event = next(
        e for e in demo.get("/api/workspace").json()["events"] if e["action"] == "need.closed"
    )
    assert event["data"]["unfilled_lb_at_close"] == 120


def test_close_need_is_tenant_scoped_and_requires_reason(demo, app):
    need_id = demo.get("/api/workspace").json()["needs"][0]["id"]
    assert demo.post(f"/api/needs/{need_id}/close", json={"reason": ""}).status_code == 422
    with TestClient(app) as other:
        register(other, "another@example.org")
        assert (
            other.post(f"/api/needs/{need_id}/close", json={"reason": "Not mine"}).status_code
            == 404
        )


def test_schema_v1_to_v3_migration_preserves_existing_data(demo, app):
    before = demo.get("/api/workspace").json()
    # The prior application version had no closed column. Build that exact schema shape.
    with transaction(app.state.settings.database, write=True) as conn:
        conn.execute("ALTER TABLE needs DROP COLUMN closed")
        conn.execute("PRAGMA user_version=1")
    initialize(app.state.settings.database)
    after = demo.get("/api/workspace").json()
    assert after == before
    with transaction(app.state.settings.database) as conn:
        assert conn.execute("PRAGMA user_version").fetchone()[0] == 3
        assert not conn.execute("PRAGMA foreign_key_check").fetchall()


def test_failed_delivery_after_pickup_releases_resources_without_restoring_stock(demo):
    transfer = reserve(demo)
    action(demo, transfer["id"], "accept", {"receiver_name": "Sam"})
    action(demo, transfer["id"], "pickup", {"condition_confirmed": True})
    failed = action(
        demo,
        transfer["id"],
        "fail",
        {"reason": "Vehicle loss; stock cannot be recovered for delivery"},
    )
    assert failed["status"] == "failed"
    assert failed["failed_lb"] == 120
    assert failed["received_lb"] == failed["rejected_lb"] == 0
    workspace = demo.get("/api/workspace").json()
    source_lot = next(lot for lot in workspace["lots"] if lot["id"] == transfer["lot_id"])
    assert source_lot["quantity_lb"] == 180
    assert source_lot["reserve_lb"] == 180
    assert source_lot["available_lb"] == 0
    assert not any(lot["origin_transfer_id"] == transfer["id"] for lot in workspace["lots"])
    need = next(need for need in workspace["needs"] if need["id"] == transfer["need_id"])
    assert need["remaining_lb"] == 120
    assert need["reserved_lb"] == need["fulfilled_lb"] == 0
    assert workspace["metrics"]["active_transfers"] == 0
    assert workspace["metrics"]["received_lb"] == 0
    event = next(event for event in workspace["events"] if event["action"] == "transfer.failed")
    assert event["data"]["failed_lb"] == 120
    assert event["data"]["source_stock_restored"] is False
    assert event["data"]["previous_status"] == "in_transit"
    assert (
        demo.patch(
            f"/api/sites/{transfer['destination_id']}", json={"capacity_lb": 140}
        ).status_code
        == 200
    )
    assert transfer["id"] not in demo.get("/api/reports/receipts.csv").text
    assert transfer["id"] in demo.get("/api/reports/audit.csv").text
    action(demo, transfer["id"], "fail", {"reason": "Replay attempt"}, expected=409)
    action(demo, transfer["id"], "arrive", expected=409)
    assert (
        demo.post(
            f"/api/needs/{transfer['need_id']}/close",
            json={"reason": "Service cancelled after delivery loss"},
        ).status_code
        == 200
    )


def test_delivery_failure_requires_dispatch_and_reason_and_is_allowed_after_arrival(demo):
    transfer = reserve(demo)
    action(demo, transfer["id"], "fail", {"reason": "Not dispatched"}, expected=409)
    action(demo, transfer["id"], "accept", {"receiver_name": "Sam"})
    action(demo, transfer["id"], "fail", {"reason": "Not dispatched"}, expected=409)
    action(demo, transfer["id"], "pickup", {"condition_confirmed": True})
    action(demo, transfer["id"], "arrive")
    action(demo, transfer["id"], "fail", {"reason": ""}, expected=422)
    failed = action(
        demo,
        transfer["id"],
        "fail",
        {"reason": "Receiving site inaccessible; delivery cannot be completed"},
    )
    assert failed["failed_lb"] == 120


def test_transfer_schema_v2_to_v3_migration_preserves_reservations_and_indexes(demo, app):
    transfer = reserve(demo)
    before = demo.get("/api/workspace").json()
    with transaction(app.state.settings.database, write=True) as conn:
        current = conn.execute(
            "SELECT sql FROM sqlite_master WHERE type='table' AND name='transfers'"
        ).fetchone()[0]
        body = current[current.index("(") :].replace(",'failed'", "")
        conn.execute("CREATE TABLE transfers_v2 " + body)
        conn.execute("INSERT INTO transfers_v2 SELECT * FROM transfers")
        conn.execute("DROP TABLE transfers")
        conn.execute("ALTER TABLE transfers_v2 RENAME TO transfers")
        conn.execute("PRAGMA user_version=2")
    initialize(app.state.settings.database)
    after = demo.get("/api/workspace").json()
    assert before == after
    with transaction(app.state.settings.database) as conn:
        indexes = {r[1] for r in conn.execute("PRAGMA index_list(transfers)")}
        assert {
            "idx_transfers_network",
            "idx_transfers_lot",
            "idx_transfers_need",
            "idx_transfers_destination",
        }.issubset(indexes)
        assert not conn.execute("PRAGMA foreign_key_check").fetchall()
        assert conn.execute("PRAGMA user_version").fetchone()[0] == 3
    action(demo, transfer["id"], "accept", {"receiver_name": "Sam"})
    action(demo, transfer["id"], "pickup", {"condition_confirmed": True})
    action(demo, transfer["id"], "fail", {"reason": "Failed after upgraded application"})
