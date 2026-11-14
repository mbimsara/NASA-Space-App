"""Deterministic candidate generation using explicit, reviewable rules."""

from dataclasses import dataclass
from itertools import product

from .models import ConstraintCheck, Crop


@dataclass(frozen=True, slots=True)
class RepeatPolicy:
    """Repeat constraints must be approved before being enabled."""

    forbid_consecutive_crop: bool = False
    forbid_consecutive_family: bool = False


@dataclass(frozen=True, slots=True)
class RotationCandidate:
    crop_ids: tuple[str, ...]
    reasons: tuple[str, ...]
    constraint_checks: tuple[ConstraintCheck, ...]


@dataclass(frozen=True, slots=True)
class RejectedSequence:
    crop_ids: tuple[str, ...]
    constraint_checks: tuple[ConstraintCheck, ...]


@dataclass(frozen=True, slots=True)
class CandidateGenerationResult:
    candidates: tuple[RotationCandidate, ...]
    reasons: tuple[str, ...]
    rejected: tuple[RejectedSequence, ...] = ()


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
    rejected_sequences = []
    for sequence in product(*eligible_by_season):
        chain = ((crop_by_id.get(previous_crop_id),) if previous_crop_id else ()) + sequence
        valid_chain = tuple(crop for crop in chain if crop is not None)
        failed_check = None
        checks = [
            ConstraintCheck("catalog_review", True, "Every crop is approved."),
            ConstraintCheck("season_eligibility", True, "Every crop matches its requested season."),
            ConstraintCheck("farmer_exclusion", True, "No crop is farmer-excluded."),
        ]

        for left, right in zip(valid_chain, valid_chain[1:]):
            if repeat_policy.forbid_consecutive_crop and left.id == right.id:
                failed_check = ConstraintCheck(
                    "consecutive_crop",
                    False,
                    f"Crop '{right.id}' repeats consecutively.",
                )
                break
            if repeat_policy.forbid_consecutive_family and left.family == right.family:
                failed_check = ConstraintCheck(
                    "consecutive_family",
                    False,
                    f"Family '{right.family}' repeats consecutively.",
                )
                break
        if failed_check is not None:
            rejected_sequences.append(
                RejectedSequence(
                    crop_ids=tuple(crop.id for crop in sequence),
                    constraint_checks=tuple(checks + [failed_check]),
                )
            )
            continue

        if repeat_policy.forbid_consecutive_crop:
            checks.append(
                ConstraintCheck(
                    "consecutive_crop",
                    True,
                    "No consecutive crop repetition under the enabled policy.",
                )
            )
        if repeat_policy.forbid_consecutive_family:
            checks.append(
                ConstraintCheck(
                    "consecutive_family",
                    True,
                    "No consecutive crop-family repetition under the enabled policy.",
                )
            )
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
    return CandidateGenerationResult(
        candidates=tuple(candidates),
        reasons=tuple(reasons),
        rejected=tuple(rejected_sequences),
    )
