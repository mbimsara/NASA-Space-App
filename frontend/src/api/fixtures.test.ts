import { beforeEach, describe, expect, it } from "vitest";
import * as fx from "./fixtures";
import { ApiClientError } from "./client";
import { asSeasonRanges } from "../utils/format";
import { utcDate } from "../utils/observations";

const rotationBody = (input_version: number, weights = { water: 0.5, soil: 0.3, climate: 0.2 }) => ({
  input_version,
  observation_id: null,
  seasons: 3,
  catalog_version: "0.1-draft",
  priority_weights: weights,
});

const comp = (c: { score_components: { name: string; value: number | null; requested_weight: number; effective_weight: number }[] }, n: string) =>
  c.score_components.find((x) => x.name === n)!;

const confirmRainfed = async () => {
  const farm = await fx.createDemoFarmFixture();
  const { schema_version: _v, ...profile } = farm.profile;
  return fx.updateFarmFixture(farm.id, farm.input_version, {
    ...profile,
    irrigation_supply_mm_per_season: 0,
  });
};

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
});

describe("observations (Matheesha's normalized shape via Dulanjaya's endpoint)", () => {
  it("returns daily[] with per-variable coverage and missing dates; nulls stay null", async () => {
    const f = await fx.createDemoFarmFixture();
    const o = await fx.getObservationsFixture(f.id, "2026-01-01", "2026-01-31");
    expect(o.daily).toHaveLength(31);
    expect(o.coverage.precipitation_valid_days).toBe(31);
    expect(o.coverage.temperature_valid_days).toBeLessThan(31);
    expect(o.coverage.available_days).toBe(o.coverage.temperature_valid_days);
    expect(o.daily!.some((d) => d.temperature_c === null)).toBe(true);
    expect(o.missing_data!.temperature_c.length).toBe(31 - o.coverage.temperature_valid_days!);
    expect(typeof o.spatial_resolution).toBe("object");
    expect(o.data_kind).toBe("synthetic");
  });

  it("rejects an end date of today (UTC), like the backend", async () => {
    const f = await fx.createDemoFarmFixture();
    await expect(fx.getObservationsFixture(f.id, utcDate(-5), utcDate(0))).rejects.toMatchObject({ status: 422 });
    await expect(fx.getObservationsFixture(f.id, utcDate(-5), utcDate(-1))).resolves.toBeTruthy();
  });
});

