import { describe, expect, it } from "vitest";
import { latestHistoricalDate, observationView } from "./observations";
import type { ObservationWire } from "./observations";

describe("backend observation contract", () => {
  it("maps daily fields, preserves null/zero and per-variable coverage", () => {
    const wire: ObservationWire = {
      observation_id: "obs", farm_id: "farm", input_version: 1, data_kind: "synthetic",
      period: { start: "2025-01-01", end: "2025-01-02" }, retrieved_at: null,
      source_refs: ["synthetic"], limitations: ["Invented test values"],
      spatial_resolution: { latitude_degrees: 0.5, longitude_degrees: 0.625 },
      coverage: { expected_days: 2, available_days: 0, temperature_valid_days: 1, precipitation_valid_days: 1 },
      summary: { rainfall_mm: null, mean_temperature_c: 25 },
      daily: [{ date: "2025-01-01", temperature_c: 25, precipitation_mm_per_day: null },
              { date: "2025-01-02", temperature_c: null, precipitation_mm_per_day: 0 }],
    };
    const view = observationView(wire);
    expect(view.time_series?.[1].rainfall_mm).toBe(0);
    expect(view.time_series?.[0].rainfall_mm).toBeNull();
    expect(view.spatial_resolution).toContain("0.625°");
    expect(view.coverage).toEqual(wire.coverage);
    expect(view.summary.rainfall_mm).toBeNull();
  });
  it("uses yesterday in UTC including month/year boundaries", () => {
    expect(latestHistoricalDate(new Date("2026-01-01T00:01:00Z"))).toBe("2025-12-31");
    expect(latestHistoricalDate(new Date("2024-03-01T12:00:00Z"))).toBe("2024-02-29");
  });
});
