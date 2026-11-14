/**
 * Global application state (Zustand, persisted to localStorage).
 * Owner: Shehani.
 *
 * Invariants:
 * - Switching to a different farm ALWAYS clears analysis/scenario/candidate selections
 *   and drops cached results for other farms, so one farm can never show another's results.
 * - Results are only accepted for the currently selected farm / baseline analysis
 *   (`putAnalysis` / `putScenario` return false and ignore stale responses).
 * - Changing language never touches farm or analysis state.
 */
import { create } from "zustand";
import { createJSONStorage, persist } from "zustand/middleware";
import type { FarmEnvelope, Language, RotationAnalysis, ScenarioResult } from "../types/api";

export interface RecentItem {
  id: string;
  name: string;
}

export interface AppState {
  farm: FarmEnvelope | null;
  selectedFarmId: string | null;
  selectedFarmInputVersion: number | null;
  selectedAnalysisId: string | null;
  selectedScenarioId: string | null;
  selectedCandidateId: string | null;
  analyses: Record<string, RotationAnalysis>;
  scenarios: Record<string, ScenarioResult>;
  /** Observation loaded for the selected farm; sent with rotation requests. */
  latestObservation: { farmId: string; observationId: string; inputVersion: number } | null;
  recentFarms: RecentItem[];
  recentPlans: (RecentItem & { farmId: string })[];
  language: Language;

  setFarm: (env: FarmEnvelope) => void;
  selectFarm: (farmId: string, inputVersion: number) => void;
  clearFarm: () => void;
  putAnalysis: (analysis: RotationAnalysis) => boolean;
  setLatestObservation: (o: { farmId: string; observationId: string; inputVersion: number }) => boolean;
  selectAnalysis: (analysisId: string) => void;
  clearAnalysis: () => void;
  putScenario: (scenario: ScenarioResult) => boolean;
  selectScenario: (scenarioId: string) => void;
  clearScenario: () => void;
  selectCandidate: (candidateId: string) => void;
  clearCandidate: () => void;
  rememberPlan: (plan: RecentItem & { farmId: string }) => void;
  setLanguage: (lang: Language) => void;
}

const cleared = {
  selectedAnalysisId: null,
  selectedScenarioId: null,
  selectedCandidateId: null,
  analyses: {},
  scenarios: {},
  latestObservation: null,
} as const;

function upsertRecent<T extends RecentItem>(list: T[], item: T, max = 8): T[] {
  return [item, ...list.filter((x) => x.id !== item.id)].slice(0, max);
}

export function initialLanguage(): Language {
  try {
    const raw = localStorage.getItem("agrosphere_app");
    const lang = raw ? JSON.parse(raw)?.state?.language : null;
    if (lang === "si" || lang === "ta" || lang === "en") return lang;
  } catch {
    /* storage unavailable */
  }
  return "en";
}

