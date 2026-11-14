/**
 * ObservationsPage — farm overview: summary, chart, per-variable coverage,
 * provenance, missing-data state, and the next step (compare rotations).
 * Owner: Shehani. Data shape: Matheesha's normalized NASA POWER result via
 * Dulanjaya's GET /farms/{id}/observations (end date must be before today, UTC).
 */
import { useCallback, useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { api } from "../api";
import { isAbortError } from "../api/requestGuard";
import { useAppStore } from "../hooks/useAppStore";
import { useLatestRequest } from "../hooks/useLatestRequest";
import { LoadingSpinner } from "../components/ui/LoadingSpinner";
import { ErrorMessage } from "../components/ui/ErrorMessage";
import { SyntheticDataBanner } from "../components/ui/SyntheticDataBanner";
import { SourceBadge } from "../components/ui/SourceBadge";
import { MissingDataPlaceholder } from "../components/ui/MissingDataPlaceholder";
import { ObservationChart } from "../components/observations/ObservationChart";
import {
  OBSERVATION_MIN_DATE,
  defaultObservationRange,
  isValidObservationRange,
  latestAllowedEnd,
  toChartPoints,
} from "../utils/observations";
import { fmtNumber } from "../utils/format";
import type { ObservationSummary } from "../types/api";

export function ObservationsPage() {
  const { t } = useTranslation();
  const farm = useAppStore((s) => s.farm)!;
  const setLatestObservation = useAppStore((s) => s.setLatestObservation);
  const guard = useLatestRequest();

  const [start, setStart] = useState(() => defaultObservationRange().start);
  const [end, setEnd] = useState(() => defaultObservationRange().end);
  const [obs, setObs] = useState<ObservationSummary | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<unknown>(null);
  const rangeInvalid = !isValidObservationRange(start, end);
  const maxEnd = latestAllowedEnd();

  const fetchObs = useCallback(
    (from: string, to: string) => {
      const ticket = guard.next();
      setLoading(true);
      setError(null);
      api
        .getObservations(farm.id, from, to, ticket.signal)
        .then((res) => {
          // Never display a response for another farm.
          if (!ticket.isCurrent() || res.farm_id !== farm.id) return;
          setObs(res);
          setLatestObservation({ farmId: farm.id, observationId: res.observation_id, inputVersion: res.input_version });
        })
        .catch((err) => {
          if (ticket.isCurrent() && !isAbortError(err)) setError(err);
        })
        .finally(() => {
          if (ticket.isCurrent()) setLoading(false);
        });
    },
    [farm.id, guard, setLatestObservation],
  );

  useEffect(() => {
    // Clear data from the previous farm before loading the current farm range.
    // oxlint-disable-next-line react/set-state-in-effect
    setObs(null);
    const r = defaultObservationRange();
    fetchObs(r.start, r.end);
  }, [fetchObs]);

  const s = obs?.summary;
  const c = obs?.coverage;
  const rainDays = c?.precipitation_valid_days ?? c?.available_days;
  const tempDays = c?.temperature_valid_days ?? c?.available_days;
  const points = obs ? toChartPoints(obs) : [];
  // missing_data lists dates per variable; match keys by name since provider keys may differ.
  const missingFor = (re: RegExp) =>
    Object.entries(obs?.missing_data ?? {}).find(([k]) => re.test(k) && !/max|min/i.test(k))?.[1] ?? [];
  const missingRain = missingFor(/prec|rain/i);
  const missingTemp = missingFor(/temp/i);
  const u = t("common.unknown");

  return (
    <div className="page">
      <h1>{t("observations.title")}</h1>

      <form
        className="card row"
        onSubmit={(e) => {
          e.preventDefault();
          if (!rangeInvalid) fetchObs(start, end);
        }}
      >
        <div className="field">
          <label htmlFor="obs-start">{t("observations.startDate")}</label>
          <input
            id="obs-start"
            type="date"
            value={start}
            min={OBSERVATION_MIN_DATE}
            max={end || maxEnd}
            onChange={(e) => setStart(e.target.value)}
          />
        </div>
        <div className="field">
          <label htmlFor="obs-end">{t("observations.endDate")}</label>
          <input
            id="obs-end"
            type="date"
            value={end}
            min={start || OBSERVATION_MIN_DATE}
            max={maxEnd}
            onChange={(e) => setEnd(e.target.value)}
            aria-describedby="obs-end-hint"
          />
        </div>
        <button type="submit" className="btn btn-secondary" disabled={loading || rangeInvalid}>
          {loading ? t("common.loading") : t("observations.load")}
        </button>
        <span id="obs-end-hint" className="muted" style={{ width: "100%" }}>
          {t("observations.rangeHint", { min: OBSERVATION_MIN_DATE, max: maxEnd })}
        </span>
        {rangeInvalid && (
          <span className="field-error" role="alert">
            {t("observations.rangeInvalid", { min: OBSERVATION_MIN_DATE, max: maxEnd })}
          </span>
        )}
      </form>

      {loading && <LoadingSpinner />}
      {!loading && error != null && <ErrorMessage error={error} onRetry={() => fetchObs(start, end)} />}

      {!loading && obs && (
        <>
          <SyntheticDataBanner dataKind={obs.data_kind} limitations={obs.limitations} />

          <div className="card">
            <div className="row" style={{ alignItems: "stretch" }}>
              <div className="notice notice-info" style={{ minWidth: 160, margin: 0 }}>
                <div className="muted">{t("observations.rainfallTotal")}</div>
                <div style={{ fontSize: 22, fontWeight: 700 }}>
                  {s?.rainfall_mm != null ? `${fmtNumber(s.rainfall_mm, u, 1)} mm` : u}
                </div>
                {s?.rainfall_mm == null && s?.rainfall_available_days_mm != null && (
                  <div className="muted" style={{ fontSize: 12 }}>
                    {t("observations.partialRain", { mm: fmtNumber(s.rainfall_available_days_mm, u, 1) })}
                  </div>
                )}
              </div>
              <div className="notice notice-warn" style={{ minWidth: 160, margin: 0 }}>
                <div className="muted">{t("observations.temperatureMean")}</div>
                <div style={{ fontSize: 22, fontWeight: 700 }}>
                  {s?.mean_temperature_c != null ? `${fmtNumber(s.mean_temperature_c, u, 1)} °C` : u}
                </div>
              </div>
            </div>

            <p className="muted">
              {obs.period.start} → {obs.period.end}
              {obs.time_standard ? ` (${obs.time_standard})` : ""}
            </p>
            <ul className="muted" style={{ margin: "0 0 8px" }} aria-label={t("observations.coverage")}>
              <li>
                {t("observations.rainCoverage", { available: rainDays ?? u, expected: c?.expected_days ?? u })}
                {missingRain.length > 0 && ` — ${t("observations.missingDates", { count: missingRain.length })}`}
              </li>
              <li>
                {t("observations.tempCoverage", { available: tempDays ?? u, expected: c?.expected_days ?? u })}
                {missingTemp.length > 0 && ` — ${t("observations.missingDates", { count: missingTemp.length })}`}
              </li>
            </ul>

            {(c?.available_days ?? 0) === 0 && (rainDays ?? 0) === 0 && (tempDays ?? 0) === 0 ? (
              <MissingDataPlaceholder reason={obs.limitations.join(" ")} />
            ) : (
              <>
                {((rainDays ?? 0) < (c?.expected_days ?? 0) || (tempDays ?? 0) < (c?.expected_days ?? 0)) && (
                  <p className="muted">{t("observations.gapsNote")}</p>
                )}
                <ObservationChart timeSeries={points} hasData={points.length > 0} />
              </>
            )}
            <SourceBadge
              sourceRefs={obs.source_refs}
              retrievedAt={obs.retrieved_at}
              spatialResolution={obs.spatial_resolution}
              dataKind={obs.data_kind}
              provider={obs.provider}
              sourceUrl={obs.source_url}
              documentationUrl={obs.documentation_url}
            />
            <p className="muted" style={{ fontSize: 12 }}>
              {t("observations.idNote", { id: obs.observation_id })}
            </p>
          </div>
        </>
      )}

      <Link to={`/farms/${farm.id}/rotations`} className="btn btn-primary">
        {t("observations.nextStep")} →
      </Link>
    </div>
  );
}
