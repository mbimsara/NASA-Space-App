"""Load reviewed, comparable seasonal crop-water ranges."""

import json
from pathlib import Path

from .models import WaterDemandRange


def load_water_requirements(path: str | Path) -> tuple[str, dict[str, WaterDemandRange]]:
    document = json.loads(Path(path).read_text(encoding="utf-8"))
    if document.get("schema_version") != "0.1":
        raise ValueError("unsupported water-requirement schema_version")
    if document.get("status") != "reviewed_for_demo":
        raise ValueError("water requirements are not reviewed for demo use")
    basis = document.get("basis")
    version = document.get("model_version")
    source_url = document.get("source", {}).get("url", "")
    requirements = {}
    for item in document.get("requirements", []):
        crop_id = item["crop_id"]
        if crop_id in requirements:
            raise ValueError(f"duplicate water requirement for {crop_id}")
        requirements[crop_id] = WaterDemandRange(
            crop_id=crop_id,
            low_mm=item["low_mm"],
            high_mm=item["high_mm"],
            nominal_mm=item["nominal_mm"],
            basis=basis,
            model_version=version,
            source_url=source_url,
            limitations=tuple(item["limitations"]),
        )
    return version, requirements
