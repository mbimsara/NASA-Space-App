import { describe, expect, it } from "vitest";
import { defaultObservationRange, formatResolution, isValidObservationRange, toChartPoints, utcDate } from "./observations";

const now = new Date("2026-11-14T02:00:00+05:30"); // still 2026-11-13 in UTC

describe("observation date rules (end must be before today, UTC)", () => {
  it("uses UTC, not local time", () => {
    expect(utcDate(0, now)).toBe("2026-11-13");
    expect(utcDate(-1, now)).toBe("2026-11-12");
  });

  it("defaults to a 31-day window ending yesterday", () => {
    expect(defaultObservationRange(now)).toEqual({ start: "2026-10-14", end: "2026-11-12" });
  });

  it("rejects today, reversed ranges and pre-1981 starts", () => {
    expect(isValidObservationRange("2026-11-01", "2026-11-12", now)).toBe(true);
    expect(isValidObservationRange("2026-11-01", "2026-11-13", now)).toBe(false);
    expect(isValidObservationRange("2026-11-10", "2026-11-01", now)).toBe(false);
    expect(isValidObservationRange("1980-12-31", "2026-11-01", now)).toBe(false);
  });
});

describe("toChartPoints", () => {
  it("maps daily[] fields and keeps nulls", () => {
    expect(
      toChartPoints({ daily: [{ date: "2026-01-01", precipitation_mm_per_day: null, temperature_c: 26.1 }] }),
    ).toEqual([{ date: "2026-01-01", rainfall_mm: null, mean_temperature_c: 26.1 }]);
  });
});

describe("formatResolution", () => {
  it("renders objects as text and null as null", () => {
    expect(formatResolution({ latitude_deg: 0.5, longitude_deg: 0.625 })).toBe("latitude deg: 0.5, longitude deg: 0.625");
    expect(formatResolution("0.5° × 0.625°")).toBe("0.5° × 0.625°");
    expect(formatResolution(null)).toBeNull();
    expect(formatResolution({ note: null })).toBeNull();
  });
});
