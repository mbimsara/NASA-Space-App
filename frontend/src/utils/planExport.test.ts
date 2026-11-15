import { describe, expect, it, vi } from "vitest";
import { planReportJson } from "./planExport";

describe("saved plan report", () => {
  it("preserves the exact plan snapshot and limitations", () => {
    vi.useFakeTimers(); vi.setSystemTime(new Date("2026-01-01T00:00:00Z"));
    const plan = { plan_id: "p1", farm_id: "f1", input_version: 1 } as never;
    const report = JSON.parse(planReportJson(plan));
    expect(report.plan).toEqual(plan);
    expect(report.exported_at).toBe("2026-01-01T00:00:00.000Z");
    expect(report.limitations.join(" ")).toContain("not a guarantee");
    vi.useRealTimers();
  });
});
