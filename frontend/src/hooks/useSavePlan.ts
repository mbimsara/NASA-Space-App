/**
 * useSavePlan — save the selected candidate as the farm's plan.
 * Refuses outdated analyses client-side (the server also returns 409).
 * Owner: Shehani.
 */
import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { api } from "../api";
import { isAnalysisOutdated, useAppStore } from "./useAppStore";
import type { RotationAnalysis } from "../types/api";

export function useSavePlan() {
  const navigate = useNavigate();
  const farm = useAppStore((s) => s.farm);
  const rememberPlan = useAppStore((s) => s.rememberPlan);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<unknown>(null);

  const save = async (analysis: RotationAnalysis, candidateId: string, scenarioId?: string) => {
    if (!farm || analysis.farm_id !== farm.id || isAnalysisOutdated(analysis, farm.input_version)) return;
    setSaving(true);
    setError(null);
    try {
      const { plan_id } = await api.savePlan(farm.id, {
        analysis_id: analysis.analysis_id,
        candidate_id: candidateId,
        scenario_id: scenarioId,
        expected_input_version: farm.input_version,
      });
      const cand = analysis.candidates.find((c) => c.candidate_id === candidateId);
      const crops = cand?.sequence.map((s) => s.crop_name ?? s.crop_id).join(" → ") ?? candidateId;
      rememberPlan({ id: plan_id, name: `${farm.profile.name}: ${crops}`, farmId: farm.id });
      navigate(`/plans/${plan_id}`);
    } catch (err) {
      setError(err);
    } finally {
      setSaving(false);
    }
  };

  return { save, saving, error };
}
