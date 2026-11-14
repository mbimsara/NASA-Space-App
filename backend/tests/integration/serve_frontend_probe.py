"""Synthetic-only test launcher, adapted from the legacy branch to canonical main."""
import json
import os
from pathlib import Path

if os.environ.get("AGROSPHERE_FRONTEND_PROBE") != "1" or not os.environ.get("DATABASE_URL"):
    raise RuntimeError("Use run_frontend_probe.py to allocate a disposable database.")

from app.main import app
from app.services import rotations
from app.services.observations import get_observation_adapter
from observation_fixtures import synthetic_observations
from services import nasa_power
import uvicorn


def main():
    root = Path(__file__).resolve().parents[3]
    raw = json.loads((root / "backend/tests/fixtures/nasa_power.synthetic.json").read_text(encoding="utf-8"))

    def forbidden(*args, **kwargs):
        raise AssertionError("Offline frontend HTTP probe must not call NASA.")

    nasa_power.urlopen = forbidden

    class Adapter:
        cache_namespace = "canonical-synthetic-frontend-probe-v1"

        def observe(self, *, start, end, **kwargs):
            return synthetic_observations(raw, start=start.isoformat(), end=end.isoformat())

    app.dependency_overrides[get_observation_adapter] = lambda: Adapter()
    # Reuse the current version, but never approve or edit original crop entries.
    catalog = json.loads((root / "data/catalogs/crops.json").read_text(encoding="utf-8"))
    catalog["status"] = "reviewed"
    catalog["crops"] = [{
        "id": "probe-crop", "name": "Synthetic browser crop", "family": "Test",
        "season_labels": ["maha", "yala"], "water_demand_mm_per_cycle": None,
        "sources": [{"url": "https://example.invalid/synthetic-probe-only"}], "review_status": "approved",
    }]
    path = Path(os.environ["AGROSPHERE_PROBE_DIRECTORY"]) / "synthetic-catalog.json"
    path.write_text(json.dumps(catalog), encoding="utf-8")
    rotations.CATALOG_PATH = path
    try:
        uvicorn.run(app, host="127.0.0.1", port=8000)
    finally:
        from app.database.connection import engine
        engine.dispose()


if __name__ == "__main__":
    main()
