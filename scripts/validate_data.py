"""Validate the subset of JSON Schema used by shared repository fixtures.

Standard library only; not a general JSON Schema implementation.
"""
import json
import math
from datetime import date
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]


def require(condition, message):
    if not condition:
        raise ValueError(message)


def validate(value, schema, path="$"):
    kinds = {
        "object": lambda v: isinstance(v, dict),
        "array": lambda v: isinstance(v, list),
        "string": lambda v: isinstance(v, str),
        "number": lambda v: type(v) in (int, float) and math.isfinite(v),
        "null": lambda v: v is None,
    }
    if "type" in schema:
        allowed = schema["type"]
        allowed = [allowed] if isinstance(allowed, str) else allowed
        require(any(kinds[k](value) for k in allowed), f"{path}: invalid type")
    if "const" in schema:
        require(value == schema["const"], f"{path}: incorrect version/value")
    if "enum" in schema:
        require(value in schema["enum"], f"{path}: unsupported value")
    if isinstance(value, dict):
        require(set(schema.get("required", [])) <= value.keys(), f"{path}: missing fields")
        properties = schema.get("properties", {})
        if schema.get("additionalProperties") is False:
            require(value.keys() <= properties.keys(), f"{path}: unexpected fields")
        for key, item in value.items():
            if key in properties:
                validate(item, properties[key], f"{path}.{key}")
    elif isinstance(value, list):
        if schema.get("uniqueItems"):
            require(len({json.dumps(v, sort_keys=True) for v in value}) == len(value), f"{path}: duplicate items")
        for index, item in enumerate(value):
            validate(item, schema.get("items", {}), f"{path}[{index}]")
    elif isinstance(value, str):
        require(len(value.strip()) >= schema.get("minLength", 0), f"{path}: empty string")
        if schema.get("format") == "date":
            require(date.fromisoformat(value).isoformat() == value, f"{path}: use YYYY-MM-DD")
        if schema.get("format") == "uri":
            parsed = urlparse(value)
            require(parsed.scheme in ("http", "https") and bool(parsed.netloc), f"{path}: invalid source URL")
    elif type(value) in (int, float):
        if "minimum" in schema:
            require(value >= schema["minimum"], f"{path}: below minimum")
        if "maximum" in schema:
            require(value <= schema["maximum"], f"{path}: above maximum")
        if "exclusiveMinimum" in schema:
            require(value > schema["exclusiveMinimum"], f"{path}: must exceed minimum")


def load(relative):
    return json.loads((ROOT / relative).read_text(encoding="utf-8"))


def main():
    farm = load("data/fixtures/farm.synthetic.json")
    catalog = load("data/catalogs/crops.json")
    water = load("data/catalogs/crop-water-requirements.json")
    validate(farm, load("data/schemas/farm.schema.json"), "farm")
    validate(catalog, load("data/schemas/crop-catalog.schema.json"), "catalog")
    validate(
        water,
        load("data/schemas/crop-water-requirements.schema.json"),
        "crop_water_requirements",
    )
    require(farm["data_kind"] == "synthetic", "Demo fixture must remain synthetic")
    require(sum(farm["priority_weights"].values()) > 0, "Priority weights need a positive total")
    for entry in farm["crop_history"]:
        if entry["harvested_on"] is not None:
            require(entry["harvested_on"] >= entry["planted_on"], "Harvest precedes planting")
    ids = [crop["id"] for crop in catalog["crops"]]
    require(len(ids) == len(set(ids)), "Duplicate crop IDs")
    for crop in catalog["crops"]:
        if crop["review_status"] == "approved":
            require(bool(crop["sources"]) and bool(crop["season_labels"]), "Approved crops need sources and seasons")
            require(crop["family"] is not None, "Approved crops need a reviewed family")
    if catalog["status"] == "reviewed":
        require(bool(ids) and all(c["review_status"] == "approved" for c in catalog["crops"]), "Reviewed catalog needs approved crops")
    water_ids = [item["crop_id"] for item in water["requirements"]]
    require(len(water_ids) == len(set(water_ids)), "Duplicate crop-water requirement IDs")
    require(set(water_ids) <= set(ids), "Crop-water requirement references an unknown crop")
    for item in water["requirements"]:
        require(
            item["low_mm"] <= item["nominal_mm"] <= item["high_mm"],
            f"Invalid crop-water range for {item['crop_id']}",
        )
    print("PASS: farm, crop catalog, and crop-water requirements satisfy current contracts.")
    if not ids:
        print("NOTE: catalog is empty; research and approval are required before recommendations.")


if __name__ == "__main__":
    main()
