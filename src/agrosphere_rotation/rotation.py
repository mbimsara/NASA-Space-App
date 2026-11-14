"""Deterministic candidate generation using explicit, reviewable rules."""

from dataclasses import dataclass
from itertools import product

from .models import Crop


@dataclass(frozen=True, slots=True)
class RepeatPolicy:
    """Repeat constraints must be approved before being enabled."""

    forbid_consecutive_crop: bool = False
    forbid_consecutive_family: bool = False


@dataclass(frozen=True, slots=True)
class RotationCandidate:
    crop_ids: tuple[str, ...]
    reasons: tuple[str, ...]
    constraint_checks: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class CandidateGenerationResult:
    candidates: tuple[RotationCandidate, ...]
    reasons: tuple[str, ...]


def generate_candidates(
    crops: tuple[Crop, ...],
    seasons: tuple[str, ...],
    *,
    excluded_crop_ids: frozenset[str] = frozenset(),
    previous_crop_id: str | None = None,
    repeat_policy: RepeatPolicy = RepeatPolicy(),
    limit: int = 100,
) -> CandidateGenerationResult:
    """Generate feasible sequences before any ranking is applied."""

    if not 3 <= len(seasons) <= 5:
        raise ValueError("rotations must contain three to five seasons")
    if limit <= 0:
        raise ValueError("limit must be positive")

    approved = tuple(crop for crop in crops if crop.review_status == "approved")
    crop_by_id = {crop.id: crop for crop in approved}
    eligible_by_season = []
    reasons = []

    for season in seasons:
        eligible = tuple(
            crop
            for crop in approved
            if crop.id not in excluded_crop_ids and season in crop.suitable_seasons
        )
        eligible_by_season.append(eligible)
        if not eligible:
            reasons.append(f"No approved, non-excluded crop is eligible for season '{season}'.")

    if reasons:
        return CandidateGenerationResult(candidates=(), reasons=tuple(reasons))

    candidates = []
    for sequence in product(*eligible_by_season):
        chain = ((crop_by_id.get(previous_crop_id),) if previous_crop_id else ()) + sequence
        valid_chain = tuple(crop for crop in chain if crop is not None)
        rejected = False
        checks = ["All crops are approved, season-eligible, and not farmer-excluded."]

        for left, right in zip(valid_chain, valid_chain[1:]):
            if repeat_policy.forbid_consecutive_crop and left.id == right.id:
                rejected = True
                break
            if repeat_policy.forbid_consecutive_family and left.family == right.family:
                rejected = True
                break
        if rejected:
            continue

        if repeat_policy.forbid_consecutive_crop:
            checks.append("No consecutive crop repetition under the configured policy.")
        if repeat_policy.forbid_consecutive_family:
            checks.append("No consecutive crop-family repetition under the configured policy.")
        candidates.append(
            RotationCandidate(
                crop_ids=tuple(crop.id for crop in sequence),
                reasons=("Feasible under the currently enabled documented constraints.",),
                constraint_checks=tuple(checks),
            )
        )
        if len(candidates) >= limit:
            break

    if not candidates:
        reasons.append("No sequence satisfies the configured repeat policy.")
    return CandidateGenerationResult(candidates=tuple(candidates), reasons=tuple(reasons))

