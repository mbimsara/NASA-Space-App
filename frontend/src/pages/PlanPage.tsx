/**
 * PlanPage — reopen a saved plan by ID (survives reload), with its input snapshot,
 * evidence and versions; warns when the farm changed afterwards; print-friendly.
 * Owner: Shehani. Report/export endpoint (Dulanjaya) to be wired when available.
 */
import { useCallback, useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { api } from "../api";
import { isAbortError } from "../api/requestGuard";
import { useLatestRequest } from "../hooks/useLatestRequest";
import { LoadingSpinner } from "../components/ui/LoadingSpinner";
import { ErrorMessage } from "../components/ui/ErrorMessage";
import { SyntheticDataBanner } from "../components/ui/SyntheticDataBanner";
import { SourceBadge } from "../components/ui/SourceBadge";
import { CandidateCard } from "../components/rotations/CandidateCard";
import type { FarmEnvelope, SavedPlan } from "../types/api";

export function PlanPage() {
  const { t } = useTranslation();
  const { planId } = useParams<{ planId: string }>();
  const guard = useLatestRequest();
  const [plan, setPlan] = useState<SavedPlan | null>(null);
  const [farm, setFarm] = useState<FarmEnvelope | null>(null);
  const [error, setError] = useState<unknown>(null);

  const load = useCallback(async () => {
    if (!planId) return;
    const ticket = guard.next();
    setError(null);
    setPlan(null);
    try {
      const p = await api.getPlan(planId, ticket.signal);
      if (!ticket.isCurrent()) return;
      setPlan(p);
      const f = await api.getFarm(p.farm_id, ticket.signal).catch(() => null);
      if (ticket.isCurrent()) setFarm(f);
    } catch (err) {
      if (ticket.isCurrent() && !isAbortError(err)) setError(err);
    }
  }, [planId, guard]);

  useEffect(() => {
    // Loading the plan selected by the route is the synchronization boundary.
    // oxlint-disable-next-line react/set-state-in-effect
    load();
  }, [load]);

  if (error) {
    return (
      <div className="page">
        <ErrorMessage error={error} onRetry={load} />
        <Link to="/">{t("nav.home")}</Link>
      </div>
    );
  }
  if (!plan) return <LoadingSpinner />;

  const snap = plan.analysis_snapshot;
  const outdated = farm !== null && farm.input_version !== plan.input_version;
  const profile = plan.input_snapshot;

  return (
    <div className="page">
      <h1>{t("plan.title")}</h1>
      <p className="muted">
        {t("plan.savedAt", { date: new Date(plan.created_at).toLocaleString() })} · {plan.plan_id}
      </p>

      {outdated && (
        <div className="notice notice-warn no-print" role="alert">
          {t("plan.outdatedBanner")}{" "}
          <Link to={`/farms/${plan.farm_id}/rotations`}>{t("plan.reanalyze")}</Link>
        </div>
      )}
      {snap.data_kind && <SyntheticDataBanner dataKind={snap.data_kind} />}

      <div className="row no-print" style={{ marginBottom: 16 }}>
        <button type="button" className="btn" onClick={() => window.print()}>
          🖨 {t("plan.export")}
        </button>
        <Link className="btn" to={`/farms/${plan.farm_id}`}>
          {t("plan.openFarm")}
        </Link>
      </div>

      <h2>{t("plan.chosenRotation")}</h2>
      {plan.candidate_snapshot?.sequence ? (
        <CandidateCard candidate={plan.candidate_snapshot} rank={1} />
      ) : (
        <p className="muted">{plan.candidate_id}</p>
      )}
      {plan.scenario_id && (
        <p className="muted">
          {t("plan.scenarioRef")}: {plan.scenario_id} ({t("scenario.hypothetical")})
        </p>
      )}

      {profile && (
        <>
          <h2>{t("plan.inputSnapshot")}</h2>
          <div className="card table-scroll">
            <table className="data">
              <tbody>
                <tr>
                  <th scope="row">{t("farm.name")}</th>
                  <td>{profile.name}</td>
                </tr>
                <tr>
                  <th scope="row">{t("farm.location")}</th>
                  <td>
                    {profile.location.latitude}, {profile.location.longitude} (WGS84)
                  </td>
                </tr>
                <tr>
                  <th scope="row">{t("farm.area")}</th>
                  <td>{profile.area_ha} ha</td>
                </tr>
                <tr>
                  <th scope="row">{t("farm.irrigation")}</th>
                  <td>
                    {profile.irrigation_supply_mm_per_season === null
                      ? t("common.unknown")
                      : `${profile.irrigation_supply_mm_per_season} mm`}
                  </td>
                </tr>
                <tr>
                  <th scope="row">{t("farm.priorities")}</th>
                  <td>
                    {t("farm.priorityWater")} {profile.priority_weights.water} · {t("farm.prioritySoil")}{" "}
                    {profile.priority_weights.soil} · {t("farm.priorityClimate")} {profile.priority_weights.climate}
                  </td>
                </tr>
                <tr>
                  <th scope="row">{t("farm.excludedCrops")}</th>
                  <td>{profile.excluded_crop_ids.join(", ") || "—"}</td>
                </tr>
                <tr>
                  <th scope="row">{t("farm.cropHistory")}</th>
                  <td>
                    {profile.crop_history.length === 0
                      ? t("common.unknown")
                      : profile.crop_history
                          .map((h) => `${h.crop_id} (${h.planted_on} → ${h.harvested_on ?? "…"})`)
                          .join("; ")}
                  </td>
                </tr>
                <tr>
                  <th scope="row">{t("farm.soilTests")}</th>
                  <td>
                    {profile.soil_tests.length === 0
                      ? t("common.unknown")
                      : profile.soil_tests.map((s) => `${s.metric} ${s.value} ${s.unit} (${s.sampled_on})`).join("; ")}
                  </td>
                </tr>
                <tr>
                  <th scope="row">{t("rotation.inputVersion")}</th>
                  <td>{plan.input_version}</td>
                </tr>
              </tbody>
            </table>
          </div>
        </>
      )}

      <h2>{t("plan.evidence")}</h2>
      <div className="card">
        <p style={{ marginTop: 0 }}>
          {t("plan.catalogVersion")}: <strong>{snap.catalog_version}</strong> · {t("plan.modelVersion")}:{" "}
          <strong>{snap.model_version}</strong> · {t("common.analysisDate")}:{" "}
          {snap.analysis_created_at ? new Date(snap.analysis_created_at).toLocaleString() : t("common.unknown")}
        </p>
        <SourceBadge sourceRefs={snap.source_refs} dataKind={snap.data_kind} />
        {snap.assumptions.length > 0 && (
          <>
            <h3 style={{ fontSize: "1rem" }}>{t("common.assumptions")}</h3>
            <ul>
              {snap.assumptions.map((a, i) => (
                <li key={i}>{a}</li>
              ))}
            </ul>
          </>
        )}
        {snap.limitations.length > 0 && (
          <>
            <h3 style={{ fontSize: "1rem" }}>{t("common.limitations")}</h3>
            <ul>
              {snap.limitations.map((l, i) => (
                <li key={i}>{l}</li>
              ))}
            </ul>
          </>
        )}
      </div>
    </div>
  );
}
