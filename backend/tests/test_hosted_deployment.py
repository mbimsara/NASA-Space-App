"""Offline checks; no hosted DB or provider access."""
import json
import os
from pathlib import Path
import subprocess
import sys

import pytest
from sqlalchemy import create_mock_engine

from app.config import load_settings
from app.database.connection import Base

ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture
def hosted_env(monkeypatch, tmp_path):
    for key, value in {
        "DEPLOYMENT_MODE": "hosted-staging", "STAGING_BACKEND_TOKEN": "a" * 48,
        "CORS_ORIGINS": "https://frontend.example", "TRUSTED_HOSTS": "backend.example,testserver",
        "DATABASE_URL": "sqlite:///" + (tmp_path / "disposable.db").as_posix(),
        "ALLOW_EPHEMERAL_SQLITE": "true", "ASSISTANT_PROVIDER": "deterministic",
        "POSTGRES_COMPATIBILITY_VERIFIED": "false",
    }.items():
        monkeypatch.setenv(key, value)
    return tmp_path / "absent.env"


def test_hosted_settings_hide_token(hosted_env):
    settings = load_settings(hosted_env)
    assert settings.deployment_mode == "hosted-staging"
    assert settings.staging_backend_token not in repr(settings)


def test_render_cannot_accidentally_start_in_local_mode(hosted_env, monkeypatch):
    monkeypatch.setenv("RENDER", "true")
    monkeypatch.setenv("DEPLOYMENT_MODE", "local")
    with pytest.raises(ValueError, match="Render requires"):
        load_settings(hosted_env)


@pytest.mark.parametrize("key,value", [
    ("STAGING_BACKEND_TOKEN", ""), ("STAGING_BACKEND_TOKEN", "short"),
    ("TRUSTED_HOSTS", "*"), ("TRUSTED_HOSTS", ""),
    ("CORS_ORIGINS", "http://frontend.example"), ("CORS_ORIGINS", ""),
    ("ALLOW_EPHEMERAL_SQLITE", "false"), ("DATABASE_URL", "sqlite:///:memory:"),
    ("DATABASE_URL", "postgresql://localhost/farms"),
    ("DATABASE_URL", "postgresql+psycopg://localhost/farms"),
])
def test_unsafe_hosted_settings_rejected(hosted_env, monkeypatch, key, value):
    monkeypatch.setenv(key, value)
    with pytest.raises(ValueError):
        load_settings(hosted_env)


def test_all_actual_routes_protected_before_record_access(hosted_env, tmp_path):
    script = '''
import json, sys
from fastapi.testclient import TestClient
from app.main import app
with TestClient(app) as client:
    for path, operations in app.openapi()["paths"].items():
        for method in operations:
            if method.upper() not in {"GET", "HEAD", "POST", "PATCH", "PUT", "DELETE", "OPTIONS"}: continue
            if path == "/api/v1/health" and method.upper() in {"GET", "HEAD"}: continue
            r = client.request(method, path)
            assert r.status_code == 401, (method, path, r.status_code)
    assert client.get("/api/v1/health").status_code == 200
    assert client.post("/api/v1/health").status_code == 401
    assert client.get("/docs").status_code == 401
    assert client.get("/api/v1/farms/unknown", headers={"Authorization": "Bearer wrong"}).status_code == 401
    assert client.get("https://untrusted.example/api/v1/health").status_code == 400
    auth = {"Authorization": "Bearer " + "a" * 48}
    assert client.get("/api/v1/farms/unknown", headers=auth).status_code == 404
    assert client.post("/api/v1/farms", json={}, headers=auth).status_code == 422
    created = client.post("/api/v1/farms", json=json.load(sys.stdin), headers=auth)
    assert created.status_code == 201, created.text
    assert client.get("/api/v1/farms/" + created.json()["id"], headers=auth).json() == created.json()
    assert client.get("/docs", headers=auth).status_code == 404
    assert client.options("/api/v1/farms", headers={"Origin":"https://frontend.example",
        "Access-Control-Request-Method":"POST"}).status_code == 401
'''
    result = subprocess.run([sys.executable, "-c", script], cwd=tmp_path,
        env={**os.environ, "PYTHONPATH": str(ROOT / "backend"), "NASA_POWER_ENABLED": "false"},
        input=(ROOT / "data/fixtures/farm.synthetic.json").read_text(encoding="utf-8"),
        text=True, capture_output=True, timeout=30)
    assert result.returncode == 0, result.stderr


def test_postgresql_ddl_compiles_without_changing_models():
    statements = []
    engine = create_mock_engine("postgresql+psycopg://", lambda sql, *args, **kw: statements.append(str(sql.compile(dialect=engine.dialect))))
    Base.metadata.create_all(engine)
    assert len([s for s in statements if "CREATE TABLE" in s]) == len(Base.metadata.tables)
    assert any("FOREIGN KEY" in s for s in statements)
    assert any(" JSON " in s for s in statements)


def test_hosting_manifests_preserve_full_context_and_spa_api_routing():
    import yaml
    service = yaml.safe_load((ROOT / "render.yaml").read_text())["services"][0]
    assert "rootDir" not in service
    assert service["autoDeployTrigger"] == "off"
    assert "pip install ." in service["buildCommand"]
    assert "$PORT" in service["startCommand"]
    config = json.loads((ROOT / "frontend/vercel.json").read_text())
    assert config["routes"][0]["dest"] == "/api/gateway"
    assert config["routes"][1] == {"handle": "filesystem"}
    assert config["routes"][-1]["dest"] == "/index.html"
