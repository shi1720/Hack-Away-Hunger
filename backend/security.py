"""Password hashing, opaque sessions, CSRF, and persistent authentication throttling."""

import hashlib
import hmac
import secrets
import time
from datetime import UTC, datetime, timedelta

from fastapi import HTTPException, Request, Response

from backend.db import transaction

COOKIE = "__session"  # Firebase Hosting forwards only this cookie to Cloud Run.


def now() -> datetime:
    return datetime.now(UTC)


def iso(value: datetime | None = None) -> str:
    return (
        (value or now()).astimezone(UTC).isoformat(timespec="microseconds").replace("+00:00", "Z")
    )


def identifier() -> str:
    return secrets.token_hex(16)


def digest(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()


def password_hash(password: str) -> str:
    salt = secrets.token_bytes(16)
    hashed = hashlib.scrypt(password.encode(), salt=salt, n=16384, r=8, p=1, dklen=32)
    return f"scrypt$16384$8$1${salt.hex()}${hashed.hex()}"


def password_matches(password: str, encoded: str) -> bool:
    try:
        _, n, r, p, salt, expected = encoded.split("$")
        actual = hashlib.scrypt(
            password.encode(), salt=bytes.fromhex(salt), n=int(n), r=int(r), p=int(p), dklen=32
        )
        return hmac.compare_digest(actual.hex(), expected)
    except (ValueError, TypeError):
        return False


# An equal-cost verification path avoids disclosing whether an account exists by timing.
DUMMY_HASH = password_hash(secrets.token_urlsafe(32))


def public_user(row) -> dict:
    return {key: row[key] for key in ("id", "name", "email", "role", "network_id")}


def issue_session(conn, request: Request, response: Response, user) -> dict:
    token, csrf = secrets.token_urlsafe(32), secrets.token_urlsafe(32)
    settings = request.app.state.settings
    old = request.cookies.get(COOKIE)
    if old:
        conn.execute("DELETE FROM sessions WHERE token_hash=?", (digest(old),))
    conn.execute("DELETE FROM sessions WHERE expires_at<=?", (iso(),))
    conn.execute(
        "INSERT INTO sessions VALUES (?,?,?,?,?)",
        (
            digest(token),
            user["id"],
            csrf,
            iso(now() + timedelta(hours=settings.session_hours)),
            iso(),
        ),
    )
    response.set_cookie(
        COOKIE,
        token,
        max_age=settings.session_hours * 3600,
        httponly=True,
        secure=settings.cookie_secure,
        samesite="lax",
        path="/",
    )
    response.headers["Cache-Control"] = "no-store"
    return {"user": public_user(user), "csrf_token": csrf}


def authenticated(request: Request) -> dict:
    token = request.cookies.get(COOKIE)
    if not token or len(token) > 200:
        raise HTTPException(401, "Sign in to continue")
    with transaction(request.app.state.settings.database) as conn:
        row = conn.execute(
            "SELECT u.*,s.csrf_token FROM sessions s JOIN users u ON u.id=s.user_id "
            "WHERE s.token_hash=? AND s.expires_at>?",
            (digest(token), iso()),
        ).fetchone()
    if row is None:
        raise HTTPException(401, "Your session has expired. Sign in again")
    if request.method not in {"GET", "HEAD", "OPTIONS"}:
        csrf = request.headers.get("X-CSRF-Token", "")
        if not hmac.compare_digest(csrf.encode("utf-8"), row["csrf_token"].encode("utf-8")):
            raise HTTPException(403, "CSRF validation failed. Refresh the page and try again")
    return dict(row)


def require_operator(user: dict) -> None:
    if user["role"] not in {"admin", "coordinator"}:
        raise HTTPException(403, "This action requires a coordinator or administrator")


def require_admin(user: dict) -> None:
    if user["role"] != "admin":
        raise HTTPException(403, "Only network administrators can manage invitations")


def throttle(request: Request, email: str | None = None) -> None:
    """Limit observed client IP and normalized account separately, without trusting XFF.

    A deployment behind a shared proxy may raise only the aggregate IP allowance.
    Account-specific throttling remains independent of that deployment setting.
    """
    settings = request.app.state.settings
    client_ip = request.client.host if request.client else "unknown"
    limits = [(digest("ip:" + client_ip), settings.auth_ip_limit)]
    if email:
        limits.append((digest("email:" + email.lower()), settings.auth_limit))
    timestamp = time.time()
    blocked = False
    with transaction(request.app.state.settings.database, write=True) as conn:
        conn.execute("DELETE FROM auth_attempts WHERE occurred_at<?", (timestamp - 900,))
        for key, limit in limits:
            count = conn.execute(
                "SELECT COUNT(*) FROM auth_attempts WHERE key=?", (key,)
            ).fetchone()[0]
            if count >= limit:
                blocked = True
        if not blocked:
            conn.executemany(
                "INSERT INTO auth_attempts VALUES (?,?)",
                [(key, timestamp) for key, _limit in limits],
            )
    if blocked:
        raise HTTPException(
            429,
            "Too many authentication attempts. Try again in 15 minutes",
            headers={"Retry-After": "900"},
        )
