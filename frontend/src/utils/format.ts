/**
 * Display formatters. Unknown (null/undefined/NaN) values render as the caller's
 * "unknown" label — they are never coerced to 0. Rounding is display-only.
 * Owner: Shehani.
 */

export const isKnown = (v: number | null | undefined): v is number => typeof v === "number" && Number.isFinite(v);

export function fmtNumber(v: number | null | undefined, unknown: string, digits = 0): string {
  return isKnown(v) ? v.toLocaleString(undefined, { maximumFractionDigits: digits, minimumFractionDigits: 0 }) : unknown;
}

export function fmtMm(v: number | null | undefined, unknown: string): string {
  return isKnown(v) ? `${fmtNumber(v, unknown)} mm` : unknown;
}

/** Signed millimetres, e.g. "+12 mm" / "−40 mm". */
export function fmtSignedMm(v: number | null | undefined, unknown: string): string {
  if (!isKnown(v)) return unknown;
  const r = Math.round(v);
  return `${r > 0 ? "+" : r < 0 ? "−" : ""}${Math.abs(r).toLocaleString()} mm`;
}

/** Low–high range; if either end is unknown, the whole range is unknown. */
export function fmtRange(
  low: number | null | undefined,
  high: number | null | undefined,
  unknown: string,
  unit = "",
  signed = false,
): string {
  if (!isKnown(low) || !isKnown(high)) return unknown;
  const f = (n: number) =>
    signed ? fmtSignedMm(n, unknown).replace(" mm", "") : Math.round(n).toLocaleString();
  return `${f(low)} – ${f(high)}${unit ? ` ${unit}` : ""}`;
}

/** Score on the 0–100 scale of rotation-score-0.1 (display rounding only). */
export function fmtScore(v: number | null | undefined, unknown: string): string {
  return isKnown(v) ? fmtNumber(v, unknown, 1) : unknown;
}

/** Weight 0..1 as a percentage. */
export function fmtWeight(v: number | null | undefined, unknown: string): string {
  return isKnown(v) ? `${Math.round(v * 100)}%` : unknown;
}

/** Per-season water records; accepts the per-season array or an older single object. */
export function asSeasonRanges<T>(r: T[] | T | null | undefined): T[] {
  if (r === null || r === undefined) return [];
  return Array.isArray(r) ? r : [r];
}
