"""Transparent NASA POWER climate similarity calculations."""

import math

from backend.services.climate import number
from backend.services.climate_baseline import compare_monthly


def profile(observations, start_year, end_year):
    if observations.get("time_standard") != "UTC":
        raise ValueError("Climate profiles require UTC histories")
    coordinates = observations["coordinates"]
    if len(coordinates) < 2:
        raise ValueError("Coordinates are required")
    lon, lat = coordinates[:2]
    number(lon, "Longitude"); number(lat, "Latitude")
    if not -180 <= lon <= 180 or not -90 <= lat <= 90:
        raise ValueError("Coordinates out of range")
    monthly = compare_monthly(observations, start_year, end_year, end_year + 1)["monthly"]
    expected = list(range(start_year, end_year + 1))
    if any(item["rain_reference_years"] != expected or item["temperature_reference_years"] != expected for item in monthly):
        raise ValueError("Every reference month must be complete for both variables in every reference year")
    return monthly


def rank_twins(target, candidates, start_year, end_year, rain_scale_mm=100, temperature_scale_c=1):
    """Rank explicitly supplied multi-year histories under configurable scales."""
    number(rain_scale_mm, "Rain scale"); number(temperature_scale_c, "Temperature scale")
    if rain_scale_mm <= 0 or temperature_scale_c <= 0:
        raise ValueError("Distance scales must be positive")
    baseline = profile(target, start_year, end_year)
    ranked, rejected, seen_names, seen_points = [], [], set(), set()
    target_point = tuple(target["coordinates"][:2])
    for candidate in candidates:
        name = candidate["name"]
        if not isinstance(name, str) or not name.strip() or name in seen_names:
            raise ValueError("Candidate names must be nonempty and unique")
        seen_names.add(name)
        observations = candidate["observations"]
        try:
            other = profile(observations, start_year, end_year)
            point = tuple(observations["coordinates"][:2])
            if point == target_point or point in seen_points:
                raise ValueError("Duplicate or target coordinates cannot be a candidate")
            seen_points.add(point)
            if observations["sources"] != target["sources"]:
                raise ValueError("Candidate and target must use matching source products")
            if observations.get("data_kind") != target.get("data_kind"):
                raise ValueError("Synthetic and provider-derived histories cannot be mixed")
            differences = [{"month": left["month"],
                            "rainfall_difference_mm": right["reference_rainfall_mm"] - left["reference_rainfall_mm"],
                            "temperature_difference_c": right["reference_mean_temperature_c"] - left["reference_mean_temperature_c"]}
                           for left, right in zip(baseline, other)]
            rain_rms = math.sqrt(sum(item["rainfall_difference_mm"] ** 2 for item in differences) / 12)
            temp_rms = math.sqrt(sum(item["temperature_difference_c"] ** 2 for item in differences) / 12)
            ranked.append({"name": name, "coordinates": observations["coordinates"],
                           "distance": math.sqrt((rain_rms / rain_scale_mm) ** 2 + (temp_rms / temperature_scale_c) ** 2),
                           "monthly_rainfall_rms_difference_mm": rain_rms,
                           "monthly_temperature_rms_difference_c": temp_rms,
                           "monthly_differences": differences, "source_url": observations.get("source_url"),
                           "retrieved_at": observations.get("retrieved_at")})
        except (ValueError, KeyError, TypeError) as error:
            rejected.append({"name": name, "reason": str(error)})
    ranked.sort(key=lambda item: (item["distance"], item["name"]))
    return {"kind": "experimental_climate_similarity", "reference_years": [start_year, end_year],
            "target_coordinates": target["coordinates"], "target_source_url": target.get("source_url"),
            "target_retrieved_at": target.get("retrieved_at"), "sources": target["sources"],
            "data_kind": target.get("data_kind"), "target_monthly_profile": baseline,
            "scales": {"rainfall_mm": rain_scale_mm, "temperature_c": temperature_scale_c},
            "ranked_candidates": ranked, "rejected_candidates": rejected,
            "limitations": ["Lower distance means more similar under this exploratory metric; it is not a probability or suitability score.",
                            "Only supplied candidates are searched; this is not a global best-match result.",
                            "Monthly means omit extremes, daily variability, soil, terrain, irrigation, economics, and crop constraints.",
                            "Nearby points may share a provider grid cell; rankings are not independent field comparisons.",
                            "No crop transfer recommendation follows from climate similarity alone."]}


def rank_snapshot_twins(target, candidates, limit=5):
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
        distance = math.sqrt((temp_delta / 2.0) ** 2 + (rain_delta / rain_scale) ** 2)
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
