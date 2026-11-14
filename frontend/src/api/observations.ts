import type { ObservationSummary } from "../types/api";

export type ObservationWire = Omit<ObservationSummary, "spatial_resolution"> & {
  spatial_resolution: string | Record<string, unknown> | null;
  daily?: { date: string; temperature_c: number | null; precipitation_mm_per_day: number | null }[];
};

/** Adapt Dulanjaya's flat observation response into the existing chart view. */
export function observationView(wire: ObservationWire): ObservationSummary {
  let resolution: string | null = null;
  if (typeof wire.spatial_resolution === "string") resolution = wire.spatial_resolution;
  else if (wire.spatial_resolution) {
    const { latitude_degrees: lat, longitude_degrees: lon } = wire.spatial_resolution;
    if (typeof lat === "number" && typeof lon === "number") {
      resolution = `${lat}° latitude × ${lon}° longitude (regional grid)`;
    }
  }
  return {
    ...wire,
    spatial_resolution: resolution,
    time_series: wire.daily ? wire.daily.map(row => ({
      date: row.date,
      rainfall_mm: row.precipitation_mm_per_day,
      mean_temperature_c: row.temperature_c,
    })) : wire.time_series,
  };
}

/** The historical POWER endpoint excludes the current UTC date. */
export function latestHistoricalDate(now = new Date()): string {
  const day = new Date(now);
  day.setUTCDate(day.getUTCDate() - 1);
  return day.toISOString().slice(0, 10);
}
