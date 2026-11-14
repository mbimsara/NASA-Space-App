import { describe, expect, it } from "vitest";
import { asSeasonRanges, fmtMm, fmtRange, fmtScore, fmtSignedMm, fmtWeight } from "./format";

const U = "Unknown";

describe("formatters never turn unknown into zero", () => {
  it("null / undefined / NaN render as unknown", () => {
    for (const v of [null, undefined, Number.NaN]) {
      expect(fmtMm(v, U)).toBe(U);
      expect(fmtScore(v, U)).toBe(U);
      expect(fmtSignedMm(v, U)).toBe(U);
    }
  });

  it("a real zero stays zero", () => {
    expect(fmtMm(0, U)).toBe("0 mm");
    expect(fmtScore(0, U)).toBe("0");
  });

  it("scores are already 0–100; weights are fractions", () => {
    expect(fmtScore(72.46, U)).toBe("72.5");
    expect(fmtWeight(0.625, U)).toBe("63%");
  });

  it("accepts per-season arrays or a single legacy object", () => {
    expect(asSeasonRanges(null)).toEqual([]);
    expect(asSeasonRanges({ a: 1 })).toEqual([{ a: 1 }]);
    expect(asSeasonRanges([{ a: 1 }, { a: 2 }])).toHaveLength(2);
  });

  it("a range with an unknown end is unknown", () => {
    expect(fmtRange(10, null, U, "mm")).toBe(U);
    expect(fmtRange(10, 20, U, "mm")).toBe("10 – 20 mm");
  });

  it("signed balances show shortfalls with a minus sign", () => {
    expect(fmtSignedMm(-40.4, U)).toBe("−40 mm");
    expect(fmtSignedMm(12, U)).toBe("+12 mm");
    expect(fmtRange(-120, 30, U, "mm", true)).toBe("−120 – +30 mm");
  });
});
