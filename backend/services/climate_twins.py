"""Experimental comparison of permitted, explicitly supplied NASA POWER sites."""
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
    number(lon, "Longitude")
    number(lat, "Latitude")
    if not -180 <= lon <= 180 or not -90 <= lat <= 90:
        raise ValueError("Coordinates out of range")
    # Reuse complete-month aggregation; target metrics are not used here.
    monthly = compare_monthly(observations, start_year, end_year, end_year + 1)["monthly"]
    expected = list(range(start_year, end_year + 1))
    if any(m["rain_reference_years"] != expected or m["temperature_reference_years"] != expected for m in monthly):
        raise ValueError("Every reference month must be complete for both variables in every reference year")
    return monthly


def rank_twins(target, candidates, start_year, end_year, rain_scale_mm=100, temperature_scale_c=1):
    """Distance = sqrt(mean squared rain differences / scale² + mean squared temperature differences / scale²).

    Scaling choices are explicit exploratory settings, not learned or validated weights.
    Candidates are named records: {name, observations}. No automatic global search.
    """
    number(rain_scale_mm, "Rain scale")
    number(temperature_scale_c, "Temperature scale")
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
            differences = [{"month": a["month"],
                            "rainfall_difference_mm": b["reference_rainfall_mm"] - a["reference_rainfall_mm"],
                            "temperature_difference_c": b["reference_mean_temperature_c"] - a["reference_mean_temperature_c"]}
                           for a, b in zip(baseline, other)]
            rain_rms = math.sqrt(sum(d["rainfall_difference_mm"] ** 2 for d in differences) / 12)
            temp_rms = math.sqrt(sum(d["temperature_difference_c"] ** 2 for d in differences) / 12)
            ranked.append({"name": name, "coordinates": observations["coordinates"],
                           "distance": math.sqrt((rain_rms / rain_scale_mm) ** 2 + (temp_rms / temperature_scale_c) ** 2),
                           "monthly_rainfall_rms_difference_mm": rain_rms,
                           "monthly_temperature_rms_difference_c": temp_rms,
                           "monthly_differences": differences,
                           "source_url": observations.get("source_url"), "retrieved_at": observations.get("retrieved_at")})
        except (ValueError, KeyError, TypeError) as error:
            rejected.append({"name": name, "reason": str(error)})
    ranked.sort(key=lambda item: (item["distance"], item["name"]))
    return {
        "kind": "experimental_climate_similarity", "reference_years": [start_year, end_year],
        "target_coordinates": target["coordinates"], "target_source_url": target.get("source_url"),
        "target_retrieved_at": target.get("retrieved_at"), "sources": target["sources"],
        "data_kind": target.get("data_kind"), "target_monthly_profile": baseline,
        "scales": {"rainfall_mm": rain_scale_mm, "temperature_c": temperature_scale_c},
        "ranked_candidates": ranked, "rejected_candidates": rejected,
        "limitations": ["Lower distance means more similar under this exploratory metric; it is not a probability or suitability score.",
                        "Only supplied candidates are searched; this is not a global best-match result.",
                        "Monthly means omit extremes, daily variability, soil, terrain, irrigation, economics, and crop constraints.",
                        "Nearby points may share a provider grid cell; rankings are not independent field comparisons.",
                        "No crop transfer recommendation follows from climate similarity alone."],
    }
