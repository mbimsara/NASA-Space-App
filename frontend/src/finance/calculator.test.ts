import { describe, expect, it } from "vitest";
import { calculateFinance, toHectares, type FinanceInput } from "./calculator";

const base = (over: Partial<FinanceInput> = {}): FinanceInput => ({
  currency: "LKR",
  area: { value: 2, unit: "ha" },
  crop_label: "Example crop",
  costs: [
    { name: "Seed", per_ha: { low: 10_000, high: 12_000 } },
    { name: "Labour", per_ha: { low: 20_000, high: 30_000 } },
  ],
  yield_kg_per_ha: { low: 3_000, high: 4_000 },
  price_per_kg: { low: 100, high: 120 },
  sources: [{ label: "Worked example (synthetic)", date: "2026-01-15" }],
  ...over,
});

describe("area conversion", () => {
  it("converts acres and perches to hectares", () => {
    expect(toHectares(1, "acre")).toBeCloseTo(0.40468564224, 10);
    expect(toHectares(160, "perch")).toBeCloseTo(toHectares(1, "acre"), 10);
    expect(toHectares(2.5, "ha")).toBe(2.5);
  });
});

describe("calculateFinance — worked example (2 ha)", () => {
  const { ok, result } = calculateFinance(base());

  it("computes cost range as sum of categories × area", () => {
    expect(ok).toBe(true);
    expect(result!.cost).toEqual({ low: 60_000, high: 84_000 });
  });

  it("computes revenue range from low×low and high×high", () => {
    expect(result!.revenue).toEqual({ low: 600_000, high: 960_000 });
  });

  it("uses conservative bounds for net", () => {
    expect(result!.net).toEqual({ low: 600_000 - 84_000, high: 960_000 - 60_000 });
  });

  it("computes break-even price range", () => {
    expect(result!.break_even_price_per_kg!.low).toBeCloseTo(60_000 / (4_000 * 2), 10);
    expect(result!.break_even_price_per_kg!.high).toBeCloseTo(84_000 / (3_000 * 2), 10);
  });
});

describe("calculateFinance — units and unknowns", () => {
  it("applies area unit conversion before multiplying", () => {
    const r = calculateFinance(base({ area: { value: 1, unit: "acre" } })).result!;
    expect(r.area_ha).toBeCloseTo(0.40468564224, 10);
    expect(r.cost!.low).toBeCloseTo(30_000 * 0.40468564224, 6);
  });

  it("returns null (not zero) when yield is unknown", () => {
    const r = calculateFinance(base({ yield_kg_per_ha: { low: null, high: null } })).result!;
    expect(r.revenue).toBeNull();
    expect(r.net).toBeNull();
    expect(r.break_even_price_per_kg).toBeNull();
    expect(r.cost).not.toBeNull();
    expect(r.unknowns).toContain("Yield range is unknown");
  });

  it("returns null cost when any category is unknown", () => {
    const costs = [...base().costs, { name: "Fertilizer", per_ha: { low: null, high: null } }];
    const r = calculateFinance(base({ costs })).result!;
    expect(r.cost).toBeNull();
    expect(r.net).toBeNull();
    expect(r.revenue).not.toBeNull();
  });
});

describe("calculateFinance — validation", () => {
  it("rejects low > high", () => {
    const out = calculateFinance(base({ price_per_kg: { low: 150, high: 100 } }));
    expect(out.ok).toBe(false);
    expect(out.errors.price_per_kg).toMatch(/Low must not exceed high/);
  });

  it("rejects negative values, non-positive area and half-entered ranges", () => {
    const out = calculateFinance(
      base({ area: { value: 0, unit: "ha" }, yield_kg_per_ha: { low: -1, high: 5 }, price_per_kg: { low: 1, high: null } }),
    );
    expect(out.ok).toBe(false);
    expect(out.errors["area.value"]).toBeDefined();
    expect(out.errors["yield_kg_per_ha.low"]).toBeDefined();
    expect(out.errors.price_per_kg).toBeDefined();
  });

  it("requires dated sources", () => {
    expect(calculateFinance(base({ sources: [] })).errors.sources).toBeDefined();
    expect(calculateFinance(base({ sources: [{ label: "x", date: "2026-02-30" }] })).errors["sources.0.date"]).toBeDefined();
  });

  it("requires a 3-letter currency code", () => {
    expect(calculateFinance(base({ currency: "Rs" })).errors.currency).toBeDefined();
  });
});
