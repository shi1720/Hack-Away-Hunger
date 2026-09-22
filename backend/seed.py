"""Clearly fictitious, private demo workspaces. No real pantry data or relationships."""

import json
from datetime import timedelta

from backend.domain import audit, units
from backend.security import identifier, iso, now


def seed_demo(conn, user):
    network_id = user["network_id"]
    locations = [
        (
            "Cedar Grove Pantry",
            "Johnston",
            "Demo location · Johnston, IA",
            41.673,
            -93.697,
            ["ambient", "chilled", "frozen"],
            1600,
            "Fictitious demo pantry. Protects stock for its own visitors before sharing surplus.",
        ),
        (
            "Eastside Community Pantry",
            "Des Moines",
            "Demo location · East Des Moines, IA",
            41.601,
            -93.563,
            ["ambient", "chilled"],
            700,
            "Fictitious demo pantry. Next service tomorrow; produce and dairy requested.",
        ),
        (
            "Prairie Bridge Pantry",
            "Ankeny",
            "Demo location · Ankeny, IA",
            41.731,
            -93.601,
            ["ambient", "chilled", "frozen"],
            1000,
            "Fictitious demo pantry. Cold storage available; accepts scheduled deliveries.",
        ),
        (
            "Riverview Food Shelf",
            "West Des Moines",
            "Demo location · West Des Moines, IA",
            41.576,
            -93.746,
            ["ambient"],
            450,
            "Fictitious demo pantry. Ambient storage only; cannot receive chilled or frozen food.",
        ),
    ]
    site_ids = []
    for name, city, address, lat, lng, storage, capacity, notes in locations:
        site_id = identifier()
        site_ids.append(site_id)
        conn.execute(
            "INSERT INTO sites VALUES (?,?,?,?,?,?,?,?,?,?,?)",
            (
                site_id,
                network_id,
                name,
                city,
                address,
                lat,
                lng,
                json.dumps(storage),
                units(capacity),
                notes,
                iso(),
            ),
        )
    lot_specs = [
        (
            0,
            "Harvest apples & carrots",
            "produce",
            "ambient",
            300,
            180,
            3,
            False,
            "180 lb protected for Cedar Grove visitors. Surplus available before next service.",
        ),
        (
            0,
            "Donor-designated turkey",
            "protein",
            "frozen",
            80,
            0,
            30,
            True,
            "Restricted to the donor-designated program. Not eligible for sharing.",
        ),
        (
            2,
            "Fresh milk",
            "dairy",
            "chilled",
            90,
            30,
            4,
            False,
            "Requires measured cold-chain temperatures at pickup and receipt.",
        ),
        (
            0,
            "Whole-grain pasta",
            "grains",
            "ambient",
            180,
            100,
            90,
            False,
            "Sealed dry goods. Protected minimum supports this week's local distribution.",
        ),
        (
            2,
            "Frozen garden vegetables",
            "produce",
            "frozen",
            100,
            40,
            20,
            False,
            "No compatible frozen destination need in this scenario.",
        ),
        (
            1,
            "Canned beans",
            "pantry",
            "ambient",
            140,
            140,
            180,
            False,
            "Fully protected for Eastside's service.",
        ),
    ]
    for idx, name, category, storage, quantity, reserve, days, restricted, notes in lot_specs:
        conn.execute(
            "INSERT INTO lots VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (
                identifier(),
                network_id,
                site_ids[idx],
                name,
                category,
                storage,
                units(quantity),
                units(reserve),
                iso(now() + timedelta(days=days)),
                int(restricted),
                notes,
                1,
                None,
                iso(),
            ),
        )
    for idx, category, quantity, hours, notes in [
        (
            1,
            "produce",
            120,
            24,
            "Produce for tomorrow's distribution. Confirm receipt before service.",
        ),
        (1, "dairy", 60, 36, "Milk requested; chilled storage available."),
        (3, "grains", 80, 48, "Shelf-stable grains for the next service."),
        (3, "produce", 60, 72, "Ambient produce only. No freezer or refrigerator at this site."),
    ]:
        conn.execute(
            "INSERT INTO needs (id,network_id,site_id,category,quantity_units,fulfilled_units,service_at,notes,created_at) VALUES (?,?,?,?,?,?,?,?,?)",
            (
                identifier(),
                network_id,
                site_ids[idx],
                category,
                units(quantity),
                0,
                iso(now() + timedelta(hours=hours)),
                notes,
                iso(),
            ),
        )
    audit(
        conn,
        user,
        "demo.created",
        "network",
        network_id,
        "Created an isolated demonstration workspace with fictitious pantry data",
    )
