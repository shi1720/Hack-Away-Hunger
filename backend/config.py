"""Explicit deployment configuration; production fails closed on unsafe settings."""

import os
from dataclasses import dataclass
from pathlib import Path


def flag(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    if value.lower() not in {"true", "false", "1", "0"}:
        raise ValueError(f"{name} must be true or false")
    return value.lower() in {"true", "1"}


@dataclass(frozen=True)
class Settings:
    database: str = "data/pantry-relay.sqlite3"
    environment: str = "development"
    demo_enabled: bool = True
    demo_only: bool = False
    cookie_secure: bool = False
    allowed_hosts: tuple[str, ...] = ("localhost", "127.0.0.1", "testserver")
    session_hours: int = 12
    auth_limit: int = 30
    frontend: str = str(Path(__file__).resolve().parent.parent / "frontend" / "dist")

    @classmethod
    def from_env(cls) -> "Settings":
        env = os.getenv("PANTRY_ENV", "development")
        return cls(
            database=os.getenv("PANTRY_DATABASE", "data/pantry-relay.sqlite3"),
            environment=env,
            demo_enabled=flag("PANTRY_DEMO_ENABLED", env != "production"),
            demo_only=flag("PANTRY_DEMO_ONLY", False),
            cookie_secure=flag("PANTRY_COOKIE_SECURE", env == "production"),
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
        if self.demo_only and not self.demo_enabled:
            raise ValueError("PANTRY_DEMO_ONLY requires PANTRY_DEMO_ENABLED=true")
        if self.environment == "production":
            if self.demo_enabled and not self.demo_only:
                raise ValueError(
                    "Production requires PANTRY_DEMO_ENABLED=false unless PANTRY_DEMO_ONLY=true"
                )
            if not self.cookie_secure:
                raise ValueError("Production requires PANTRY_COOKIE_SECURE=true and HTTPS")
            if "*" in self.allowed_hosts or "testserver" in self.allowed_hosts:
                raise ValueError("Production requires explicit PANTRY_ALLOWED_HOSTS")
            if self.database == ":memory:":
                raise ValueError("Production requires a persistent PANTRY_DATABASE")
