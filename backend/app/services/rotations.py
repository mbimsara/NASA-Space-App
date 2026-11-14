"""HTTP-independent adapter to Bhagya's unchanged, pinned rotation engine."""
from dataclasses import asdict
import json
from pathlib import Path
from uuid import uuid4, uuid5, UUID
from datetime import datetime, timezone

from agrosphere_rotation.catalog import load_catalog
from agrosphere_rotation.rotation import generate_candidates
from agrosphere_rotation.scoring import MODEL_VERSION, rank_candidates

ENGINE_COMMIT = "5407f56a2f81615ecaab72a780e0da096ba03f83"
CATALOG_PATH = Path(__file__).resolve().parents[3] / "data/catalogs/crops.json"


def get_rotation_service():
    return RotationService(CATALOG_PATH)


class CatalogVersionError(ValueError):
    pass


class RotationService:
    def __init__(self, catalog_path):
        self.catalog_path = Path(catalog_path)

    def analyze(self, request, profile, observation):
        # Read once; the snapshot and the engine loader must see identical bytes.
        catalog = json.loads(self.catalog_path.read_text(encoding="utf-8"))
        from tempfile import TemporaryDirectory
        with TemporaryDirectory() as directory:
            path = Path(directory) / "catalog.json"
            path.write_text(json.dumps(catalog), encoding="utf-8")
            version, crops = load_catalog(path)
        if version != request.catalog_version:
            raise CatalogVersionError("catalog_version does not match the installed catalog.")
        ids = [crop.id for crop in crops]
        if len(ids) != len(set(ids)):
            raise ValueError("Duplicate catalog IDs")
        reasons = []
        limitations = list(observation["limitations"]) + [
            "No approved mapping from observation dates to crop-season periods is available; water budgets and water-based scores are unavailable.",
            "Effective rainfall, soil recovery and global repeat rules are not approved; none are inferred.",
            "At most 100 feasible sequences are enumerated; ranking is limited to that set.",
        ]
        generated = None
        if request.season_labels is None:
            reasons.append("Explicit season_labels are required to evaluate seasonal eligibility; a season count does not define a calendar.")
        else:
            history = sorted(profile["crop_history"], key=lambda item: item["planted_on"])
            generated = generate_candidates(
                crops, tuple(request.season_labels),
                excluded_crop_ids=frozenset(profile["excluded_crop_ids"]),
                previous_crop_id=history[-1]["crop_id"] if history else None,
            )
            reasons.extend(generated.reasons)
        if not any(crop.review_status == "approved" for crop in crops):
            reasons.append("The catalog has no approved crops available for recommendations.")
        candidates = []
        analysis_id = str(uuid4())
        weights = request.priority_weights.model_dump()
        for candidate in (() if generated is None else generated.candidates):
            # Never reuse a single historical rainfall period across future seasons.
            budgets = (None,) * request.seasons
            score = None
            components = []
            candidate_reasons = list(candidate.reasons)
            if weights["soil"] > 0:
                scored = rank_candidates(((candidate, budgets),), weights)[0]
                score = scored.score
                components = [asdict(component) for component in scored.score_components]
                candidate_reasons.extend(scored.reasons)
            else:
                candidate_reasons.append("No positively weighted score component is available; score is null.")
            candidates.append({
                "candidate_id": str(uuid5(UUID(analysis_id), json.dumps(candidate.crop_ids))),
                "sequence": [{"season_index": i, "crop_id": crop_id} for i, crop_id in enumerate(candidate.crop_ids, 1)],
                "score": score, "score_components": components,
                "water_budget": {"period": "unavailable: crop periods are unspecified", "demand_mm": None,
                    "rainfall_mm": None, "effective_rainfall_mm": None, "irrigation_supply_mm": None,
                    "deficit_mm": None, "unit": "mm", "assumptions": []},
                "water_budget_range": None, "reasons": candidate_reasons,
                "constraint_checks": [asdict(check) for check in candidate.constraint_checks],
            })
        candidates.sort(key=lambda item: (-(item["score"] if item["score"] is not None else -1), tuple(step["crop_id"] for step in item["sequence"])))
        sources = list(dict.fromkeys(observation["source_refs"] + [url for crop in crops if crop.review_status == "approved" for url in crop.source_urls]))
        payload = {"analysis_id": analysis_id, "farm_id": observation["farm_id"],
            "input_version": request.input_version, "observation_id": request.observation_id,
            "catalog_version": version, "model_version": MODEL_VERSION,
            "data_kind": "synthetic" if profile["data_kind"] == "synthetic" or observation["data_kind"] == "synthetic" else "mixed",
            "created_at": datetime.now(timezone.utc).isoformat(), "candidates": candidates,
            "reasons": reasons, "assumptions": ["Only catalog-reviewed and individually approved crops are eligible."],
            "source_refs": sources, "limitations": limitations, "priority_weights": weights}
        return payload, catalog
