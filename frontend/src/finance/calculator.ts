/**
 * Deterministic cost / revenue range calculator.
 * Owner: Shehani (implementation). Reviewer: Bhagya.
 *
 * Specification v0.1 — docs/FINANCIAL_SPECIFICATION.md (Bhagya, reviewed 2026-11-14,
 * commit 9a6425a on branch zerokali20). Formula status: approved with implementation
 * conditions. Input-data status: pending sourced local values.
 *
 * Approved formulas (A = area in ha; C_i = cost ranges per ha per cycle;
 * Y = yield scenario range in kg/ha per cycle; P = farm-gate price range in currency/kg):
 *   cost    = [A × ΣC_i_low,  A × ΣC_i_high]
 *   revenue = [A × Y_low × P_low,  A × Y_high × P_high]
 *   net     = [revenue_low − cost_high,  revenue_high − cost_low]   (conservative interval arithmetic)
 *   break-even price = [cost_low / (A × Y_high),  cost_high / (A × Y_low)]  (unknown if Y_low = 0)
 * Area: 1 acre = 0.40468564224 ha; 1 perch = 1/160 acre.
 *
 * Implementation conditions honoured here:
 * - No rounding during calculation (`roundMoney` is for display only).
 * - A range is complete or unknown; unknown stays null and never becomes zero.
 * - Unknown cost category → cost and net unknown. Unknown yield or price → revenue and net unknown.
 * - Negative net is reported as is (never clamped).
 * - Every known input links to its own source record(s) with URL/document provenance.
 * - Omitted standard cost categories are disclosed, not treated as zero.
 */

export type AreaUnit = "ha" | "acre" | "perch";

export const HECTARES_PER: Record<AreaUnit, number> = {
  ha: 1,
  acre: 0.40468564224,
  perch: 0.40468564224 / 160,
};

export const FINANCE_SPEC_VERSION = "0.1";
export const FINANCE_SPEC_REFERENCE = "docs/FINANCIAL_SPECIFICATION.md";

/** Cost categories the interface prompts for (FINANCIAL_SPECIFICATION.md → required cost categories). */
export const STANDARD_COST_CATEGORIES = [
  { key: "seed", name: "Seed / planting material" },
  { key: "land_preparation", name: "Land preparation" },
  { key: "fertilizer", name: "Fertilizer and soil amendments" },
  { key: "crop_protection", name: "Crop protection" },
  { key: "irrigation_energy", name: "Irrigation / energy" },
  { key: "hired_labour", name: "Hired labour" },
  { key: "machinery", name: "Machinery" },
  { key: "harvest_post_harvest", name: "Harvest / post-harvest" },
  { key: "transport", name: "Transport" },
  { key: "other", name: "Other costs" },
] as const;

export type StandardCostKey = (typeof STANDARD_COST_CATEGORIES)[number]["key"];

export interface Range {
  low: number;
  high: number;
}

export interface NullableRange {
  low: number | null;
  high: number | null;
}

export type SourceKind = "farmer_entered" | "observed" | "researched" | "synthetic";

/** Provenance record. Inputs reference these by `id`. */
export interface SourceRecord {
  id: string;
  label: string;
  /** http(s) URL or a document reference (e.g. "DOA price bulletin No. 12, p. 4"). */
  reference: string;
  /** YYYY-MM-DD the value was quoted/observed. */
  quoted_on: string;
  /** YYYY-MM-DD the source was accessed. */
  accessed_on: string;
  /** Geographic market or production area. */
  area: string;
  /** Crop / variety / grade, where relevant. */
  crop_variety_grade: string;
  /** Unit and period as stated by the source, e.g. "LKR/kg, Yala 2026". */
  unit_period: string;
  kind: SourceKind;
}

export interface CostCategory {
  /** Standard category key, or null for a custom category. */
  key: StandardCostKey | null;
  name: string;
  /** Cost per hectare for one cycle, in `currency`. */
  per_ha: NullableRange;
  source_ids: string[];
}

export interface FinanceInput {
  currency: string;
  area: { value: number; unit: AreaUnit };
  crop_label: string;
  costs: CostCategory[];
  /** Yield scenario range, kg per hectare per cycle. */
  yield_kg_per_ha: NullableRange;
  yield_source_ids: string[];
  /** Farm-gate price range, currency per kg. */
  price_per_kg: NullableRange;
  price_source_ids: string[];
  sources: SourceRecord[];
}

export interface FinanceResult {
  spec_version: string;
  currency: string;
  area_ha: number;
  cost: Range | null;
  revenue: Range | null;
  net: Range | null;
  break_even_price_per_kg: Range | null;
  assumptions: string[];
  /** Unknown inputs and why dependent results are unknown. */
  unknowns: string[];
  /** Standard cost categories not entered at all (disclosed, never assumed zero). */
  omitted_categories: string[];
  /** Data limitations to show beside the results. */
  limitations: string[];
  /** True when any referenced source is synthetic. */
  uses_synthetic: boolean;
}

