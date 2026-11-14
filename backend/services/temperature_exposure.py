"""Explicit threshold exposure based on daily temperature extrema."""
from backend.services.climate import checked_rows, number


def temperature_exposure(observations, hot_at_or_above_c=35, cold_below_c=10):
    number(hot_at_or_above_c, "Hot threshold")
    number(cold_below_c, "Cold threshold")
    if cold_below_c >= hot_at_or_above_c:
        raise ValueError("Cold threshold must be below hot threshold")
    rows = checked_rows(observations)
    highs, lows, longest, current = [], [], 0, 0
    for row in rows:
        high, low = row.get("temperature_max_c"), row.get("temperature_min_c")
        if high is not None:
            highs.append(number(high, "Daily maximum"))
        if low is not None:
            lows.append(number(low, "Daily minimum"))
        if high is not None and low is not None and low > high:
            raise ValueError("Daily minimum exceeds daily maximum")
        current = current + 1 if high is not None and high >= hot_at_or_above_c else 0
        longest = max(longest, current)
    return {
        "kind": "historical_temperature_exposure", "start": rows[0]["date"], "end": rows[-1]["date"],
        "hot_at_or_above_c": hot_at_or_above_c, "cold_below_c": cold_below_c,
        "expected_days": len(rows), "maximum_valid_days": len(highs), "minimum_valid_days": len(lows),
        "hot_days": sum(v >= hot_at_or_above_c for v in highs) if highs else None,
        "cold_nights": sum(v < cold_below_c for v in lows) if lows else None,
        "highest_available_daily_max_c": max(highs) if highs else None,
        "lowest_available_daily_min_c": min(lows) if lows else None,
        "longest_observed_hot_run_days": longest if highs else None,
        "hot_run_is_lower_bound": len(highs) != len(rows),
        "limitations": ["Thresholds are exploratory, not crop-specific stress limits or heatwave definitions.",
                        "Missing maxima break runs; counts describe available days only.",
                        "Cold nights is a label for daily minimum threshold counts, not verified nighttime measurements.",
                        "Daily extrema are gridded source estimates, not field sensor readings."],
    }
