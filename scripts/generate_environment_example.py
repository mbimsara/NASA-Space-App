"""Create a small reproducible synthetic integration payload, without network."""
import json
from pathlib import Path
from backend.services.environment import build_environment

ROOT = Path(__file__).resolve().parents[1]


def main():
    power = json.loads((ROOT / "data/fixtures/climate-bundle.synthetic.json").read_text(encoding="utf-8"))["observation"]
    power["sources"] = power["source_refs"]
    unknown = {"accepted": False, "soil_moisture_m3_m3": None, "rejection_reason": "synthetic_missing_pass"}
    smap = {
        "kind": "smap_surface_soil_moisture_series", "product": "SPL3SMP_E", "version": "006", "data_kind": "synthetic",
        "units": "m3/m3", "requested_point": {"latitude": 8.3, "longitude": 80.4},
        "period": {"start": "2025-01-01", "end": "2025-01-01"},
        "coverage": {"expected_days": 1, "supplied_granule_days": 1, "accepted_AM": 0, "accepted_PM": 1},
        "daily": [{"date": "2025-01-01", "granule_supplied": True, "AM": dict(unknown),
                   "PM": {"accepted": True, "soil_moisture_m3_m3": 0.25, "retrieval_quality_flag": 8,
                          "distance_km": 4, "rejection_reason": None}}],
        "provenance": [], "limitations": ["Invented integration example, not NASA observations or a real farm."],
    }
    result = build_environment(power, "farm-synthetic-001", "environment-synthetic-001", 1, smap)
    path = ROOT / "data/fixtures/environment.synthetic.json"
    path.write_text(json.dumps(result, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    print(f"Generated {path.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
