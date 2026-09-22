"""Inventory invariants and an explainable, deterministic allocation engine."""

import json
import math
from datetime import datetime
from decimal import Decimal

from fastapi import HTTPException

from backend.security import identifier, iso, now

ACTIVE = ("reserved", "accepted", "in_transit", "arrived")


def units(value: float) -> int:
    return int(Decimal(str(value)) * 100)


def pounds(value: int) -> float:
    return value / 100


def get_row(conn, table: str, entity_id: str, network_id: str):
    # Table names are exclusively internal constants, never user input.
    row = conn.execute(
        f"SELECT * FROM {table} WHERE id=? AND network_id=?", (entity_id, network_id)
    ).fetchone()
    if row is None:
        raise HTTPException(404, "Resource not found in your network")
    return dict(row)


def audit(conn, user, action: str, entity_type: str, entity_id: str, description: str, data=None):
    conn.execute(
        "INSERT INTO events VALUES (?,?,?,?,?,?,?,?,?,?)",
        (
            identifier(),
            user["network_id"],
            user["id"],
            user["name"],
            action,
            entity_type,
            entity_id,
            description,
            json.dumps(data or {}, separators=(",", ":")),
            iso(),
        ),
    )


def outbound_units(conn, lot_id: str) -> int:
    return conn.execute(
        "SELECT COALESCE(SUM(quantity_units),0) FROM transfers WHERE lot_id=? AND status IN ('reserved','accepted')",
        (lot_id,),
    ).fetchone()[0]


def incoming_units(conn, site_id: str) -> int:
    return conn.execute(
        "SELECT COALESCE(SUM(quantity_units),0) FROM transfers WHERE destination_id=? AND status IN ('reserved','accepted','in_transit','arrived')",
        (site_id,),
    ).fetchone()[0]


def stock_units(conn, site_id: str) -> int:
    return conn.execute(
        "SELECT COALESCE(SUM(quantity_units),0) FROM lots WHERE site_id=?", (site_id,)
    ).fetchone()[0]


def need_reserved_units(conn, need_id: str) -> int:
    return conn.execute(
        "SELECT COALESCE(SUM(quantity_units),0) FROM transfers WHERE need_id=? AND status IN ('reserved','accepted','in_transit','arrived')",
        (need_id,),
    ).fetchone()[0]


def available_units(conn, lot) -> int:
    if lot["restricted"] or lot["expires_at"] <= iso():
        return 0
    return max(0, lot["quantity_units"] - lot["reserve_units"] - outbound_units(conn, lot["id"]))


def remaining_units(conn, need) -> int:
    if need["closed"]:
        return 0
    return max(
        0, need["quantity_units"] - need["fulfilled_units"] - need_reserved_units(conn, need["id"])
    )


def serialize_site(row) -> dict:
    result = dict(row)
    result.pop("network_id", None)
    result["storage_types"] = json.loads(result["storage_types"])
    result["capacity_lb"] = pounds(result.pop("capacity_units"))
    return result


def serialize_lot(conn, row) -> dict:
    result = dict(row)
    result.pop("network_id", None)
    result["quantity_lb"] = pounds(result.pop("quantity_units"))
    result["reserve_lb"] = pounds(result.pop("reserve_units"))
    result["available_lb"] = pounds(available_units(conn, row))
    result["restricted"] = bool(result["restricted"])
    return result


def serialize_need(conn, row) -> dict:
    result = dict(row)
    result.pop("network_id", None)
    result["quantity_lb"] = pounds(result.pop("quantity_units"))
    result["fulfilled_lb"] = pounds(result.pop("fulfilled_units"))
    result["reserved_lb"] = pounds(need_reserved_units(conn, row["id"]))
    result["remaining_lb"] = pounds(remaining_units(conn, row))
    result["closed"] = bool(result["closed"])
    return result


