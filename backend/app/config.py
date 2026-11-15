"""Backend settings, read once at startup from the environment and root .env."""

import os
from dataclasses import dataclass, field
from pathlib import Path
from urllib.parse import urlsplit

from dotenv import dotenv_values


ENV_FILE = Path(__file__).resolve().parents[2] / ".env"
DEFAULT_DATABASE_URL = "sqlite:///./agrosphere.db"
DEFAULT_CORS_ORIGINS = "http://localhost:5173,http://127.0.0.1:5173"


@dataclass(frozen=True)
class Settings:
    database_url: str = field(repr=False)
    cors_origins: tuple[str, ...]
    nasa_power_enabled: bool = True
    observation_cache_ttl_seconds: int = 86400
    assistant_provider: str = "deterministic"
    openai_model: str | None = None
    deployment_mode: str = "local"
    staging_backend_token: str | None = field(default=None, repr=False)
    trusted_hosts: tuple[str, ...] = ()


def load_settings(env_file: Path = ENV_FILE) -> Settings:
    # Read an explicit path, without modifying the process environment.
    # Disable interpolation so database passwords containing ${...} stay literal.
    values = {**dotenv_values(env_file, interpolate=False), **os.environ}
    database_url = (values.get("DATABASE_URL", DEFAULT_DATABASE_URL) or "").strip()
    if not database_url:
        raise ValueError("DATABASE_URL must not be empty.")

    origins = tuple(dict.fromkeys(
        origin.strip()
        for origin in (values.get("CORS_ORIGINS", DEFAULT_CORS_ORIGINS) or "").split(",")
        if origin.strip()
    ))
    for origin in origins:
        parsed = urlsplit(origin)
        if (
            parsed.scheme not in {"http", "https"}
            or "*" in origin
            or not parsed.hostname
            or parsed.username is not None
            or parsed.password is not None
            or parsed.path
            or parsed.query
            or parsed.fragment
        ):
            raise ValueError(
                "CORS_ORIGINS must contain comma-separated HTTP(S) origins "
                "without paths, credentials, or wildcards."
            )

    nasa_power_enabled = (values.get("NASA_POWER_ENABLED", "true") or "").strip().lower()
    if nasa_power_enabled not in {"true", "false"}:
        raise ValueError("NASA_POWER_ENABLED must be true or false.")

    try:
        cache_ttl = int(values.get("OBSERVATION_CACHE_TTL_SECONDS", "86400"))
    except (ValueError, TypeError):
        raise ValueError("OBSERVATION_CACHE_TTL_SECONDS must be a positive integer.") from None
    if cache_ttl <= 0:
        raise ValueError("OBSERVATION_CACHE_TTL_SECONDS must be a positive integer.")

    assistant_provider = (values.get("ASSISTANT_PROVIDER", "deterministic") or "").strip().lower()
    if assistant_provider not in {"deterministic", "openai"}:
        raise ValueError("ASSISTANT_PROVIDER must be deterministic or openai.")
    openai_model = (values.get("OPENAI_MODEL", "") or "").strip() or None
    if assistant_provider == "openai" and not openai_model:
        raise ValueError("OPENAI_MODEL is required when ASSISTANT_PROVIDER=openai.")

    deployment_mode = (values.get("DEPLOYMENT_MODE", "local") or "").strip()
    if deployment_mode not in {"local", "hosted-staging"}:
        raise ValueError("DEPLOYMENT_MODE must be local or hosted-staging.")
    if values.get("RENDER") == "true" and deployment_mode != "hosted-staging":
        raise ValueError("Render requires DEPLOYMENT_MODE=hosted-staging; local mode would expose unprotected APIs.")
    token = values.get("STAGING_BACKEND_TOKEN") or None
    hosts = tuple(h.strip() for h in (values.get("TRUSTED_HOSTS", "") or "").split(",") if h.strip())
    if deployment_mode == "hosted-staging":
        from sqlalchemy.engine import make_url
        if not token or len(token) < 32 or not token.isascii() or any(c.isspace() for c in token):
            raise ValueError("Hosted staging requires a random STAGING_BACKEND_TOKEN of at least 32 ASCII characters without whitespace.")
        if not origins or any(urlsplit(o).scheme != "https" for o in origins):
            raise ValueError("Hosted staging requires explicit HTTPS CORS_ORIGINS.")
        if not hosts or any(not h or any(c in h for c in "*/:@?# ") for h in hosts):
            raise ValueError("Hosted staging TRUSTED_HOSTS requires exact hostnames without ports or wildcards.")
        if assistant_provider != "deterministic":
            raise ValueError("Hosted staging requires the deterministic assistant.")
        url = make_url(database_url)
        if url.get_backend_name() == "sqlite":
            if (values.get("ALLOW_EPHEMERAL_SQLITE") != "true" or not url.database
                    or not Path(url.database).is_absolute() or url.query):
                raise ValueError("Disposable hosted SQLite requires an absolute file path and ALLOW_EPHEMERAL_SQLITE=true; it is not persistent storage.")
        elif url.drivername == "postgresql+psycopg":
            if values.get("POSTGRES_COMPATIBILITY_VERIFIED") != "true":
                raise ValueError("PostgreSQL requires explicit compatibility verification before hosted use.")
        else:
            raise ValueError("Hosted database driver must be explicitly sqlite or postgresql+psycopg.")

    return Settings(
        database_url=database_url, cors_origins=origins,
        nasa_power_enabled=nasa_power_enabled == "true",
        observation_cache_ttl_seconds=cache_ttl,
        assistant_provider=assistant_provider, openai_model=openai_model,
        deployment_mode=deployment_mode, staging_backend_token=token, trusted_hosts=hosts,
    )


settings = load_settings()