export interface FinanceOutcome {
  ok: boolean;
  errors: Record<string, string>;
  result: FinanceResult | null;
}

export function toHectares(value: number, unit: AreaUnit): number {
  return value * HECTARES_PER[unit];
}

export function roundMoney(n: number): number {
  return Math.round(n);
}

function isIsoDate(s: string) {
  if (!/^\d{4}-\d{2}-\d{2}$/.test(s)) return false;
  const d = new Date(`${s}T00:00:00Z`);
  return !Number.isNaN(d.getTime()) && d.toISOString().slice(0, 10) === s;
}

/** A reference is valid if it is an http(s) URL, or non-URL text naming a document. */
export function isValidReference(ref: string): boolean {
  const r = ref.trim();
  if (!r) return false;
  if (/^[a-z][a-z0-9+.-]*:\/\//i.test(r)) {
    try {
      const u = new URL(r);
      return (u.protocol === "http:" || u.protocol === "https:") && u.host.length > 0;
    } catch {
      return false;
    }
  }
  return r.length >= 3;
}

const SOURCE_KINDS: SourceKind[] = ["farmer_entered", "observed", "researched", "synthetic"];

function checkRange(r: NullableRange, key: string, errors: Record<string, string>): boolean {
  const bad = (v: number | null) => v !== null && (!Number.isFinite(v) || v < 0);
  if (bad(r.low)) errors[`${key}.low`] = "Must be a non-negative number";
  if (bad(r.high)) errors[`${key}.high`] = "Must be a non-negative number";
  if ((r.low === null) !== (r.high === null)) errors[key] = "Enter both low and high, or leave both unknown";
  if (r.low !== null && r.high !== null && r.low > r.high) errors[key] = "Low must not exceed high";
  return r.low !== null && r.high !== null;
}

function checkSourceLinks(
  ids: string[],
  known: boolean,
  key: string,
  sourceIds: Set<string>,
  errors: Record<string, string>,
) {
  const missing = ids.filter((id) => !sourceIds.has(id));
  if (missing.length > 0) errors[`${key}.sources`] = `Unknown source reference: ${missing.join(", ")}`;
  else if (known && ids.length === 0) errors[`${key}.sources`] = "Link at least one source to this input";
}

