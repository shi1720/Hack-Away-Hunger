"""Pantry Relay HTTP API and static application host.

Run: uv run uvicorn backend.main:app --host 127.0.0.1 --port 8000
"""

import csv
import io
import json
import secrets
import sqlite3
from contextlib import asynccontextmanager
from datetime import timedelta
from pathlib import Path
from urllib.parse import urlparse

import psycopg
from fastapi import Depends, FastAPI, HTTPException, Request, Response
from fastapi.exceptions import RequestValidationError
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.trustedhost import TrustedHostMiddleware

from backend.config import Settings
from backend.db import initialize, transaction
from backend.domain import (
    ACTIVE,
    audit,
    check_temperature,
    feasibility,
    get_row,
    incoming_units,
    outbound_units,
    plan,
    pounds,
    serialize_event,
    serialize_lot,
    serialize_need,
    serialize_site,
    serialize_transfer,
    stock_units,
    units,
)
from backend.models import (
    AcceptInput,
    CancelInput,
    Credentials,
    Invite,
    Join,
    LotInput,
    LotUpdate,
    NeedInput,
    PickupInput,
    PlanInput,
    ReceiveInput,
    Registration,
    SiteInput,
    SiteUpdate,
    TransferInput,
)
from backend.security import (
    COOKIE,
    DUMMY_HASH,
    authenticated,
    digest,
    identifier,
    iso,
    issue_session,
    now,
    password_hash,
    password_matches,
    public_user,
    require_admin,
    require_operator,
    throttle,
)
from backend.seed import seed_demo


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or Settings.from_env()
    settings.validate()

    @asynccontextmanager
    async def lifespan(application: FastAPI):
        initialize(settings.database)
        yield

    application = FastAPI(
        title="Pantry Relay",
        version="1.0.0",
        lifespan=lifespan,
        docs_url="/api/docs",
        openapi_url="/api/openapi.json",
        redoc_url=None,
    )
    application.state.settings = settings
    application.add_middleware(TrustedHostMiddleware, allowed_hosts=list(settings.allowed_hosts))

    @application.middleware("http")
    async def security_headers(request: Request, call_next):
        if request.method not in {"GET", "HEAD", "OPTIONS"}:
            origin = request.headers.get("origin")
            if origin:
                try:
                    parsed = urlparse(origin)
                    exact_origin = origin in settings.trusted_origins
                    same_host = parsed.netloc == request.headers.get("host")
                    valid_scheme = parsed.scheme == (
                        "https" if settings.cookie_secure else request.url.scheme
                    )
                    allowed = exact_origin or (
                        same_host
                        and valid_scheme
                        and not parsed.path
                        and not parsed.query
                        and not parsed.fragment
                        and not parsed.username
                    )
                except ValueError:
                    allowed = False
                if not allowed:
                    return JSONResponse(
                        {"detail": "Cross-origin writes are not allowed"}, status_code=403
                    )
        length = request.headers.get("content-length")
        if length and (not length.isdigit() or int(length) > 65536):
            return JSONResponse({"detail": "Request body exceeds the 64 KB limit"}, status_code=413)
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "same-origin"
        response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
        # Inline styles are required by responsive React components; scripts remain self-only.
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; font-src 'self' https://fonts.gstatic.com; img-src 'self' data:; connect-src 'self'; frame-ancestors 'none'; base-uri 'self'; form-action 'self'"
        )
        if request.url.path == "/api/docs":
            # Swagger UI's pinned assets and initialization are scoped to this documentation route.
            response.headers["Content-Security-Policy"] = (
                "default-src 'self'; script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; img-src 'self' data: https://fastapi.tiangolo.com; frame-ancestors 'none'; base-uri 'self'; form-action 'self'"
            )
        if request.url.path.startswith("/api/"):
            response.headers["Cache-Control"] = "no-store"
        if settings.cookie_secure:
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        return response

    @application.exception_handler(RequestValidationError)
    async def validation_error(_request, exc):
        errors = []
        for error in exc.errors():
            field = ".".join(str(item) for item in error["loc"] if item != "body")
            errors.append(f"{field}: {error['msg']}" if field else error["msg"])
        return JSONResponse({"detail": "; ".join(errors)}, status_code=422)

    @application.exception_handler(psycopg.Error)
    @application.exception_handler(sqlite3.OperationalError)
    async def database_busy(_request, _exc):
        # Do not disclose SQL or filesystem paths. The journal preserves atomicity.
        return JSONResponse(
            {"detail": "Storage is temporarily unavailable. Please retry"},
            status_code=503,
            headers={"Retry-After": "2"},
        )

    @application.get("/api/health")
    def health():
        with transaction(settings.database) as conn:
            conn.execute("SELECT 1").fetchone()
        return {"status": "ok"}

    @application.get("/api/config")
    def public_config():
        return {
            "demo_enabled": settings.demo_enabled,
            "demo_only": settings.demo_only,
            "registration_enabled": not settings.demo_only,
        }

    def require_real_workspace_mode():
        if settings.demo_only:
            raise HTTPException(
                403,
                "This public showcase supports disposable demo workspaces only. Real accounts and invitations are disabled",
            )

    @application.post("/api/auth/register", status_code=201)
    def register(payload: Registration, request: Request, response: Response):
        require_real_workspace_mode()
        throttle(request, payload.email)
        hashed = password_hash(payload.password)
        with transaction(settings.database, write=True) as conn:
            if conn.execute("SELECT 1 FROM users WHERE email=?", (payload.email,)).fetchone():
                raise HTTPException(409, "This email already has an account. Sign in instead")
            network_id, user_id = identifier(), identifier()
            conn.execute(
                "INSERT INTO networks VALUES (?,?,0,?)", (network_id, payload.network_name, iso())
            )
            conn.execute(
                "INSERT INTO users VALUES (?,?,?,?,?,?,?)",
                (user_id, network_id, payload.name, payload.email, hashed, "admin", iso()),
            )
            user = dict(conn.execute("SELECT * FROM users WHERE id=?", (user_id,)).fetchone())
            audit(conn, user, "network.created", "network", network_id, "Created a pantry network")
            return issue_session(conn, request, response, user)

    @application.post("/api/auth/login")
    def login(payload: Credentials, request: Request, response: Response):
        require_real_workspace_mode()
        throttle(request, payload.email)
        with transaction(settings.database) as conn:
            user = conn.execute("SELECT * FROM users WHERE email=?", (payload.email,)).fetchone()
        valid = password_matches(payload.password, user["password_hash"] if user else DUMMY_HASH)
        if not user or not valid:
            raise HTTPException(401, "Email or password is incorrect")
        with transaction(settings.database, write=True) as conn:
            return issue_session(conn, request, response, user)

    @application.get("/api/auth/me")
    def me(user=Depends(authenticated)):
        return {"user": public_user(user), "csrf_token": user["csrf_token"]}

    @application.post("/api/auth/logout")
    def logout(request: Request, response: Response, user=Depends(authenticated)):
        with transaction(settings.database, write=True) as conn:
            conn.execute(
                "DELETE FROM sessions WHERE token_hash=?", (digest(request.cookies[COOKIE]),)
            )
        response.delete_cookie(
            COOKIE, path="/", secure=settings.cookie_secure, httponly=True, samesite="lax"
        )
        return {"ok": True}

    @application.post("/api/auth/demo", status_code=201)
    def demo(request: Request, response: Response):
        if not settings.demo_enabled:
            raise HTTPException(404, "Demo workspaces are disabled on this deployment")
        throttle(request)
        with transaction(settings.database, write=True) as conn:
            # Reclaim disposable workspaces after 24 hours, including their sessions.
            expired = [
                r[0]
                for r in conn.execute(
                    "SELECT id FROM networks WHERE is_demo=1 AND created_at<?",
                    (iso(now() - timedelta(hours=24)),),
                )
            ]
            for expired_id in expired:
                conn.execute(
                    "DELETE FROM sessions WHERE user_id IN (SELECT id FROM users WHERE network_id=?)",
                    (expired_id,),
                )
                for table in ("events", "invites", "transfers", "needs", "lots", "sites", "users"):
                    conn.execute(f"DELETE FROM {table} WHERE network_id=?", (expired_id,))
                conn.execute("DELETE FROM networks WHERE id=?", (expired_id,))
            network_id, user_id = identifier(), identifier()
            conn.execute(
                "INSERT INTO networks VALUES (?,?,1,?)",
                (network_id, "Central Iowa Demo Network", iso()),
            )
            conn.execute(
                "INSERT INTO users VALUES (?,?,?,?,?,?,?)",
                (
                    user_id,
                    network_id,
                    "Demo Coordinator",
                    f"demo-{user_id}@example.invalid",
                    password_hash(secrets.token_urlsafe(32)),
                    "admin",
                    iso(),
                ),
            )
            user = dict(conn.execute("SELECT * FROM users WHERE id=?", (user_id,)).fetchone())
            seed_demo(conn, user)
            return issue_session(conn, request, response, user)

    @application.post("/api/invites", status_code=201)
    def invite(payload: Invite, user=Depends(authenticated)):
        require_real_workspace_mode()
        require_admin(user)
        token, invite_id = secrets.token_urlsafe(32), identifier()
        expires = iso(now() + timedelta(days=7))
        with transaction(settings.database, write=True) as conn:
            network = conn.execute(
                "SELECT is_demo FROM networks WHERE id=?", (user["network_id"],)
            ).fetchone()
            if network["is_demo"]:
                raise HTTPException(
                    403,
                    "Disposable demo workspaces cannot invite members. Create a real network first",
                )
            conn.execute(
                "INSERT INTO invites VALUES (?,?,?,?,?,?,?)",
                (invite_id, user["network_id"], digest(token), payload.role, expires, None, iso()),
            )
            audit(
                conn,
                user,
                "invite.created",
                "invite",
                invite_id,
                f"Created a one-use {payload.role} invitation",
            )
        return {"token": token, "expires_at": expires, "role": payload.role}

    @application.post("/api/auth/join", status_code=201)
    def join(payload: Join, request: Request, response: Response):
        require_real_workspace_mode()
        throttle(request, payload.email)
        hashed = password_hash(payload.password)
        with transaction(settings.database, write=True) as conn:
            invite_row = conn.execute(
                "SELECT * FROM invites WHERE token_hash=? AND used_at IS NULL AND expires_at>?",
                (digest(payload.token), iso()),
            ).fetchone()
            if not invite_row:
                raise HTTPException(400, "This invitation is invalid, expired, or already used")
            network = conn.execute(
                "SELECT is_demo FROM networks WHERE id=?", (invite_row["network_id"],)
            ).fetchone()
            if network["is_demo"]:
                raise HTTPException(
                    403,
                    "Disposable demo workspaces cannot accept real members. Create a real network first",
                )
            if conn.execute("SELECT 1 FROM users WHERE email=?", (payload.email,)).fetchone():
                raise HTTPException(409, "This email already has an account")
            user_id = identifier()
            conn.execute(
                "INSERT INTO users VALUES (?,?,?,?,?,?,?)",
                (
                    user_id,
                    invite_row["network_id"],
                    payload.name,
                    payload.email,
                    hashed,
                    invite_row["role"],
                    iso(),
                ),
            )
            conn.execute("UPDATE invites SET used_at=? WHERE id=?", (iso(), invite_row["id"]))
            user = dict(conn.execute("SELECT * FROM users WHERE id=?", (user_id,)).fetchone())
            audit(
                conn,
                user,
                "member.joined",
                "user",
                user_id,
                f"Joined network as {invite_row['role']}",
            )
            return issue_session(conn, request, response, user)

    @application.get("/api/team")
    def team(user=Depends(authenticated)):
        require_operator(user)
        with transaction(settings.database) as conn:
            users = [
                public_user(r)
                for r in conn.execute(
                    "SELECT * FROM users WHERE network_id=? ORDER BY created_at,id",
                    (user["network_id"],),
                )
            ]
            invites = (
                [
                    dict(r)
                    for r in conn.execute(
                        "SELECT id,role,expires_at,used_at,created_at FROM invites WHERE network_id=? ORDER BY created_at DESC",
                        (user["network_id"],),
                    )
                ]
                if user["role"] == "admin"
                else []
            )
        return {"users": users, "invites": invites}

    @application.get("/api/workspace")
    def workspace(user=Depends(authenticated)):
        network_id = user["network_id"]
        with transaction(settings.database) as conn:
            network = dict(
                conn.execute(
                    "SELECT id,name,is_demo FROM networks WHERE id=?", (network_id,)
                ).fetchone()
            )
            network["is_demo"] = bool(network["is_demo"])
            sites = [
                serialize_site(r)
                for r in conn.execute(
                    "SELECT * FROM sites WHERE network_id=? ORDER BY created_at,id", (network_id,)
                )
            ]
            lots = [
                serialize_lot(conn, r)
                for r in conn.execute(
                    "SELECT * FROM lots WHERE network_id=? ORDER BY expires_at,id", (network_id,)
                )
            ]
            needs = [
                serialize_need(conn, r)
                for r in conn.execute(
                    "SELECT * FROM needs WHERE network_id=? ORDER BY service_at,id", (network_id,)
                )
            ]
            transfers = [
                serialize_transfer(r, conn)
                for r in conn.execute(
                    "SELECT * FROM transfers WHERE network_id=? ORDER BY created_at DESC,id",
                    (network_id,),
                )
            ]
            events = [
                serialize_event(r)
                for r in conn.execute(
                    "SELECT * FROM events WHERE network_id=? ORDER BY created_at DESC,id LIMIT 150",
                    (network_id,),
                )
            ]
            at, soon = iso(), iso(now() + timedelta(days=3))
            usable_lots = [lot for lot in lots if not lot["restricted"] and lot["expires_at"] > at]
            metrics = {
                "received_lb": round(
                    sum(t["received_lb"] for t in transfers if t["status"] == "received"), 2
                ),
                "active_transfers": sum(t["status"] in ACTIVE for t in transfers),
                "available_lb": round(sum(lot["available_lb"] for lot in usable_lots), 2),
                "at_risk_lb": round(
                    sum(lot["available_lb"] for lot in usable_lots if lot["expires_at"] <= soon), 2
                ),
                "unmet_need_lb": round(
                    sum(need["remaining_lb"] for need in needs if need["service_at"] > at), 2
                ),
            }
            if user["role"] == "driver":
                lots, needs = [], []
                events = [event for event in events if event["entity_type"] == "transfer"]
            return {
                "user": public_user(user),
                "network": network,
                "sites": sites,
                "lots": lots,
                "needs": needs,
                "transfers": transfers,
                "events": events,
                "metrics": metrics,
            }

    @application.post("/api/sites", status_code=201)
    def create_site(payload: SiteInput, user=Depends(authenticated)):
        require_operator(user)
        site_id = identifier()
        with transaction(settings.database, write=True) as conn:
            conn.execute(
                "INSERT INTO sites VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                (
                    site_id,
                    user["network_id"],
                    payload.name,
                    payload.city,
                    payload.address,
                    payload.lat,
                    payload.lng,
                    json.dumps(payload.storage_types),
                    units(payload.capacity_lb),
                    payload.notes,
                    iso(),
                ),
            )
            audit(conn, user, "site.created", "site", site_id, f"Added {payload.name}")
            return serialize_site(get_row(conn, "sites", site_id, user["network_id"]))

    @application.patch("/api/sites/{site_id}")
    def update_site(site_id: str, payload: SiteUpdate, user=Depends(authenticated)):
        require_operator(user)
        with transaction(settings.database, write=True) as conn:
            old = get_row(conn, "sites", site_id, user["network_id"])
            values = serialize_site(old)
            values.update(payload.model_dump(exclude_none=True))
            validated = SiteInput(**{key: values[key] for key in SiteInput.model_fields})
            occupied = stock_units(conn, site_id) + incoming_units(conn, site_id)
            if units(validated.capacity_lb) < occupied:
                raise HTTPException(
                    409, "Capacity cannot be below physical stock plus held incoming transfers"
                )
            used_storage = {
                r[0]
                for r in conn.execute(
                    "SELECT storage FROM lots WHERE site_id=? AND quantity_units>0 UNION SELECT storage FROM transfers WHERE destination_id=? AND status IN ('reserved','accepted','in_transit','arrived')",
                    (site_id, site_id),
                )
            }
            if not used_storage.issubset(set(validated.storage_types)):
                raise HTTPException(
                    409, "Storage required by current stock or incoming transfers cannot be removed"
                )
            conn.execute(
                "UPDATE sites SET name=?,city=?,address=?,lat=?,lng=?,storage_types=?,capacity_units=?,notes=? WHERE id=?",
                (
                    validated.name,
                    validated.city,
                    validated.address,
                    validated.lat,
                    validated.lng,
                    json.dumps(validated.storage_types),
                    units(validated.capacity_lb),
                    validated.notes,
                    site_id,
                ),
            )
            audit(
                conn,
                user,
                "site.updated",
                "site",
                site_id,
                f"Updated {validated.name}",
                {"fields": list(payload.model_fields_set)},
            )
            return serialize_site(get_row(conn, "sites", site_id, user["network_id"]))

    @application.post("/api/lots", status_code=201)
    def create_lot(payload: LotInput, user=Depends(authenticated)):
        require_operator(user)
        lot_id = identifier()
        with transaction(settings.database, write=True) as conn:
            site = get_row(conn, "sites", payload.site_id, user["network_id"])
            if payload.reserve_lb > payload.quantity_lb:
                raise HTTPException(422, "Protected reserve cannot exceed physical stock")
            if iso(payload.expires_at) <= iso():
                raise HTTPException(422, "Enter a future use-by cutoff")
            if payload.storage not in json.loads(site["storage_types"]):
                raise HTTPException(409, "This pantry does not support the required storage")
            if (
                stock_units(conn, site["id"])
                + incoming_units(conn, site["id"])
                + units(payload.quantity_lb)
                > site["capacity_units"]
            ):
                raise HTTPException(
                    409, "This lot exceeds pantry capacity, including incoming transfers"
                )
            conn.execute(
                "INSERT INTO lots VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                (
                    lot_id,
                    user["network_id"],
                    payload.site_id,
                    payload.food_name,
                    payload.category,
                    payload.storage,
                    units(payload.quantity_lb),
                    units(payload.reserve_lb),
                    iso(payload.expires_at),
                    int(payload.restricted),
                    payload.notes,
                    1,
                    None,
                    iso(),
                ),
            )
            audit(
                conn,
                user,
                "lot.created",
                "lot",
                lot_id,
                f"Added {payload.quantity_lb:g} lb of {payload.food_name}",
                {"quantity_lb": payload.quantity_lb, "reserve_lb": payload.reserve_lb},
            )
            return serialize_lot(conn, get_row(conn, "lots", lot_id, user["network_id"]))

    @application.patch("/api/lots/{lot_id}")
    def update_lot(lot_id: str, payload: LotUpdate, user=Depends(authenticated)):
        require_operator(user)
        with transaction(settings.database, write=True) as conn:
            lot = get_row(conn, "lots", lot_id, user["network_id"])
            if lot["version"] != payload.version:
                raise HTTPException(
                    409, "Stock changed since you opened this form. Refresh before adjusting"
                )
            changes = payload.model_dump(exclude_none=True, exclude={"version"})
            values = serialize_lot(conn, lot)
            values.update(changes)
            if values["site_id"] != lot["site_id"]:
                raise HTTPException(409, "Use a transfer to move stock between pantries")
            if "expires_at" in changes:
                values["expires_at"] = iso(changes["expires_at"])
            active = conn.execute(
                "SELECT 1 FROM transfers WHERE lot_id=? AND status IN ('reserved','accepted','in_transit','arrived') LIMIT 1",
                (lot_id,),
            ).fetchone()
            if active and any(
                values[key] != lot[key]
                for key in ("food_name", "category", "storage", "expires_at", "restricted")
            ):
                raise HTTPException(
                    409,
                    "Lot identity, restriction, storage, and cutoff cannot change during an active transfer",
                )
            quantity, reserve = units(values["quantity_lb"]), units(values["reserve_lb"])
            if quantity < reserve + outbound_units(conn, lot_id):
                raise HTTPException(
                    409, "Stock must cover the protected reserve plus all outgoing reservations"
                )
            site = get_row(conn, "sites", lot["site_id"], user["network_id"])
            if values["storage"] not in json.loads(site["storage_types"]):
                raise HTTPException(409, "This pantry does not support the required storage")
            if (
                stock_units(conn, site["id"])
                - lot["quantity_units"]
                + quantity
                + incoming_units(conn, site["id"])
                > site["capacity_units"]
            ):
                raise HTTPException(
                    409, "Stock adjustment exceeds pantry capacity including incoming transfers"
                )
            conn.execute(
                "UPDATE lots SET food_name=?,category=?,storage=?,quantity_units=?,reserve_units=?,expires_at=?,restricted=?,notes=?,version=version+1 WHERE id=?",
                (
                    values["food_name"],
                    values["category"],
                    values["storage"],
                    quantity,
                    reserve,
                    values["expires_at"],
                    int(values["restricted"]),
                    values["notes"],
                    lot_id,
                ),
            )
            audit(
                conn,
                user,
                "lot.adjusted",
                "lot",
                lot_id,
                f"Adjusted {values['food_name']} to {values['quantity_lb']:g} lb",
                {
                    "before_quantity_lb": pounds(lot["quantity_units"]),
                    "after_quantity_lb": values["quantity_lb"],
                    "before_reserve_lb": pounds(lot["reserve_units"]),
                    "after_reserve_lb": values["reserve_lb"],
                    "fields": list(changes),
                },
            )
            return serialize_lot(conn, get_row(conn, "lots", lot_id, user["network_id"]))

    @application.post("/api/needs", status_code=201)
    def create_need(payload: NeedInput, user=Depends(authenticated)):
        require_operator(user)
        need_id = identifier()
        with transaction(settings.database, write=True) as conn:
            get_row(conn, "sites", payload.site_id, user["network_id"])
            if iso(payload.service_at) <= iso():
                raise HTTPException(422, "Enter a future service time")
            conn.execute(
                "INSERT INTO needs (id,network_id,site_id,category,quantity_units,fulfilled_units,service_at,notes,created_at) VALUES (?,?,?,?,?,?,?,?,?)",
                (
                    need_id,
                    user["network_id"],
                    payload.site_id,
                    payload.category,
                    units(payload.quantity_lb),
                    0,
                    iso(payload.service_at),
                    payload.notes,
                    iso(),
                ),
            )
            audit(
                conn,
                user,
                "need.created",
                "need",
                need_id,
                f"Requested {payload.quantity_lb:g} lb of {payload.category}",
            )
            return serialize_need(conn, get_row(conn, "needs", need_id, user["network_id"]))

    @application.post("/api/needs/{need_id}/close")
    def close_need(need_id: str, payload: CancelInput, user=Depends(authenticated)):
        require_operator(user)
        with transaction(settings.database, write=True) as conn:
            need = get_row(conn, "needs", need_id, user["network_id"])
            if need["closed"]:
                raise HTTPException(409, "This need is already closed")
            if conn.execute(
                "SELECT 1 FROM transfers WHERE need_id=? AND status IN ('reserved','accepted','in_transit','arrived') LIMIT 1",
                (need_id,),
            ).fetchone():
                raise HTTPException(409, "Resolve all active transfers before closing this need")
            conn.execute("UPDATE needs SET closed=1 WHERE id=?", (need_id,))
            audit(
                conn,
                user,
                "need.closed",
                "need",
                need_id,
                f"Closed {need['category']} request: {payload.reason}",
                {
                    "reason": payload.reason,
                    "fulfilled_lb": pounds(need["fulfilled_units"]),
                    "unfilled_lb_at_close": pounds(
                        need["quantity_units"] - need["fulfilled_units"]
                    ),
                },
            )
            return serialize_need(conn, get_row(conn, "needs", need_id, user["network_id"]))

    @application.post("/api/planner")
    def planner(payload: PlanInput, user=Depends(authenticated)):
        require_operator(user)
        with transaction(settings.database) as conn:
            return plan(conn, user["network_id"], payload)

    @application.post("/api/transfers", status_code=201)
    def create_transfer(payload: TransferInput, user=Depends(authenticated)):
        require_operator(user)
        with transaction(settings.database, write=True) as conn:
            lot = get_row(conn, "lots", payload.lot_id, user["network_id"])
            need = get_row(conn, "needs", payload.need_id, user["network_id"])
            source = get_row(conn, "sites", lot["site_id"], user["network_id"])
            destination = get_row(conn, "sites", need["site_id"], user["network_id"])
            amount, distance, reason = feasibility(
                conn, lot, need, source, destination, payload, iso()
            )
            if reason:
                raise HTTPException(409, reason)
            if units(payload.quantity_lb) > amount:
                raise HTTPException(
                    409,
                    f"Only {pounds(amount):g} lb fits the current stock, need, destination capacity, and vehicle constraints. Refresh the planner",
                )
            transfer_id, timestamp = identifier(), iso()
            conn.execute(
                "INSERT INTO transfers VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                (
                    transfer_id,
                    user["network_id"],
                    lot["id"],
                    need["id"],
                    source["id"],
                    destination["id"],
                    lot["food_name"],
                    lot["category"],
                    lot["storage"],
                    units(payload.quantity_lb),
                    0,
                    "reserved",
                    round(distance, 1),
                    "",
                    "",
                    timestamp,
                    timestamp,
                    lot["expires_at"],
                    None,
                    None,
                    int(payload.refrigerated),
                ),
            )
            conn.execute("UPDATE lots SET version=version+1 WHERE id=?", (lot["id"],))
            audit(
                conn,
                user,
                "transfer.reserved",
                "transfer",
                transfer_id,
                f"Reserved {payload.quantity_lb:g} lb of {lot['food_name']} from {source['name']} to {destination['name']}",
                {
                    "quantity_lb": payload.quantity_lb,
                    "source_id": source["id"],
                    "destination_id": destination["id"],
                },
            )
            return serialize_transfer(
                get_row(conn, "transfers", transfer_id, user["network_id"]), conn
            )

    def transfer_for_action(conn, transfer_id, user, allowed):
        transfer = get_row(conn, "transfers", transfer_id, user["network_id"])
        if transfer["status"] not in allowed:
            raise HTTPException(
                409,
                f"Cannot perform this action while transfer is {transfer['status']}. Refresh to see its current state",
            )
        return transfer

    @application.post("/api/transfers/{transfer_id}/accept")
    def accept(transfer_id: str, payload: AcceptInput, user=Depends(authenticated)):
        require_operator(user)
        with transaction(settings.database, write=True) as conn:
            transfer_for_action(conn, transfer_id, user, {"reserved"})
            conn.execute(
                "UPDATE transfers SET status='accepted',receiver_name=?,updated_at=? WHERE id=?",
                (payload.receiver_name, iso(), transfer_id),
            )
            audit(
                conn,
                user,
                "transfer.accepted",
                "transfer",
                transfer_id,
                f"Receiving approval recorded by {payload.receiver_name}",
            )
            return serialize_transfer(
                get_row(conn, "transfers", transfer_id, user["network_id"]), conn
            )

    @application.post("/api/transfers/{transfer_id}/pickup")
    def pickup(transfer_id: str, payload: PickupInput, user=Depends(authenticated)):
        with transaction(settings.database, write=True) as conn:
            transfer = transfer_for_action(conn, transfer_id, user, {"accepted"})
            if transfer["expires_at"] <= iso():
                raise HTTPException(
                    409,
                    "The use-by cutoff has passed. Cancel this transfer and follow local food-safety policy",
                )
            need = get_row(conn, "needs", transfer["need_id"], user["network_id"])
            if need["service_at"] <= iso():
                raise HTTPException(
                    409, "The receiving service deadline has passed. Cancel and reassess the need"
                )
            check_temperature(transfer["storage"], payload.temperature_f)
            lot = get_row(conn, "lots", transfer["lot_id"], user["network_id"])
            if (
                lot["quantity_units"] - transfer["quantity_units"]
                < lot["reserve_units"]
                + outbound_units(conn, lot["id"])
                - transfer["quantity_units"]
            ):
                raise HTTPException(
                    409, "Source stock cannot cover protected reserves and remaining reservations"
                )
            conn.execute(
                "UPDATE lots SET quantity_units=quantity_units-?,version=version+1 WHERE id=?",
                (transfer["quantity_units"], lot["id"]),
            )
            conn.execute(
                "UPDATE transfers SET status='in_transit',pickup_temperature_f=?,updated_at=? WHERE id=?",
                (payload.temperature_f, iso(), transfer_id),
            )
            audit(
                conn,
                user,
                "transfer.picked_up",
                "transfer",
                transfer_id,
                f"Picked up {pounds(transfer['quantity_units']):g} lb; source physical stock decreased",
                {
                    "quantity_lb": pounds(transfer["quantity_units"]),
                    "temperature_f": payload.temperature_f,
                    "condition_confirmed": True,
                },
            )
            return serialize_transfer(
                get_row(conn, "transfers", transfer_id, user["network_id"]), conn
            )

    @application.post("/api/transfers/{transfer_id}/arrive")
    def arrive(transfer_id: str, user=Depends(authenticated)):
        with transaction(settings.database, write=True) as conn:
            transfer_for_action(conn, transfer_id, user, {"in_transit"})
            conn.execute(
                "UPDATE transfers SET status='arrived',updated_at=? WHERE id=?",
                (iso(), transfer_id),
            )
            audit(
                conn,
                user,
                "transfer.arrived",
                "transfer",
                transfer_id,
                "Driver reported arrival; receiving verification remains required",
            )
            return serialize_transfer(
                get_row(conn, "transfers", transfer_id, user["network_id"]), conn
            )

    @application.post("/api/transfers/{transfer_id}/receive")
    def receive(transfer_id: str, payload: ReceiveInput, user=Depends(authenticated)):
        require_operator(user)
        with transaction(settings.database, write=True) as conn:
            transfer = transfer_for_action(conn, transfer_id, user, {"arrived"})
            received = units(payload.received_lb)
            # A complete rejection is an accounting action, not acceptance of unsafe food.
            # It releases held space and demand while recording all dispatched weight as rejected.
            if received:
                if transfer["expires_at"] <= iso():
                    raise HTTPException(
                        409,
                        "The use-by cutoff has passed. Hold the food and follow local policy; record a full rejection with zero accepted weight",
                    )
                check_temperature(transfer["storage"], payload.temperature_f)
            if received > transfer["quantity_units"]:
                raise HTTPException(422, "Received weight cannot exceed dispatched weight")
            rejected = transfer["quantity_units"] - received
            if rejected and len(payload.exception_reason.strip()) < 3:
                raise HTTPException(
                    422, "Explain the rejected or missing weight before completing receipt"
                )
            destination = get_row(conn, "sites", transfer["destination_id"], user["network_id"])
            if (
                stock_units(conn, destination["id"])
                + incoming_units(conn, destination["id"])
                - transfer["quantity_units"]
                + received
                > destination["capacity_units"]
            ):
                raise HTTPException(409, "Receiving this stock would exceed destination capacity")
            need = get_row(conn, "needs", transfer["need_id"], user["network_id"])
            timestamp = iso()
            on_time = timestamp <= need["service_at"]
            if received:
                lot_id = identifier()
                conn.execute(
                    "INSERT INTO lots VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                    (
                        lot_id,
                        user["network_id"],
                        destination["id"],
                        transfer["food_name"],
                        transfer["category"],
                        transfer["storage"],
                        received,
                        received,
                        transfer["expires_at"],
                        0,
                        f"Received through relay {transfer_id}. Original lot: {transfer['lot_id']}. Protected for destination service; coordinator may intentionally release stock later.",
                        1,
                        transfer_id,
                        timestamp,
                    ),
                )
            credited = received if on_time else 0
            conn.execute(
                "UPDATE needs SET fulfilled_units=fulfilled_units+? WHERE id=?",
                (credited, transfer["need_id"]),
            )
            conn.execute(
                "UPDATE transfers SET status='received',received_units=?,receipt_temperature_f=?,receiver_name=?,exception_reason=?,updated_at=? WHERE id=?",
                (
                    received,
                    payload.temperature_f,
                    payload.receiver_name,
                    payload.exception_reason,
                    timestamp,
                    transfer_id,
                ),
            )
            timing_note = (
                ""
                if on_time
                else "; receipt confirmed after service deadline, so no service-gap fulfillment credited"
            )
            audit(
                conn,
                user,
                "transfer.received",
                "transfer",
                transfer_id,
                f"{payload.receiver_name} confirmed {payload.received_lb:g} lb received; {pounds(rejected):g} lb rejected or missing{timing_note}",
                {
                    "received_lb": payload.received_lb,
                    "rejected_lb": pounds(rejected),
                    "temperature_f": payload.temperature_f,
                    "exception_reason": payload.exception_reason,
                    "on_time": on_time,
                    "need_credited_lb": pounds(credited),
                },
            )
            return serialize_transfer(
                get_row(conn, "transfers", transfer_id, user["network_id"]), conn
            )

    @application.post("/api/transfers/{transfer_id}/fail")
    def fail_transfer(transfer_id: str, payload: CancelInput, user=Depends(authenticated)):
        require_operator(user)
        with transaction(settings.database, write=True) as conn:
            transfer = transfer_for_action(conn, transfer_id, user, {"in_transit", "arrived"})
            conn.execute(
                "UPDATE transfers SET status='failed',exception_reason=?,updated_at=? WHERE id=?",
                (payload.reason, iso(), transfer_id),
            )
            audit(
                conn,
                user,
                "transfer.failed",
                "transfer",
                transfer_id,
                f"Delivery failed after dispatch; {pounds(transfer['quantity_units']):g} lb not received. {payload.reason}",
                {
                    "failed_lb": pounds(transfer["quantity_units"]),
                    "received_lb": 0,
                    "reason": payload.reason,
                    "previous_status": transfer["status"],
                    "source_stock_restored": False,
                },
            )
            return serialize_transfer(
                get_row(conn, "transfers", transfer_id, user["network_id"]), conn
            )

    @application.post("/api/transfers/{transfer_id}/cancel")
    def cancel(transfer_id: str, payload: CancelInput, user=Depends(authenticated)):
        require_operator(user)
        with transaction(settings.database, write=True) as conn:
            transfer = transfer_for_action(conn, transfer_id, user, {"reserved", "accepted"})
            conn.execute(
                "UPDATE transfers SET status='cancelled',exception_reason=?,updated_at=? WHERE id=?",
                (payload.reason, iso(), transfer_id),
            )
            conn.execute("UPDATE lots SET version=version+1 WHERE id=?", (transfer["lot_id"],))
            audit(
                conn,
                user,
                "transfer.cancelled",
                "transfer",
                transfer_id,
                f"Cancelled before dispatch: {payload.reason}",
            )
            return serialize_transfer(
                get_row(conn, "transfers", transfer_id, user["network_id"]), conn
            )

    def csv_response(filename: str, headers: list[str], rows: list[list]):
        def cell(value):
            if value is None:
                return ""
            if not isinstance(value, str):
                return value
            # Excel/Sheets formula injection can hide after whitespace/control characters.
            stripped = value.lstrip(" \t\r\n\x00")
            return (
                "'" + value
                if stripped.startswith(("=", "+", "-", "@")) or value.startswith(("\t", "\r", "\n"))
                else value
            )

        output = io.StringIO(newline="")
        writer = csv.writer(output)
        writer.writerow(headers)
        writer.writerows([[cell(value) for value in row] for row in rows])
        return Response(
            "\ufeff" + output.getvalue(),
            media_type="text/csv; charset=utf-8",
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"',
                "Cache-Control": "no-store",
            },
        )

    @application.get("/api/reports/receipts.csv")
    def receipts_csv(user=Depends(authenticated)):
        require_operator(user)
        with transaction(settings.database) as conn:
            rows = conn.execute(
                "SELECT t.*,s.name AS source_name,d.name AS destination_name,n.service_at FROM transfers t JOIN sites s ON s.id=t.source_id JOIN sites d ON d.id=t.destination_id JOIN needs n ON n.id=t.need_id WHERE t.network_id=? AND t.status='received' ORDER BY t.updated_at DESC",
                (user["network_id"],),
            ).fetchall()
            return csv_response(
                "pantry-relay-receipts.csv",
                [
                    "transfer_id",
                    "source",
                    "destination",
                    "food",
                    "category",
                    "storage",
                    "dispatched_lb",
                    "received_lb",
                    "rejected_lb",
                    "receiver",
                    "exception_reason",
                    "received_at",
                    "pickup_temperature_f",
                    "receipt_temperature_f",
                    "on_time",
                    "need_credited_lb",
                ],
                [
                    [
                        r["id"],
                        r["source_name"],
                        r["destination_name"],
                        r["food_name"],
                        r["category"],
                        r["storage"],
                        pounds(r["quantity_units"]),
                        pounds(r["received_units"]),
                        pounds(r["quantity_units"] - r["received_units"]),
                        r["receiver_name"],
                        r["exception_reason"],
                        r["updated_at"],
                        r["pickup_temperature_f"],
                        r["receipt_temperature_f"],
                        r["updated_at"] <= r["service_at"],
                        pounds(r["received_units"]) if r["updated_at"] <= r["service_at"] else 0,
                    ]
                    for r in rows
                ],
            )

    @application.get("/api/reports/audit.csv")
    def audit_csv(user=Depends(authenticated)):
        require_operator(user)
        with transaction(settings.database) as conn:
            rows = conn.execute(
                "SELECT * FROM events WHERE network_id=? ORDER BY created_at DESC,id",
                (user["network_id"],),
            ).fetchall()
            fields = [
                "created_at",
                "actor_name",
                "action",
                "entity_type",
                "entity_id",
                "description",
                "data",
            ]
            return csv_response(
                "pantry-relay-audit.csv", fields, [[r[field] for field in fields] for r in rows]
            )

    frontend = Path(settings.frontend)
    if (frontend / "assets").is_dir():
        application.mount("/assets", StaticFiles(directory=frontend / "assets"), name="assets")

    @application.get("/{path:path}", include_in_schema=False)
    def frontend_or_404(path: str):
        if path == "api" or path.startswith("api/"):
            raise HTTPException(404, "API endpoint not found")
        target = (frontend / path).resolve()
        if target.is_relative_to(frontend.resolve()) and target.is_file():
            return FileResponse(target)
        index = frontend / "index.html"
        if index.is_file():
            return FileResponse(index)
        return JSONResponse(
            {
                "detail": "Frontend not built. Run npm ci && npm run build in frontend, or use the Vite dev server. API documentation: /api/docs"
            },
            status_code=503,
        )

    return application


app = create_app()
