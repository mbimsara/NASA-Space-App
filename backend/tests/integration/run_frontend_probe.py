"""Run the actual frontend API client against this review's canonical backend.

Usage: python backend/tests/integration/run_frontend_probe.py PATH_TO_FRONTEND
Adapted from origin/dulanjaya/backend; no legacy services/tables or live NASA calls.
"""
from contextlib import contextmanager
import os
from pathlib import Path
import socket
import subprocess
import sys
from tempfile import TemporaryDirectory
import time
from urllib.request import urlopen


@contextmanager
def temporary_directory():
    directory = TemporaryDirectory(prefix="canonical-frontend-probe-")
    try:
        yield directory.name
    finally:
        for attempt in range(20):
            try:
                directory.cleanup()
                break
            except PermissionError:
                if attempt == 19:
                    raise
                time.sleep(.25)


def main():
    frontend = Path(sys.argv[1]).resolve()
    here = Path(__file__).resolve().parent
    root = here.parents[2]
    for port in (8000, 5173):
        with socket.socket() as sock:
            if sock.connect_ex(("127.0.0.1", port)) == 0:
                raise RuntimeError(f"Port {port} is occupied; refusing to reuse an existing server.")
    with temporary_directory() as directory:
        env = {**os.environ, "PYTHONPATH": os.pathsep.join([
            str(root / "backend"), str(root / "backend/tests"), str(root), str(root / "src")]),
            "DATABASE_URL": "sqlite:///" + (Path(directory) / "test.db").as_posix(),
            "AGROSPHERE_FRONTEND_PROBE": "1", "AGROSPHERE_PROBE_DIRECTORY": directory,
            "NASA_POWER_ENABLED": "false", "NO_PROXY": "localhost,127.0.0.1",
            "CORS_ORIGINS": "http://localhost:5173,http://127.0.0.1:5173"}
        with (Path(directory) / "server.log").open("w+", encoding="utf-8") as log:
            process = subprocess.Popen([sys.executable, str(here / "serve_frontend_probe.py")],
                cwd=directory, env=env, stdout=log, stderr=log,
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0)
            try:
                for _ in range(100):
                    if process.poll() is not None:
                        log.seek(0)
                        raise RuntimeError(log.read())
                    try:
                        with urlopen("http://127.0.0.1:8000/api/v1/health", timeout=1):
                            break
                    except OSError:
                        time.sleep(.1)
                else:
                    raise RuntimeError("Backend startup timed out")
                result = subprocess.run(["node", str(here / "frontend_probe.mjs"), str(frontend)],
                    cwd=directory, env=env, text=True, capture_output=True, encoding="utf-8", timeout=90)
                print(result.stdout)
                if result.returncode:
                    raise RuntimeError(result.stderr)
            finally:
                process.terminate()
                try:
                    process.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait()


if __name__ == "__main__":
    main()
