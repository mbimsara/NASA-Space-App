"""Opt-in real FastAPI E2E server with disposable SQLite; never a deployed app."""
import json
import os
from copy import deepcopy
from pathlib import Path
import sys
from tempfile import TemporaryDirectory

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT / "backend"), str(ROOT), str(ROOT / "src")]


def main():
    if os.environ.get("AGROSPHERE_E2E") != "1":
        raise RuntimeError("Start through the Playwright configuration, not as a production server.")
    with TemporaryDirectory(prefix="agrosphere-browser-") as directory:
        os.environ["DATABASE_URL"] = "sqlite:///" + (Path(directory) / "test.db").as_posix()
        backend_port = int(os.environ.get("E2E_BACKEND_PORT", "8000"))
        frontend_port = int(os.environ.get("E2E_FRONTEND_PORT", "5173"))
        os.environ["CORS_ORIGINS"] = (
            f"http://localhost:{frontend_port},http://127.0.0.1:{frontend_port}"
        )
        os.environ["NASA_POWER_ENABLED"] = "true"
        from app.main import app
        from app.database.connection import engine
        import uvicorn

        if os.environ.get("E2E_LIVE_NASA") != "1":
            from app.services.observations import get_observation_adapter
            from app.services import rotations
            from services import nasa_power

            raw = json.loads((ROOT / "backend/tests/fixtures/nasa_power.synthetic.json").read_text(encoding="utf-8"))

            class SyntheticObservations:
                cache_namespace = "explicit-synthetic-browser-test-v1"

                def observe(self, *, latitude, longitude, start, end):
                    provider_response = deepcopy(raw)
                    provider_response["header"]["start"] = start.strftime("%Y%m%d")
                    provider_response["header"]["end"] = end.strftime("%Y%m%d")
                    result = nasa_power.normalize(provider_response, start.isoformat(), end.isoformat(),
                        retrieved_at="2024-03-02T00:00:00+00:00",
                        source_url="https://example.invalid/synthetic-browser-fixture")
                    result["data_kind"] = "synthetic"
                    result["limitations"].append("Explicit synthetic browser fixture; not a NASA retrieval or approved agronomic advice.")
                    return result

            def forbidden(*args, **kwargs):
                raise AssertionError("Browser fixture tests cannot call NASA.")

            nasa_power.urlopen = forbidden
            app.dependency_overrides[get_observation_adapter] = lambda: SyntheticObservations()
            catalog = json.loads((ROOT / "data/catalogs/crops.json").read_text(encoding="utf-8"))
            # Only this temporary test catalog is reviewed. Original draft crops
            # and source files are never changed or promoted to approved status.
            catalog["crops"] = [] if os.environ.get("E2E_CATALOG") == "empty" else [{
                "id": "test-crop", "name": "Synthetic browser crop", "family": "Test",
                "season_labels": ["maha", "yala", "inter-season"],
                "water_demand_mm_per_cycle": None,
                "sources": [{"url": "https://example.invalid/test-only"}], "review_status": "approved",
            }]
            catalog["status"] = "research_pending" if not catalog["crops"] else "reviewed"
            path = Path(directory) / "test-catalog.json"
            path.write_text(json.dumps(catalog), encoding="utf-8")
            rotations.CATALOG_PATH = path
        try:
            uvicorn.run(app, host="127.0.0.1", port=backend_port)
        finally:
            engine.dispose()


if __name__ == "__main__":
    main()
