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
    app_env: str = "development"


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

    app_env = (values.get("APP_ENV", "development") or "").strip().lower()
    if app_env not in {"development", "test", "staging"}:
        raise ValueError("APP_ENV must be development, test or staging.")
    if app_env == "staging":
        from sqlalchemy.engine import make_url
        url = make_url(database_url)
        # This release supports one SQLite writer on a persistent local volume.
        # A PostgreSQL URL alone is not a validated database migration.
        if (url.get_backend_name() != "sqlite" or not url.database
                or not Path(url.database).is_absolute() or url.query):
            raise ValueError("Staging DATABASE_URL requires an absolute SQLite file path on persistent storage.")
        if not origins or any(urlsplit(origin).scheme != "https" for origin in origins):
            raise ValueError("Staging CORS_ORIGINS requires explicit HTTPS origins.")
        if assistant_provider != "deterministic":
            raise ValueError("Staging requires ASSISTANT_PROVIDER=deterministic until external AI review.")

    return Settings(
        database_url=database_url, cors_origins=origins,
        nasa_power_enabled=nasa_power_enabled == "true",
        observation_cache_ttl_seconds=cache_ttl,
        assistant_provider=assistant_provider, openai_model=openai_model,
        app_env=app_env,
    )


settings = load_settings()
