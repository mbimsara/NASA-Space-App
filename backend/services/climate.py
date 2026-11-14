"""Descriptive historical indicators and hypothetical rainfall scaling.

Thresholds are user-selected exploration settings, not validated crop risk limits.
No drought prediction, crop demand, or yield calculation is performed here.
"""
import math
from datetime import date, timedelta


def number(value, name):
    if type(value) not in (int, float) or not math.isfinite(value):
        raise ValueError(f"{name} must be a finite number")
    return value


def checked_rows(observations):
    if observations.get("provider") != "NASA POWER":
        raise ValueError("Only the configured competition-listed NASA POWER adapter is supported")
    rows = observations["daily"]
    if not rows:
        raise ValueError("Daily series is empty")
    previous = None
    for row in rows:
        day = date.fromisoformat(row["date"])
        if previous is not None and day != previous + timedelta(days=1):
            raise ValueError("Daily series must be chronological and contiguous; represent missing values as null")
        previous = day
        for key in ("temperature_c", "precipitation_mm_per_day"):
            if row[key] is not None:
                number(row[key], key)
        if row["precipitation_mm_per_day"] is not None and row["precipitation_mm_per_day"] < 0:
            raise ValueError("Precipitation cannot be negative")
    return rows


def historical_indicators(observations, dry_below_mm=1.0, warm_at_or_above_c=30.0, rain_at_or_above_mm=20.0):
    """Count threshold events; report observed dry runs as lower bounds if incomplete."""
    for name, value in (("dry threshold", dry_below_mm), ("warm threshold", warm_at_or_above_c), ("rain threshold", rain_at_or_above_mm)):
        number(value, name)
    if dry_below_mm < 0 or rain_at_or_above_mm <= dry_below_mm:
        raise ValueError("Rain threshold must exceed a nonnegative dry threshold")
    rows = checked_rows(observations)
    rain = [r["precipitation_mm_per_day"] for r in rows if r["precipitation_mm_per_day"] is not None]
    temps = [r["temperature_c"] for r in rows if r["temperature_c"] is not None]
    longest = current = 0
    for row in rows:
        value = row["precipitation_mm_per_day"]
        current = current + 1 if value is not None and value < dry_below_mm else 0
        longest = max(longest, current)
    return {
        "kind": "historical_threshold_summary", "start": rows[0]["date"], "end": rows[-1]["date"],
        "thresholds": {"dry_below_mm_per_day": dry_below_mm,
                       "warm_daily_mean_at_or_above_c": warm_at_or_above_c,
                       "rain_at_or_above_mm_per_day": rain_at_or_above_mm},
        "expected_days": len(rows), "rain_valid_days": len(rain), "temperature_valid_days": len(temps),
        "dry_days": sum(v < dry_below_mm for v in rain) if rain else None,
        "warm_daily_mean_days": sum(v >= warm_at_or_above_c for v in temps) if temps else None,
        "high_rain_days": sum(v >= rain_at_or_above_mm for v in rain) if rain else None,
        "longest_observed_dry_run_days": longest if rain else None,
        "dry_run_is_lower_bound": len(rain) != len(rows),
        "limitations": ["Exploratory thresholds, not validated crop risk classifications.",
                        "Daily mean temperature is not maximum temperature or a heatwave measure.",
                        "Unknown rainfall breaks dry runs; incomplete coverage can undercount events.",
                        "One year does not establish climate trends, drought probabilities, or forecasts."],
    }


def rainfall_scenario(observations, change_pct):
    number(change_pct, "Rainfall change")
    if not -100 <= change_pct <= 100:
        raise ValueError("Rainfall change must be between -100 and 100 percent")
    rows = checked_rows(observations)
    factor = 1 + change_pct / 100
    monthly = {}
    daily = []
    for row in rows:
        rain = row["precipitation_mm_per_day"]
        daily.append({"date": row["date"], "baseline_mm_per_day": rain,
                      "scenario_mm_per_day": None if rain is None else round(rain * factor, 6)})
        monthly.setdefault(row["date"][:7], []).append(rain)

    def totals(values):
        valid = [v for v in values if v is not None]
        baseline = sum(valid) if len(valid) == len(values) else None
        return {"expected_days": len(values), "valid_days": len(valid),
                "baseline_rainfall_mm": None if baseline is None else round(baseline, 4),
                "scenario_rainfall_mm": None if baseline is None else round(baseline * factor, 4),
                "difference_mm": None if baseline is None else round(baseline * change_pct / 100, 4)}

    return {
        "kind": "hypothetical_rainfall_scenario", "rainfall_change_pct": change_pct,
        "baseline_source_url": observations.get("source_url"),
        "baseline_retrieved_at": observations.get("retrieved_at"),
        "summary": totals([r["precipitation_mm_per_day"] for r in rows]),
        "monthly": [{"month": month, **totals(values)} for month, values in monthly.items()],
        "daily": daily,
        "assumptions": ["Uniformly scale each available daily rainfall value; preserve missing values and event dates.",
                        "Historical baseline is unchanged. This is not a future weather forecast.",
                        "No effective rainfall, irrigation deficit, soil response, yield or rotation ranking is calculated."],
    }
