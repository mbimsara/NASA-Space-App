import { beforeEach, describe, expect, it } from "vitest";
import * as fx from "./fixtures";
import { ApiClientError } from "./client";

const rotationBody = (input_version: number) => ({
  input_version,
  observation_id: null,
  seasons: 3,
  catalog_version: "0.1-draft",
  priority_weights: { water: 0.5, soil: 0.3, climate: 0.2 },
});

beforeEach(() => fx.resetFixtures());

describe("fixture API workflow (persistence + regressions)", () => {
  it("save → reload keeps history, units, soil and priorities", async () => {
    const created = await fx.createDemoFarmFixture();
    const reloaded = await fx.getFarmFixture(created.id);
    expect(reloaded).toEqual(created);
    expect(reloaded.profile.irrigation_supply_mm_per_season).toBeNull();
  });

  it("PATCH with an old version returns 409 VERSION_CONFLICT", async () => {
    const f = await fx.createDemoFarmFixture();
    const { schema_version: _v, ...profile } = f.profile;
    const updated = await fx.updateFarmFixture(f.id, 1, profile);
    expect(updated.input_version).toBe(2);
    await expect(fx.updateFarmFixture(f.id, 1, profile)).rejects.toMatchObject({ status: 409, code: "VERSION_CONFLICT" });
  });

  it("exclusions reduce candidates and the reason is reported", async () => {
    const f = await fx.createDemoFarmFixture();
    const { schema_version: _v, ...profile } = f.profile;
    const f2 = await fx.updateFarmFixture(f.id, 1, { ...profile, excluded_crop_ids: ["maize"] });
    const a = await fx.createRotationFixture(f.id, rotationBody(f2.input_version));
    expect(a.candidates.map((c) => c.candidate_id)).toEqual(["cand-2"]);
    expect(a.limitations.join(" ")).toMatch(/excluded crop "maize"/);
  });

  it("scenario recomputes from the same baseline and reports differences", async () => {
    const f = await fx.createDemoFarmFixture();
    const a = await fx.createRotationFixture(f.id, rotationBody(1));
    const s = await fx.createScenarioFixture(a.analysis_id, -30);
    expect(s.baseline_analysis_id).toBe(a.analysis_id);
    expect(s.candidates[0].water_budget.rainfall_mm).toBe(210);
    expect(Object.keys(s.baseline_differences).sort()).toEqual(a.candidates.map((c) => c.candidate_id).sort());
  });

  it("plan saves, reopens with snapshot, and outdated analyses cannot be saved", async () => {
    const f = await fx.createDemoFarmFixture();
    const a = await fx.createRotationFixture(f.id, rotationBody(1));
    const { plan_id } = await fx.savePlanFixture(f.id, {
      analysis_id: a.analysis_id,
      candidate_id: a.candidates[0].candidate_id,
      expected_input_version: 1,
    });
    const plan = await fx.getPlanFixture(plan_id);
    expect(plan.candidate_snapshot.candidate_id).toBe(a.candidates[0].candidate_id);
    expect(plan.input_snapshot?.name).toBe(f.profile.name);

    const { schema_version: _v, ...profile } = f.profile;
    await fx.updateFarmFixture(f.id, 1, profile);
    const err = await fx
      .savePlanFixture(f.id, { analysis_id: a.analysis_id, candidate_id: "cand-1", expected_input_version: 2 })
      .catch((e) => e);
    expect(err).toBeInstanceOf(ApiClientError);
    expect(err.status).toBe(409);
  });

  it("observations keep missing days as null, never zero", async () => {
    const f = await fx.createDemoFarmFixture();
    const o = await fx.getObservationsFixture(f.id, "2026-01-01", "2026-01-31");
    expect(o.coverage.expected_days).toBe(31);
    expect(o.coverage.available_days).toBeLessThan(31);
    expect(o.time_series!.some((p) => p.rainfall_mm === null)).toBe(true);
    expect(o.data_kind).toBe("synthetic");
  });
});
