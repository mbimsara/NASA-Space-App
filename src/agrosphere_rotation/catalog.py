"""Load the team crop-catalog contract into rotation-engine models."""

import json
from pathlib import Path

from .models import Crop


def load_catalog(path: str | Path) -> tuple[str, tuple[Crop, ...]]:
    document = json.loads(Path(path).read_text(encoding="utf-8"))
    if document.get("schema_version") != "0.1":
        raise ValueError("unsupported crop catalog schema_version")
    version = document.get("catalog_version")
    if not isinstance(version, str) or not version:
        raise ValueError("catalog_version is required")
    status = document.get("status")
    if status not in {"research_pending", "reviewed"}:
        raise ValueError("catalog status must be research_pending or reviewed")

    crops = []
    for record in document.get("crops", []):
        family = record.get("family")
        if family is None:
            raise ValueError(f"crop {record.get('id', '<unknown>')} needs a known family")
        crops.append(
            Crop(
                id=record["id"],
                name=record["name"],
                family=family,
                suitable_seasons=frozenset(record["season_labels"]),
                water_demand_mm=record["water_demand_mm_per_cycle"],
                source_urls=tuple(source["url"] for source in record["sources"]),
                # The catalog-level review is a safety gate. A prematurely
                # approved record cannot become recommendable while the full
                # catalog is still explicitly research-pending.
                review_status=(
                    record["review_status"] if status == "reviewed" else "draft"
                ),
            )
        )
    return version, tuple(crops)
