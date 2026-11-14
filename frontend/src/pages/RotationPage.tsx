/**
 * RotationPage — rotation workspace: farmer-priority controls, generate, compare,
 * select and save. Outdated analyses are flagged and cannot be saved.
 * Owner: Shehani. Score formula and catalog values: Bhagya.
 */
import { useEffect, useState } from "react";
import { Link, useLocation } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { api, USE_FIXTURES } from "../api";
import { isAbortError } from "../api/requestGuard";
import { isAnalysisOutdated, selectCurrentAnalysis, useAppStore } from "../hooks/useAppStore";
import { useLatestRequest } from "../hooks/useLatestRequest";
import { useCanWrite } from "../hooks/useCanWrite";
import { useSavePlan } from "../hooks/useSavePlan";
import { LoadingSpinner } from "../components/ui/LoadingSpinner";
import { ErrorMessage } from "../components/ui/ErrorMessage";
import { SyntheticDataBanner } from "../components/ui/SyntheticDataBanner";
import { OutdatedAnalysisBanner } from "../components/ui/OutdatedAnalysisBanner";
import { SourceBadge } from "../components/ui/SourceBadge";
import { IrrigationUnknownNotice } from "../components/ui/IrrigationUnknownNotice";
import { CandidateCard } from "../components/rotations/CandidateCard";
import { CATALOG_VERSION, loadedCatalog } from "../catalog";
import { SEASON_LABELS, type SeasonLabel } from "../api/client";
import { normalizeWeights } from "../utils/validation";
import type { PriorityWeights } from "../types/api";

