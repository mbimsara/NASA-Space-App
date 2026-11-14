/**
 * Zod validation schemas for the farm form (zod v4).
 * These mirror data/schemas/farm.schema.json v0.1 and add human-readable messages.
 * Owner: Shehani. Server validation (Dulanjaya) remains authoritative.
 *
 * Rules:
 * - Unknown values are `null` (irrigation) or omitted (soil tests) — never 0.
 * - Area must be positive and is always hectares internally.
 * - Dates are YYYY-MM-DD; harvest on/after planting; planting not in the future.
 */
import { z } from "zod";

const ISO_DATE = /^\d{4}-\d{2}-\d{2}$/;

/** True when `s` is a real calendar date written as YYYY-MM-DD. */
export function isIsoDate(s: string): boolean {
  if (!ISO_DATE.test(s)) return false;
  const d = new Date(`${s}T00:00:00Z`);
  return !Number.isNaN(d.getTime()) && d.toISOString().slice(0, 10) === s;
}

export function todayIso(now: Date = new Date()): string {
  const y = now.getFullYear();
  const m = String(now.getMonth() + 1).padStart(2, "0");
  const d = String(now.getDate()).padStart(2, "0");
  return `${y}-${m}-${d}`;
}

const isoDate = z.string().refine(isIsoDate, { message: "Date must be a valid YYYY-MM-DD date" });

const finiteNumber = (label: string) =>
  z.number({ error: `${label} is required` }).refine(Number.isFinite, { message: `${label} is required` });

export const locationSchema = z.object({
  latitude: finiteNumber("Latitude").pipe(
    z.number().min(-90, "Latitude must be ≥ −90").max(90, "Latitude must be ≤ 90"),
  ),
  longitude: finiteNumber("Longitude").pipe(
    z.number().min(-180, "Longitude must be ≥ −180").max(180, "Longitude must be ≤ 180"),
  ),
});

export const cropHistoryEntrySchema = z
  .object({
    crop_id: z.string().trim().min(1, "Crop is required"),
    planted_on: isoDate.refine((d) => d <= todayIso(), { message: "Planting date cannot be in the future" }),
    harvested_on: z.union([isoDate, z.null()]),
  })
  .refine((d) => !d.harvested_on || d.planted_on <= d.harvested_on, {
    message: "Harvest date must be on or after planting date",
    path: ["harvested_on"],
  });

export const soilTestEntrySchema = z.object({
  metric: z.string().trim().min(1, "Metric name is required"),
  // Unknown soil values are omitted from the array, never entered as 0.
  value: finiteNumber("Value"),
  unit: z.string().trim().min(1, "Unit is required (e.g. pH, mg/kg)"),
  sampled_on: isoDate.refine((d) => d <= todayIso(), { message: "Sample date cannot be in the future" }),
});

export const priorityWeightsSchema = z
  .object({
    water: z.number().min(0, "Must be ≥ 0"),
    soil: z.number().min(0, "Must be ≥ 0"),
    climate: z.number().min(0, "Must be ≥ 0"),
  })
  .refine((w) => w.water + w.soil + w.climate > 0, {
    message: "At least one priority weight must be greater than zero",
  });

export const farmFormSchema = z.object({
  name: z.string().trim().min(1, "Farm name is required"),
  location: locationSchema,
  area_ha: finiteNumber("Area").pipe(z.number().positive("Area must be greater than zero")),
  // null means irrigation supply is unknown — do NOT default to 0
  irrigation_supply_mm_per_season: z.number().min(0, "Must be ≥ 0").nullable(),
  crop_history: z.array(cropHistoryEntrySchema),
  soil_tests: z.array(soilTestEntrySchema),
  priority_weights: priorityWeightsSchema,
  excluded_crop_ids: z.array(z.string().trim().min(1)),
});

export type FarmFormValues = z.infer<typeof farmFormSchema>;

/** Flatten zod issues into `{ "location.latitude": "message" }` (first message per path wins). */
export function fieldErrors(error: z.ZodError): Record<string, string> {
  const out: Record<string, string> = {};
  for (const issue of error.issues) {
    const key = issue.path.map(String).join(".");
    if (!(key in out)) out[key] = issue.message;
  }
  return out;
}

/** Normalize priority weights to sum to 1 (server also normalizes and returns effective weights). */
export function normalizeWeights(w: { water: number; soil: number; climate: number }) {
  const total = w.water + w.soil + w.climate;
  if (!(total > 0)) return { ...w };
  const r = (n: number) => Math.round((n / total) * 1000) / 1000;
  return { water: r(w.water), soil: r(w.soil), climate: r(w.climate) };
}
