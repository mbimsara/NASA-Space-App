"""Isolated HTTP test server. Never launch against the normal application DB."""
import json
import os
from pathlib import Path
from tempfile import TemporaryDirectory

import uvicorn

if not os.environ.get("DATABASE_URL") or not os.environ.get("INTEGRATION_MODE"):
    raise RuntimeError("Use run_frontend_http.py to allocate an isolated database.")

from app.main import app


if __name__ == "__main__":
    with TemporaryDirectory(prefix="agrosphere-catalog-") as directory:
        if os.environ["INTEGRATION_MODE"] == "synthetic":
            from app.services.observations import get_observation_adapter
            from app.services.rotations import get_rotation_service, RotationService
            from services import nasa_power
            from observation_fixtures import synthetic_observations

            root = Path(__file__).resolve().parents[1]
            raw = json.loads((root / "fixtures/nasa_power.synthetic.json").read_text(encoding="utf-8"))

            def forbidden(*args, **kwargs):
                raise AssertionError("Synthetic HTTP integration must never call NASA.")

            nasa_power.urlopen = forbidden

            class SyntheticAdapter:
                cache_namespace = "isolated-synthetic-http-v1"

                def observe(self, **kwargs):
                    return synthetic_observations(raw)

            path = Path(directory) / "catalog.json"
            path.write_text(json.dumps({
                "schema_version": "0.1", "catalog_version": "integration-synthetic-v1", "status": "reviewed",
                "crops": [{"id": "test-crop", "name": "Synthetic integration crop", "family": "Test",
                    "season_labels": ["maha", "yala"], "water_demand_mm_per_cycle": None,
                    "review_status": "approved", "sources": [{"url": "https://example.invalid/test-only"}]}],
            }), encoding="utf-8")
            app.dependency_overrides[get_observation_adapter] = lambda: SyntheticAdapter()
            app.dependency_overrides[get_rotation_service] = lambda: RotationService(path)
        uvicorn.run(app, host="127.0.0.1", port=8000)
