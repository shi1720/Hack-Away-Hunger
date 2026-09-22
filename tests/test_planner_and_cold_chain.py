from collections import defaultdict
from datetime import timedelta

import pytest
from conftest import action, create_lot, create_need, create_site, dispatch, register, reserve

from backend.db import transaction
from backend.security import iso, now


def test_demo_planner_explains_protected_stock_restricted_lots_and_storage(demo):
    result = demo.post("/api/planner", json={}).json()
    assert result["proposals"][0]["quantity_lb"] == 120
    assert result["proposals"][0]["food_name"] == "Harvest apples & carrots"
    assert any("180 lb" in text for text in result["proposals"][0]["reasons"])
    assert any("restricted" in item["reason"] for item in result["excluded"])
    assert any("storage" in item["reason"] for item in result["excluded"])
    assert "straight-line" in " ".join(result["assumptions"])
    without_cold = demo.post("/api/planner", json={"refrigerated": False}).json()
    assert all(proposal["storage"] == "ambient" for proposal in without_cold["proposals"])
    tiny_vehicle = demo.post("/api/planner", json={"vehicle_capacity_lb": 10}).json()
    assert all(proposal["quantity_lb"] <= 10 for proposal in tiny_vehicle["proposals"])
    assert demo.post("/api/planner", json={"max_distance_miles": 1}).json()["proposals"] == []


def test_planner_globally_prevents_double_allocation_and_prefers_fefo(client):
    register(client)
    source = create_site(client, "Source")
    target = create_site(client, "Target", capacity=100)
    earlier = create_lot(client, source["id"], quantity=70, reserve=10, hours=48, name="Earlier")
    later = create_lot(client, source["id"], quantity=70, hours=72, name="Later")
    first_need = create_need(client, target["id"], quantity=80, hours=24)
    second_need = create_need(client, target["id"], quantity=80, hours=36)
    first = client.post("/api/planner", json={}).json()["proposals"]
    second = client.post("/api/planner", json={}).json()["proposals"]
    assert first == second
    assert first[0]["lot_id"] == earlier["id"]
    assert first[0]["need_id"] == first_need["id"]
    assert first[0]["quantity_lb"] == 60
    used_lots, used_needs = defaultdict(float), defaultdict(float)
    for proposal in first:
        used_lots[proposal["lot_id"]] += proposal["quantity_lb"]
        used_needs[proposal["need_id"]] += proposal["quantity_lb"]
    assert sum(p["quantity_lb"] for p in first) == 100
    assert used_lots[earlier["id"]] <= 60
    assert used_lots[later["id"]] <= 70
    assert used_needs[first_need["id"]] == 80
    assert used_needs[second_need["id"]] == 20
    # Reserving proposals sequentially succeeds because the batch tracks shared capacity.
    for proposal in first:
        reserve(client, proposal)
    assert client.post("/api/planner", json={}).json()["proposals"] == []


def test_no_feasible_plan_for_expiry_before_service_and_restricted_stock(client, app):
    register(client)
    source = create_site(client, "Source")
    target = create_site(client, "Target")
    lot = create_lot(client, source["id"], hours=12)
    need = create_need(client, target["id"], hours=24)
    assert client.post("/api/planner", json={}).json()["proposals"] == []
    payload = {"lot_id": lot["id"], "need_id": need["id"], "quantity_lb": 1}
    assert client.post("/api/transfers", json=payload).status_code == 409
    with transaction(app.state.settings.database, write=True) as conn:
        conn.execute(
            "UPDATE lots SET expires_at=? WHERE id=?",
            (iso(now() - timedelta(seconds=1)), lot["id"]),
        )
    assert "passed" in client.post("/api/planner", json={}).json()["excluded"][0]["reason"]
    assert client.post("/api/transfers", json=payload).status_code == 409


def test_direct_api_reservation_enforces_cold_distance_vehicle_and_restriction(demo):
    workspace = demo.get("/api/workspace").json()
    plans = demo.post("/api/planner", json={}).json()["proposals"]
    milk = next(p for p in plans if p["storage"] == "chilled")
    payload = {key: milk[key] for key in ("lot_id", "need_id", "quantity_lb")}
    for override in (
        {"refrigerated": False},
        {"max_distance_miles": 1},
        {"vehicle_capacity_lb": 59},
    ):
        assert demo.post("/api/transfers", json={**payload, **override}).status_code == 409
    restricted = next(lot for lot in workspace["lots"] if lot["restricted"])
    assert (
        demo.post("/api/transfers", json={**payload, "lot_id": restricted["id"]}).status_code == 409
    )


