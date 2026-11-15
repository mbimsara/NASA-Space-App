"""Offline staging configuration, HTTP boundary, readiness and backup checks."""
import importlib.util
import json
import os
from pathlib import Path
import sqlite3
import subprocess
import sys

import pytest
from sqlalchemy.exc import OperationalError

from app.config import load_settings
from app.database.connection import get_db
from app.main import app

ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture
def staging_env(tmp_path, monkeypatch):
    for name, value in {
        "APP_ENV": "staging",
        "DATABASE_URL": "sqlite:///" + (tmp_path / "staging.db").as_posix(),
        "CORS_ORIGINS": "https://staging.example:8443",
        "ASSISTANT_PROVIDER": "deterministic",
    }.items():
        monkeypatch.setenv(name, value)
    return tmp_path / "absent.env"


def test_valid_staging_configuration(staging_env):
    assert load_settings(staging_env).app_env == "staging"


@pytest.mark.parametrize("key,value", [
    ("DATABASE_URL", "sqlite:///./ephemeral.db"),
    ("DATABASE_URL", "sqlite:///:memory:"),
    ("DATABASE_URL", "postgresql://localhost/staging"),
    ("DATABASE_URL", "sqlite:///file:temporary?mode=memory&uri=true"),
    ("CORS_ORIGINS", ""),
    ("CORS_ORIGINS", "http://localhost:5173"),
    ("CORS_ORIGINS", "*"),
    ("ASSISTANT_PROVIDER", "openai"),
    ("APP_ENV", "production"),
])
def test_unsafe_staging_configuration_rejected(staging_env, monkeypatch, key, value):
    monkeypatch.setenv(key, value)
    monkeypatch.setenv("OPENAI_MODEL", "test-model")
    with pytest.raises(ValueError):
        load_settings(staging_env)


def test_readiness_success(client):
    assert client.get("/api/v1/ready").json() == {"status": "ready"}


def test_readiness_failure_hides_connection_details(client):
    class Unavailable:
        def execute(self, statement):
            raise OperationalError("private database path", {}, Exception("secret"))

    app.dependency_overrides[get_db] = lambda: Unavailable()
    response = client.get("/api/v1/ready")
    assert response.status_code == 503
    assert response.json()["error"]["code"] == "SERVICE_UNAVAILABLE"
    assert "secret" not in response.text and "private" not in response.text


def test_actual_staging_startup_and_http_boundary(staging_env, tmp_path):
    script = '''
import json, sys
from fastapi.testclient import TestClient
from app.main import app
with TestClient(app) as client:
    base = "https://staging.example:8443"
    def url(path): return base + "/api/v1" + path
    assert client.get(url("/ready")).status_code == 200
    for path in ("/docs", "/redoc", "/openapi.json"):
        assert client.get(base + path).status_code == 404
    assert client.get("https://untrusted.example/api/v1/health").status_code == 400
    for origin in (None, "https://untrusted.example"):
        headers = {} if origin is None else {"Origin": origin}
        r = client.post(url("/farms"), json={}, headers=headers)
        assert r.status_code == 403
        assert r.json()["error"]["code"] == "STAGING_ORIGIN_REQUIRED"
    headers = {"Origin": base}
    preflight = client.options(url("/farms"), headers={**headers,
        "Access-Control-Request-Method": "POST", "Access-Control-Request-Headers": "Content-Type"})
    assert preflight.status_code == 200
    assert preflight.headers["access-control-allow-origin"] == base
    assert client.options(url("/farms"), headers={"Origin": "https://bad.example",
        "Access-Control-Request-Method": "POST"}).status_code == 400
    farm = client.post(url("/farms"), json=json.load(sys.stdin), headers=headers)
    assert farm.status_code == 201
    assert farm.headers["cache-control"] == "no-store"
    assert farm.headers["x-content-type-options"] == "nosniff"
    assert farm.headers["x-request-id"]
    saved = client.get(url("/farms/" + farm.json()["id"])).json()
    assert saved == farm.json()
    print(saved["id"])
'''
    profile = (ROOT / "data/fixtures/farm.synthetic.json").read_text(encoding="utf-8")
    env = {**os.environ, "PYTHONPATH": str(ROOT / "backend"), "NASA_POWER_ENABLED": "false"}
    result = subprocess.run([sys.executable, "-c", script], env=env, cwd=tmp_path,
                            input=profile, capture_output=True, text=True, timeout=30)
    assert result.returncode == 0, result.stderr
    # Actual second process: persisted farm remains readable across restart.
    check = subprocess.run([sys.executable, "-c", '''
from fastapi.testclient import TestClient
from app.main import app
import sys
with TestClient(app) as c:
    assert c.get("https://staging.example:8443/api/v1/farms/" + sys.argv[1]).status_code == 200
''', result.stdout.strip()], env=env, cwd=tmp_path, capture_output=True, text=True, timeout=30)
    assert check.returncode == 0, check.stderr


def test_sqlite_backup_preserves_records_and_refuses_overwrite(tmp_path):
    spec = importlib.util.spec_from_file_location("backup", ROOT / "deploy/staging/backup_sqlite.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    source, destination = tmp_path / "original.db", tmp_path / "backup.db"
    with sqlite3.connect(source) as db:
        db.execute("CREATE TABLE snapshots (payload TEXT)")
        db.execute("INSERT INTO snapshots VALUES (?)", (json.dumps({"synthetic": True}),))
    module.backup(source, destination)
    with sqlite3.connect(destination) as db:
        assert json.loads(db.execute("SELECT payload FROM snapshots").fetchone()[0]) == {"synthetic": True}
    with pytest.raises(FileExistsError):
        module.backup(source, destination)
    with pytest.raises(FileExistsError):
        module.backup(source, source)


def test_compose_has_no_public_api_port_and_requires_gateway_credentials():
    import yaml
    compose = yaml.safe_load((ROOT / "deploy/staging/compose.yaml").read_text())
    backend, gateway = compose["services"]["backend"], compose["services"]["gateway"]
    assert "ports" not in backend
    assert gateway["ports"] == ["127.0.0.1:8443:443"]
    assert "database:/var/lib/agrosphere" in backend["volumes"]
    assert backend["read_only"] is True
    assert "STAGING_PASSWORD_HASH:?" in gateway["environment"]["STAGING_PASSWORD_HASH"]
    caddy = (ROOT / "deploy/staging/Caddyfile").read_text()
    assert caddy.index("basic_auth") < caddy.index("handle /api/*")
    assert "header_up -Authorization" in caddy


def test_deployment_and_workflow_yaml_is_valid():
    import yaml
    for path in [ROOT / "deploy/staging/compose.yaml", *sorted((ROOT / ".github/workflows").glob("*.yml"))]:
        assert isinstance(yaml.safe_load(path.read_text(encoding="utf-8")), dict), path
