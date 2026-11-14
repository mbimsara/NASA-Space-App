/**
 * RotationPage — rotation workspace: farmer-priority controls, generate, compare,
 * select and save. Outdated analyses are flagged and cannot be saved.
 * Owner: Shehani. Score formula and catalog values: Bhagya.
 */
import { useState } from "react";
import { Link } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { api } from "../api";
import { isAbortError } from "../api/requestGuard";
import { isAnalysisOutdated, selectCurrentAnalysis, useAppStore } from "../hooks/useAppStore";
import { useLatestRequest } from "../hooks/useLatestRequest";
import { useSavePlan } from "../hooks/useSavePlan";
import { LoadingSpinner } from "../components/ui/LoadingSpinner";
import { ErrorMessage } from "../components/ui/ErrorMessage";
import { SyntheticDataBanner } from "../components/ui/SyntheticDataBanner";
import { OutdatedAnalysisBanner } from "../components/ui/OutdatedAnalysisBanner";
import { SourceBadge } from "../components/ui/SourceBadge";
import { CandidateCard } from "../components/rotations/CandidateCard";
import { CATALOG_VERSION, loadedCatalog } from "../catalog";
import { normalizeWeights } from "../utils/validation";
import type { PriorityWeights } from "../types/api";

export function RotationPage() {
  const { t } = useTranslation();
  const farm = useAppStore((s) => s.farm)!;
  const analysis = useAppStore(selectCurrentAnalysis);
  const putAnalysis = useAppStore((s) => s.putAnalysis);
  const selectedCandidateId = useAppStore((s) => s.selectedCandidateId);
  const selectCandidate = useAppStore((s) => s.selectCandidate);
  const guard = useLatestRequest();
  const { save, saving, error: saveError } = useSavePlan();

  const [seasons, setSeasons] = useState(analysis?.candidates[0]?.sequence.length ?? 3);
  const [weights, setWeights] = useState<PriorityWeights>(farm.profile.priority_weights);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<unknown>(null);

  const outdated = isAnalysisOutdated(analysis, farm.input_version);
  const weightTotal = weights.water + weights.soil + weights.climate;

  const runRotation = async () => {
    const ticket = guard.next();
    setLoading(true);
    setError(null);
    try {
      const result = await api.createRotation(
        farm.id,
        {
          input_version: farm.input_version,
          observation_id: null,
          seasons,
          catalog_version: CATALOG_VERSION,
          priority_weights: normalizeWeights(weights),
        },
        ticket.signal,
      );
      // putAnalysis ignores results for a farm that is no longer selected.
      if (ticket.isCurrent()) putAnalysis(result);
    } catch (err) {
      if (ticket.isCurrent() && !isAbortError(err)) setError(err);
    } finally {
      if (ticket.isCurrent()) setLoading(false);
    }
  };

  return (
    <div className="page">
      <h1>{t("rotation.title")}</h1>

      {!loadedCatalog.ok && (
        <div className="notice notice-warn" role="alert">
          {t("catalog.invalidBlocking")} <Link to="/catalog">{t("nav.catalog")}</Link>
        </div>
      )}
      {loadedCatalog.ok && loadedCatalog.approvedCrops.length === 0 && (
        <div className="notice notice-info" role="note">
          {t("catalog.emptyNote")}
        </div>
      )}

      <OutdatedAnalysisBanner isOutdated={outdated} onRerun={runRotation} />

      <div className="card">
        <div className="row">
          <div className="field">
            <label htmlFor="seasons-select">{t("rotation.seasons")}</label>
            <select id="seasons-select" value={seasons} onChange={(e) => setSeasons(Number(e.target.value))}>
              {[3, 4, 5].map((n) => (
                <option key={n} value={n}>
                  {n}
                </option>
              ))}
            </select>
          </div>
        </div>
        <fieldset style={{ border: 0, padding: 0, margin: "12px 0 0" }}>
          <legend style={{ fontWeight: 600 }}>{t("rotation.priorityControls")}</legend>
          <div className="grid-2">
            {(["water", "soil", "climate"] as const).map((k) => (
              <div className="field" key={k}>
                <label htmlFor={`rw-${k}`} style={{ display: "flex", justifyContent: "space-between" }}>
                  <span>{t(`farm.priority${k.charAt(0).toUpperCase() + k.slice(1)}`)}</span>
                  <span>{weightTotal > 0 ? `${Math.round((weights[k] / weightTotal) * 100)}%` : "—"}</span>
                </label>
                <input
                  id={`rw-${k}`}
                  type="range"
                  min={0}
                  max={1}
                  step={0.1}
                  value={weights[k]}
                  onChange={(e) => setWeights((w) => ({ ...w, [k]: Number(e.target.value) }))}
                  style={{ padding: 0 }}
                />
              </div>
            ))}
          </div>
          <p className="muted">{t("rotation.priorityHelp")}</p>
        </fieldset>
        <button
          type="button"
          className="btn btn-primary"
          onClick={runRotation}
          disabled={loading || !(weightTotal > 0)}
        >
          {loading ? t("common.loading") : analysis ? t("rotation.rerun") : t("rotation.run")}
        </button>
        {!(weightTotal > 0) && <span className="field-error"> {t("rotation.weightsZero")}</span>}
      </div>

      {loading && <LoadingSpinner label={t("rotation.running")} />}
      {!loading && error != null && <ErrorMessage error={error} onRetry={runRotation} />}
      <ErrorMessage error={saveError} />

      {!loading && !analysis && error == null && <p className="muted">{t("rotation.empty")}</p>}

      {!loading && analysis && (
        <>
          <SyntheticDataBanner dataKind={analysis.data_kind} />
          <p className="muted">
            {analysis.candidates.length === 0
              ? t("rotation.noCandidates")
              : t("rotation.candidates", { count: analysis.candidates.length })}
            {analysis.candidates.length > 0 && analysis.candidates.length < 3 && ` ${t("rotation.fewerThanThree")}`}
          </p>
          {analysis.limitations.length > 0 && (
            <div className="notice notice-warn">
              <strong>{t("common.limitations")}</strong>
              <ul style={{ margin: "4px 0 0" }}>
                {analysis.limitations.map((l, i) => (
                  <li key={i}>{l}</li>
                ))}
              </ul>
            </div>
          )}

          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(280px, 1fr))", gap: 16 }}>
            {analysis.candidates.map((cand, i) => {
              const isSelected = cand.candidate_id === selectedCandidateId;
              return (
                <CandidateCard key={cand.candidate_id} candidate={cand} rank={i + 1} selected={isSelected}>
                  <div className="row" style={{ marginTop: 12 }}>
                    <button
                      type="button"
                      className="btn"
                      aria-pressed={isSelected}
                      onClick={() => selectCandidate(cand.candidate_id)}
                    >
                      {isSelected ? `✓ ${t("rotation.selected")}` : t("rotation.selectPlan")}
                    </button>
                    {isSelected && (
                      <button
                        type="button"
                        className="btn btn-primary"
                        disabled={outdated || saving}
                        title={outdated ? t("rotation.cannotSaveOutdated") : undefined}
                        onClick={() => save(analysis, cand.candidate_id)}
                      >
                        {saving ? t("common.loading") : t("rotation.savePlan")}
                      </button>
                    )}
                  </div>
                </CandidateCard>
              );
            })}
          </div>

          {selectedCandidateId && (
            <div className="row" style={{ marginTop: 8 }}>
              <Link className="btn btn-secondary" to={`/farms/${farm.id}/scenario`}>
                {t("rotation.toScenario")} →
              </Link>
              <Link className="btn" to={`/farms/${farm.id}/assistant`}>
                {t("rotation.toAssistant")} →
              </Link>
            </div>
          )}

          <SourceBadge sourceRefs={analysis.source_refs} dataKind={analysis.data_kind} />
          <p className="muted">
            {t("common.analysisDate")}: {new Date(analysis.created_at).toLocaleString()} · {analysis.analysis_id} ·{" "}
            {t("plan.catalogVersion")}: {analysis.catalog_version} · {t("plan.modelVersion")}: {analysis.model_version} ·{" "}
            {t("rotation.inputVersion")}: {analysis.input_version}
          </p>
          {analysis.assumptions.length > 0 && (
            <details className="muted">
              <summary style={{ cursor: "pointer" }}>{t("common.assumptions")}</summary>
              <ul>
                {analysis.assumptions.map((a, i) => (
                  <li key={i}>{a}</li>
                ))}
              </ul>
            </details>
          )}
        </>
      )}
    </div>
  );
}
