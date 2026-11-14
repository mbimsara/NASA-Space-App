"""Generate small, explicitly synthetic team fixtures; no network requests."""
import json
from pathlib import Path
from backend.services.nasa_power import normalize
from backend.services.climate_handoff import climate_bundle, season_inputs

ROOT = Path(__file__).resolve().parents[1]


def main():
    raw = {
        "header": {"start": "20250101", "end": "20250107", "time_standard": "UTC",
                   "fill_value": -999, "sources": ["synthetic-team-fixture"], "api": {"name": "Synthetic example", "version": "test"}},
        "geometry": {"coordinates": [80.4, 8.3]},
        "parameters": {"T2M": {"units": "C"}, "PRECTOTCORR": {"units": "mm/day"}},
        "properties": {"parameter": {
            "T2M": {f"202501{day:02}": value for day, value in enumerate([25, 26, 30, 28, 27, 25, 24], 1)},
            "PRECTOTCORR": {f"202501{day:02}": value for day, value in enumerate([0, 0, 5, 20, 0, 10, 0], 1)},
        }},
    }
    observations = normalize(raw, "2025-01-01", "2025-01-07")
    observations["data_kind"] = "synthetic"
    observations["limitations"].insert(0, "Invented values for development; not NASA observations or farm advice.")
    bundle = climate_bundle(observations, "farm-synthetic-001", "obs-synthetic-001", 1)
    bundle["season_inputs"] = season_inputs(observations, "2025-01-01", "2025-01-07")
    path = ROOT / "data/fixtures/climate-bundle.synthetic.json"
    path.write_text(json.dumps(bundle, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    print(f"Generated {path.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