export const useAppStore = create<AppState>()(
  persist(
    (set, get) => ({
      farm: null,
      selectedFarmId: null,
      selectedFarmInputVersion: null,
      selectedAnalysisId: null,
      selectedScenarioId: null,
      selectedCandidateId: null,
      analyses: {},
      scenarios: {},
      latestObservation: null,
      recentFarms: [],
      recentPlans: [],
      language: "en",

      setFarm: (env) => {
        const sameFarm = get().selectedFarmId === env.id;
        set((s) => ({
          ...(sameFarm ? {} : cleared),
          farm: env,
          selectedFarmId: env.id,
          selectedFarmInputVersion: env.input_version,
          recentFarms: upsertRecent(s.recentFarms, { id: env.id, name: env.profile.name }),
        }));
      },

      selectFarm: (farmId, inputVersion) => {
        const sameFarm = get().selectedFarmId === farmId;
        set({
          ...(sameFarm ? {} : { ...cleared, farm: null }),
          selectedFarmId: farmId,
          selectedFarmInputVersion: inputVersion,
        });
      },

      clearFarm: () =>
        set({ ...cleared, farm: null, selectedFarmId: null, selectedFarmInputVersion: null }),

      putAnalysis: (analysis) => {
        if (analysis.farm_id !== get().selectedFarmId) return false;
        set((s) => ({
          analyses: { ...s.analyses, [analysis.analysis_id]: analysis },
          selectedAnalysisId: analysis.analysis_id,
          selectedScenarioId: null,
          selectedCandidateId: null,
        }));
        return true;
      },

      setLatestObservation: (o) => {
        if (o.farmId !== get().selectedFarmId) return false;
        set({ latestObservation: o });
        return true;
      },

      selectAnalysis: (analysisId) =>
        set({ selectedAnalysisId: analysisId, selectedScenarioId: null, selectedCandidateId: null }),
      clearAnalysis: () =>
        set({ selectedAnalysisId: null, selectedScenarioId: null, selectedCandidateId: null }),

      putScenario: (scenario) => {
        if (scenario.baseline_analysis_id !== get().selectedAnalysisId) return false;
        set((s) => ({
          scenarios: { ...s.scenarios, [scenario.scenario_id]: scenario },
          selectedScenarioId: scenario.scenario_id,
        }));
        return true;
      },

      // Candidate IDs are stable across baseline and scenario, so keep the selection.
      selectScenario: (scenarioId) => set({ selectedScenarioId: scenarioId }),
      clearScenario: () => set({ selectedScenarioId: null }),

      selectCandidate: (candidateId) => set({ selectedCandidateId: candidateId }),
      clearCandidate: () => set({ selectedCandidateId: null }),

      rememberPlan: (plan) => set((s) => ({ recentPlans: upsertRecent(s.recentPlans, plan) })),

      setLanguage: (lang) => set({ language: lang }),
    }),
    {
      name: "agrosphere_app",
      // v2: rotation-score-0.1 shapes (0–100 scores, per-season water). Older cached results are dropped.
      version: 2,
      migrate: (persisted, version) => {
        const p = (persisted ?? {}) as Partial<AppState>;
        if (version < 2) {
          return {
            ...p,
            analyses: {},
            scenarios: {},
            selectedAnalysisId: null,
            selectedScenarioId: null,
            selectedCandidateId: null,
            latestObservation: null,
            recentPlans: [],
          } as AppState;
        }
        return p as AppState;
      },
      storage: createJSONStorage(() => localStorage),
      partialize: (s) => ({
        selectedFarmId: s.selectedFarmId,
        selectedFarmInputVersion: s.selectedFarmInputVersion,
        selectedAnalysisId: s.selectedAnalysisId,
        selectedScenarioId: s.selectedScenarioId,
        selectedCandidateId: s.selectedCandidateId,
        analyses: s.analyses,
        scenarios: s.scenarios,
        latestObservation: s.latestObservation,
        recentFarms: s.recentFarms,
        recentPlans: s.recentPlans,
        language: s.language,
      }),
    },
  ),
);

/** Selected analysis, only if it belongs to the selected farm. */
export function selectCurrentAnalysis(s: AppState): RotationAnalysis | null {
  const a = s.selectedAnalysisId ? s.analyses[s.selectedAnalysisId] : undefined;
  return a && a.farm_id === s.selectedFarmId ? a : null;
}

/** Selected scenario, only if it is based on the selected analysis. */
export function selectCurrentScenario(s: AppState): ScenarioResult | null {
  const sc = s.selectedScenarioId ? s.scenarios[s.selectedScenarioId] : undefined;
  return sc && sc.baseline_analysis_id === s.selectedAnalysisId ? sc : null;
}

/** An analysis is outdated when the farm profile changed after it was computed. */
export function isAnalysisOutdated(analysis: { input_version: number } | null, farmInputVersion: number | null): boolean {
  return !!analysis && farmInputVersion !== null && analysis.input_version !== farmInputVersion;
}
