import csv
import io
from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta

import pytest
from conftest import action, create_lot, create_need, create_site, dispatch, register, reserve

from backend.db import transaction
from backend.security import iso, now


def by_id(items, entity_id):
    return next(item for item in items if item["id"] == entity_id)


def test_complete_partial_receipt_preserves_stock_reserves_demand_and_provenance(demo):
    transfer = reserve(demo)
    transfer_id = transfer["id"]
    workspace = demo.get("/api/workspace").json()
    source = by_id(workspace["lots"], transfer["lot_id"])
    assert source["quantity_lb"] == 300
    assert source["reserve_lb"] == 180
    assert source["available_lb"] == 0
    need = by_id(workspace["needs"], transfer["need_id"])
    assert (need["fulfilled_lb"], need["reserved_lb"], need["remaining_lb"]) == (0, 120, 0)
    dispatch(demo, transfer_id)
    before = demo.get("/api/workspace").json()
    assert by_id(before["lots"], source["id"])["quantity_lb"] == 180
    assert not any(lot["origin_transfer_id"] == transfer_id for lot in before["lots"])
    action(
        demo,
        transfer_id,
        "receive",
        {"received_lb": 112, "receiver_name": "Sam", "exception_reason": "8 lb damaged packaging"},
    )
    after = demo.get("/api/workspace").json()
    receipt_lot = next(lot for lot in after["lots"] if lot["origin_transfer_id"] == transfer_id)
    assert receipt_lot["quantity_lb"] == 112
    assert receipt_lot["expires_at"] == source["expires_at"]
    assert receipt_lot["site_id"] == transfer["destination_id"]
    assert source["id"] in receipt_lot["notes"]
    need = by_id(after["needs"], transfer["need_id"])
    assert (need["fulfilled_lb"], need["reserved_lb"], need["remaining_lb"]) == (112, 0, 8)
    assert after["metrics"]["received_lb"] == 112
    receipt_event = next(
        event for event in after["events"] if event["action"] == "transfer.received"
    )
    assert receipt_event["data"]["rejected_lb"] == 8
    exported = list(
        csv.DictReader(io.StringIO(demo.get("/api/reports/receipts.csv").text.lstrip("\ufeff")))
    )
    assert len(exported) == 1
    assert exported[0]["received_lb"] == "112.0"
    assert exported[0]["rejected_lb"] == "8.0"
    action(demo, transfer_id, "receive", {"received_lb": 112, "receiver_name": "Sam"}, expected=409)
    assert demo.get("/api/workspace").json()["metrics"]["received_lb"] == 112


def test_atomic_duplicate_reservations_and_concurrent_conflict(demo):
    proposal = demo.post("/api/planner", json={}).json()["proposals"][0]
    payload = {key: proposal[key] for key in ("lot_id", "need_id", "quantity_lb")}
    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(lambda _: demo.post("/api/transfers", json=payload), range(2)))
    assert sorted(response.status_code for response in results) == [201, 409]
    workspace = demo.get("/api/workspace").json()
    assert len(workspace["transfers"]) == 1
    assert by_id(workspace["lots"], proposal["lot_id"])["available_lb"] == 0


def test_oversized_allocation_does_not_mutate_and_reserve_is_protected(demo):
    proposal = demo.post("/api/planner", json={}).json()["proposals"][0]
    before = demo.get("/api/workspace").json()
    response = demo.post(
        "/api/transfers",
        json={"lot_id": proposal["lot_id"], "need_id": proposal["need_id"], "quantity_lb": 120.01},
    )
    assert response.status_code == 409
    assert demo.get("/api/workspace").json() == before
    transfer = reserve(demo, proposal)
    lot = by_id(demo.get("/api/workspace").json()["lots"], proposal["lot_id"])
    for fields in ({"quantity_lb": 299.99}, {"reserve_lb": 180.01}):
        response = demo.patch(f"/api/lots/{lot['id']}", json={"version": lot["version"], **fields})
        assert response.status_code == 409
    action(demo, transfer["id"], "cancel", {"reason": "Recipient unavailable"})
    after = demo.get("/api/workspace").json()
    assert by_id(after["lots"], lot["id"])["available_lb"] == 120
    assert by_id(after["needs"], transfer["need_id"])["remaining_lb"] == 120


