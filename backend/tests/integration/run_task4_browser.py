"""Run unchanged Task 4 browser cases against the *reviewed* canonical backend.

Usage: python backend/tests/integration/run_task4_browser.py PATH_TO_TASK4_FRONTEND
All configuration/results and SQLite data are temporary; no frontend files change.
"""
import json
import os
from pathlib import Path
import shlex
import subprocess
import sys

from run_frontend_probe import temporary_directory


def main():
    frontend = Path(sys.argv[1]).resolve()
    here = Path(__file__).resolve().parent
    root = here.parents[2]
    command = [sys.executable, str(here / "serve_frontend_probe.py")]
    server_command = subprocess.list2cmdline(command) if os.name == "nt" else shlex.join(command)
    with temporary_directory() as directory:
        temporary = Path(directory)
        env = {**os.environ, "PYTHONPATH": os.pathsep.join([
            str(root / "backend"), str(root / "backend/tests"), str(root), str(root / "src")]),
            "DATABASE_URL": "sqlite:///" + (temporary / "test.db").as_posix(),
            "AGROSPHERE_FRONTEND_PROBE": "1", "AGROSPHERE_PROBE_DIRECTORY": directory,
            "NASA_POWER_ENABLED": "false", "NO_PROXY": "localhost,127.0.0.1",
            "CORS_ORIGINS": "http://localhost:5173,http://127.0.0.1:5173"}
        for key in ("E2E_LIVE_NASA", "E2E_CATALOG", "E2E_FRONTEND_FIXTURES"):
            env.pop(key, None)
        configuration = {
            "testDir": str(frontend / "e2e"), "testMatch": "live-mode.spec.ts",
            "outputDir": str(temporary / "browser-results"), "workers": 1, "timeout": 90000,
            "expect": {"timeout": 15000},
            "use": {"baseURL": "http://localhost:5173", "browserName": "chromium",
                "channel": os.environ.get("PLAYWRIGHT_CHANNEL", "msedge" if os.name == "nt" else "chromium")},
            "webServer": [
                {"command": server_command, "cwd": str(root), "url": "http://127.0.0.1:8000/api/v1/health",
                    "reuseExistingServer": False, "timeout": 30000},
                {"command": "npm run dev -- --host localhost --port 5173 --strictPort",
                    "cwd": str(frontend), "url": "http://localhost:5173", "reuseExistingServer": False,
                    "timeout": 30000, "env": {"VITE_USE_FIXTURES": "false", "VITE_API_BASE_URL": "http://localhost:8000/api/v1"}},
            ],
        }
        module = (frontend / "node_modules/@playwright/test/index.mjs").as_uri()
        config = temporary / "playwright.config.mjs"
        config.write_text("import { defineConfig } from " + json.dumps(module) + ";\nexport default defineConfig(" +
            json.dumps(configuration) + ");\n", encoding="utf-8")
        result = subprocess.run(["node", str(frontend / "node_modules/@playwright/test/cli.js"),
            "test", "--config", str(config)], cwd=frontend, env=env, timeout=240)
        if result.returncode:
            raise SystemExit(result.returncode)


if __name__ == "__main__":
    main()
