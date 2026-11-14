"""Report ranking dependence on explicit scales; no calibrated risk claims."""
import math
from backend.services.climate import number


def sensitivity(ranking, settings):
    if not settings:
        raise ValueError("Supply at least one scale setting")
    candidates = ranking["ranked_candidates"]
    if len({item["name"] for item in candidates}) != len(candidates):
        raise ValueError("Candidate names must be unique")
    trials = []
    for setting in settings:
        rain, temp = setting["rainfall_mm"], setting["temperature_c"]
        number(rain, "Rainfall scale")
        number(temp, "Temperature scale")
        if rain <= 0 or temp <= 0:
            raise ValueError("Scales must be positive")
        scores = []
        for item in candidates:
            r, t = item["monthly_rainfall_rms_difference_mm"], item["monthly_temperature_rms_difference_c"]
            number(r, "Rainfall RMS")
            number(t, "Temperature RMS")
            if r < 0 or t < 0:
                raise ValueError("RMS differences cannot be negative")
            scores.append({"name": item["name"], "distance": math.hypot(r / rain, t / temp)})
        scores.sort(key=lambda item: (item["distance"], item["name"]))
        best = scores[0]["distance"] if scores else None
        winners = [item["name"] for item in scores if math.isclose(item["distance"], best, rel_tol=1e-9, abs_tol=1e-12)]
        trials.append({"scales": dict(setting), "ranking": scores, "tied_best_candidates": winners})
    winner_sets = {tuple(trial["tied_best_candidates"]) for trial in trials}
    return {"kind": "experimental_twin_scale_sensitivity", "trials": trials,
            "best_set_unchanged_in_tested_settings": len(winner_sets) == 1 if candidates else None,
            "reference_years": ranking["reference_years"],
            "limitations": ["Stability applies only to supplied candidates and tested settings, not global robustness.",
                            "Ties are reported explicitly; alphabetical display order is not evidence of superiority.",
                            "Scale sensitivity does not validate the metric or establish crop suitability."]}
