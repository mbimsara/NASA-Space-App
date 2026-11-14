/**
 * Checks for financial specification v0.1 (docs/FINANCIAL_SPECIFICATION.md).
 * All numbers below are SYNTHETIC arithmetic fixtures. Formula approval does not
 * approve them as Sri Lankan market or yield evidence.
 */
import { describe, expect, it } from "vitest";
import {
  FINANCE_SPEC_VERSION,
  calculateFinance,
  isValidReference,
  toHectares,
  type FinanceInput,
  type SourceRecord,
} from "./calculator";

const src = (id: string, over: Partial<SourceRecord> = {}): SourceRecord => ({
  id,
  label: `Synthetic fixture ${id}`,
  reference: "https://example.org/synthetic-fixture",
  quoted_on: "2026-01-15",
  accessed_on: "2026-01-20",
  area: "Synthetic test area",
  crop_variety_grade: "Example crop",
  unit_period: "per crop cycle",
  kind: "synthetic",
  ...over,
});

const base = (over: Partial<FinanceInput> = {}): FinanceInput => ({
  currency: "LKR",
  area: { value: 2, unit: "ha" },
  crop_label: "Example crop",
  costs: [
    { key: "seed", name: "Seed / planting material", per_ha: { low: 10_000, high: 12_000 }, source_ids: ["S1"] },
    { key: "hired_labour", name: "Hired labour", per_ha: { low: 20_000, high: 30_000 }, source_ids: ["S1"] },
  ],
  yield_kg_per_ha: { low: 3_000, high: 4_000 },
  yield_source_ids: ["S2"],
  price_per_kg: { low: 100, high: 120 },
  price_source_ids: ["S3"],
  sources: [src("S1"), src("S2"), src("S3")],
  ...over,
});

describe("specification version", () => {
  it("is v0.1 and referenced in assumptions", () => {
    const r = calculateFinance(base()).result!;
    expect(FINANCE_SPEC_VERSION).toBe("0.1");
    expect(r.spec_version).toBe("0.1");
    expect(r.assumptions[0]).toMatch(/FINANCIAL_SPECIFICATION\.md/);
  });
});

describe("area conversion", () => {
  it("converts acres and perches to hectares", () => {
    expect(toHectares(1, "acre")).toBeCloseTo(0.40468564224, 10);
    expect(toHectares(160, "perch")).toBeCloseTo(toHectares(1, "acre"), 10);
    expect(toHectares(1, "perch")).toBeCloseTo(0.002529285264, 12);
  });
});

describe("approved formulas — synthetic worked example (2 ha)", () => {
  const { ok, result } = calculateFinance(base());

  it("cost = A × ΣC", () => {
    expect(ok).toBe(true);
    expect(result!.cost).toEqual({ low: 60_000, high: 84_000 });
  });
  it("revenue = A × Y × P (low×low, high×high)", () => {
    expect(result!.revenue).toEqual({ low: 600_000, high: 960_000 });
  });
  it("net uses conservative interval arithmetic", () => {
    expect(result!.net).toEqual({ low: 600_000 - 84_000, high: 960_000 - 60_000 });
  });
  it("break-even price range", () => {
    expect(result!.break_even_price_per_kg!.low).toBeCloseTo(60_000 / (2 * 4_000), 10);
    expect(result!.break_even_price_per_kg!.high).toBeCloseTo(84_000 / (2 * 3_000), 10);
  });
  it("does not round during calculation", () => {
    const r = calculateFinance(base({ area: { value: 1, unit: "acre" } })).result!;
    expect(r.cost!.low).toBe(30_000 * 0.40468564224);
  });
});

describe("missing data", () => {
  it("unknown yield → revenue, net and break-even unknown (null, not zero)", () => {
    const r = calculateFinance(base({ yield_kg_per_ha: { low: null, high: null }, yield_source_ids: [] })).result!;
    expect(r.revenue).toBeNull();
    expect(r.net).toBeNull();
    expect(r.break_even_price_per_kg).toBeNull();
    expect(r.unknowns).toContain("Yield scenario range is unknown");
  });

  it("unknown cost category → cost and net unknown", () => {
    const costs = [
      ...base().costs,
      { key: "fertilizer" as const, name: "Fertilizer and soil amendments", per_ha: { low: null, high: null }, source_ids: [] },
    ];
    const r = calculateFinance(base({ costs })).result!;
    expect(r.cost).toBeNull();
    expect(r.net).toBeNull();
    expect(r.revenue).not.toBeNull();
  });

  it("zero is a valid endpoint, but zero minimum yield makes break-even unknown", () => {
    const r = calculateFinance(base({ yield_kg_per_ha: { low: 0, high: 4_000 } })).result!;
    expect(r.revenue!.low).toBe(0);
    expect(r.break_even_price_per_kg).toBeNull();
  });

  it("negative net is reported, not clamped", () => {
    const r = calculateFinance(base({ price_per_kg: { low: 1, high: 2 } })).result!;
    expect(r.net!.low).toBeLessThan(0);
    expect(r.net!.low).toBe(2 * 3_000 * 1 - 84_000);
  });
});