def serialize_transfer(row, conn) -> dict:
    result = dict(row)
    result.pop("network_id", None)
    result["quantity_lb"] = pounds(result.pop("quantity_units"))
    result["received_lb"] = pounds(result.pop("received_units"))
    result["rejected_lb"] = (
        round(result["quantity_lb"] - result["received_lb"], 2)
        if result["status"] == "received"
        else 0
    )
    result["failed_lb"] = result["quantity_lb"] if result["status"] == "failed" else 0
    result["refrigerated"] = bool(result["refrigerated"])
    service_at = conn.execute(
        "SELECT service_at FROM needs WHERE id=?", (row["need_id"],)
    ).fetchone()[0]
    result["service_at"] = service_at
    result["on_time"] = row["updated_at"] <= service_at if row["status"] == "received" else None
    result["late"] = row["status"] == "received" and not result["on_time"]
    result["need_credited_lb"] = result["received_lb"] if result["on_time"] else 0
    return result


def serialize_event(row) -> dict:
    result = dict(row)
    result.pop("network_id", None)
    result["data"] = json.loads(result["data"])
    return result


def distance_miles(source, destination) -> float:
    lat1, lat2 = math.radians(source["lat"]), math.radians(destination["lat"])
    dlat = lat2 - lat1
    dlng = math.radians(destination["lng"] - source["lng"])
    a = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlng / 2) ** 2
    return 3958.7613 * 2 * math.asin(min(1, math.sqrt(a)))


def feasibility(
    conn, lot, need, source, destination, constraints, at: str
) -> tuple[int, float, str | None]:
    distance = distance_miles(source, destination)
    if need["closed"]:
        return 0, distance, "This need has been closed by its coordinator"
    if lot["restricted"]:
        return 0, distance, "Donor-restricted stock cannot be transferred"
    if lot["expires_at"] <= at:
        return 0, distance, "Use-by cutoff has passed"
    if need["service_at"] <= at:
        return 0, distance, "The receiving service deadline has passed"
    if lot["expires_at"] < need["service_at"]:
        return 0, distance, "Use-by cutoff is before the receiving service"
    if source["id"] == destination["id"]:
        return 0, distance, "Source and destination must be different pantries"
    if lot["category"] != need["category"]:
        return 0, distance, "Food category does not match the need"
    if lot["storage"] not in json.loads(destination["storage_types"]):
        return 0, distance, "Destination lacks the required storage"
    if lot["storage"] in {"chilled", "frozen"} and not constraints.refrigerated:
        return 0, distance, "Cold transport capability is required"
    if distance > constraints.max_distance_miles:
        return 0, distance, "Straight-line distance exceeds the configured limit"
    available = available_units(conn, lot)
    if available <= 0:
        return 0, distance, "All stock is protected or already reserved"
    remaining = remaining_units(conn, need)
    if remaining <= 0:
        return 0, distance, "Need is already fulfilled or reserved"
    space = (
        destination["capacity_units"]
        - stock_units(conn, destination["id"])
        - incoming_units(conn, destination["id"])
    )
    if space <= 0:
        return 0, distance, "Destination capacity is fully held by stock and incoming transfers"
    return min(available, remaining, space, units(constraints.vehicle_capacity_lb)), distance, None