def test_stale_inventory_version_conflicts_after_reservation_and_pickup(demo):
    workspace = demo.get("/api/workspace").json()
    transfer = reserve(demo)
    before = by_id(workspace["lots"], transfer["lot_id"])
    response = demo.patch(
        f"/api/lots/{before['id']}", json={"version": before["version"], "quantity_lb": 300}
    )
    assert response.status_code == 409
    lot = by_id(demo.get("/api/workspace").json()["lots"], transfer["lot_id"])
    assert (
        demo.patch(
            f"/api/lots/{lot['id']}", json={"version": lot["version"], "restricted": True}
        ).status_code
        == 409
    )
    dispatch(demo, transfer["id"])
    assert (
        demo.patch(
            f"/api/lots/{lot['id']}", json={"version": lot["version"], "quantity_lb": 300}
        ).status_code
        == 409
    )


def test_inbound_capacity_held_through_arrival_then_released_by_partial_receipt(demo):
    transfer = reserve(demo)
    site_id = transfer["destination_id"]
    assert demo.patch(f"/api/sites/{site_id}", json={"capacity_lb": 259.99}).status_code == 409
    assert demo.patch(f"/api/sites/{site_id}", json={"capacity_lb": 260}).status_code == 200
    new_lot = {
        "site_id": site_id,
        "food_name": "Extra apples",
        "category": "produce",
        "storage": "ambient",
        "quantity_lb": 0.01,
        "expires_at": iso(now() + timedelta(days=5)),
    }
    assert demo.post("/api/lots", json=new_lot).status_code == 409
    dispatch(demo, transfer["id"])
    assert demo.post("/api/lots", json=new_lot).status_code == 409
    action(
        demo,
        transfer["id"],
        "receive",
        {"received_lb": 112, "receiver_name": "Sam", "exception_reason": "8 lb missing"},
    )
    assert demo.post("/api/lots", json={**new_lot, "quantity_lb": 8}).status_code == 201
    assert demo.post("/api/lots", json=new_lot).status_code == 409


def test_receipt_requires_explanation_and_never_accepts_more_than_dispatched(demo):
    transfer = reserve(demo)
    dispatch(demo, transfer["id"])
    for amount, reason in [(121, ""), (112, ""), (0, " ")]:
        action(
            demo,
            transfer["id"],
            "receive",
            {"received_lb": amount, "receiver_name": "Sam", "exception_reason": reason},
            expected=422,
        )
    workspace = demo.get("/api/workspace").json()
    assert workspace["transfers"][0]["status"] == "arrived"
    assert workspace["metrics"]["received_lb"] == 0


def test_invalid_state_transitions_are_non_mutating(demo):
    transfer = reserve(demo)
    tid = transfer["id"]
    action(demo, tid, "pickup", {"condition_confirmed": True}, expected=409)
    action(demo, tid, "arrive", expected=409)
    action(demo, tid, "receive", {"received_lb": 120, "receiver_name": "Sam"}, expected=409)
    action(demo, tid, "accept", {"receiver_name": "Sam"})
    action(demo, tid, "accept", {"receiver_name": "Sam"}, expected=409)
    action(demo, tid, "pickup", {"condition_confirmed": False}, expected=422)
    action(demo, tid, "pickup", {"condition_confirmed": True})
    action(demo, tid, "pickup", {"condition_confirmed": True}, expected=409)
    action(demo, tid, "cancel", {"reason": "Too late"}, expected=409)
    action(demo, tid, "arrive")
    action(demo, tid, "arrive", expected=409)
    assert demo.get("/api/workspace").json()["transfers"][0]["status"] == "arrived"