export function calculateFinance(input: FinanceInput): FinanceOutcome {
  const errors: Record<string, string> = {};
  const unknowns: string[] = [];

  if (!/^[A-Z]{3}$/.test(input.currency)) errors.currency = "Use a 3-letter currency code, e.g. LKR";
  if (!(Number.isFinite(input.area.value) && input.area.value > 0)) errors["area.value"] = "Area must be greater than zero";
  if (!(input.area.unit in HECTARES_PER)) errors["area.unit"] = "Unsupported area unit";

  // --- Source records -------------------------------------------------------
  const seen = new Set<string>();
  input.sources.forEach((s, i) => {
    const p = `sources.${i}`;
    if (!s.id.trim()) errors[`${p}.id`] = "Source ID is required";
    else if (seen.has(s.id)) errors[`${p}.id`] = `Duplicate source ID "${s.id}"`;
    seen.add(s.id);
    if (!s.label.trim()) errors[`${p}.label`] = "Source label is required";
    if (!isValidReference(s.reference)) errors[`${p}.reference`] = "Enter an http(s) URL or a document reference";
    if (!isIsoDate(s.quoted_on)) errors[`${p}.quoted_on`] = "Use YYYY-MM-DD";
    if (!isIsoDate(s.accessed_on)) errors[`${p}.accessed_on`] = "Use YYYY-MM-DD";
    if (isIsoDate(s.quoted_on) && isIsoDate(s.accessed_on) && s.accessed_on < s.quoted_on) {
      errors[`${p}.accessed_on`] = "Access date cannot be before the quoted date";
    }
    if (!s.area.trim()) errors[`${p}.area`] = "Market or production area is required";
    if (!s.unit_period.trim()) errors[`${p}.unit_period`] = "Unit and period are required";
    if (!SOURCE_KINDS.includes(s.kind)) errors[`${p}.kind`] = "Choose farmer-entered, observed, researched or synthetic";
  });

  // --- Inputs + their source links -------------------------------------------
  const knownCosts: Range[] = [];
  input.costs.forEach((c, i) => {
    if (!c.name.trim()) errors[`costs.${i}.name`] = "Category name is required";
    const known = checkRange(c.per_ha, `costs.${i}`, errors);
    checkSourceLinks(c.source_ids, known, `costs.${i}`, seen, errors);
    if (known) knownCosts.push(c.per_ha as Range);
    else if (c.per_ha.low === null && c.per_ha.high === null) unknowns.push(`Cost "${c.name || `#${i + 1}`}" is unknown`);
  });
  const yieldKnown = checkRange(input.yield_kg_per_ha, "yield_kg_per_ha", errors);
  checkSourceLinks(input.yield_source_ids, yieldKnown, "yield_kg_per_ha", seen, errors);
  const priceKnown = checkRange(input.price_per_kg, "price_per_kg", errors);
  checkSourceLinks(input.price_source_ids, priceKnown, "price_per_kg", seen, errors);
  if (!yieldKnown) unknowns.push("Yield scenario range is unknown");
  if (!priceKnown) unknowns.push("Price range is unknown");

  if (Object.keys(errors).length > 0) return { ok: false, errors, result: null };

  // --- Calculation (no rounding) --------------------------------------------
  const area_ha = toHectares(input.area.value, input.area.unit);
  const costsComplete = input.costs.length > 0 && knownCosts.length === input.costs.length;
  if (input.costs.length === 0) unknowns.push("No cost categories entered");

  const cost: Range | null = costsComplete
    ? {
        low: knownCosts.reduce((a, c) => a + c.low, 0) * area_ha,
        high: knownCosts.reduce((a, c) => a + c.high, 0) * area_ha,
      }
    : null;
  if (!costsComplete && input.costs.length > 0) unknowns.push("Total cost and net are unknown while any cost category is unknown");

  const y = input.yield_kg_per_ha as Range;
  const p = input.price_per_kg as Range;
  const revenue: Range | null =
    yieldKnown && priceKnown ? { low: area_ha * y.low * p.low, high: area_ha * y.high * p.high } : null;

  const net: Range | null = cost && revenue ? { low: revenue.low - cost.high, high: revenue.high - cost.low } : null;

  const break_even_price_per_kg: Range | null =
    cost && yieldKnown && y.low > 0
      ? { low: cost.low / (area_ha * y.high), high: cost.high / (area_ha * y.low) }
      : null;
  if (cost && yieldKnown && y.low === 0) unknowns.push("Break-even price is unknown when the minimum yield is 0");

  // --- Disclosure --------------------------------------------------------------
  const entered = new Set(input.costs.map((c) => c.key).filter(Boolean));
  const omitted_categories = STANDARD_COST_CATEGORIES.filter((c) => !entered.has(c.key)).map((c) => c.name);

  const used = new Set([
    ...input.costs.flatMap((c) => c.source_ids),
    ...input.yield_source_ids,
    ...input.price_source_ids,
  ]);
  const usedSources = input.sources.filter((s) => used.has(s.id));
  const uses_synthetic = usedSources.some((s) => s.kind === "synthetic");

  const limitations: string[] = [];
  if (omitted_categories.length > 0) {
    limitations.push(`Not entered (not assumed zero): ${omitted_categories.join(", ")}.`);
  }
  if (uses_synthetic) limitations.push("Some inputs are synthetic examples, not Sri Lankan market or yield evidence.");
  const areas = new Set(usedSources.map((s) => s.area.trim().toLowerCase()));
  if (areas.size > 1) limitations.push("Inputs come from different market/production areas; check that they are comparable.");
  const grades = new Set(usedSources.map((s) => s.crop_variety_grade.trim().toLowerCase()).filter(Boolean));
  if (grades.size > 1) limitations.push("Inputs refer to different crop varieties/grades; check that they are comparable.");
  const unlinked = input.sources.filter((s) => !used.has(s.id)).map((s) => s.label || s.id);
  if (unlinked.length > 0) limitations.push(`Sources not linked to any input: ${unlinked.join(", ")}.`);

  const assumptions = [
    `Specification v${FINANCE_SPEC_VERSION} (${FINANCE_SPEC_REFERENCE}); formulas approved by Bhagya with implementation conditions.`,
    `Area ${input.area.value} ${input.area.unit} = ${area_ha.toFixed(4)} ha.`,
    "Period: one crop cycle. Costs and yields are per hectare per cycle; price is farm-gate currency per kg.",
    "Net range uses conservative interval arithmetic: low = lowest revenue − highest cost; high = highest revenue − lowest cost. Endpoints are not equally likely and are not confidence intervals.",
    "Results are rounded for display only.",
  ];

  return {
    ok: true,
    errors,
    result: {
      spec_version: FINANCE_SPEC_VERSION,
      currency: input.currency,
      area_ha,
      cost,
      revenue,
      net,
      break_even_price_per_kg,
      assumptions,
      unknowns,
      omitted_categories,
      limitations,
      uses_synthetic,
    },
  };
}
