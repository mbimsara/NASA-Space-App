import { beforeEach, describe, expect, it } from "vitest";
import { MAX_CACHED_PLANS, cachePlan, getCachedPlan, listCachedPlanIds } from "./offlineCache";
import type { SavedPlan } from "../types/api";

const plan = (id: string) => ({ plan_id: id, farm_id: "farm-1" }) as unknown as SavedPlan;

beforeEach(() => localStorage.clear());

describe("offline plan cache (read-only)", () => {
  it("stores and returns a copy with its cache time", () => {
    cachePlan(plan("p1"), null, new Date("2026-11-14T10:00:00Z"));
    const c = getCachedPlan("p1")!;
    expect(c.plan.plan_id).toBe("p1");
    expect(c.cachedAt).toBe("2026-11-14T10:00:00.000Z");
    expect(getCachedPlan("missing")).toBeNull();
  });

  it(`keeps only the ${MAX_CACHED_PLANS} most recently cached plans`, () => {
    for (let i = 0; i < MAX_CACHED_PLANS + 3; i++) {
      cachePlan(plan(`p${i}`), null, new Date(Date.UTC(2026, 10, 1, 0, i)));
    }
    const ids = listCachedPlanIds();
    expect(ids).toHaveLength(MAX_CACHED_PLANS);
    expect(ids).not.toContain("p0");
    expect(ids).toContain(`p${MAX_CACHED_PLANS + 2}`);
  });

  it("survives corrupt storage", () => {
    localStorage.setItem("agrosphere_offline_plans", "{not json");
    expect(getCachedPlan("p1")).toBeNull();
    expect(() => cachePlan(plan("p1"), null)).not.toThrow();
  });
});