export function RotationPage() {
  const { t } = useTranslation();
  const farm = useAppStore((s) => s.farm)!;
  const analysis = useAppStore(selectCurrentAnalysis);
  const putAnalysis = useAppStore((s) => s.putAnalysis);
  const selectedCandidateId = useAppStore((s) => s.selectedCandidateId);
  const selectCandidate = useAppStore((s) => s.selectCandidate);
  const latestObservation = useAppStore((s) => s.latestObservation);
  const guard = useLatestRequest();
  const canWrite = useCanWrite();
  const { save, saving, error: saveError } = useSavePlan();
  const { hash } = useLocation();

  // Result navigation: /rotations#candidate-<id> (e.g. from assistant citations) jumps to that plan.
  useEffect(() => {
    if (!hash.startsWith("#candidate-")) return;
    const el = document.getElementById(decodeURIComponent(hash.slice(1)));
    if (el) {
      el.scrollIntoView({ block: "start" });
      el.focus({ preventScroll: true });
    }
  }, [hash, analysis]);

  const [seasons, setSeasons] = useState(analysis?.candidates[0]?.sequence.length ?? 3);
  const defaultLabels = (n: number): SeasonLabel[] => Array.from({ length: n }, (_, i) => (i % 2 === 0 ? "maha" : "yala"));
  const [seasonLabels, setSeasonLabels] = useState<SeasonLabel[]>(() => defaultLabels(seasons));
  const changeSeasons = (n: number) => {
    setSeasons(n);
    setSeasonLabels((cur) => [...cur.slice(0, n), ...defaultLabels(n).slice(cur.length)].slice(0, n));
  };
  const [weights, setWeights] = useState<PriorityWeights>(farm.profile.priority_weights);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<unknown>(null);

  const outdated = isAnalysisOutdated(analysis, farm.input_version);
  // The live API requires an observation snapshot for this farm at its current version.
  const observationId =
    latestObservation && latestObservation.farmId === farm.id && latestObservation.inputVersion === farm.input_version
      ? latestObservation.observationId
      : null;
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
          // Only reference an observation loaded for this farm at its current version.
          observation_id: observationId,
          seasons,
          season_labels: seasonLabels,
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
      <IrrigationUnknownNotice farmId={farm.id} irrigation={farm.profile.irrigation_supply_mm_per_season} />
      {loadedCatalog.ok && loadedCatalog.approvedCrops.length === 0 && (
        <div className="notice notice-info" role="note">
          {USE_FIXTURES ? t("catalog.emptyNoteFixture") : t("catalog.emptyNoteLive")}
        </div>
      )}

      <OutdatedAnalysisBanner isOutdated={outdated} onRerun={observationId ? runRotation : undefined} />
      {!observationId && (
        <div className="notice notice-warn" role="note">
          {t("rotation.needsObservation")} <Link to={`/farms/${farm.id}`}>{t("rotation.loadObservations")}</Link>
        </div>
      )}

      <div className="card">
        <div className="row">
          <div className="field">
            <label htmlFor="seasons-select">{t("rotation.seasons")}</label>
            <select id="seasons-select" value={seasons} onChange={(e) => changeSeasons(Number(e.target.value))}>
              {[3, 4, 5].map((n) => (
                <option key={n} value={n}>
                  {n}
                </option>
              ))}
            </select>
          </div>
        </div>
        <fieldset style={{ border: 0, padding: 0, margin: "12px 0 0" }}>
          <legend style={{ fontWeight: 600 }}>{t("rotation.seasonLabels")}</legend>
          <div className="row" style={{ alignItems: "flex-start" }}>
            {seasonLabels.map((label, i) => (
              <div className="field" key={i}>
                <label htmlFor={`season-label-${i}`}>{t("rotation.seasonN", { n: i + 1 })}</label>
                <select
                  id={`season-label-${i}`}
                  value={label}
                  onChange={(e) => setSeasonLabels((ls) => ls.map((l, j) => (j === i ? (e.target.value as SeasonLabel) : l)))}
                >
                  {SEASON_LABELS.map((s) => (
                    <option key={s} value={s}>
                      {t(`rotation.seasonLabel.${s}`)}
                    </option>
                  ))}
                </select>
              </div>
            ))}
          </div>
          <p className="muted">{t("rotation.seasonLabelsHelp")}</p>
        </fieldset>
        <fieldset style={{ border: 0, padding: 0, margin: "12px 0 0" }}>
          <legend style={{ fontWeight: 600 }}>{t("rotation.mode")}</legend>
          <div className="row" style={{ alignItems: "flex-start" }}>
            {(["standard", "soilRevive", "farmRecovery"] as const).map((m) => (
              <label key={m} style={{ display: "flex", gap: 6, alignItems: "center", fontWeight: 400, opacity: m === "standard" ? 1 : 0.75 }}>
                <input type="radio" name="planning-mode" checked={m === "standard"} disabled={m !== "standard"} readOnly />
                {t(`rotation.modes.${m}`)}
                {m !== "standard" && <span className="badge-planned">{t("common.roadmapFeature")}</span>}
              </label>
            ))}
          </div>
          <p className="muted">
            {t("rotation.modeHelp")} <Link to="/roadmap">{t("nav.roadmap")}</Link>
          </p>
        </fieldset>
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
          disabled={loading || !(weightTotal > 0) || !canWrite || !observationId}
        >
          {loading ? t("common.loading") : analysis ? t("rotation.rerun") : t("rotation.run")}
        </button>
        {!(weightTotal > 0) && <span className="field-error"> {t("rotation.weightsZero")}</span>}
      </div>

      {!canWrite && <p className="muted" role="note">{t("offline.writeBlocked")}</p>}
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
          {(analysis.reasons?.length ?? 0) > 0 && (
            <div
              className={`notice ${analysis.candidates.length === 0 ? "notice-warn" : "notice-info"}`}
              role={analysis.candidates.length === 0 ? "alert" : "note"}
            >
              <strong>{analysis.candidates.length === 0 ? t("rotation.infeasibleTitle") : t("rotation.reasonsTitle")}</strong>
              <ul style={{ margin: "4px 0 0" }}>
                {analysis.reasons!.map((r, i) => (
                  <li key={i}>{r}</li>
                ))}
              </ul>
            </div>
          )}
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
                        disabled={outdated || saving || !canWrite}
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