def plan(conn, network_id: str, constraints) -> dict:
    """Earliest service, then earliest expiry, then distance; IDs break ties.

    Track provisional resources across the entire response. Proposals are advisory
    snapshots; creation rechecks every invariant under a write transaction.
    """
    at = iso()
    lots = [
        dict(r)
        for r in conn.execute(
            "SELECT * FROM lots WHERE network_id=? ORDER BY expires_at,id", (network_id,)
        )
    ]
    needs = [
        dict(r)
        for r in conn.execute(
            "SELECT * FROM needs WHERE network_id=? ORDER BY service_at,id", (network_id,)
        )
    ]
    sites = {
        r["id"]: dict(r)
        for r in conn.execute("SELECT * FROM sites WHERE network_id=?", (network_id,))
    }
    candidates, reasons = [], {}
    for lot in lots:
        for need in needs:
            amount, distance, reason = feasibility(
                conn, lot, need, sites[lot["site_id"]], sites[need["site_id"]], constraints, at
            )
            if reason:
                # Prefer substantive constraints over irrelevant category/site comparisons.
                if lot["id"] not in reasons or reason not in {
                    "Food category does not match the need",
                    "Source and destination must be different pantries",
                }:
                    reasons[lot["id"]] = reason
            elif amount:
                candidates.append(
                    (
                        need["service_at"],
                        lot["expires_at"],
                        distance,
                        lot["id"],
                        need["id"],
                        amount,
                        lot,
                        need,
                    )
                )
    used_lots, used_needs, used_capacity = {}, {}, {}
    proposals = []
    for _, _, distance, lot_id, need_id, maximum, lot, need in sorted(candidates):
        destination = sites[need["site_id"]]
        dest_id = destination["id"]
        available = available_units(conn, lot) - used_lots.get(lot_id, 0)
        unmet = remaining_units(conn, need) - used_needs.get(need_id, 0)
        capacity = (
            destination["capacity_units"]
            - stock_units(conn, dest_id)
            - incoming_units(conn, dest_id)
            - used_capacity.get(dest_id, 0)
        )
        amount = min(maximum, available, unmet, capacity)
        if amount <= 0:
            reasons[lot_id] = (
                "Earlier proposals use the remaining need, stock, or destination capacity"
            )
            continue
        used_lots[lot_id] = used_lots.get(lot_id, 0) + amount
        used_needs[need_id] = used_needs.get(need_id, 0) + amount
        used_capacity[dest_id] = used_capacity.get(dest_id, 0) + amount
        hours = max(
            0,
            (
                datetime.fromisoformat(need["service_at"].replace("Z", "+00:00")) - now()
            ).total_seconds()
            / 3600,
        )
        score = round(max(0, 100 - min(hours, 168) * 0.3 - distance * 0.2), 1)
        proposals.append(
            {
                "lot_id": lot_id,
                "need_id": need_id,
                "source_id": lot["site_id"],
                "destination_id": dest_id,
                "food_name": lot["food_name"],
                "category": lot["category"],
                "storage": lot["storage"],
                "quantity_lb": pounds(amount),
                "distance_miles": round(distance, 1),
                "score": score,
                "expires_at": lot["expires_at"],
                "service_at": need["service_at"],
                "reasons": [
                    "Ranked by earliest receiving service, then earliest use-by cutoff",
                    f"Protects {pounds(lot['reserve_units']):g} lb at the source pantry",
                    f"Fills {pounds(amount):g} lb of an unreserved {lot['category']} need",
                    f"{round(distance, 1):g} approximate straight-line miles; confirm the route before dispatch",
                    "Destination storage and capacity checked, including pending deliveries",
                    "Cold transport required at dispatch"
                    if lot["storage"] != "ambient"
                    else "Ambient transport is compatible",
                ],
            }
        )
    proposed = {p["lot_id"] for p in proposals}
    excluded = [
        {
            "lot_id": lot["id"],
            "reason": reasons.get(lot["id"], "No matching open need in the network"),
        }
        for lot in lots
        if lot["id"] not in proposed
    ]
    return {
        "proposals": proposals,
        "excluded": excluded,
        "generated_at": at,
        "assumptions": [
            "Demonstrates approved pantry-network rebalancing; local operator approval is required.",
            "Distances are straight-line estimates, not driving routes or travel-time guarantees.",
            "Vehicle capacity applies to each proposed transfer; this is not a combined multi-stop route.",
            "Rank: earliest service, earliest use-by cutoff, shortest straight-line distance, stable IDs.",
            "Use-by cutoffs must cover the receiving service. Operators confirm actual delivery timing.",
            "Temperature checks assist operators and do not certify food safety or replace local policy.",
        ],
    }


def check_temperature(storage: str, temperature: float | None):
    if storage == "ambient":
        return
    if temperature is None:
        raise HTTPException(
            422, "A measured food temperature is required for chilled or frozen stock"
        )
    if storage == "chilled" and not 32 <= temperature <= 41:
        raise HTTPException(
            409,
            "Chilled temperature must be 32–41°F. Hold the food and follow your organization's food-safety exception policy; this app cannot override the hold",
        )
    if storage == "frozen" and temperature > 0:
        raise HTTPException(
            409,
            "Frozen temperature must be 0°F or below. Hold the food and follow your organization's food-safety exception policy; this app cannot override the hold",
        )
