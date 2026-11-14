import json
import os
from pathlib import Path
import sqlite3
import subprocess
import sys
from unittest.mock import patch

import pytest

from app.config import load_settings
from app.database.connection import create_database_engine


@pytest.fixture
def env_file(tmp_path, monkeypatch):
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.delenv("CORS_ORIGINS", raising=False)
    monkeypatch.delenv("NASA_POWER_ENABLED", raising=False)
    monkeypatch.delenv("OBSERVATION_CACHE_TTL_SECONDS", raising=False)
    return tmp_path / ".env"


def test_defaults_preserve_existing_configuration(env_file):
    settings = load_settings(env_file)
    assert settings.database_url == "sqlite:///./agrosphere.db"
    assert settings.nasa_power_enabled is True
    assert settings.observation_cache_ttl_seconds == 86400
    assert settings.cors_origins == (
        "http://localhost:5173", "http://127.0.0.1:5173"
    )


def test_dotenv_configuration(env_file):
    env_file.write_text(
        "DATABASE_URL=sqlite:///./custom.db\n"
        "CORS_ORIGINS= https://farm.example, http://localhost:3000,https://farm.example, \n",
        encoding="utf-8",
    )
    settings = load_settings(env_file)
    assert settings.database_url == "sqlite:///./custom.db"
    assert settings.cors_origins == ("https://farm.example", "http://localhost:3000")
    assert "DATABASE_URL" not in os.environ


def test_environment_overrides_dotenv(env_file, monkeypatch):
    env_file.write_text(
        "DATABASE_URL=sqlite:///./file.db\nCORS_ORIGINS=https://file.example\n",
        encoding="utf-8",
    )
    monkeypatch.setenv("DATABASE_URL", "sqlite:///./environment.db")
    monkeypatch.setenv("CORS_ORIGINS", "https://environment.example")
    settings = load_settings(env_file)
    assert settings.database_url == "sqlite:///./environment.db"
    assert settings.cors_origins == ("https://environment.example",)


def test_empty_origins_disable_cors(env_file, monkeypatch):
    monkeypatch.setenv("CORS_ORIGINS", "  ,  ")
    assert load_settings(env_file).cors_origins == ()


def test_empty_database_url_fails(env_file, monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "  ")
    with pytest.raises(ValueError, match="DATABASE_URL must not be empty"):
        load_settings(env_file)


def test_nasa_power_flag_environment_overrides_dotenv(env_file, monkeypatch):
    env_file.write_text("NASA_POWER_ENABLED=true\n", encoding="utf-8")
    monkeypatch.setenv("NASA_POWER_ENABLED", "false")
    assert load_settings(env_file).nasa_power_enabled is False


def test_invalid_nasa_power_flag_fails(env_file, monkeypatch):
    monkeypatch.setenv("NASA_POWER_ENABLED", "maybe")
    with pytest.raises(ValueError, match="NASA_POWER_ENABLED"):
        load_settings(env_file)


def test_cache_ttl_environment_overrides_dotenv(env_file, monkeypatch):
    env_file.write_text("OBSERVATION_CACHE_TTL_SECONDS=3600\n", encoding="utf-8")
    assert load_settings(env_file).observation_cache_ttl_seconds == 3600
    monkeypatch.setenv("OBSERVATION_CACHE_TTL_SECONDS", "60")
    assert load_settings(env_file).observation_cache_ttl_seconds == 60


@pytest.mark.parametrize("ttl", ["", "0", "-1", "1.5", "never"])
def test_invalid_cache_ttl_fails(env_file, monkeypatch, ttl):
    monkeypatch.setenv("OBSERVATION_CACHE_TTL_SECONDS", ttl)
    with pytest.raises(ValueError, match="OBSERVATION_CACHE_TTL_SECONDS"):
        load_settings(env_file)


@pytest.mark.parametrize("origin", [
    "*", "https://*.example", "ftp://farm.example", "https://farm.example/path",
    "https://farm.example/", "https://farm.example?query=1",
    "https://farm.example#fragment", "https://user:password@farm.example",
])
def test_invalid_origins_fail(env_file, monkeypatch, origin):
    monkeypatch.setenv("CORS_ORIGINS", origin)
    with pytest.raises(ValueError, match="CORS_ORIGINS"):
        load_settings(env_file)


def test_database_password_is_literal_and_hidden(env_file):
    env_file.write_text(
        "DATABASE_URL=postgresql://user:${PASSWORD}@localhost/farms\n",
        encoding="utf-8",
    )
    settings = load_settings(env_file)
    assert "${PASSWORD}" in settings.database_url
    assert "${PASSWORD}" not in repr(settings)


