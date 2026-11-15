"""Transparent similarity ranking for complete, same-period POWER summaries."""

from math import sqrt


def rank_twins(target, candidates, limit=5):
    if type(limit) is not int or not 1 <= limit <= 20:
        raise ValueError("limit must be 1..20")
    period = target["period"]
    target_rain = target["summary"].get("rainfall_total_mm")
    target_temp = target["summary"].get("mean_temperature_c")
    if target_rain is None or target_temp is None:
        raise ValueError("Target requires complete rainfall and available temperature")
    ranked, excluded = [], []
    for candidate in candidates:
        reason = None
        if candidate.get("period") != period:
            reason = "period_mismatch"
        elif candidate.get("farm_id") == target.get("farm_id"):
            reason = "same_farm"
        else:
            rain = candidate.get("summary", {}).get("rainfall_total_mm")
            temp = candidate.get("summary", {}).get("mean_temperature_c")
            if rain is None or temp is None:
                reason = "incomplete_climate_summary"
        if reason:
            excluded.append({"observation_id": candidate.get("observation_id"), "reason": reason})
            continue
        # Scale components to interpretable differences: 2 C and 50% of the
        # target period rainfall each contribute one distance unit.
        rain_scale = max(abs(target_rain) * 0.5, 25.0)
        rain_delta = rain - target_rain
        temp_delta = temp - target_temp
        distance = sqrt((temp_delta / 2.0) ** 2 + (rain_delta / rain_scale) ** 2)
        ranked.append({
            "farm_id": candidate["farm_id"], "observation_id": candidate["observation_id"],
            "input_version": candidate["input_version"],
            "requested_location": candidate["requested_location"],
            "mean_temperature_c": temp, "rainfall_total_mm": rain,
            "temperature_difference_c": temp_delta, "rainfall_difference_mm": rain_delta,
            "similarity_score": round(100 / (1 + distance), 2),
        })
    ranked.sort(key=lambda item: (-item["similarity_score"], item["farm_id"]))
    return ranked[:limit], excluded
