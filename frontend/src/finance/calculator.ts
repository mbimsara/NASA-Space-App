/**
 * Deterministic cost / revenue range calculator.
 * Owner: Shehani (implementation). Formulas and range semantics: Bhagya (PENDING APPROVAL).
 *
 * Proposed specification v0.1-draft (docs/AGRONOMY_RULES.md → Finance):
 * - Area basis: hectares internally. 1 acre = 0.40468564224 ha (international acre);
 *   1 perch = 1/160 acre = 0.002529285264 ha.
 * - Period: one crop cycle (season). Currency: explicit ISO code, default LKR.
 * - Costs: sum of categories, each a [low, high] range per hectare, × area.
 * - Revenue: [yield_low × price_low, yield_high × price_high] × area (kg/ha × currency/kg).
 * - Net: conservative bounds [revenue_low − cost_high, revenue_high − cost_low].
 * - Break-even price: [cost_low / (yield_high × area), cost_high / (yield_low × area)].
 * - Unknown inputs stay null; results that depend on them are null, never 0.
 * - Values are rounded only for display (`roundMoney`), never during calculation.
 */

export type AreaUnit = "ha" | "acre" | "perch";

export const HECTARES_PER: Record<AreaUnit, number> = {
  ha: 1,
  acre: 0.40468564224,
  perch: 0.40468564224 / 160,
};

export interface Range {
  low: number;
  high: number;
}

export interface NullableRange {
  low: number | null;
  high: number | null;
}

export interface CostCategory {
  name: string;
  /** Cost per hectare for one cycle, in `currency`. */
  per_ha: NullableRange;
}

export interface DatedSource {
  label: string;
  /** YYYY-MM-DD the value was observed/quoted. */
  date: string;
}

export interface FinanceInput {
  currency: string;
  area: { value: number; unit: AreaUnit };
  crop_label: string;
  costs: CostCategory[];
  /** kg per hectare per cycle */
  yield_kg_per_ha: NullableRange;
  /** currency per kg */
  price_per_kg: NullableRange;
  sources: DatedSource[];
}

export interface FinanceResult {
  currency: string;
  area_ha: number;
  cost: Range | null;
  revenue: Range | null;
  net: Range | null;
  break_even_price_per_kg: Range | null;
  assumptions: string[];
  unknowns: string[];
}

export interface FinanceOutcome {
  ok: boolean;
  errors: Record<string, string>;
  result: FinanceResult | null;
}

export const FINANCE_SPEC_VERSION = "0.1-draft";

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

function checkRange(r: NullableRange, key: string, errors: Record<string, string>): r is Range {
  const bad = (v: number | null) => v !== null && (!Number.isFinite(v) || v < 0);
  if (bad(r.low)) errors[`${key}.low`] = "Must be a non-negative number";
  if (bad(r.high)) errors[`${key}.high`] = "Must be a non-negative number";
  if ((r.low === null) !== (r.high === null)) errors[key] = "Enter both low and high, or leave both unknown";
  if (r.low !== null && r.high !== null && r.low > r.high) errors[key] = "Low must not exceed high";
  return r.low !== null && r.high !== null;
}

export function calculateFinance(input: FinanceInput): FinanceOutcome {
  const errors: Record<string, string> = {};
  const unknowns: string[] = [];

  if (!/^[A-Z]{3}$/.test(input.currency)) errors.currency = "Use a 3-letter currency code, e.g. LKR";
  if (!(Number.isFinite(input.area.value) && input.area.value > 0)) errors["area.value"] = "Area must be greater than zero";
  if (!(input.area.unit in HECTARES_PER)) errors["area.unit"] = "Unsupported area unit";

  if (input.sources.length === 0) errors.sources = "Add at least one dated source for prices and costs";
  input.sources.forEach((s, i) => {
    if (!s.label.trim()) errors[`sources.${i}.label`] = "Source label is required";
    if (!isIsoDate(s.date)) errors[`sources.${i}.date`] = "Use YYYY-MM-DD";
  });

  const knownCosts: Range[] = [];
  input.costs.forEach((c, i) => {
    if (!c.name.trim()) errors[`costs.${i}.name`] = "Category name is required";
    if (checkRange(c.per_ha, `costs.${i}`, errors)) knownCosts.push(c.per_ha as Range);
    else if (c.per_ha.low === null && c.per_ha.high === null) unknowns.push(`Cost "${c.name || `#${i + 1}`}" is unknown`);
  });
  const yieldKnown = checkRange(input.yield_kg_per_ha, "yield_kg_per_ha", errors);
  const priceKnown = checkRange(input.price_per_kg, "price_per_kg", errors);
  if (!yieldKnown) unknowns.push("Yield range is unknown");
  if (!priceKnown) unknowns.push("Price range is unknown");

  if (Object.keys(errors).length > 0) return { ok: false, errors, result: null };

  const area_ha = toHectares(input.area.value, input.area.unit);
  const costsComplete = input.costs.length > 0 && knownCosts.length === input.costs.length;
  if (input.costs.length === 0) unknowns.push("No cost categories entered");

  const cost: Range | null = costsComplete
    ? {
        low: knownCosts.reduce((a, c) => a + c.low, 0) * area_ha,
        high: knownCosts.reduce((a, c) => a + c.high, 0) * area_ha,
      }
    : null;

  const y = input.yield_kg_per_ha as Range;
  const p = input.price_per_kg as Range;
  const revenue: Range | null =
    yieldKnown && priceKnown ? { low: y.low * p.low * area_ha, high: y.high * p.high * area_ha } : null;

  const net: Range | null = cost && revenue ? { low: revenue.low - cost.high, high: revenue.high - cost.low } : null;

  const break_even_price_per_kg: Range | null =
    cost && yieldKnown && y.low > 0
      ? { low: cost.low / (y.high * area_ha), high: cost.high / (y.low * area_ha) }
      : null;
  if (cost && yieldKnown && y.low === 0) unknowns.push("Break-even price undefined when minimum yield is 0");

  const assumptions = [
    `Specification ${FINANCE_SPEC_VERSION} — pending Bhagya's approval.`,
    `Area ${input.area.value} ${input.area.unit} = ${area_ha.toFixed(4)} ha.`,
    "Period: one crop cycle. Costs and yields are per hectare per cycle.",
    "Net range uses conservative bounds: low = lowest revenue − highest cost; high = highest revenue − lowest cost.",
    "Ranges are illustrative scenario bounds from dated inputs, not a forecast or guarantee.",
  ];

  return {
    ok: true,
    errors,
    result: { currency: input.currency, area_ha, cost, revenue, net, break_even_price_per_kg, assumptions, unknowns },
  };
}