@pytest.mark.parametrize("url,expected_args", [
    ("sqlite:///./test.db", {"check_same_thread": False}),
    ("sqlite+pysqlite:///./test.db", {"check_same_thread": False}),
    ("postgresql+psycopg://user:password@localhost/farms", {}),
])
def test_database_connect_args_are_driver_specific(url, expected_args):
    # No external driver or database server is required for this option check.
    with patch("app.database.connection.create_engine") as create_engine:
        create_database_engine(url)
    create_engine.assert_called_once_with(url, connect_args=expected_args)


def test_configured_app_cors_and_sqlite_persistence(tmp_path):
    backend = Path(__file__).resolve().parents[1]
    profile = json.loads(
        (backend.parent / "data/fixtures/farm.synthetic.json").read_text(encoding="utf-8")
    )
    database_path = tmp_path / "configured.db"
    # Seed the pre-change schema directly, before the configured app starts.
    with sqlite3.connect(database_path) as db:
        db.execute(
            "CREATE TABLE farms (id VARCHAR(36) NOT NULL PRIMARY KEY, "
            "input_version INTEGER NOT NULL, profile JSON NOT NULL)"
        )
        db.execute(
            "INSERT INTO farms (id, input_version, profile) VALUES (?, ?, ?)",
            ("existing-farm", 7, json.dumps(profile)),
        )
    env = {
        **os.environ,
        "PYTHONPATH": str(backend),
        "DATABASE_URL": f"sqlite:///{database_path.as_posix()}",
        "CORS_ORIGINS": "https://farm.example,https://second.example",
    }
    # Fresh processes exercise import-time configuration and a real restart.
    create_script = '''
import json, sys
from fastapi.testclient import TestClient
from app.main import app
from app.database.connection import engine
from sqlalchemy import inspect

with TestClient(app) as client:
    assert "observation_snapshots" in inspect(engine).get_table_names()
    assert [column["name"] for column in inspect(engine).get_columns("farms")] == [
        "id", "input_version", "profile",
    ]
    existing = client.get("/api/v1/farms/existing-farm")
    assert existing.status_code == 200
    assert existing.json()["input_version"] == 7
    assert existing.json()["profile"]["area_ha"] == 1.0
    for origin in ("https://farm.example", "https://second.example"):
        for method in ("GET", "POST", "PATCH"):
            response = client.options("/api/v1/farms", headers={
                "Origin": origin,
                "Access-Control-Request-Method": method,
                "Access-Control-Request-Headers": "Content-Type",
            })
            assert response.status_code == 200
            assert response.headers["access-control-allow-origin"] == origin
            assert response.headers["access-control-allow-credentials"] == "true"
    for origin in ("http://localhost:5173", "https://untrusted.example"):
        response = client.options("/api/v1/farms", headers={
            "Origin": origin, "Access-Control-Request-Method": "POST",
        })
        assert response.status_code == 400
        assert "access-control-allow-origin" not in response.headers
    response = client.options("/api/v1/farms", headers={
        "Origin": "https://farm.example", "Access-Control-Request-Method": "DELETE",
    })
    assert response.status_code == 400
    response = client.get("/api/v1/health", headers={"Origin": "https://untrusted.example"})
    assert response.status_code == 200
    assert "access-control-allow-origin" not in response.headers
    response = client.get("/api/v1/health", headers={"Origin": "https://farm.example"})
    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "https://farm.example"
    created = client.post("/api/v1/farms", json=json.load(sys.stdin))
    assert created.status_code == 201
    result = created.json()
    result["profile"]["area_ha"] = 2.5
    updated = client.patch("/api/v1/farms/" + result["id"], json={
        "expected_input_version": 1, "profile": result["profile"],
    })
    assert updated.status_code == 200
    assert updated.json()["input_version"] == 2
    print(json.dumps(updated.json()))
engine.dispose()
'''
    created = subprocess.run(
        [sys.executable, "-c", create_script], input=json.dumps(profile),
        cwd=tmp_path, env=env, capture_output=True, text=True, timeout=30,
    )
    assert created.returncode == 0, created.stderr
    saved = json.loads(created.stdout)
    assert database_path.is_file()
    read_script = '''
import json, sys
from fastapi.testclient import TestClient
from app.main import app
with TestClient(app) as client:
    saved = json.load(sys.stdin)
    response = client.get("/api/v1/farms/" + saved["id"])
    assert response.status_code == 200
    assert response.json() == saved
    existing = client.get("/api/v1/farms/existing-farm")
    assert existing.json()["input_version"] == 7
    assert existing.json()["profile"]["area_ha"] == 1.0
'''
    retrieved = subprocess.run(
        [sys.executable, "-c", read_script], input=json.dumps(saved),
        cwd=tmp_path, env=env, capture_output=True, text=True, timeout=30,
    )
    assert retrieved.returncode == 0, retrieved.stderr
