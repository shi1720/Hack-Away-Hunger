"""Explicit deployment configuration; production fails closed on unsafe settings."""

import os
from dataclasses import dataclass, field
from pathlib import Path
from urllib.parse import urlparse

from backend.db import is_postgres


def flag(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    if value.lower() not in {"true", "false", "1", "0"}:
        raise ValueError(f"{name} must be true or false")
    return value.lower() in {"true", "1"}


@dataclass(frozen=True)
class Settings:
    database: str = field(default="data/pantry-relay.sqlite3", repr=False)
    environment: str = "development"
    demo_enabled: bool = True
    demo_only: bool = False
    allow_public_demo: bool = False
    trusted_origins: tuple[str, ...] = ()
    cookie_secure: bool = False
    allowed_hosts: tuple[str, ...] = ("localhost", "127.0.0.1", "testserver")
    session_hours: int = 12
    auth_limit: int = 30
    auth_ip_limit: int = 30
    frontend: str = str(Path(__file__).resolve().parent.parent / "frontend" / "dist")

    @classmethod
    def from_env(cls) -> "Settings":
        env = os.getenv("PANTRY_ENV", "development")
        return cls(
            database=os.getenv("PANTRY_DATABASE", "data/pantry-relay.sqlite3"),
            environment=env,
            demo_enabled=flag("PANTRY_DEMO_ENABLED", env != "production"),
            demo_only=flag("PANTRY_DEMO_ONLY", False),
            allow_public_demo=flag("PANTRY_ALLOW_PUBLIC_DEMO", False),
            trusted_origins=tuple(
                origin.strip().rstrip("/")
                for origin in os.getenv("PANTRY_TRUSTED_ORIGINS", "").split(",")
                if origin.strip()
            ),
            cookie_secure=flag("PANTRY_COOKIE_SECURE", env == "production"),
            auth_ip_limit=int(os.getenv("PANTRY_AUTH_IP_LIMIT", "30")),
            allowed_hosts=tuple(
                h.strip()
                for h in os.getenv("PANTRY_ALLOWED_HOSTS", "localhost,127.0.0.1,testserver").split(
                    ","
                )
                if h.strip()
            ),
        )

    def validate(self) -> None:
        if self.environment not in {"development", "test", "production"}:
            raise ValueError("PANTRY_ENV must be development, test, or production")
        if not self.allowed_hosts:
            raise ValueError("PANTRY_ALLOWED_HOSTS must contain an allowed host")
        if not 1 <= self.auth_ip_limit <= 1000:
            raise ValueError("PANTRY_AUTH_IP_LIMIT must be between 1 and 1000")
        if self.demo_only and not self.demo_enabled:
            raise ValueError("PANTRY_DEMO_ONLY requires PANTRY_DEMO_ENABLED=true")
        for origin in self.trusted_origins:
            try:
                parsed = urlparse(origin)
                if (
                    parsed.scheme not in {"http", "https"}
                    or not parsed.netloc
                    or parsed.path
                    or parsed.query
                    or parsed.fragment
                    or parsed.username
                    or parsed.password
                    or "*" in origin
                ):
                    raise ValueError("Invalid trusted origin")
                if self.environment == "production" and parsed.scheme != "https":
                    raise ValueError("Production trusted origins require HTTPS")
            except ValueError as exc:
                raise ValueError(
                    "PANTRY_TRUSTED_ORIGINS must list exact HTTPS origins in production"
                ) from exc
        if self.environment == "production":
            if (
                self.demo_enabled
                and not self.demo_only
                and not (self.allow_public_demo and is_postgres(self.database))
            ):
                raise ValueError(
                    "Production requires demos disabled, demo-only mode, or PostgreSQL with PANTRY_ALLOW_PUBLIC_DEMO=true"
                )
            if not self.cookie_secure:
                raise ValueError("Production requires PANTRY_COOKIE_SECURE=true and HTTPS")
            if (
                any("*" in host for host in self.allowed_hosts)
                or "testserver" in self.allowed_hosts
            ):
                raise ValueError("Production requires explicit PANTRY_ALLOWED_HOSTS")
            if self.database == ":memory:":
                raise ValueError("Production requires a persistent PANTRY_DATABASE")
