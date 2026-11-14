import { beforeEach, describe, expect, it } from "vitest";
import { isAnalysisOutdated, selectCurrentAnalysis, useAppStore } from "./useAppStore";
import type { FarmEnvelope, RotationAnalysis, ScenarioResult } from "../types/api";

const farm = (id: string, v = 1): FarmEnvelope => ({
  id,
  input_version: v,
  profile: {
    schema_version: "0.1",
    data_kind: "synthetic",
    name: id,
    location: { latitude: 8, longitude: 80 },
    area_ha: 1,
    irrigation_supply_mm_per_season: null,
    crop_history: [],
    soil_tests: [],
    priority_weights: { water: 1, soil: 0, climate: 0 },
    excluded_crop_ids: [],
  },
});

const analysis = (id: string, farmId: string, v = 1): RotationAnalysis => ({
  analysis_id: id,
  farm_id: farmId,
  input_version: v,
  observation_id: null,
  catalog_version: "x",
  model_version: "x",
  data_kind: "synthetic",
  created_at: "2026-01-01T00:00:00Z",
  candidates: [],
  assumptions: [],
  source_refs: [],
  limitations: [],
});

const scenario = (id: string, baseline: string): ScenarioResult => ({
  scenario_id: id,
  baseline_analysis_id: baseline,
  parameters: { rainfall_change_pct: -30 },
  candidates: [],
  baseline_differences: {},
  limitations: [],
  data_kind: "synthetic",
});

beforeEach(() => {
  useAppStore.getState().clearFarm();
});

describe("useAppStore invariants", () => {
  it("drops old observations when the same farm is edited and rejects late results", () => {
    const s = useAppStore.getState();
    s.setFarm(farm("farm-A", 1));
    s.setLatestObservation({ farmId: "farm-A", observationId: "obs-old", inputVersion: 1 });
    s.setFarm(farm("farm-A", 2));
    expect(useAppStore.getState().latestObservation).toBeNull();
    expect(s.setLatestObservation({ farmId: "farm-A", observationId: "late", inputVersion: 1 })).toBe(false);
    expect(s.putAnalysis(analysis("late", "farm-A", 1))).toBe(false);
    expect(s.setLatestObservation({ farmId: "farm-A", observationId: "current", inputVersion: 2 })).toBe(true);
  });
  it("switching farm clears results so another farm's analysis is never shown", () => {
    const s = useAppStore.getState();
    s.setFarm(farm("farm-A"));
    s.putAnalysis(analysis("an-A", "farm-A"));
    s.selectCandidate("cand-1");
    useAppStore.getState().setFarm(farm("farm-B"));
    const now = useAppStore.getState();
    expect(now.selectedAnalysisId).toBeNull();
    expect(now.selectedCandidateId).toBeNull();
    expect(now.analyses).toEqual({});
    expect(selectCurrentAnalysis(now)).toBeNull();
  });

  it("ignores a late analysis response for a farm that is no longer selected", () => {
    useAppStore.getState().setFarm(farm("farm-B"));
    expect(useAppStore.getState().putAnalysis(analysis("an-A", "farm-A"))).toBe(false);
    expect(useAppStore.getState().selectedAnalysisId).toBeNull();
  });

  it("reloading the same farm with a new version keeps results but marks them outdated", () => {
    useAppStore.getState().setFarm(farm("farm-A", 1));
    useAppStore.getState().putAnalysis(analysis("an-A", "farm-A", 1));
    useAppStore.getState().setFarm(farm("farm-A", 2));
    const s = useAppStore.getState();
    const a = selectCurrentAnalysis(s);
    expect(a?.analysis_id).toBe("an-A");
    expect(isAnalysisOutdated(a, s.selectedFarmInputVersion)).toBe(true);
  });

  it("ignores scenarios whose baseline is no longer selected", () => {
    const s = useAppStore.getState();
    s.setFarm(farm("farm-A"));
    s.putAnalysis(analysis("an-1", "farm-A"));
    useAppStore.getState().putAnalysis(analysis("an-2", "farm-A"));
    expect(useAppStore.getState().putScenario(scenario("sc-1", "an-1"))).toBe(false);
    expect(useAppStore.getState().putScenario(scenario("sc-2", "an-2"))).toBe(true);
  });

  it("language changes keep farm and analysis selection", () => {
    useAppStore.getState().setFarm(farm("farm-A"));
    useAppStore.getState().putAnalysis(analysis("an-A", "farm-A"));
    useAppStore.getState().setLanguage("ta");
    const s = useAppStore.getState();
    expect(s.language).toBe("ta");
    expect(s.selectedFarmId).toBe("farm-A");
    expect(s.selectedAnalysisId).toBe("an-A");
  });
});