describe("rotation-score-0.1 (synthetic fixture implementation)", () => {
  it("uses the three named components on a 0–100 scale, higher_is_better", async () => {
    const f = await fx.createDemoFarmFixture();
    const a = await fx.createRotationFixture(f.id, rotationBody(1));
    for (const c of a.candidates) {
      expect(c.score_components.map((x) => x.name)).toEqual(["water_sufficiency", "crop_diversity", "scenario_resilience"]);
      for (const x of c.score_components) {
        expect(x.direction).toBe("higher_is_better");
        if (x.value !== null) expect(x.value).toBeGreaterThanOrEqual(0);
        if (x.value !== null) expect(x.value).toBeLessThanOrEqual(100);
      }
      expect(c.score).toBeGreaterThanOrEqual(0);
      expect(c.score).toBeLessThanOrEqual(100);
    }
  });

  it("baseline: scenario_resilience is null, its weight is 0, others renormalize", async () => {
    const f = await confirmRainfed();
    const c = (await fx.createRotationFixture(f.id, rotationBody(f.input_version))).candidates[0];
    const sr = comp(c, "scenario_resilience");
    expect(sr.value).toBeNull();
    expect(sr.requested_weight).toBe(0.2);
    expect(sr.effective_weight).toBe(0);
    expect(comp(c, "water_sufficiency").effective_weight).toBeCloseTo(0.5 / 0.8, 10);
    expect(comp(c, "crop_diversity").effective_weight).toBeCloseTo(0.3 / 0.8, 10);
    const expected = comp(c, "water_sufficiency").value! * (0.5 / 0.8) + comp(c, "crop_diversity").value! * (0.3 / 0.8);
    expect(c.score).toBeCloseTo(expected, 10);
  });

  it("crop_diversity = unique crops / length × 100", async () => {
    const f = await fx.createDemoFarmFixture();
    const a = await fx.createRotationFixture(f.id, { ...rotationBody(1), seasons: 4 });
    for (const c of a.candidates) {
      const ids = c.sequence.map((s) => s.crop_id);
      expect(comp(c, "crop_diversity").value).toBeCloseTo((new Set(ids).size / ids.length) * 100, 10);
    }
  });

  it("water_sufficiency = mean of min(100, available / high demand × 100) per season", async () => {
    const f = await confirmRainfed();
    const c = (await fx.createRotationFixture(f.id, rotationBody(f.input_version))).candidates[0];
    const ranges = asSeasonRanges(c.water_budget_range);
    const expected = ranges.reduce((a, r) => a + Math.min(100, (r.available_water_mm! / r.demand_high_mm!) * 100), 0) / ranges.length;
    expect(comp(c, "water_sufficiency").value).toBeCloseTo(expected, 10);
  });

  it("only climate weighted + no scenario → score unavailable (null), not 0", async () => {
    const f = await fx.createDemoFarmFixture();
    const a = await fx.createRotationFixture(f.id, rotationBody(1, { water: 0, soil: 0, climate: 1 }));
    expect(a.candidates.every((c) => c.score === null)).toBe(true);
  });

  it("ranks by score descending", async () => {
    const f = await fx.createDemoFarmFixture();
    const a = await fx.createRotationFixture(f.id, rotationBody(1));
    const scores = a.candidates.map((c) => c.score!);
    expect([...scores].sort((x, y) => y - x)).toEqual(scores);
  });

  it("returns enabled hard checks as {rule, passed, note}", async () => {
    const f = await fx.createDemoFarmFixture();
    const c = (await fx.createRotationFixture(f.id, rotationBody(1))).candidates[0];
    expect(c.constraint_checks.map((x) => x.rule)).toEqual(["catalog_review", "season_eligibility", "farmer_exclusion"]);
  });

  it("per-season water records; effective rainfall null; no placeholder fraction", async () => {
    const f = await confirmRainfed();
    const c = (await fx.createRotationFixture(f.id, rotationBody(f.input_version))).candidates[0];
    const ranges = asSeasonRanges(c.water_budget_range);
    expect(ranges).toHaveLength(3);
    expect(ranges.map((r) => r.season_index)).toEqual([1, 2, 3]);
    expect(ranges.map((r) => r.crop_id)).toEqual(c.sequence.map((s) => s.crop_id));
    expect(c.water_budget.effective_rainfall_mm).toBeNull();
    const r = ranges[0];
    expect(r.balance_low_mm).toBe(r.available_water_mm! - r.demand_high_mm!);
    expect(r.balance_high_mm).toBe(r.available_water_mm! - r.demand_low_mm!);
  });

  it("unknown irrigation keeps water screening unavailable, never rainfall-only", async () => {
    const f = await fx.createDemoFarmFixture();
    const candidate = (await fx.createRotationFixture(f.id, rotationBody(1))).candidates[0];
    const r = asSeasonRanges(candidate.water_budget_range)[0];
    expect(r.irrigation_mm).toBeNull();
    expect(r.available_water_mm).toBeNull();
    expect(r.balance_low_mm).toBeNull();
    expect(r.coverage_low_percent).toBeNull();
    expect((r.limitations ?? []).join(" ")).toMatch(/unavailable until it is confirmed/);
    expect(candidate.score_components.find((c) => c.name === "water_sufficiency")?.value).toBeNull();
  });

  it("exclusions report farmer_exclusion reasons and fewer plans", async () => {
    const f = await fx.createDemoFarmFixture();
    const { schema_version: _v, ...profile } = f.profile;
    const f2 = await fx.updateFarmFixture(f.id, 1, { ...profile, excluded_crop_ids: ["maize"] });
    const a = await fx.createRotationFixture(f.id, rotationBody(f2.input_version));
    expect(a.candidates.map((c) => c.candidate_id)).toEqual(["cand-2"]);
    expect(a.reasons!.join(" ")).toMatch(/farmer_exclusion failed \("maize"/);
    expect(a.reasons!.join(" ")).toMatch(/Only 1 feasible plan/);
  });
});

describe("scenarios", () => {
  it("recompute from the same baseline: scenario rainfall scaled, resilience computed, IDs stable", async () => {
    const f = await confirmRainfed();
    const a = await fx.createRotationFixture(f.id, rotationBody(f.input_version));
    const s = await fx.createScenarioFixture(a.analysis_id, -30);
    expect(s.baseline_analysis_id).toBe(a.analysis_id);
    const r = asSeasonRanges(s.candidates[0].water_budget_range)[0];
    expect(r.scenario_rainfall_mm).toBeCloseTo(r.baseline_rainfall_mm! * 0.7, 10);
    expect(comp(s.candidates[0], "scenario_resilience").value).not.toBeNull();
    expect(Object.keys(s.baseline_differences).sort()).toEqual(a.candidates.map((c) => c.candidate_id).sort());
  });
});

describe("assistant", () => {
  it("returns 422 UNSUPPORTED_LANGUAGE for si/ta, like Akash's service", async () => {
    const f = await fx.createDemoFarmFixture();
    const a = await fx.createRotationFixture(f.id, rotationBody(1));
    const body = { farm_id: f.id, analysis_id: a.analysis_id, message: "Why?" };
    await expect(fx.sendAssistantMessageFixture({ ...body, language: "si" })).rejects.toMatchObject({
      status: 422,
      code: "UNSUPPORTED_LANGUAGE",
    });
    const ok = await fx.sendAssistantMessageFixture({ ...body, language: "en" });
    expect(ok.source_ids).toContain(a.analysis_id);
  });
});
