"""Monthly historical reference means, using complete months only."""
from calendar import monthrange
from datetime import date
try:
    from backend.services.climate import checked_rows
except ModuleNotFoundError:
    from services.climate import checked_rows


def compare_monthly(observations, reference_start_year, reference_end_year, target_year):
    if any(type(v) is not int for v in (reference_start_year, reference_end_year, target_year)):
        raise ValueError("Years must be integers")
    if reference_start_year > reference_end_year or reference_end_year - reference_start_year < 1:
        raise ValueError("Reference must span at least two years")
    if reference_start_year <= target_year <= reference_end_year:
        raise ValueError("Target year must be outside the reference period")
    rows = checked_rows(observations)
    groups = {}
    for row in rows:
        day = date.fromisoformat(row["date"])
        groups.setdefault((day.year, day.month), []).append(row)

    def metrics(year, month):
        group = groups.get((year, month), [])
        expected = monthrange(year, month)[1]
        # Contiguity is validated globally; reject truncated first/last months.
        full = len(group) == expected
        rain = [r["precipitation_mm_per_day"] for r in group if r["precipitation_mm_per_day"] is not None]
        temps = [r["temperature_c"] for r in group if r["temperature_c"] is not None]
        return (sum(rain) if full and len(rain) == expected else None,
                sum(temps) / expected if full and len(temps) == expected else None)

    comparisons = []
    for month in range(1, 13):
        refs = [(year, metrics(year, month)) for year in range(reference_start_year, reference_end_year + 1)]
        rain_years = [year for year, values in refs if values[0] is not None]
        temp_years = [year for year, values in refs if values[1] is not None]
        rain_values = [values[0] for _, values in refs if values[0] is not None]
        temp_values = [values[1] for _, values in refs if values[1] is not None]
        # At least two valid years per variable; return actual contributing years.
        rain_mean = sum(rain_values) / len(rain_values) if len(rain_values) >= 2 else None
        temp_mean = sum(temp_values) / len(temp_values) if len(temp_values) >= 2 else None
        target_rain, target_temp = metrics(target_year, month)
        comparisons.append({
            "month": month, "rain_reference_years": rain_years, "temperature_reference_years": temp_years,
            "reference_rainfall_mm": rain_mean, "reference_mean_temperature_c": temp_mean,
            "target_rainfall_mm": target_rain, "target_mean_temperature_c": target_temp,
            "rainfall_difference_pct": (100 * (target_rain - rain_mean) / rain_mean
                                        if target_rain is not None and rain_mean is not None and rain_mean > 0 else None),
            "temperature_difference_c": (target_temp - temp_mean if target_temp is not None and temp_mean is not None else None),
        })
    return {
        "kind": "monthly_historical_comparison", "reference_start_year": reference_start_year,
        "reference_end_year": reference_end_year, "target_year": target_year,
        "source_url": observations.get("source_url"), "retrieved_at": observations.get("retrieved_at"),
        "monthly": comparisons,
        "limitations": ["Descriptive reference averages, not an official climate normal or a forecast.",
                        "Only complete calendar months contribute, independently for each variable.",
                        "Reference means weight each contributing year equally; inspect contributing year lists.",
                        "Zero reference rainfall has undefined percentage change and returns null.",
                        "Differences alone do not establish climate trends or crop risk."],
    }
