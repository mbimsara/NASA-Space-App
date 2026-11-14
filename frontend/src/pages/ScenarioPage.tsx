/**
 * ScenarioPage — hypothetical rainfall change recomputed from the SAME baseline analysis.
 * Owner: Shehani. Recalculation model: Bhagya (water budget) + Matheesha (climate inputs).
 */
import { useState } from "react";
import { Link } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { api } from "../api";
import { isAbortError } from "../api/requestGuard";
import {
  isAnalysisOutdated,
  selectCurrentAnalysis,
  selectCurrentScenario,
  useAppStore,
} from "../hooks/useAppStore";
import { useLatestRequest } from "../hooks/useLatestRequest";
import { useCanWrite } from "../hooks/useCanWrite";
import { useSavePlan } from "../hooks/useSavePlan";
import { LoadingSpinner } from "../components/ui/LoadingSpinner";
import { ErrorMessage } from "../components/ui/ErrorMessage";
import { OutdatedAnalysisBanner } from "../components/ui/OutdatedAnalysisBanner";
import { SyntheticDataBanner } from "../components/ui/SyntheticDataBanner";
import { IrrigationUnknownNotice } from "../components/ui/IrrigationUnknownNotice";
import { SeasonWaterTable } from "../components/rotations/SeasonWaterTable";
import { asSeasonRanges } from "../utils/format";
import { BaselineVsScenario } from "../components/scenarios/BaselineVsScenario";
import { ObservationRainfallCard } from "../components/scenarios/ObservationRainfallCard";

export function ScenarioPage() {
  const { t } = useTranslation();
  const farm = useAppStore((s) => s.farm)!;
  const baseline = useAppStore(selectCurrentAnalysis);
  const scenario = useAppStore(selectCurrentScenario);
  const putScenario = useAppStore((s) => s.putScenario);
  const clearScenario = useAppStore((s) => s.clearScenario);
  const selectedCandidateId = useAppStore((s) => s.selectedCandidateId);
  const selectCandidate = useAppStore((s) => s.selectCandidate);
  const guard = useLatestRequest();
  const canWrite = useCanWrite();
  const { save, saving, error: saveError } = useSavePlan();

  const [rainfallChange, setRainfallChange] = useState(scenario?.parameters.rainfall_change_pct ?? -30);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<unknown>(null);

  if (!baseline) {
    return (
      <div className="page">
        <h1>{t("scenario.title")}</h1>
        <div className="card muted">
          {t("scenario.needsBaseline")}{" "}
          <Link to={`/farms/${farm.id}/rotations`}>{t("rotation.run")}</Link>
        </div>
      </div>
    );
  }

  const runScenario = async () => {
    const ticket = guard.next();
    setLoading(true);
    setError(null);
    try {
      const result = await api.createScenario(baseline.analysis_id, rainfallChange, ticket.signal);
      // putScenario ignores results whose baseline is no longer selected.
      if (ticket.isCurrent()) putScenario(result);
    } catch (err) {
      if (ticket.isCurrent() && !isAbortError(err)) setError(err);
    } finally {
      if (ticket.isCurrent()) setLoading(false);
    }
  };

  const stale = scenario && scenario.parameters.rainfall_change_pct !== rainfallChange;

  return (
    <div className="page">
      <h1>{t("scenario.title")}</h1>
      <OutdatedAnalysisBanner isOutdated={isAnalysisOutdated(baseline, farm.input_version)} />
      <IrrigationUnknownNotice farmId={farm.id} irrigation={farm.profile.irrigation_supply_mm_per_season} />

      <div className="card">
        <p className="muted" style={{ marginTop: 0 }}>
          {t("scenario.baselineInfo", { id: baseline.analysis_id, date: new Date(baseline.created_at).toLocaleString() })}
        </p>
        <label htmlFor="rainfall-slider" style={{ fontWeight: 600, display: "block", marginBottom: 8 }}>
          {t("scenario.rainfallChange")}: {rainfallChange > 0 ? "+" : ""}
          {rainfallChange}%
        </label>
        <input
          id="rainfall-slider"
          type="range"
          min={-100}
          max={100}
          step={5}
          value={rainfallChange}
          onChange={(e) => setRainfallChange(Number(e.target.value))}
          aria-valuetext={`${rainfallChange}%`}
          style={{ width: "100%" }}
        />
        <div className="muted" style={{ display: "flex", justifyContent: "space-between" }}>
          <span>−100%</span>
          <span>0 ({t("scenario.baseline")})</span>
          <span>+100%</span>
        </div>
        <div className="notice notice-warn" style={{ marginTop: 12 }}>
          {t("scenario.hypotheticalLabel")}
        </div>
        <div className="row">
          <button type="button" className="btn btn-secondary" onClick={runScenario} disabled={loading || !canWrite}>
            {loading ? t("common.loading") : t("scenario.run")}
          </button>
          {scenario && (
            <button type="button" className="btn" onClick={clearScenario}>
              {t("scenario.backToBaseline")}
            </button>
          )}
        </div>
        {!canWrite && <p className="muted" role="note">{t("offline.writeBlocked")}</p>}
        {stale && <p className="muted">{t("scenario.sliderChanged")}</p>}
      </div>

      {loading && <LoadingSpinner />}
      {!loading && error != null && <ErrorMessage error={error} onRetry={runScenario} />}

      {!loading && scenario && (
        <>
          <SyntheticDataBanner dataKind={scenario.data_kind} />
          <BaselineVsScenario baseline={baseline} scenario={scenario} />
          {scenario.observation_rainfall && <ObservationRainfallCard rain={scenario.observation_rainfall} />}
          {(() => {
            const c = scenario.candidates.find((x) => x.candidate_id === selectedCandidateId) ?? scenario.candidates[0];
            if (!c) return null;
            const outdated = isAnalysisOutdated(baseline, farm.input_version);
            return (
              <div className="card">
                <div className="field" style={{ maxWidth: 420, marginBottom: 12 }}>
                  <label htmlFor="scenario-plan">{t("scenario.choosePlan")}</label>
                  <select id="scenario-plan" value={c.candidate_id} onChange={(e) => selectCandidate(e.target.value)}>
                    {scenario.candidates.map((x) => (
                      <option key={x.candidate_id} value={x.candidate_id}>
                        {x.candidate_id}: {x.sequence.map((q) => q.crop_name ?? q.crop_id).join(" → ")}
                      </option>
                    ))}
                  </select>
                </div>
                <h2 style={{ marginTop: 0, fontSize: "1.05rem" }}>
                  {t("scenario.seasonDetail", { plan: c.candidate_id, crops: c.sequence.map((x) => x.crop_name ?? x.crop_id).join(" → ") })}
                </h2>
                <SeasonWaterTable ranges={asSeasonRanges(c.water_budget_range)} sequence={c.sequence} />
                <div className="row" style={{ marginTop: 12 }}>
                  <button
                    type="button"
                    className="btn btn-primary"
                    disabled={saving || outdated || !canWrite}
                    title={outdated ? t("rotation.cannotSaveOutdated") : undefined}
                    onClick={() => save(baseline, c.candidate_id, scenario.scenario_id)}
                  >
                    {saving ? t("common.loading") : t("scenario.saveScenarioPlan")}
                  </button>
                  <span className="muted" style={{ fontSize: 12 }}>
                    {t("scenario.saveScenarioHelp")}
                  </span>
                </div>
                <ErrorMessage error={saveError} />
              </div>
            );
          })()}
          <Link className="btn" to={`/farms/${farm.id}/assistant`}>
            {t("scenario.askAssistant")} →
          </Link>
        </>
      )}
    </div>
  );
}
