"""Run Node/Vite's actual frontend API client against isolated uvicorn processes.

Usage: python backend/tests/integration/run_frontend_http.py PATH_TO_FRONTEND
No browser testing is implied. Does not change frontend or environment files.
"""
import os
from pathlib import Path
import socket
import subprocess
import sys
from tempfile import TemporaryDirectory
import time
from urllib.request import urlopen
from contextlib import contextmanager


@contextmanager
def isolated_directory():
    temporary = TemporaryDirectory(prefix="agrosphere-http-")
    try:
        yield temporary.name
    finally:
        # Windows may briefly retain a SQLite handle after the server exits.
        # Retry cleanup of this exact tempfile-owned directory, never other data.
        for attempt in range(20):
            try:
                temporary.cleanup()
                break
            except PermissionError:
                if attempt == 19:
                    raise
                time.sleep(.25)


def main():
    frontend = Path(sys.argv[1]).resolve()
    here = Path(__file__).resolve().parent
    backend = here.parents[1]
    # Refuse to connect tests to somebody else's app or stop their processes.
    for port in (8000, 5173):
        with socket.socket() as connection:
            if connection.connect_ex(("127.0.0.1", port)) == 0:
                raise RuntimeError(f"Port {port} is already in use; stop your own server before testing.")
    with isolated_directory() as directory:
        for mode in ("synthetic", "live"):
            database = Path(directory) / f"{mode}.db"
            env = {**os.environ, "PYTHONPATH": os.pathsep.join([str(backend), str(backend / 'tests')]),
                "DATABASE_URL": f"sqlite:///{database.as_posix()}", "INTEGRATION_MODE": mode,
                "NASA_POWER_ENABLED": "true", "CORS_ORIGINS": "http://localhost:5173,http://127.0.0.1:5173"}
            with (Path(directory) / f"{mode}.log").open("w+", encoding="utf-8") as log:
                process = subprocess.Popen([sys.executable, str(here / "serve_backend.py")],
                    env=env, cwd=directory, stdout=log, stderr=log,
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
                        raise RuntimeError("Backend did not become ready")
                    result = subprocess.run(["node", str(here / "frontend_http.mjs"), str(frontend), mode],
                        cwd=directory, env={**env, "NO_PROXY": "localhost,127.0.0.1"},
                        capture_output=True, text=True, timeout=150, encoding="utf-8")
                    print(result.stdout)
                    if result.returncode:
                        print(result.stderr, file=sys.stderr)
                        raise RuntimeError(f"{mode} HTTP checks failed")
                finally:
                    process.terminate()
                    try:
                        process.wait(timeout=10)
                    except subprocess.TimeoutExpired:
                        process.kill()
                        process.wait()


if __name__ == "__main__":
    main()