describe("validation", () => {
  it("rejects low > high, negatives, zero area and half-entered ranges", () => {
    const out = calculateFinance(
      base({
        area: { value: 0, unit: "ha" },
        yield_kg_per_ha: { low: -1, high: 5 },
        price_per_kg: { low: 1, high: null },
      }),
    );
    expect(out.ok).toBe(false);
    expect(out.errors["area.value"]).toBeDefined();
    expect(out.errors["yield_kg_per_ha.low"]).toBeDefined();
    expect(out.errors.price_per_kg).toBeDefined();
    expect(calculateFinance(base({ price_per_kg: { low: 150, high: 100 } })).errors.price_per_kg).toMatch(/Low must not exceed/);
  });

  it("requires a 3-letter currency code", () => {
    expect(calculateFinance(base({ currency: "Rs" })).errors.currency).toBeDefined();
  });
});

describe("provenance", () => {
  it("every known input must link to a source", () => {
    const out = calculateFinance(base({ price_source_ids: [] }));
    expect(out.ok).toBe(false);
    expect(out.errors["price_per_kg.sources"]).toMatch(/Link at least one source/);
  });

  it("each cost category needs its own source link", () => {
    const costs = base().costs.map((c, i) => (i === 1 ? { ...c, source_ids: [] } : c));
    expect(calculateFinance(base({ costs })).errors["costs.1.sources"]).toBeDefined();
  });

  it("unknown inputs do not need a source", () => {
    const out = calculateFinance(base({ yield_kg_per_ha: { low: null, high: null }, yield_source_ids: [] }));
    expect(out.ok).toBe(true);
  });

  it("rejects links to missing source IDs", () => {
    expect(calculateFinance(base({ yield_source_ids: ["S9"] })).errors["yield_kg_per_ha.sources"]).toMatch(/S9/);
  });

  it("requires URL/document reference, dates, area, unit/period and kind", () => {
    const bad = src("S3", {
      reference: "ftp://x",
      quoted_on: "2026-02-30",
      accessed_on: "2026-01-01",
      area: "",
      unit_period: " ",
      kind: "guess" as never,
    });
    const e = calculateFinance(base({ sources: [src("S1"), src("S2"), bad] })).errors;
    for (const k of ["reference", "quoted_on", "area", "unit_period", "kind"]) expect(e[`sources.2.${k}`]).toBeDefined();
  });

  it("rejects access date before quoted date and duplicate IDs", () => {
    const e = calculateFinance(
      base({ sources: [src("S1"), src("S2", { quoted_on: "2026-03-01", accessed_on: "2026-02-01" }), src("S2")] }),
    ).errors;
    expect(e["sources.1.accessed_on"]).toBeDefined();
    expect(e["sources.2.id"]).toMatch(/Duplicate/);
  });

  it("accepts http(s) URLs or document references", () => {
    expect(isValidReference("https://www.doa.gov.lk/report.pdf")).toBe(true);
    expect(isValidReference("HARTI weekly price bulletin, 2026-03-02, p. 4")).toBe(true);
    expect(isValidReference("ftp://example.org")).toBe(false);
    expect(isValidReference("  ")).toBe(false);
  });
});

describe("disclosure", () => {
  it("lists omitted standard cost categories instead of assuming zero", () => {
    const r = calculateFinance(base()).result!;
    expect(r.omitted_categories).toContain("Fertilizer and soil amendments");
    expect(r.omitted_categories).not.toContain("Hired labour");
    expect(r.limitations.join(" ")).toMatch(/not assumed zero/);
  });

  it("labels synthetic inputs", () => {
    const r = calculateFinance(base()).result!;
    expect(r.uses_synthetic).toBe(true);
    expect(r.limitations.join(" ")).toMatch(/not Sri Lankan market or yield evidence/);
    const real = calculateFinance(base({ sources: ["S1", "S2", "S3"].map((id) => src(id, { kind: "researched" })) })).result!;
    expect(real.uses_synthetic).toBe(false);
  });

  it("flags mixed areas/grades and unlinked sources", () => {
    const r = calculateFinance(
      base({
        sources: [src("S1"), src("S2", { area: "Other area", crop_variety_grade: "Grade B" }), src("S3"), src("S4")],
      }),
    ).result!;
    const text = r.limitations.join(" ");
    expect(text).toMatch(/different market\/production areas/);
    expect(text).toMatch(/different crop varieties\/grades/);
    expect(text).toMatch(/not linked to any input/);
  });
});