@pytest.mark.parametrize(
    "storage,pickup_good,receipt_bad", [("chilled", 38, 50), ("frozen", -5, 5)]
)
def test_cold_chain_blocks_unsafe_positive_receipt_but_allows_audited_full_rejection(
    client, storage, pickup_good, receipt_bad
):
    register(client)
    source = create_site(client, "Source")
    destination = create_site(client, "Destination")
    lot = create_lot(client, source["id"], storage=storage)
    need = create_need(client, destination["id"])
    transfer = reserve(client, {"lot_id": lot["id"], "need_id": need["id"], "quantity_lb": 120})
    action(client, transfer["id"], "accept", {"receiver_name": "Sam"})
    action(client, transfer["id"], "pickup", {"condition_confirmed": True}, expected=422)
    action(
        client,
        transfer["id"],
        "pickup",
        {"condition_confirmed": True, "temperature_f": receipt_bad},
        expected=409,
    )
    action(
        client,
        transfer["id"],
        "pickup",
        {"condition_confirmed": True, "temperature_f": pickup_good},
    )
    action(client, transfer["id"], "arrive")
    action(
        client,
        transfer["id"],
        "receive",
        {"received_lb": 120, "temperature_f": receipt_bad, "receiver_name": "Sam"},
        expected=409,
    )
    action(
        client,
        transfer["id"],
        "receive",
        {"received_lb": 0, "temperature_f": receipt_bad, "receiver_name": "Sam"},
        expected=422,
    )
    receipt = action(
        client,
        transfer["id"],
        "receive",
        {
            "received_lb": 0,
            "temperature_f": receipt_bad,
            "receiver_name": "Sam",
            "exception_reason": "Food held and fully rejected under local temperature policy",
        },
    )
    assert receipt["rejected_lb"] == 120
    assert receipt["receipt_temperature_f"] == receipt_bad
    workspace = client.get("/api/workspace").json()
    assert not any(lot["origin_transfer_id"] for lot in workspace["lots"])
    assert workspace["needs"][0]["remaining_lb"] == 120
    assert workspace["needs"][0]["fulfilled_lb"] == 0
    assert workspace["metrics"]["active_transfers"] == 0
    # Destination capacity is released even though no stock was accepted.
    assert (
        client.patch(f"/api/sites/{destination['id']}", json={"capacity_lb": 1}).status_code == 200
    )


def test_expiry_during_transit_allows_arrival_and_full_rejection(demo, app):
    transfer = reserve(demo)
    action(demo, transfer["id"], "accept", {"receiver_name": "Sam"})
    action(demo, transfer["id"], "pickup", {"condition_confirmed": True})
    with transaction(app.state.settings.database, write=True) as conn:
        conn.execute(
            "UPDATE transfers SET expires_at=? WHERE id=?",
            (iso(now() - timedelta(seconds=1)), transfer["id"]),
        )
    action(demo, transfer["id"], "arrive")
    action(
        demo, transfer["id"], "receive", {"received_lb": 120, "receiver_name": "Sam"}, expected=409
    )
    receipt = action(
        demo,
        transfer["id"],
        "receive",
        {
            "received_lb": 0,
            "receiver_name": "Sam",
            "exception_reason": "Cutoff passed during delay; full rejection recorded",
        },
    )
    assert receipt["status"] == "received"
    assert receipt["rejected_lb"] == 120
    assert demo.get("/api/workspace").json()["metrics"]["received_lb"] == 0


@pytest.mark.parametrize("storage,temperature", [("chilled", 32), ("chilled", 41), ("frozen", 0)])
def test_cold_chain_inclusive_boundaries_are_accepted(client, storage, temperature):
    register(client)
    source = create_site(client, "Source")
    destination = create_site(client, "Destination")
    lot = create_lot(client, source["id"], storage=storage)
    need = create_need(client, destination["id"])
    transfer = reserve(client, {"lot_id": lot["id"], "need_id": need["id"], "quantity_lb": 120})
    dispatch(client, transfer["id"], temperature)
    receipt = action(
        client,
        transfer["id"],
        "receive",
        {"received_lb": 120, "temperature_f": temperature, "receiver_name": "Sam"},
    )
    assert receipt["received_lb"] == 120
