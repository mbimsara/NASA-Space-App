/**
 * Helpers for Matheesha's normalized observation shape as served by
 * Dulanjaya's GET /farms/{id}/observations. Owner: Shehani.
 */
import type { ObservationSummary, TimeSeriesPoint } from "../types/api";

/** NASA POWER history starts here (backend rejects earlier dates). */
export const OBSERVATION_MIN_DATE = "1981-01-01";

/** YYYY-MM-DD in UTC, offset by whole days. The backend requires end < today (UTC). */
export function utcDate(offsetDays = 0, now: Date = new Date()): string {
  const d = new Date(Date.UTC(now.getUTCFullYear(), now.getUTCMonth(), now.getUTCDate() + offsetDays));
  return d.toISOString().slice(0, 10);
}

export const latestAllowedEnd = (now?: Date) => utcDate(-1, now);

export function defaultObservationRange(now?: Date) {
  return { start: utcDate(-30, now), end: utcDate(-1, now) };
}

export function isValidObservationRange(start: string, end: string, now?: Date): boolean {
  return !!start && !!end && start >= OBSERVATION_MIN_DATE && start <= end && end <= latestAllowedEnd(now);
}

/** Chart points from `daily[]` (live) or legacy `time_series[]` (old fixtures). Nulls stay null. */
export function toChartPoints(obs: Pick<ObservationSummary, "daily" | "time_series">): TimeSeriesPoint[] {
  if (obs.daily && obs.daily.length > 0) {
    return obs.daily.map((d) => ({
      date: d.date,
      rainfall_mm: d.precipitation_mm_per_day,
      mean_temperature_c: d.temperature_c,
    }));
  }
  return obs.time_series ?? [];
}

/** Render a resolution object (or legacy string) as readable text, never "[object Object]". */
export function formatResolution(res: ObservationSummary["spatial_resolution"]): string | null {
  if (res === null || res === undefined) return null;
  if (typeof res === "string") return res.trim() || null;
  const parts = Object.entries(res)
    .filter(([, v]) => v !== null && v !== undefined && v !== "")
    .map(([k, v]) => `${k.replace(/_/g, " ")}: ${typeof v === "object" ? JSON.stringify(v) : String(v)}`);
  return parts.length > 0 ? parts.join(", ") : null;
}