@pytest.mark.parametrize(
    "field,value",
    [
        ("quantity_lb", -1),
        ("quantity_lb", 1.001),
        ("reserve_lb", -0.01),
        ("quantity_lb", 1_000_001),
    ],
)
def test_weight_validation_rejects_invalid_adjustments_without_mutation(demo, field, value):
    lot = demo.get("/api/workspace").json()["lots"][0]
    response = demo.patch(f"/api/lots/{lot['id']}", json={"version": lot["version"], field: value})
    assert response.status_code == 422
    assert by_id(demo.get("/api/workspace").json()["lots"], lot["id"]) == lot


def test_non_finite_input_is_rejected(demo):
    response = demo.post(
        "/api/planner",
        content='{"max_distance_miles":NaN}',
        headers={"Content-Type": "application/json"},
    )
    assert response.status_code == 422
    assert "finite" in response.json()["detail"].lower()


def test_fractional_pounds_use_exact_integer_accounting(client):
    register(client)
    source = create_site(client, "Source")
    target = create_site(client, "Target")
    lot = create_lot(client, source["id"], quantity=0.3, reserve=0.1)
    need = create_need(client, target["id"], quantity=0.2)
    transfer = reserve(client, {"lot_id": lot["id"], "need_id": need["id"], "quantity_lb": 0.2})
    dispatch(client, transfer["id"])
    action(client, transfer["id"], "receive", {"received_lb": 0.2, "receiver_name": "Sam"})
    workspace = client.get("/api/workspace").json()
    assert by_id(workspace["lots"], lot["id"])["quantity_lb"] == 0.1
    assert by_id(workspace["needs"], need["id"])["remaining_lb"] == 0
    assert workspace["metrics"]["received_lb"] == 0.2


def test_cold_storage_cannot_be_removed_while_delivery_pending(demo):
    milk = next(
        p
        for p in demo.post("/api/planner", json={}).json()["proposals"]
        if p["storage"] == "chilled"
    )
    transfer = reserve(demo, milk)
    response = demo.patch(
        f"/api/sites/{transfer['destination_id']}", json={"storage_types": ["ambient"]}
    )
    assert response.status_code == 409


def test_csv_escapes_spreadsheet_formulas_in_untrusted_cells(demo):
    transfer = reserve(demo)
    dispatch(demo, transfer["id"])
    action(
        demo,
        transfer["id"],
        "receive",
        {"received_lb": 112, "receiver_name": '=HYPERLINK("bad")', "exception_reason": "@SUM(1,1)"},
    )
    response = demo.get("/api/reports/receipts.csv")
    row = next(csv.DictReader(io.StringIO(response.text.lstrip("\ufeff"))))
    assert row["receiver"].startswith("'=")
    assert row["exception_reason"].startswith("'@")
    assert response.headers["content-disposition"].endswith('"pantry-relay-receipts.csv"')


def test_expired_pickup_blocks_but_cancellation_reopens_resources(demo, app):
    transfer = reserve(demo)
    action(demo, transfer["id"], "accept", {"receiver_name": "Sam"})
    with transaction(app.state.settings.database, write=True) as conn:
        conn.execute(
            "UPDATE transfers SET expires_at=? WHERE id=?",
            (iso(now() - timedelta(seconds=1)), transfer["id"]),
        )
    action(demo, transfer["id"], "pickup", {"condition_confirmed": True}, expected=409)
    assert (
        by_id(demo.get("/api/workspace").json()["lots"], transfer["lot_id"])["quantity_lb"] == 300
    )
    action(demo, transfer["id"], "cancel", {"reason": "Use-by cutoff passed"})
    assert (
        by_id(demo.get("/api/workspace").json()["needs"], transfer["need_id"])["remaining_lb"]
        == 120
    )
